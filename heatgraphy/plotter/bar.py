from typing import Callable

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from .base import StatsBase
from ..utils import ECHARTS16


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
    """Show numbers in bar plot

    Parameters
    ----------
    data : np.ndarray
        1D data
    width : float
        The width of bar
    color : color
        The color of bar
    show_value : bool
        Whether to show value on the bar
    fmt : str
        Format the value show on the bar
    label : str
        The label of the plot
    label_pad : float
        The spacing between label and the plot
    props : dict
        See :class:`matplotlib.text.Text`
    
    """

    def __init__(self, data, width=.7, color="C0",
                 show_value=True, fmt=None, label=None, label_pad=2.,
                 props=None, **kwargs):
        self.data = self.data_validator(data, target="1d")
        self.width = width
        self.color = color
        self.show_value = show_value
        self.axis_label = label
        self.fmt = fmt
        self.label_pad = label_pad
        self.props = props if props is not None else {}
        self.options = kwargs
        self.bars = None

    def render_ax(self, ax: Axes, data):
        bar = ax.bar if self.is_body else ax.barh
        if self.is_flank:
            data = data[::-1]
        self.bars = bar(np.arange(0, len(data)) + 0.5, data,
                        self.width, color=self.color, **self.options)
        if self.is_body:
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
        orient = "h" if self.is_flank else "v"
        stacked_bar(data, ax=ax, orient=orient)
