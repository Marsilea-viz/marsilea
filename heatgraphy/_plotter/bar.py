from typing import Sequence

import numpy as np
import pandas as pd

from ._base import _PlotBase
from seaborn import barplot, despine


class Bar(_PlotBase):

    def __init__(self,
                 axes,
                 data,
                 **options,
                 ):
        self.axes = axes
        self.data = data
        self.options = options
        if self.is_whole():
            self.vmin = np.nanmin(data)
            self.vmax = np.nanmax(data)
        else:
            self.vmin = np.min([np.nanmin(d) for d in data])
            self.vmax = np.max([np.nanmax(d) for d in data])

    def render(self, orient="top"):
        if self.is_whole():
            self._draw_ax(self.axes, self.data, orient)
        else:
            for ax, arr in zip(self.axes, self.data):
                self._draw_ax(ax, arr, orient)

    def _draw_ax(self, ax, data, orient="top"):
        if data.ndim == 1:
            data = pd.DataFrame(data.reshape(1, -1))
        else:
            data = pd.DataFrame(data)
        bar_orient = "h" if orient in ["left", "right"] else "v"
        if orient == "left":
            ax.invert_xaxis()
        barplot(data=data, orient=bar_orient,
                ax=ax, **self.options)
        if orient in ["top", "bottom"]:
            despine(ax=ax, bottom=True)
            ax.tick_params(bottom=False, labelbottom=False)
            lower, upper = ax.get_ylim()
            lower = lower if self.vmin > lower else self.vmin
            upper = upper if self.vmax < upper else self.vmax
            ax.set_ylim(lower, upper)
        else:
            ax.tick_params(left=False, labelleft=False)
            despine(ax=ax, left=True)
