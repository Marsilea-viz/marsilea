from typing import Mapping

import numpy as np
import pandas as pd
from legendkit import CatLegend
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter

from ._utils import _format_labels
from .base import StatsBase
from ..utils import ECHARTS16


def simple_bar(
    data,
    ax: Axes = None,
    orient="v",
    width=0.8,
    show_value=True,
    fmt=None,
    label_pad=2,
    text_props=None,
    **kwargs,
):
    if ax is None:
        ax = plt.gca()
    if text_props is None:
        text_props = {}
    bar = ax.bar if orient == "v" else ax.barh
    bars = bar(np.arange(0, len(data)) + 0.5, data, width, **kwargs)
    if show_value:
        ax.bar_label(bars, data, fmt=fmt, padding=label_pad, **text_props)
    return ax


class _BarBase(StatsBase):
    def _process_params(
        self,
        width=0.7,
        orient=None,
        show_value=True,
        fmt=None,
        label=None,
        value_pad=2.0,
        props=None,
        **kwargs,
    ):
        self.width = width
        self.orient = orient
        self.show_value = show_value
        self.label = label
        self.fmt = "%g" if fmt is None else fmt
        self.value_pad = value_pad
        self.props = props if props is not None else {}
        self.options = kwargs


class Numbers(_BarBase):
    """Show numbers in bar plot

    This is used to show 1D data specifically.

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
    fmt : str, callable
        Format the value show on the bar
    label : str
        The label of the plot
    value_pad : float
        The spacing between label and the plot
    props : dict
        See :class:`matplotlib.text.Text`

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import marsilea as ma
        >>> from marsilea.plotter import Numbers
        >>> data = np.random.randint(1, 10, 10)
        >>> _, ax = plt.subplots()
        >>> Numbers(data).render(ax)

    """

    def __init__(
        self,
        data,
        width=0.8,
        color="C0",
        orient=None,
        show_value=True,
        fmt=None,
        label=None,
        value_pad=2.0,
        props=None,
        **kwargs,
    ):
        self.set_data(self.data_validator(data, target="1d"))
        self.color = color
        self.bars = None

        self._process_params(
            width, orient, show_value, fmt, label, value_pad, props, **kwargs
        )

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        lim = len(data)
        orient = self.get_orient()
        bar = ax.bar if orient == "v" else ax.barh
        if orient == "h":
            data = data[::-1]
        self.bars = bar(
            np.arange(0, lim) + 0.5, data, self.width, color=self.color, **self.options
        )

        if orient == "v":
            ax.set_xlim(0, lim)
        else:
            ax.set_ylim(0, lim)

        if self.side == "left":
            ax.invert_xaxis()

        if self.show_value:
            ax.bar_label(self.bars, fmt=self.fmt, padding=self.value_pad, **self.props)


class CenterBar(_BarBase):
    """Two comparable bar plots with center line

    Parameters
    ----------
    data : np.ndarray, pd.DataFrame
        If input with array, must be 2D array with shape (n, 2).
        If input with DataFrame, must have two columns.
    names : list of str
        The names of the two bars
    width : float
        The width of bar
    colors : list of color
        The colors of the two bars
    orient : {"v", "h"}
        The orientation of the plot
    show_value : bool
        Whether to show value on the bar
    fmt : str, callable
        Format the value show on the bar
    label : str
        The label of the plot
    value_pad : float
        The spacing between value and the plot
    props : dict
        See :class:`matplotlib.text.Text`
    kwargs:
        Other keyword arguments passed to :meth:`matplotlib.axes.Axes.bar`

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> import marsilea as ma
        >>> from marsilea.plotter import CenterBar
        >>> data = np.random.randint(1, 10, (10, 2))
        >>> _, ax = plt.subplots()
        >>> CenterBar(data, names=["Bar 1", "Bar 2"]).render(ax)


    .. plot::
        :context: close-figs

        >>> _, ax = plt.subplots()
        >>> CenterBar(data, names=["Bar 1", "Bar 2"], orient="h").render(ax)

    """

    def __init__(
        self,
        data,
        names=None,
        width=0.8,
        colors=None,
        orient=None,
        show_value=True,
        fmt=None,
        label=None,
        value_pad=2.0,
        props=None,
        **kwargs,
    ):
        self.set_data(self.data_validator(data.T, target="2d"))
        if names is None:
            if isinstance(data, pd.DataFrame):
                names = data.columns
        self.names = names
        if colors is None:
            colors = ["C0", "C1"]
        self.colors = colors

        self._process_params(
            width, orient, show_value, fmt, label, value_pad, props, **kwargs
        )

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        orient = self.get_orient()
        bar = ax.bar
        line = ax.axhline
        options = {"bottom": 0, **self.options}

        if orient == "h":
            bar = ax.barh
            line = ax.axvline
            data = data[::-1]

            del options["bottom"]
            options["left"] = 0

        left_bar, right_bar = data[0], data[1]
        locs = np.arange(0, len(left_bar)) + 0.5

        bar1 = bar(locs, left_bar, self.width, color=self.colors[0], **self.options)
        bar2 = bar(locs, -right_bar, self.width, color=self.colors[1], **self.options)
        line(0, color="black", lw=1)
        if self.names is not None:
            n1, n2 = self.names
            if orient == "h" and spec.is_first:
                ax.text(0.45, 1, n1, ha="right", va="bottom", transform=ax.transAxes)
                ax.text(0.55, 1, n2, ha="left", va="bottom", transform=ax.transAxes)
            elif orient == "v" and spec.is_last:
                ax.text(1, 0.75, n1, ha="left", va="center", transform=ax.transAxes)
                ax.text(1, 0.25, n2, ha="left", va="center", transform=ax.transAxes)

        lim_value = np.max(data) * 1.05

        if orient == "v":
            ax.set_xlim(0, len(left_bar))
            ax.set_ylim(-lim_value, lim_value)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{np.abs(x):g}"))
        else:
            ax.set_ylim(0, len(left_bar))
            ax.set_xlim(-lim_value, lim_value)
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{np.abs(x):g}"))

        if self.is_flank:
            ax.invert_yaxis()

        if self.show_value:
            left_label = _format_labels(left_bar, self.fmt)
            right_label = _format_labels(right_bar, self.fmt)
            ax.bar_label(bar1, left_label, padding=self.value_pad, **self.props)
            ax.bar_label(bar2, right_label, padding=self.value_pad, **self.props)


class StackBar(_BarBase):
    """Stacked Bar

     Parameters
     ----------
     data : np.ndarray, pd.DataFrame
        2D data, index of dataframe is used as the name of items.
     items : list of str
        The name of items.
     colors : list of colors, mapping of (item, color)
        The colors of the bar for each item.
    orient : {"v", "h"}
        The orientation of the plot
    show_value : bool
        Whether to show value on the bar
    value_loc : {"center", "edge"}
        The location of the value
    fmt : str, callable
        Format the value show on the bar
    label : str
        The label of the plot
    value_pad : float
        The spacing between value and the bar
    props : dict
        See :class:`matplotlib.text.Text`
    kwargs :
        Other keyword arguments passed to :meth:`matplotlib.axes.Axes.bar`


    Examples
    --------

    .. plot::
        :context: close-figs

        >>> from marsilea.plotter import StackBar
        >>> stack_data = pd.DataFrame(data=np.random.randint(1, 10, (5, 10)),
        ...                           index=list("abcde"))
        >>> _, ax = plt.subplots()
        >>> StackBar(stack_data).render(ax)


    You may find the text is too big for a bar to display on, to not display certain value.

    .. plot::
        :context: close-figs

        >>> fmt = lambda v: int(v) if v > 2 else ""
        >>> _, ax = plt.subplots()
        >>> StackBar(stack_data, show_value=True, fmt=fmt).render(ax)

    """

    def __init__(
        self,
        data,
        items=None,
        colors=None,
        orient=None,
        show_value=False,
        value_loc="center",
        width=0.8,
        value_size=6,
        fmt=None,
        props=None,
        label=None,
        value_pad=0,
        legend_kws=None,
        **kwargs,
    ):
        # TODO: Support bare bone numpy array as input
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
                    raise ValueError(
                        "Please provide the name of each item "
                        "before assigning color."
                    )
                bar_colors = [colors[name] for name in item_names]
            else:
                bar_colors = colors

        if len(bar_colors) < len(item_names):
            msg = "The number of colors is less than the number of items."
            raise ValueError(msg)

        self.set_data(data)
        self.labels = item_names
        self.bar_colors = bar_colors

        props = {} if props is None else props
        value_props = dict(label_type=value_loc)
        value_props.update(props)

        self._process_params(
            width, orient, show_value, fmt, label, value_pad, value_props, **kwargs
        )

        self.value_size = value_size
        self._legend_kws = dict(title=self.label, size=1)
        if legend_kws is not None:
            self._legend_kws.update(legend_kws)

    def get_legends(self):
        if self.labels is not None:
            return CatLegend(
                colors=self.bar_colors, labels=self.labels, **self._legend_kws
            )

    def render_ax(self, spec):
        ax = spec.ax
        data = spec.data

        orient = self.get_orient()
        bar = ax.bar if orient == "v" else ax.barh

        lim = data.shape[1]
        if orient == "h":
            ax.set_ylim(0, lim)
        else:
            ax.set_xlim(0, lim)
        if self.side == "left":
            ax.invert_xaxis()

        # Hanlde data
        if orient == "h":
            data = data[:, ::-1]

        locs = np.arange(0, lim) + 0.5
        bottom = np.zeros(lim)

        # reverse to make the order more visually intuitive
        if self.labels is not None:
            labels = self.labels[::-1]
        else:
            labels = [None for _ in range(len(data))]
        colors = self.bar_colors[: len(data)]
        for ix, row in enumerate(data):
            bars = bar(
                locs,
                row,
                self.width,
                bottom,
                fc=colors[ix],
                label=labels[ix],
                **self.options,
            )
            bottom += row

            if self.show_value:
                ax.bar_label(bars, fmt=self.fmt, padding=self.value_pad, **self.props)
