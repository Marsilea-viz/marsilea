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
              x=None,
              y=None,
              wspace=0.05,
              hspace=0.05,
              mode="placeholder",
              mask_placeholder=True,
              ):
        """

        Parameters
        ----------
        name :
        x : array
            The ratio of each chunk, the sum the array should be 1
        y
        wspace
        hspace
        mode : {'blank', 'placeholder'}
        mask_placeholder

        Returns
        -------

        """

        if (wspace >= 1.) & (wspace < 0):
            raise ValueError("wspace should be in (0, 1)")

        if (hspace >= 1.) & (hspace < 0):
            raise ValueError("hspace should be in (0, 1)")

        if mode == "blank":
            self._split_blank(name, x=x, y=y, wspace=wspace, hspace=hspace)
        elif mode == "placeholder":
            self._split_placeholder(name, x=x, y=y, wspace=wspace,
                                    hspace=hspace)
        else:
            raise ValueError(f"Don't know mode='{mode}', "
                             f"options are (blank or placeholder)")

    def _split_placeholder(self,
                           name,
                           x=None,
                           y=None,
                           wspace=0.05,
                           hspace=0.05,
                           mask_placeholder=True
                           ):
        # TODO: check wspace and hspace range in (0, 1)

        split_x = x is not None
        split_y = y is not None

        gb = self.layout[name]
        gb.is_split = True
        sub_layout = gb.sub_layout
        sub_layout.wspace = 0
        sub_layout.hspace = 0
        sub_layout.mode = "placeholder"
        sub_layout.mask_placeholder = mask_placeholder

        if split_x:
            if sub_layout.col != 1:
                raise ValueError("Can only be split once")
            sub_layout.col = 2 * len(x) + 1
            inject_x = []
            for pt in x:
                inject_x.append(pt - wspace / 2.)
                inject_x.append(pt + wspace / 2.)
            sub_layout.w_ratios = _interval(gb.wsize, inject_x)

        if split_y:
            if sub_layout.row != 1:
                raise ValueError("Can only be split once")
            sub_layout.row = 2 * len(y) + 1
            inject_y = []
            for pt in y:
                inject_y.append(pt - hspace / 2.)
                inject_y.append(pt + hspace / 2.)
            sub_layout.h_ratios = _interval(gb.hsize, inject_y)

        # create a binary mask to label
        # which is canvas ax (1) which is placeholder (0)
        masks = np.ones((sub_layout.row, sub_layout.col))

        for loc in np.arange(1, sub_layout.row, step=2):
            masks[loc, :] = 0
        for loc in np.arange(1, sub_layout.col, step=2):
            masks[:, loc] = 0
        gb.ax_masks = masks.flatten().astype(bool)

    def _split_blank(self, name, x=None, y=None, wspace=0.05, hspace=0.05):
        gb = self.layout[name]
        gb.is_split = True
        sub_layout = gb.sub_layout
        sub_layout.wspace = wspace
        sub_layout.hspace = hspace
        sub_layout.mode = "blank"

        if x is not None:
            if sub_layout.col != 1:
                raise ValueError("Can only be split once")
            sub_layout.col += len(x)
            sub_layout.w_ratios = _interval(gb.wsize, x)

        if y is not None:
            if sub_layout.row != 1:
                raise ValueError("Can only be split once")
            sub_layout.row += len(y)
            sub_layout.h_ratios = _interval(gb.hsize, y)
        gb.ax_masks = np.ones((sub_layout.row, sub_layout.col)).flatten()

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
                print(gb)

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
                            ax.tick_params(labelbottom=False, labelleft=False)
                            ax.set_xticks([])
                            ax.set_yticks([])
                            ax.text(0.5, 0.5, f"{block} {ix}-{iy}",
                                    va="center", ha="center")
                            # If it is placeholder mark it in gray
                            if gb.ax_masks[num] == 0:
                                ax.set_facecolor("gray")
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
                    ax.text(0.5, 0.5, block, va="center", ha="center")

    @staticmethod
    def _set_axis_dir(gi, ax):
        if gi.side == "left":
            ax.invert_xaxis()
        if gi.side == "bottom":
            ax.invert_yaxis()

    def get_ax(self, name) -> (Axes, np.ndarray):
        gb = self.layout[name]
        return gb.ax, gb.ax_masks

    def get_canvas_ax(self, name) -> Axes:
        return self.layout[name].get_canvas_ax()

    def plot(self):
        if self.gs is None:
            figure = plt.figure()
            self.freeze(figure=figure, debug=True)
