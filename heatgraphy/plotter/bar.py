from typing import Callable, Mapping

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from legendkit import ColorArt, CatLegend, ListLegend, SizeLegend
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
    """Stacked Bar


     Parameters
     ----------
     data : np.ndarray, pd.DataFrame
        2D data, index of dataframe is used as the name of items.
     items : list of str
        The name of items.
     colors : list of colors, mapping of (item, color)
        The colors of the bar for each item.



    Examples
    --------

    .. plot::
        :context: close-figs

        >>> from heatgraphy.plotter import StackBar
        >>> stack_data = pd.DataFrame(data=np.random.randint(0, 10, (5, 3)),
        ...                           index=list("abcde"))
        >>> _, ax = plt.subplots()
        >>> StackBar(stack_data).render(ax)


    You may find the text is too big for a bar to display on, to not display
    certain value.

    .. plot::
        :context: close-figs

        >>> cut_off = lambda v: v if v > 2 else ""
        >>> _, ax = plt.subplots()
        >>> StackBar(stack_data, show_value=cut_off).render(ax)

     """

    def __init__(self, data,
                 items=None, colors=None,
                 show_value=True,
                 value_loc="center",
                 width=.5,
                 value_size=6,
                 fmt=None,
                 props=None,
                 legend_kws=None,
                 **kwargs,
                 ):

        item_names = None
        if isinstance(data, pd.DataFrame):
            item_names = data.index
            data = data.to_numpy()
        data = self.data_validator(data, target="2d")

        if items is not None:
            item_names = items

        if colors is None:
            bar_colors = ECHARTS16
        else:
            if isinstance(colors, Mapping):
                if item_names is None:
                    raise ValueError("Please provide the name of each item "
                                     "before assigning color.")
                bar_colors = [colors[name] for name in item_names]
            else:
                bar_colors = colors

        fmt_func = None
        if isinstance(show_value, Callable):
            fmt_func = show_value
            show_value = True
        else:
            if show_value:
                fmt_func = _fmt_func

        self.data = data
        self.labels = item_names
        self.bar_colors = bar_colors
        self.show_value = show_value
        self.fmt_func = fmt_func
        self.width = width
        self.value_size = value_size
        self.fmt = "%g" if fmt is None else fmt
        self.kwargs = kwargs

        props = {} if props is None else props
        value_props = dict(label_type=value_loc)
        value_props.update(props)
        self.props = value_props
        self.legend_kws = {} if legend_kws is None else legend_kws

    ''''''

    def get_legends(self):
        if self.labels is not None:
            return CatLegend(colors=self.bar_colors, labels=self.labels,
                             **self.legend_kws)

    def render_ax(self, ax, data):
        orient = "h" if self.is_flank else "v"
        bar = ax.bar if orient == "v" else ax.barh

        lim = data.shape[1]
        if self.is_flank:
            ax.set_ylim(0, lim)
        else:
            ax.set_xlim(0, lim)
        if self.side == "left":
            ax.invert_xaxis()

        locs = np.arange(0, lim) + 0.5
        bottom = np.zeros(lim)

        # reverse to make the order more visually intuitive
        labels = self.labels[::-1]
        colors = self.bar_colors[:len(data)][::-1]
        for ix, row in enumerate(data[::-1]):
            bars = bar(locs, row, self.width, bottom,
                       fc=colors[ix],
                       label=labels[ix], **self.kwargs)
            bottom += row

            display_value = row
            if self.fmt_func is not None:
                display_value = [self.fmt_func(i) for i in row]

            if self.show_value:
                ax.bar_label(bars, display_value, fmt=self.fmt,
                             **self.props)


class Lollipop(StatsBase):

    def __init__(self, data):
        self.data = data

    def get_legends(self):
        return CatLegend(label=['Lollipop'], handle="circle")

    def render_ax(self, ax, data):
        orient = "horizontal" if self.is_flank else "vertical"

        lim = len(data)
        if self.is_flank:
            ax.set_ylim(0, lim)
        else:
            ax.set_xlim(0, lim)
        if self.side == "left":
            ax.invert_xaxis()

        # Plot on every .5 start from 0
        locs = np.arange(0, lim) + 0.5
        ax.stem(locs, data, orientation=orient)
