from dataclasses import dataclass, field
from typing import Any

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec


def _interval(size, breakpoints):
    bp = np.sort(np.array(breakpoints)) * size
    bp = np.array([*bp, size])

    start = 0.0
    end = 0.0
    result = []
    for i in bp:
        end = i - start
        start += end
        result.append(end)

    return result


@dataclass
class SubLayout:
    row: int = 1
    col: int = 1
    wspace: float = 0.05
    hspace: float = 0.05
    mode: str = "blank"  # blank or placeholder
    w_ratios: list = field(default=None)
    h_ratios: list = field(default=None)
    ax: Any = field(default=None, repr=False)
    ax_labels: Any = field(default_factory=list)

    def get_canvas_ax(self):
        pass

    def get_placeholder_ax(self):
        pass


@dataclass
class Block:
    row: int
    col: int
    hsize: float
    wsize: float
    is_split: bool = field(default=False)
    sub_layout: SubLayout = field(default_factory=SubLayout)
    ax: Any = field(default=None, repr=False)


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
        self.layout = {name: Block(row=self.crow_ix, col=self.ccol_ix, hsize=h, wsize=w)}

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

        for _, gi in self.layout.items():
            gi.row += 1

        self.layout[name] = Block(row=0, col=self.ccol_ix,
                                  hsize=size, wsize=self.heat_w)
        self.h_ratios = [size, *self.h_ratios]

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

        for _, gi in self.layout.items():
            gi.row += n

        for row_i, (name, s) in enumerate(zip(names, sizes)):
            self.layout[name] = Block(row=row_i, col=self.ccol_ix, hsize=s, wsize=self.heat_w)
        self.h_ratios = [*sizes, *self.h_ratios]

    def bottom(self, name, size=1):
        self._check_name(name)
        self.nrow += 1

        self.layout[name] = Block(row=self.nrow - 1, col=self.ccol_ix,
                                  hsize=size, wsize=self.heat_w)
        self.h_ratios.append(size)

    def left(self, name, size=1):
        self._check_name(name)
        self.ncol += 1
        self.ccol_ix += 1

        for _, gi in self.layout.items():
            gi.col += 1

        self.layout[name] = Block(row=self.crow_ix, col=0,
                                  hsize=self.heat_h, wsize=size)
        self.w_ratios = [size, *self.w_ratios]

    def right(self, name, size=1):
        self._check_name(name)
        self.ncol += 1

        self.layout[name] = Block(row=self.crow_ix, col=self.ncol - 1,
                                  hsize=self.heat_h, wsize=size)
        self.w_ratios.append(size)

    def split(self, name, x=None, y=None, wspace=0.05, hspace=0.05, mode="blank"):

        if (wspace >= 1.) & (wspace < 0):
            raise ValueError("wspace should be in (0, 1)")

        if (hspace >= 1.) & (hspace < 0):
            raise ValueError("hspace should be in (0, 1)")

        if mode == "blank":
            self._split_blank(name, x=x, y=y, wspace=wspace, hspace=hspace)
        elif mode == "placeholder":
            self._split_placeholder(name, x=x, y=y, wspace=wspace, hspace=hspace)
        else:
            raise ValueError(f"Don't know mode='{mode}', "
                             f"options are (blank or placeholder)")

    def _split_placeholder(self, name, x=None, y=None, wspace=0.05, hspace=0.05):
        # TODO: check wspace and hspace range in (0, 1)

        split_x = x is not None
        split_y = y is not None
        if split_x & split_y:
            raise ValueError("Should only split in one direction, "
                             "you split on both x and y.")

        gi = self.layout[name]
        gi.is_split = True
        sub_layout = gi.sub_layout
        sub_layout.wspace = 0
        sub_layout.hspace = 0

        if split_x:
            if sub_layout.col != 1:
                raise ValueError("Can only be split once")
            sub_layout.col = 2 * len(x) + 1
            inject_x = []
            for pt in x:
                inject_x.append(pt - wspace / 2.)
                inject_x.append(pt + wspace / 2.)
            sub_layout.w_ratios = _interval(1., inject_x)

    def _split_blank(self, name, x=None, y=None, wspace=0.05, hspace=0.05):
        gi = self.layout[name]
        gi.is_split = True
        sub_layout = gi.sub_layout
        sub_layout.wspace = wspace
        sub_layout.hspace = hspace

        if x is not None:
            if sub_layout.col != 1:
                raise ValueError("Can only be split once")
            sub_layout.col += len(x)
            sub_layout.w_ratios = _interval(gi.wsize, x)

        if y is not None:
            if sub_layout.row != 1:
                raise ValueError("Can only be split once")
            sub_layout.row += len(y)
            sub_layout.h_ratios = _interval(gi.hsize, y)

    def freeze(self, figure, wspace=0, hspace=0, debug=False):
        gs = GridSpec(self.nrow, self.ncol,
                      figure=figure,
                      wspace=wspace, hspace=hspace,
                      height_ratios=self.h_ratios,
                      width_ratios=self.w_ratios)
        self.gs = gs

        for block, gi in self.layout.items():
            ax_loc = gs[gi.row, gi.col]
            if gi.is_split:
                sub_layout = gi.sub_layout
                print(sub_layout)

                new_gs = GridSpecFromSubplotSpec(sub_layout.row, sub_layout.col, ax_loc,
                                                 wspace=sub_layout.wspace,
                                                 hspace=sub_layout.hspace,
                                                 width_ratios=sub_layout.w_ratios,
                                                 height_ratios=sub_layout.h_ratios)
                axes = []
                for ix in range(sub_layout.row):
                    for iy in range(sub_layout.col):
                        ax = figure.add_subplot(new_gs[ix, iy])
                        axes.append(ax)
                        if debug:
                            ax.tick_params(labelbottom=False, labelleft=False)
                            ax.set_xticks([])
                            ax.set_yticks([])
                            # ax.text(0.5, 0.5, f"{block} {ix}-{iy}", va="center", ha="center")
                gi.ax = axes

            else:
                ax = figure.add_subplot(ax_loc)
                gi.ax = ax
                if debug:
                    ax.tick_params(labelbottom=False, labelleft=False)
                    ax.set_xticks([])
                    ax.set_yticks([])
                    # ax.text(0.5, 0.5, block, va="center", ha="center")

    def get_ax(self, name) -> Axes:
        return self.layout[name].ax

    def plot(self):
        if self.gs is None:
            figure = plt.figure(constrained_layout=True)
            self.freeze(figure=figure, debug=True)
