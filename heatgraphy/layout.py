from dataclasses import dataclass, field
from typing import Any

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec


def _interval(size, breakpoints):
    bp = np.sort(np.array(breakpoints)) * size
    bp = np.array([*bp, size])

    start = 0
    end = 0
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
    w_ratios: list = field(default=None)
    h_ratios: list = field(default=None)
    ax: Any = field(default=None, repr=False)


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
        self.index_mapper = {name: Block(row=self.crow_ix, col=self.ccol_ix, hsize=h, wsize=w)}

    def __repr__(self):
        return f"{self.nrow}*{self.ncol} Grid"

    def _check_name(self, name):
        if self.index_mapper.get(name) is not None:
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

        for _, gi in self.index_mapper.items():
            gi.row += 1

        self.index_mapper[name] = Block(row=0, col=self.ccol_ix,
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

        for _, gi in self.index_mapper.items():
            gi.row += n

        for row_i, (name, s) in enumerate(zip(names, sizes)):
            self.index_mapper[name] = Block(row=row_i, col=self.ccol_ix, hsize=s, wsize=self.heat_w)
        self.h_ratios = [*sizes, *self.h_ratios]

    def bottom(self, name, size=1):
        self._check_name(name)
        self.nrow += 1

        self.index_mapper[name] = Block(row=self.nrow - 1, col=self.ccol_ix,
                                        hsize=size, wsize=self.heat_w)
        self.h_ratios.append(size)

    def left(self, name, size=1):
        self._check_name(name)
        self.ncol += 1
        self.ccol_ix += 1

        for _, gi in self.index_mapper.items():
            gi.col += 1

        self.index_mapper[name] = Block(row=self.crow_ix, col=0,
                                        hsize=self.heat_h, wsize=size)
        self.w_ratios = [size, *self.w_ratios]

    def right(self, name, size=1):
        self._check_name(name)
        self.ncol += 1

        self.index_mapper[name] = Block(row=self.crow_ix, col=self.ncol - 1,
                                        hsize=self.heat_h, wsize=size)
        self.w_ratios.append(size)

    def split(self, name, x=None, y=None, wspace=0.05, hspace=0.05):
        gi = self.index_mapper[name]
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

        for block, gi in self.index_mapper.items():
            ax_loc = gs[gi.row, gi.col]
            if gi.is_split:
                sub_layout = gi.sub_layout

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
                            ax.text(0.5, 0.5, f"{block} {ix}-{iy}", va="center", ha="center")
                gi.ax = axes

            else:
                ax = figure.add_subplot(ax_loc)
                gi.ax = ax
                if debug:
                    ax.tick_params(labelbottom=False, labelleft=False)
                    ax.text(0.5, 0.5, block, va="center", ha="center")

    def get_ax(self, name) -> Axes:
        return self.index_mapper[name].ax

    def plot(self):
        if self.gs is None:
            figure = plt.figure(constrained_layout=True)
            self.freeze(figure=figure, debug=True)
