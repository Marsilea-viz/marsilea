from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure, figaspect
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from mpl_toolkits.axes_grid1 import make_axes_locatable

import logging

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
class GridBlock:
    row: int
    col: int
    hsize: float
    wsize: float
    side: str
    is_split: bool = field(default=False)
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


class Grid:
    """
    A grid layout system

    - Everything is drawn within axes
    - No ticks, no ticklabels, no label, no title etc.
    - Elements outside axes will make the layout incorrect.

    Use the `enlarge` parameter to control figure size when rendering

    """
    nrow: int = 1
    ncol: int = 1
    gs: GridSpec = None

    def __init__(self, w=5, h=5, name="main", aspect="auto"):
        self._adjust_render_size = []
        self.nrow = 1
        self.ncol = 1
        if aspect == "auto":
            self.aspect = None
        elif aspect == "equal":
            self.aspect = 1
        else:
            self.aspect = aspect

        self.crow_ix = 0
        self.ccol_ix = 0

        self.main_w = w
        self.main_h = h
        self.main_name = name

        self.h_ratios = [h]
        self.w_ratios = [w]

        self.side_tracker = {"right": [], "left": [], "top": [], "bottom": []}
        self.layout = {name: GridBlock(row=self.crow_ix, col=self.ccol_ix,
                                       side="main", hsize=h, wsize=w)}

    def __repr__(self):
        return f"{self.nrow}*{self.ncol} Grid"

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        pass

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        pass

    def append_horizontal(self):
        pass

    def append_vertical(self):
        pass

    def _check_name(self, name):
        if self.layout.get(name) is not None:
            raise NameError(f"{name} has been used.")

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
        ratios_append = [size, pad] if pad > 0 else [size]

        self.nrow += gain
        self.crow_ix += gain

        for _, gb in self.layout.items():
            gb.row += gain

        self.layout[name] = GridBlock(row=0, col=self.ccol_ix, side="top",
                                      hsize=size, wsize=self.main_w)
        self.h_ratios = [*ratios_append, *self.h_ratios]
        self.side_tracker['top'].append(name)

    def bottom(self, name, size=1., pad=0.):
        self._check_name(name)
        gain = 2 if pad > 0 else 1
        ratios_append = [pad, size] if pad > 0 else [size]

        self.nrow += gain

        self.layout[name] = GridBlock(row=self.nrow - 1, col=self.ccol_ix,
                                      side="bottom",
                                      hsize=size, wsize=self.main_w)
        self.h_ratios = [*self.h_ratios, *ratios_append]
        self.side_tracker['bottom'].append(name)

    def left(self, name, size=1., pad=0.):
        self._check_name(name)
        gain = 2 if pad > 0 else 1
        ratios_append = [size, pad] if pad > 0 else [size]

        self.ncol += gain
        self.ccol_ix += gain

        for _, gb in self.layout.items():
            gb.col += gain

        self.layout[name] = GridBlock(row=self.crow_ix, col=0, side="left",
                                      hsize=self.main_h, wsize=size)
        self.w_ratios = [*ratios_append, *self.w_ratios]
        self.side_tracker['left'].append(name)

    def right(self, name, size=1., pad=0.):
        self._check_name(name)
        gain = 2 if pad > 0 else 1
        ratios_append = [pad, size] if pad > 0 else [size]

        self.ncol += gain

        self.layout[name] = GridBlock(row=self.crow_ix, col=self.ncol - 1,
                                      side="right",
                                      hsize=self.main_h, wsize=size)
        self.w_ratios = [*self.w_ratios, *ratios_append]
        self.side_tracker['right'].append(name)

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

        h_ratios = np.asarray(self.h_ratios)
        w_ratios = np.asarray(self.w_ratios)

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
            ax_loc = gs[gb.row, gb.col]
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
                                        rotation=rotation
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
                    ax.text(0.5, 0.5, block,
                            va="center", ha="center",
                            rotation=rotation)

    @staticmethod
    def _set_axis_dir(gi, ax):
        if gi.side == "left":
            ax.invert_xaxis()
        if gi.side == "bottom":
            ax.invert_yaxis()

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


def close_ticks(ax):
    ax.tick_params(bottom=False, top=False, left=False, right=False,
                   labelbottom=False, labeltop=False,
                   labelleft=False, labelright=False,
                   )


class GridLayout:

    def __init__(self, figure: Figure = None, aspect="auto", name="main"):
        if figure is None:
            figure = plt.figure()
        else:
            figure.clear()
        ax = Axes(figure, (0, 0, 1, 1), label=name)
        ax.set_aspect(aspect)
        figure.add_axes(ax)
        self._main = ax
        self._divider = make_axes_locatable(ax)
        self._ax_mapper = {name: ax}

    def add(self, name, side, size=1., pad=0, ):
        ax = self._divider.append_axes(side, size=size,
                                       pad=pad, label=name)
        self._ax_mapper[name] = ax

    def set_main_ax(self, name):
        self._divider = make_axes_locatable(self._ax_mapper[name])

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        pass

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        pass
