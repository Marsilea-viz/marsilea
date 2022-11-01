from typing import Callable

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from seaborn import barplot, despine

from .base import RenderPlan

ECHARTS16 = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666",
    "#9a60b4", "#73c0de", "#3ba272", "#fc8452",
    "#27727b", "#ea7ccc", "#d7504b", "#e87c25",
    "#b5c334", "#fe8463", "#26c0c0", "#f4e001"
]


class Bar(RenderPlan):

    def __init__(self, data):
        self.data = data

    def render_ax(self, ax: Axes, data):
        if data.ndim == 1:
            data = pd.DataFrame(data.reshape(1, -1))
        else:
            if self.h:
                data = data.T
            data = pd.DataFrame(data)
        bar_orient = "h" if self.h else "v"
        if self.side == "left":
            ax.invert_xaxis()
        barplot(data=data, orient=bar_orient,
                ax=ax)

    def render_axes(self, axes):
        for ax, data in zip(axes, self.get_render_data()):
            self.render_ax(ax, data)
        self.align_lim(axes)

    def render(self, axes):
        if self.is_split(axes):
            self.render_axes(axes)
            for i, ax in enumerate(axes):
                # leave axis for the first ax
                if (i == 0) & self.v:
                    self._setup_axis(ax)
                # leave axis for the last ax
                elif (i == len(axes) - 1) & self.h:
                    self._setup_axis(ax)
                else:
                    ax.set_axis_off()
        else:
            # axes.set_axis_off()
            self.render_ax(axes, self.get_render_data())
            self._setup_axis(axes)

    def _setup_axis(self, ax):
        if self.v:
            despine(ax=ax, bottom=True)
            ax.tick_params(left=True, labelleft=True,
                           bottom=False, labelbottom=False)
        else:
            despine(ax=ax, left=True)
            ax.tick_params(left=False, labelleft=False,
                           bottom=True, labelbottom=True)


def simple_bar(data,
               ax: Axes = None,
               orient="v",
               width=.8,
               show_value=True,
               fmt=None,
               label_pad=2,
               text_props=None,
               **kwargs
               ):
    if ax is None:
        ax = plt.gca()
    if text_props is None:
        text_props = {}
    bar = ax.bar if orient == "v" else ax.barh
    bars = bar(np.arange(0, len(data)) + 0.5, data, width, **kwargs)
    if show_value:
        ax.bar_label(bars, data, fmt=fmt,
                     padding=label_pad,
                     **text_props)
    return ax


def _fmt_func(v):
    if v != 0:
        return v
    else:
        return ""


def stacked_bar(data, ax: Axes = None,
                labels=None, colors=None,
                show_value=True,
                orient="v", width=.8,
                **kwargs,
                ):
    if ax is None:
        ax = plt.gca()
    bar = ax.bar if orient == "v" else ax.barh

    if colors is None:
        colors = ECHARTS16

    if isinstance(show_value, Callable):
        fmt_func = show_value
    else:
        if show_value:
            fmt_func = _fmt_func

    data = data[::-1]

    locs = np.arange(0, data.shape[1]) + 0.5
    bottom = np.zeros(data.shape[1])
    for ix, row in enumerate(data):
        bars = bar(locs, row, width, bottom=bottom, fc=colors[ix], **kwargs)
        bottom += row
        if show_value:
            ax.bar_label(bars, [fmt_func(v) for v in row], label_type="center")
    return ax


class Numbers(RenderPlan):

    def __init__(self, data):
        self.data = data
