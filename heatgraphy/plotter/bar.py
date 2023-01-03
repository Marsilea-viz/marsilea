from typing import Callable

import numpy as np
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


def stacked_bar(data, ax: Axes = None,
                labels=None, colors=None,
                show_value=True,
                orient="v", width=.5, value_size=6,
                show_labels=False,
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
    ax.set_ylim(0, data.shape[1])
    # Add limitation here to make bars in center


    bottom = np.zeros(data.shape[1])
    for ix, row in enumerate(data):
        bars = bar(locs, row, width, bottom,
                   fc=colors[ix], label=labels[ix], **kwargs)
        bottom += row

        if show_value:
            ax.bar_label(bars, [fmt_func(v) for v in row], label_type="center", fontsize=value_size)



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
    """Stacked Bar


     Parameters
     ----------------
     data : np.ndarray, pd.DataFrame
        2D data
     labels : str or list of str, optional
        A list with the same length as data
     colors : color or list of color, optional
        The colors of the bar faces.


    .. plot::
        :context: close-figs

        >>> import heatgraphy as hg
        >>> import numpy as np
        >>> d1 = np.random.rand(10,12)
        >>> d2 = np.random.randint(1,100,(12,10))
        >>> plot = {cls_name}(np.random.randint(0, 10, {shape}))
        >>> hg.plotter.StackBar(d2,show_value=True, value_size = 4, show_labels=True, label_position=(-0.4,0.9))



     """


    def __init__(self, data,
                 labels=None, colors=None,
                 show_value=True,
                 width=.5,
                 value_size=6,
                 show_labels=False,
                 label_size=8,
                 **kwargs,
                 ):
        self.data = data
        self.labels = labels
        self.colors = colors
        self.show_value = show_value
        self.width = width
        self.value_size = value_size
        self.show_labels = show_labels
        self.label_position = label_position
        self.label_size = label_size

    ''''''
    def get_legends(self):
        if self.labels is None:
            self.labels = list(range(1, self.data.shape[0] + 1))

        return CatLegend(colors=self.colors, labels=self.labels, **self._legend_kws)


    def render_ax(self, ax, data):
        orient = "h" if self.is_flank else "v"

        if self.is_flank:
            data = data[::-1]

        if self.is_body:
            ax.set_xlim(0, len(data))
        else:
            ax.set_ylim(0, len(data))
        if self.side == "left":
            ax.invert_xaxis()




        stacked_bar(data, ax=ax, orient=orient,
                    labels=self.labels,
                    show_value=self.show_value,
                    width=self.width, value_size=self.value_size,
                    show_labels=self.show_labels,
                    label_position=self.label_position,
                    label_size=self.label_size
                    )

