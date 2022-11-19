import numpy as np
import pandas as pd
import seaborn

from .base import StatsBase


class _SeabornBase(StatsBase):

    _seaborn_plot = None

    def __init__(self, data, label=None, **kwargs):
        if isinstance(data, pd.DataFrame):
            data = data.to_numpy()
        else:
            data = np.asarray(data)
            if data.ndim == 1:
                data = data.reshape(1, -1)
        self.data = data
        kwargs.pop("x", None)
        kwargs.pop("y", None)
        kwargs.pop("hue", None)
        kwargs.pop("hue_order", None)
        kwargs.pop("orient", None)
        kwargs.pop("ax", None)
        if kwargs.get("color") is None:
            kwargs["color"] = "C0"
        self.kws = kwargs
        self.axis_label = label

    def set_side(self, side):
        self.side = side
        if side in ["left", "right"]:
            self.data = self.data.T

    def render_ax(self, ax, data):
        if self.h:
            data = data.T
        data = pd.DataFrame(data)
        orient = "h" if self.h else "v"
        if self.side == "left":
            ax.invert_xaxis()
        # barplot(data=data, orient=orient, ax=ax, **self.kws)
        plotter = getattr(seaborn, self._seaborn_plot)
        plotter(data=data, orient=orient, ax=ax, **self.kws)


def _seaborn_doc(obj: _SeabornBase):
    obj.__doc__ = f"""Wrapper for seaborn's {obj._seaborn_plot}
    
    .. note::
        .. rubric:: About data format
        
        You can only use wide-format for this plot, the number of columns
        of your input data should match your main data, this allow the data
        to be split and reorder if split and cluster is applied.
        
    
    Parameters
    ----------
    data : np.ndarray, pd.DataFrame
        The wide-format data
    label : str
        The label of your data
    kwargs : 
        See :func:`seaborn.{obj._seaborn_plot}`
        
    
    """
    return obj


@_seaborn_doc
class Bar(_SeabornBase):
    _seaborn_plot = "barplot"


class Box(_SeabornBase):
    _seaborn_plot = "boxplot"


class Boxen(_SeabornBase):
    _seaborn_plot = "boxenplot"


class Violin(_SeabornBase):
    _seaborn_plot = "violinplot"


class Point(_SeabornBase):
    _seaborn_plot = "pointplot"


class Count(_SeabornBase):
    _seaborn_plot = "countplot"


class Strip(_SeabornBase):
    _seaborn_plot = "stripplot"


class Swarm(_SeabornBase):
    _seaborn_plot = "swarmplot"


