from typing import Mapping

import pandas as pd
import seaborn
from legendkit import CatLegend
from seaborn import color_palette

from .base import StatsBase
from ..utils import ECHARTS16


class _SeabornBase(StatsBase):
    _seaborn_plot = None
    datasets = None
    hue = None
    data = None

    def __init__(self, data, hue_order=None, palette=None,
                 label=None, legend_kws=None, **kwargs):

        if isinstance(data, Mapping):
            self.datasets = []
            self.hue = []
            if hue_order is None:
                hue_order = data.keys()
            for name in hue_order:
                self.hue.append(name)
                self.datasets.append(
                    self.data_validator(data[name]))
            if isinstance(palette, Mapping):
                self.palette = palette
            else:
                if palette is None:
                    colors = ECHARTS16
                else:
                    colors = color_palette(palette, as_cmap=False)
                self.palette = dict(zip(self.hue, colors))
            kwargs['palette'] = self.palette
        else:
            self.data = self.data_validator(data)
            kwargs.setdefault('color', 'C0')
            # if (palette is None) and ('color' not in kwargs):
            #     kwargs['palette'] = "dark:C0"
            # if palette is not None:
            #     kwargs['palette'] = palette
        kwargs.pop("x", None)
        kwargs.pop("y", None)
        kwargs.pop("hue", None)
        kwargs.pop("orient", None)
        kwargs.pop("ax", None)
        self.kws = kwargs
        self.axis_label = label
        self.legend_kws = {} if legend_kws is None else legend_kws

    def get_render_data(self):
        if self.data is not None:
            return super().get_render_data()
        else:
            return self.create_render_datasets(*self.datasets)

    def get_legends(self):
        if self.hue is not None:
            labels = []
            colors = []
            for label, color in self.palette.items():
                labels.append(label)
                colors.append(color)
            options = dict(handle="square", size=1, draw=False)
            options.update(self.legend_kws)
            return CatLegend(colors=colors, labels=labels, **options)

    def render_ax(self, ax, data):
        if self.hue is not None:

            x, y = "var", "value"
            dfs = []
            for d, hue in zip(data, self.hue):
                df = pd.DataFrame(d)
                df = df.melt(var_name="var", value_name="value")
                df['hue'] = hue
                dfs.append(df)

            pdata = pd.concat(dfs)
            self.kws['hue'] = 'hue'
            self.kws['hue_order'] = self.hue
            if self.is_flank:
                x, y = y, x
            self.kws['x'] = x
            self.kws['y'] = y

        else:
            pdata = pd.DataFrame(data)
        orient = "h" if self.is_flank else "v"
        if self.side == "left":
            ax.invert_xaxis()
        # barplot(data=data, orient=orient, ax=ax, **self.kws)
        plotter = getattr(seaborn, self._seaborn_plot)

        plotter(data=pdata, orient=orient, ax=ax, **self.kws)
        ax.set(xlabel=None, ylabel=None)
        leg = ax.get_legend()
        if leg is not None:
            leg.remove()


def _seaborn_doc(obj: _SeabornBase):
    cls_name = obj.__name__
    shape = (10, 10)
    obj.__doc__ = f"""Wrapper for seaborn's {obj._seaborn_plot}
    
    .. note::
        .. rubric:: About data format
        
        You can only use wide-format for this plot, the number of columns
        of your input data should match your main data, this allow the data
        to be split and reorder if split and cluster is applied.
        
    
    Parameters
    ----------
    data : np.ndarray, pd.DataFrame
        The wide-format data. To input 'hue' like data, you need to input a dict.
        eg: :code:`{{'hue1': data1, 'hue2': data2}}`.
    hue_order : array of str
        The order of hue
    palette : dict of label, color
    label : str
        The label of your data
    kwargs : 
        See :func:`seaborn.{obj._seaborn_plot}`
        
    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        >>> import heatgraphy as hg
        >>> from heatgraphy.plotter import {cls_name}
        >>> data = np.random.randn(10, 10)
        >>> plot = {cls_name}(np.random.randint(0, 10, {shape}))
        >>> h = hg.Heatmap(data)
        >>> h.hsplit(cut=[3, 7])
        >>> h.add_right(plot)
        >>> h.render()
        
    
    """
    return obj


@_seaborn_doc
class Bar(_SeabornBase):
    _seaborn_plot = "barplot"


@_seaborn_doc
class Box(_SeabornBase):
    _seaborn_plot = "boxplot"


@_seaborn_doc
class Boxen(_SeabornBase):
    _seaborn_plot = "boxenplot"


@_seaborn_doc
class Violin(_SeabornBase):
    _seaborn_plot = "violinplot"


@_seaborn_doc
class Point(_SeabornBase):
    _seaborn_plot = "pointplot"


@_seaborn_doc
class Count(_SeabornBase):
    _seaborn_plot = "countplot"


@_seaborn_doc
class Strip(_SeabornBase):
    _seaborn_plot = "stripplot"


@_seaborn_doc
class Swarm(_SeabornBase):
    _seaborn_plot = "swarmplot"
