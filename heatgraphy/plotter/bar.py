from typing import Callable

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from .base import StatsBase

ECHARTS16 = [
    "#5470c6", "#91cc75", "#fac858", "#ee6666",
    "#9a60b4", "#73c0de", "#3ba272", "#fc8452",
    "#27727b", "#ea7ccc", "#d7504b", "#e87c25",
    "#b5c334", "#fe8463", "#26c0c0", "#f4e001"
]


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
        bars = bar(locs, row, width, bottom,
                   fc=colors[ix], **kwargs)
        bottom += row
        if show_value:
            ax.bar_label(bars, [fmt_func(v) for v in row], label_type="center")
    return ax


class Numbers(StatsBase):

    def __init__(self, data, width=.7, color="C0",
                 show_value=True, fmt=None, label_pad=2,
                 props=None, **kwargs):
        self.data = data
        self.width = width
        self.color = color
        self.show_value = show_value
        self.fmt = fmt
        self.label_pad = label_pad
        self.props = props if props is not None else {}
        self.options = kwargs
        self.bars = None

    def render_ax(self, ax: Axes, data):
        bar = ax.bar if self.v else ax.barh
        if self.h:
            data = data[::-1]
        self.bars = bar(np.arange(0, len(data)) + 0.5, data,
                        self.width, color=self.color, **self.options)
        if self.v:
            ax.set_xlim(0, len(data))
        else:
            ax.set_ylim(0, len(data))
        if self.side == "left":
            ax.invert_xaxis()

        if self.show_value:
            ax.bar_label(self.bars, data, fmt=self.fmt,
                         padding=self.label_pad,
                         **self.props)


# TODO: Not fully implemented
#       Align the axis lim
class StackBar(StatsBase):

    def __init__(self, data,
                 labels=None, colors=None,
                 show_value=True,
                 width=.7,
                 **kwargs,
                 ):
        self.data = data

    def render_ax(self, ax, data):
        orient = "h" if self.h else "v"
        stacked_bar(data, ax=ax, orient=orient)
