from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable, Dict, List
from uuid import uuid4

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure, figaspect
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from mpl_toolkits.axes_grid1 import make_axes_locatable

import logging

from .utils import pairwise

log = logging.getLogger("heatgraphy")


@dataclass
class SubLayout:
    row: int = 1
    col: int = 1
    wspace: float = 0.05
    hspace: float = 0.05
    mode: str = "blank"  # blank or placeholder
    w_ratios: list = field(default=None)
    h_ratios: list = field(default=None)
    mask_placeholder: bool = True
    # ax: Any = field(default=None, repr=False)


@dataclass
class BaseCell:
    row: int
    col: int
    height: float
    width: float
    side: str  # For debug purpose
    attach_main: str  # the main canvas it attaches to


@dataclass
class Pad(BaseCell):
    pass


@dataclass
class GridCell(BaseCell):
    name: str
    # row: int  # left-most
    # col: int  # top-most
    # height: float
    # width: float
    # attach_main: str
    # side: str
    row_span: int = 1
    col_span: int = 1
    is_split: bool = False
    sub_layout: SubLayout = field(default_factory=SubLayout)
    ax: Any = field(default=None, repr=False)
    ax_masks: Any = field(default_factory=list)
    render_size: float = None

    def get_canvas_ax(self):
        if self.ax is None:
            return None
        if isinstance(self.ax, Axes):
            return self.ax
        return self.ax[self.ax_masks]

    def get_placeholder_ax(self):
        if self.ax is None:
            return None
        return self.ax[~self.ax_masks]

    def create_subplotspec(self, gs: GridSpec):
        row_slice = slice(self.row, self.row + self.row_span)
        col_slice = slice(self.col, self.col + self.col_span)
        return gs[row_slice, col_slice]


class CrossGrid:
    """
    A grid layout system that can be expanded at four direction

    - Everything is drawn within axes
    - No ticks, no ticklabels, no label, no title etc.
    - Elements outside axes will make the layout incorrect.

    Use the `enlarge` parameter to control figure size when rendering

    """
    nrow: int = 1
    ncol: int = 1
    gs: GridSpec = None

    def __init__(self, w=5, h=5, name=None):
        if name is None:
            # add uuid to name to avoid collide
            name = f"main-{uuid4().hex}"

        # track the index of center axes
        self.crow_ix = 0
        self.ccol_ix = 0

        self.main_w = w
        self.main_h = h
        self.main_name = name

        self.side_ratios = {"right": [], "left": [], "top": [], "bottom": []}
        self.side_tracker = {"right": [], "left": [], "top": [], "bottom": []}
        self.main_cell = GridCell(name=self.main_name,
                                  row=self.crow_ix, col=self.ccol_ix,
                                  side="main", height=h, width=w,
                                  attach_main=self.main_name)
        self.layout = {name: self.main_cell}
        self._pad = []
        self._adjust_render_size = []

    def __repr__(self):
        return f"{self.nrow}*{self.ncol} Grid"

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        pass

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        pass

    def set_side_tracker(self, **kws):
        for k, v in kws.items():
            self.side_tracker[k] = v

    def set_side_ratios(self, **kws):
        for k, v in kws.items():
            self.side_ratios[k] = v

    def get_gridlines(self, other, side):
        ratios1 = self.side_ratios[side]
        ratios2 = other.side_ratios[side]

        g1 = np.cumsum(ratios1)
        g2 = np.cumsum(ratios2)

        gridlines = np.concatenate((g1, g2))
        gridlines = np.sort(np.unique(gridlines))
        ratios = [gridlines[0]] + [i2 - i1 for i1, i2 in pairwise(gridlines)]

        n_grid = len(gridlines)
        # how much to move for current grid
        offset_current = n_grid - len(ratios1)
        # how much to move for other grid
        offset_other = n_grid - len(ratios2)

        return gridlines, ratios, offset_current, offset_other

    @staticmethod
    def group_cells(cells: List[GridCell | Pad]):
        container = {}
        for cell in cells:
            name = cell.attach_main
            if container.get(name) is None:
                container[name] = [cell]
            else:
                container[name].append(cell)
        return container

    @staticmethod
    def sort_cells(cells: List[GridCell | Pad], by="row", ascending=True):
        if by == "row":
            key = lambda cell: cell.row
        else:
            key = lambda cell: cell.col
        return sorted(cells, key=key, reverse=not ascending)

    def set_id_span(self, cells: List[GridCell | Pad], gridlines,
                    side="top", start_ix=0):
        side_v = side in ["top", "bottom"]
        side_first = side in ["top", "left"]
        attr = "height" if side_v else "width"
        by = "row" if side_v else "col"
        ascending = not side_first

        group_cells = self.group_cells(cells)

        for group, cells in group_cells.items():
            sorted_cells = self.sort_cells(cells, by=by, ascending=ascending)
            segments = [getattr(cell, attr) for cell in sorted_cells]
            it = enumerate(gridlines)
            pre_add = 0
            ixs = []
            for s in segments:
                while True:
                    ix, g = next(it)
                    if (s + pre_add) == g:
                        ixs.append(ix)
                        pre_add += s
                        break
            spans = np.array(
                [i2 - i1 for ix, (i1, i2) in enumerate(pairwise(ixs))])
            if side_first:
                ordered_ixs = len(gridlines) - np.array(ixs) - 1
            else:
                ordered_ixs = start_ix + 1 + np.array(ixs)[1::] - (spans - 1)
                ordered_ixs = [start_ix + 1, *ordered_ixs]
            spans = [ixs[0] + 1, *spans]
            for cell, ix, span in zip(cells, ordered_ixs, spans):
                if side_v:
                    cell.row = ix
                    cell.row_span = span
                else:
                    cell.col = ix
                    cell.col_span = span

    def _check_duplicated_names(self, other: CrossGrid):
        # check for unique name for each heatmap
        current_names = set(self.layout.keys())
        other_names = set(other.layout.keys())
        duplicated_names = set(current_names).intersection(other_names)
        if len(duplicated_names) > 0:
            msg = f"Found exist axes with same name {duplicated_names} " \
                  f"in '{self.main_name}'."
            raise NameError(msg)

    @staticmethod
    def _adjust_head(offset_current, offset_other, current_cells,
                     other_cells, other_main, append="v"):
        attr = "col" if append == "v" else "row"
        if offset_current > 0:
            for _, cells in current_cells.items():
                for cell in cells:
                    setattr(cell, attr, getattr(cell, attr) + offset_current)
        if offset_other > 0:
            for _, cells in other_cells.items():
                for cell in cells:
                    setattr(cell, attr, getattr(cell, attr) + offset_other)
            setattr(other_main, attr, getattr(other_main, attr) + offset_other)

    @staticmethod
    def _adjust_tail(offset_current, offset_other, current_cells,
                     other_cells, append="v"):
        attr, side = ("col", "right") if append == "v" else ("row", "bottom")
        if offset_current > 0:
            for cell in current_cells.get(side):
                setattr(cell, attr, getattr(cell, attr) + offset_current)
        if offset_other > 0:
            for cell in other_cells.get(side):
                setattr(cell, attr, getattr(cell, attr) + offset_other)

    def _setup_new_grid(self, other_main):
        self.nrow = len(self.side_ratios['top']) + len(
            self.side_ratios['bottom']) + 1
        self.ncol = len(self.side_ratios['left']) + len(
            self.side_ratios['right']) + 1

        total_cells = (self.side_tracker['top'] +
                       self.side_tracker['bottom'] +
                       self.side_tracker['left'] +
                       self.side_tracker['right'])

        for cell in total_cells:
            if isinstance(cell, GridCell):
                self.layout[cell.name] = cell
                if cell.render_size is not None:
                    self._adjust_render_size.append(cell)
            elif isinstance(cell, Pad):
                self._pad.append(cell)
        self.layout[other_main.name] = other_main

    def append_horizontal(self, other: CrossGrid) -> CrossGrid:

        self._check_duplicated_names(other)
        assert self.main_h == other.main_h

        # return as new grid
        new_grid = CrossGrid(self.main_w,
                             self.main_h,
                             name=self.main_name)

        horizontal_offset = self.ncol
        current_cells = deepcopy(self.side_tracker)
        other_cells = deepcopy(other.side_tracker)
        other_main = deepcopy(other.main_cell)
        # move other cells right
        for _, cells in other_cells.items():
            for cell in cells:
                cell.col += horizontal_offset
        other_main.col += horizontal_offset

        # handle top
        gridlines, top_ratios, voffset_current, voffset_other = \
            self.get_gridlines(other, "top")

        self._adjust_head(voffset_current, voffset_other, current_cells,
                          other_cells, other_main, "h")

        # move main cell
        new_grid.main_cell.row = len(top_ratios)
        new_grid.main_cell.col = len(self.side_tracker['left'])

        top_cells = other_cells['top'] + current_cells['top']
        self.set_id_span(top_cells, gridlines, side="top")

        # handle bottom
        gridlines, bottom_ratios, voffset_current, voffset_other = \
            self.get_gridlines(other, "bottom")

        # increase the row count for only bottom cell
        self._adjust_tail(voffset_current, voffset_other, current_cells,
                          other_cells, "h")

        bottom_cells = other_cells['bottom'] + current_cells['bottom']
        self.set_id_span(bottom_cells, gridlines, side="bottom",
                         start_ix=len(top_ratios))

        # setup new_grid
        left_cells = current_cells['left']
        right_cells = (current_cells['right'] + other_cells['left'] +
                       [other_main] + other_cells['right'])

        left_ratios = deepcopy(self.side_ratios['left'])
        right_ratios = (self.side_ratios['right'] + other.side_ratios['left'] +
                        [other.main_w] + other.side_ratios['right'])

        new_grid.set_side_tracker(top=top_cells, bottom=bottom_cells,
                                  left=left_cells, right=right_cells)
        new_grid.set_side_ratios(top=top_ratios, bottom=bottom_ratios,
                                 left=left_ratios, right=right_ratios)
        new_grid._setup_new_grid(other_main)
        return new_grid

    def append_vertical(self, other: CrossGrid) -> CrossGrid:

        self._check_duplicated_names(other)
        assert self.main_w == other.main_w

        # return as new grid
        new_grid = CrossGrid(self.main_w,
                             self.main_h,
                             name=self.main_name)

        vertical_offset = self.nrow
        current_cells = deepcopy(self.side_tracker)
        other_cells = deepcopy(other.side_tracker)
        other_main = deepcopy(other.main_cell)
        # move other cells down
        for _, cells in other_cells.items():
            for cell in cells:
                cell.row += vertical_offset
        other_main.row += vertical_offset

        # handle left
        gridlines, left_ratios, hoffset_current, hoffset_other = \
            self.get_gridlines(other, "left")

        self._adjust_head(hoffset_current, hoffset_other, current_cells,
                          other_cells, other_main, "v")

        # move main cell
        new_grid.main_cell.col = len(left_ratios)
        new_grid.main_cell.row = len(self.side_tracker['top'])

        left_cells = other_cells['left'] + current_cells['left']
        self.set_id_span(left_cells, gridlines, side="left")

        # handle right
        gridlines, right_ratios, hoffset_current, hoffset_other = \
            self.get_gridlines(other, "right")

        # increase the col count for only right cell
        self._adjust_tail(hoffset_current, hoffset_other, current_cells,
                          other_cells, "v")

        right_cells = other_cells['right'] + current_cells['right']
        self.set_id_span(right_cells, gridlines, side="right",
                         start_ix=len(left_ratios))

        # setup new_grid
        top_cells = current_cells['top']
        bottom_cells = (current_cells['bottom'] + other_cells['top'] +
                        [other_main] + other_cells['bottom'])

        top_ratios = deepcopy(self.side_ratios['top'])
        bottom_ratios = (
                    self.side_ratios['bottom'] + other.side_ratios['top'] +
                    [other.main_w] + other.side_ratios['bottom'])

        new_grid.set_side_tracker(top=top_cells, bottom=bottom_cells,
                                  left=left_cells, right=right_cells)
        new_grid.set_side_ratios(top=top_ratios, bottom=bottom_ratios,
                                 left=left_ratios, right=right_ratios)
        new_grid._setup_new_grid(other_main)
        return new_grid

    def _check_name(self, name):
        if self.layout.get(name) is not None:
            raise NameError(f"Axes with name '{name}' already exist.")

    def add_ax(self, side, name, size=1, pad=0.):
        if side == "top":
            self.top(name, size=size, pad=pad)
        elif side == "bottom":
            self.bottom(name, size=size, pad=pad)
        elif side == "right":
            self.right(name, size=size, pad=pad)
        elif side == "left":
            self.left(name, size=size, pad=pad)
        else:
            raise ValueError(f"Cannot add axes at {side}")

    def top(self, name, size=1., pad=0.):
        self._check_name(name)

        gain = 2 if pad > 0 else 1
        self.nrow += gain
        self.crow_ix += gain
        for _, gb in self.layout.items():
            gb.row += gain
        for pb in self._pad:
            pb.row += gain

        if pad > 0:
            self.side_ratios['top'].append(pad)
            pad_block = Pad(row=1, col=self.ccol_ix, side="top",
                            height=pad, width=self.main_w,
                            attach_main=self.main_name)
            self._pad.append(pad_block)
            self.side_tracker['top'].append(pad_block)

        gb = GridCell(name=name, row=0, col=self.ccol_ix, side="top",
                      height=size, width=self.main_w,
                      attach_main=self.main_name)
        self.layout[name] = gb
        self.side_tracker['top'].append(gb)
        self.side_ratios['top'].append(size)

    def bottom(self, name, size=1., pad=0.):
        self._check_name(name)

        gain = 2 if pad > 0 else 1
        self.nrow += gain

        if pad > 0:
            self.side_ratios['bottom'].append(pad)

            pad_block = Pad(row=self.nrow - 2, col=self.ccol_ix, side="bottom",
                            height=pad, width=self.main_w,
                            attach_main=self.main_name)
            self._pad.append(pad_block)
            self.side_tracker['bottom'].append(pad_block)

        gb = GridCell(name=name, row=self.nrow - 1, col=self.ccol_ix,
                      side="bottom", height=size, width=self.main_w,
                      attach_main=self.main_name)
        self.layout[name] = gb
        self.side_tracker['bottom'].append(gb)
        self.side_ratios['bottom'].append(size)

    def left(self, name, size=1., pad=0.):
        self._check_name(name)

        gain = 2 if pad > 0 else 1
        self.ncol += gain
        self.ccol_ix += gain
        for _, gb in self.layout.items():
            gb.col += gain
        for pb in self._pad:
            pb.col += gain

        if pad > 0:
            self.side_ratios['left'].append(pad)

            pad_block = Pad(row=self.crow_ix, col=1, side="left",
                            height=self.main_h, width=size,
                            attach_main=self.main_name)
            self._pad.append(pad_block)
            self.side_tracker['left'].append(pad_block)

        gb = GridCell(name=name, row=self.crow_ix, col=0, side="left",
                      height=self.main_h, width=size,
                      attach_main=self.main_name)
        self.layout[name] = gb
        self.side_tracker['left'].append(gb)
        self.side_ratios['left'].append(size)

    def right(self, name, size=1., pad=0.):
        self._check_name(name)

        gain = 2 if pad > 0 else 1
        self.ncol += gain

        if pad > 0:
            self.side_ratios['right'].append(pad)

            pad_block = Pad(row=self.crow_ix, col=self.ncol - 2, side="right",
                            height=self.main_h, width=size,
                            attach_main=self.main_name)
            self._pad.append(pad_block)
            self.side_tracker["right"].append(pad_block)

        gb = GridCell(name=name, row=self.crow_ix, col=self.ncol - 1,
                      side="right", height=self.main_h, width=size,
                      attach_main=self.main_name)
        self.layout[name] = gb
        self.side_tracker['right'].append(gb)
        self.side_ratios['right'].append(size)

    def split(self, name, w_ratios=None, h_ratios=None,
              wspace=0.05, hspace=0.05, mode="placeholder"):
        """

        Parameters
        ----------
        name :
        w_ratios : array
            The length of each chunk, the sum the array should be 1
        h_ratios
        wspace : float or array
            The horizontal space between each axes
        hspace
        mode : {'blank', 'placeholder'}
        mask_placeholder

        Returns
        -------

        """
        if w_ratios is not None:
            w_ratios = np.asarray(w_ratios)
            w_ratios = w_ratios / np.sum(w_ratios)

        if h_ratios is not None:
            h_ratios = np.asarray(h_ratios)
            h_ratios = h_ratios / np.sum(h_ratios)

        if mode == "blank":
            self._split_blank(name, w_ratios=w_ratios, h_ratios=h_ratios,
                              wspace=wspace, hspace=hspace)
        elif mode == "placeholder":
            self._split_placeholder(name, w_ratios=w_ratios, h_ratios=h_ratios,
                                    wspace=wspace, hspace=hspace)
        else:
            raise ValueError(f"Don't know mode='{mode}', "
                             f"options are (blank or placeholder)")

    def _split_placeholder(self, name, w_ratios=None, h_ratios=None,
                           wspace=0.05, hspace=0.05, mask_placeholder=True):
        gb = self.layout[name]
        gb.is_split = True
        sub_layout = gb.sub_layout
        sub_layout.wspace = 0
        sub_layout.hspace = 0
        sub_layout.mode = "placeholder"
        sub_layout.mask_placeholder = mask_placeholder

        if w_ratios is not None:
            if sub_layout.col != 1:
                raise ValueError("Can only be split once")
            sub_layout.col = 2 * len(w_ratios) - 1
            sub_layout.w_ratios = self._inject_placeholder(w_ratios, wspace)

        if h_ratios is not None:
            if sub_layout.row != 1:
                raise ValueError("Can only be split once")
            sub_layout.row = 2 * len(h_ratios) - 1
            sub_layout.h_ratios = self._inject_placeholder(h_ratios, hspace)

        # create a binary mask to label
        # which is canvas ax (1) which is placeholder (0)
        masks = np.ones((sub_layout.row, sub_layout.col))

        for loc in np.arange(1, sub_layout.row, step=2):
            masks[loc, :] = 0
        for loc in np.arange(1, sub_layout.col, step=2):
            masks[:, loc] = 0
        gb.ax_masks = masks.flatten().astype(bool)

    @staticmethod
    def _inject_placeholder(ratios, space):

        ratios = np.asarray(ratios)
        count = len(ratios)
        if not isinstance(space, Iterable):
            space = [space for _ in range(count - 1)]

        canvas_size = 1 - np.sum(space)
        ratios = ratios * canvas_size

        inject = []
        for ix, i in enumerate(ratios):
            inject.append(i)
            if ix != count - 1:
                inject.append(space[ix])

        return inject

    def _split_blank(self, name,
                     w_ratios=None,
                     h_ratios=None,
                     wspace=0.05,
                     hspace=0.05,
                     ):
        gb = self.layout[name]
        gb.is_split = True
        sub_layout = gb.sub_layout
        sub_layout.wspace = wspace
        sub_layout.hspace = hspace
        sub_layout.mode = "blank"

        if w_ratios is not None:
            if sub_layout.col != 1:
                raise ValueError("Can only be split once")
            sub_layout.col += len(w_ratios) - 1
            sub_layout.w_ratios = w_ratios

        if h_ratios is not None:
            if sub_layout.row != 1:
                raise ValueError("Can only be split once")
            sub_layout.row += len(h_ratios) - 1
            sub_layout.h_ratios = h_ratios
        gb.ax_masks = np.ones((sub_layout.row, sub_layout.col),
                              dtype=bool).flatten()

    def _adjust_ratios(self, figure, aspect=None):
        pass

    def freeze(self, figure,
               debug=False, aspect: float = None, enlarge=1.1):

        h_ratios = self.get_height_ratios()
        w_ratios = self.get_width_ratios()

        offset_w = []
        offset_w_gb = []
        offset_h = []
        offset_h_gb = []

        for gb in self._adjust_render_size:
            if gb.side in ["top", "bottom"]:
                h_ratios[gb.row] = 0
                offset_h.append(gb.render_size)
                offset_h_gb.append(gb)
            else:
                w_ratios[gb.col] = 0
                offset_w.append(gb.render_size)
                offset_w_gb.append(gb)

        offset_w_sum = np.sum(offset_w)
        offset_h_sum = np.sum(offset_h)

        if aspect is None:
            fig_w, fig_h = figure.get_size_inches()

            # ensure space for other axes
            if offset_w_sum > fig_w:
                fig_w += 5
            if offset_h_sum > fig_h:
                fig_h += 5
            fig_w *= enlarge
            fig_h *= enlarge

            h_ratios = h_ratios / np.sum(h_ratios) * (fig_h - offset_h_sum)
            w_ratios = w_ratios / np.sum(w_ratios) * (fig_w - offset_w_sum)

            for gb, offset in zip(offset_h_gb, offset_h):
                h_ratios[gb.row] = offset
            for gb, offset in zip(offset_w_gb, offset_w):
                w_ratios[gb.col] = offset

        else:
            h_ratios *= aspect
            sum_w = np.sum(w_ratios)
            sum_h = np.sum(h_ratios)
            fig_w, fig_h = figaspect(sum_h / sum_w) * enlarge

            h_ratios = h_ratios / np.sum(h_ratios) * fig_h
            w_ratios = w_ratios / np.sum(w_ratios) * fig_w

            fig_w += offset_w_sum
            fig_h += offset_h_sum

            for gb, offset in zip(offset_h_gb, offset_h):
                h_ratios[gb.row] = offset
            for gb, offset in zip(offset_w_gb, offset_w):
                w_ratios[gb.col] = offset

        figure.set_size_inches(fig_w, fig_h)
        # print(f"Setting figure size: {fig_w}, {fig_h}")
        # print(f"width ratios: {w_ratios}")
        # print(f"height ratios: {h_ratios}")

        gs = GridSpec(self.nrow, self.ncol,
                      figure=figure,
                      wspace=0, hspace=0,
                      height_ratios=h_ratios,
                      width_ratios=w_ratios)
        self.gs = gs

        for block, gb in self.layout.items():
            ax_loc = gb.create_subplotspec(gs)
            if gb.is_split:
                sub_layout = gb.sub_layout

                new_gs = GridSpecFromSubplotSpec(
                    sub_layout.row,
                    sub_layout.col,
                    ax_loc,
                    wspace=sub_layout.wspace,
                    hspace=sub_layout.hspace,
                    width_ratios=sub_layout.w_ratios,
                    height_ratios=sub_layout.h_ratios)
                axes = []

                num = 0
                for ix in range(sub_layout.row):
                    for iy in range(sub_layout.col):

                        ax = figure.add_subplot(new_gs[ix, iy])
                        close_ticks(ax)
                        axes.append(ax)
                        if debug:
                            # If it is placeholder mark it in gray
                            if gb.ax_masks[num] == 0:
                                ax.set_axis_off()
                            else:
                                rotation = 0
                                if gb.side == "left":
                                    rotation = 90
                                elif gb.side == "right":
                                    rotation = -90
                                ax.text(0.5, 0.5, f"{block} ({ix}-{iy})",
                                        va="center", ha="center",
                                        rotation=rotation, fontsize=6,
                                        )

                        num += 1
                gb.ax = np.array(axes)
                if sub_layout.mask_placeholder:
                    for pax in gb.get_placeholder_ax():
                        pax.set_axis_off()

            else:
                ax = figure.add_subplot(ax_loc)
                close_ticks(ax)
                gb.ax = ax
                if debug:
                    rotation = 0
                    if gb.side == "left":
                        rotation = 90
                    elif gb.side == "right":
                        rotation = -90
                    ax.text(0.5, 0.5, block, fontsize=6,
                            va="center", ha="center",
                            rotation=rotation)

    def get_height_ratios(self):
        top_h = self.side_ratios['top'][::-1]
        bottom_h = self.side_ratios['bottom']
        main_h = self.main_h
        return np.array([*top_h, main_h, *bottom_h])

    def get_width_ratios(self):
        left_w = self.side_ratios['left'][::-1]
        right_w = self.side_ratios['right']
        main_w = self.main_w
        return np.array([*left_w, main_w, *right_w])

    def get_ax(self, name) -> Axes:
        gb = self.layout[name]
        return gb.ax

    def get_canvas_ax(self, name) -> Axes:
        return self.layout[name].get_canvas_ax()

    def get_main_ax(self):
        return self.get_canvas_ax(self.main_name)

    def plot(self, figure=None, **kwargs):
        if self.gs is None:
            figure = plt.figure()
        self.freeze(figure=figure, debug=True, **kwargs)

    def set_render_size_inches(self, name, size):
        gb = self.layout[name]
        gb.render_size = size
        self._adjust_render_size.append(gb)

    @property
    def name(self):
        return self.main_name


def close_ticks(ax):
    ax.tick_params(bottom=False, top=False, left=False, right=False,
                   labelbottom=False, labeltop=False,
                   labelleft=False, labelright=False,
                   )

# class Grid:
#
#     def __init__(self, figure: Figure = None, aspect="auto", name="main"):
#         if figure is None:
#             figure = plt.figure()
#         else:
#             figure.clear()
#         ax = Axes(figure, (0, 0, 1, 1), label=name)
#         ax.set_aspect(aspect)
#         figure.add_axes(ax)
#         self._main = ax
#         self._divider = make_axes_locatable(ax)
#         self._ax_mapper = {name: ax}
#
#     def add(self, name, side, size=1., pad=0, ):
#         ax = self._divider.append_axes(side, size=size,
#                                        pad=pad, label=name)
#         self._ax_mapper[name] = ax
#
#     def set_main_ax(self, name):
#         self._divider = make_axes_locatable(self._ax_mapper[name])
#
#     def __add__(self, other):
#         """Define behavior that horizontal appends two grid"""
#         pass
#
#     def __truediv__(self, other):
#         """Define behavior that vertical appends two grid"""
#         pass
