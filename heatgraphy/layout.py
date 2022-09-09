from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec


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
    nrow: int = 1
    ncol: int = 1
    gs: GridSpec = None

    def __init__(self, w=5, h=5, name="main"):
        self.nrow = 1
        self.ncol = 1

        self.crow_ix = 0
        self.ccol_ix = 0

        self.heat_w = w
        self.heat_h = h

        self.h_ratios = [h]
        self.w_ratios = [w]

        self.side_tracker = {"right": [], "left": [], "top": [], "bottom": []}
        self.layout = {name: GridBlock(row=self.crow_ix, col=self.ccol_ix,
                                       side="main", hsize=h, wsize=w)}

    def __repr__(self):
        return f"{self.nrow}*{self.ncol} Grid"

    def _check_name(self, name):
        if self.layout.get(name) is not None:
            raise NameError(f"{name} has been used.")

    def add_ax(self, side, name, size=1):
        if side == "top":
            self.top(name, size=size)
        elif side == "bottom":
            self.bottom(name, size=size)
        elif side == "right":
            self.right(name, size=size)
        elif side == "left":
            self.left(name, size=size)
        else:
            raise ValueError(f"Cannot add axes at {side}")

    def top(self, name, size=1):
        self._check_name(name)
        self.nrow += 1
        self.crow_ix += 1

        for _, gb in self.layout.items():
            gb.row += 1

        self.layout[name] = GridBlock(row=0, col=self.ccol_ix, side="top",
                                      hsize=size, wsize=self.heat_w)
        self.h_ratios = [size, *self.h_ratios]
        self.side_tracker['top'].append(name)

    def top_n(self, names, sizes=None):
        n = len(names)
        for name in names:
            self._check_name(name)

        if sizes is None:
            sizes = [1 for _ in range(n)]
        names = names[::-1]
        sizes = sizes[::-1]

        self.nrow += n
        self.crow_ix += n

        for _, gb in self.layout.items():
            gb.row += n

        for row_i, (name, s) in enumerate(zip(names, sizes)):
            self.layout[name] = GridBlock(row=row_i, col=self.ccol_ix,
                                          side="top",
                                          hsize=s, wsize=self.heat_w)
        self.h_ratios = [*sizes, *self.h_ratios]

    def bottom(self, name, size=1):
        self._check_name(name)
        self.nrow += 1

        self.layout[name] = GridBlock(row=self.nrow - 1, col=self.ccol_ix,
                                      side="bottom",
                                      hsize=size, wsize=self.heat_w)
        self.h_ratios.append(size)
        self.side_tracker['bottom'].append(name)

    def left(self, name, size=1):
        self._check_name(name)
        self.ncol += 1
        self.ccol_ix += 1

        for _, gb in self.layout.items():
            gb.col += 1

        self.layout[name] = GridBlock(row=self.crow_ix, col=0, side="left",
                                      hsize=self.heat_h, wsize=size)
        self.w_ratios = [size, *self.w_ratios]
        self.side_tracker['left'].append(name)

    def right(self, name, size=1):
        self._check_name(name)
        self.ncol += 1

        self.layout[name] = GridBlock(row=self.crow_ix, col=self.ncol - 1,
                                      side="right",
                                      hsize=self.heat_h, wsize=size)
        self.w_ratios.append(size)
        self.side_tracker['right'].append(name)

    def split(self,
              name,
              w_ratios=None,
              h_ratios=None,
              wspace=0.05,
              hspace=0.05,
              mode="placeholder",
              mask_placeholder=True,
              ):
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

    def _split_placeholder(self,
                           name,
                           w_ratios=None,
                           h_ratios=None,
                           wspace=0.05,
                           hspace=0.05,
                           mask_placeholder=True
                           ):
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

    def freeze(self, figure, wspace=0, hspace=0, debug=False):
        gs = GridSpec(self.nrow, self.ncol,
                      figure=figure,
                      wspace=wspace, hspace=hspace,
                      height_ratios=self.h_ratios,
                      width_ratios=self.w_ratios)
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
                        self._set_axis_dir(gb, ax)
                        axes.append(ax)
                        if debug:
                            # If it is placeholder mark it in gray
                            if gb.ax_masks[num] == 0:
                                ax.set_axis_off()
                            else:
                                ax.tick_params(labelbottom=False, labelleft=False)
                                ax.set_xticks([])
                                ax.set_yticks([])
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
                self._set_axis_dir(gb, ax)
                gb.ax = ax
                if debug:
                    ax.tick_params(labelbottom=False, labelleft=False)
                    ax.set_xticks([])
                    ax.set_yticks([])
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

    def plot(self, figure=None):
        if self.gs is None:
            figure = plt.figure()
        self.freeze(figure=figure, debug=True)
