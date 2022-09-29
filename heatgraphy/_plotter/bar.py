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
        # By default, make the bar color the same
        if "color" not in options.keys():
            options["color"] = "#E1A679"
        self.options = options
        if self.is_whole():
            self.vmin = np.nanmin(data)
            self.vmax = np.nanmax(data)
        else:
            self.vmin = np.min([np.nanmin(d) for d in data])
            self.vmax = np.max([np.nanmax(d) for d in data])

    def render(self):
        if self.is_whole():
            self._draw_ax(self.axes, self.data)
            self._setup_axes(self.axes)
        else:
            for ax, arr in zip(self.axes, self.data):
                self._draw_ax(ax, arr)
            # ensure that all axes has the same lim
            for i, ax in enumerate(self.axes):
                self._unify_lim(ax)
                # leave axis for the first ax
                if (i == 0) & self.is_vertical:
                    self._setup_axes(ax)
                # leave axis for the last ax
                elif (i == len(self.axes)-1) & self.is_horizontal:
                    self._setup_axes(ax)
                else:
                    ax.set_axis_off()

    def _draw_ax(self, ax, data):
        if data.ndim == 1:
            data = pd.DataFrame(data.reshape(1, -1))
        else:
            data = pd.DataFrame(data)
        bar_orient = "h" if self.is_horizontal else "v"
        if self.orient == "left":
            ax.invert_xaxis()
        barplot(data=data, orient=bar_orient,
                ax=ax, **self.options)

        # Update the lims
        if self.is_vertical:
            lower, upper = ax.get_ylim()
            if ax.yaxis_inverted():
                lower, upper = upper, lower
            if self.vmin > lower:
                self.vmin = lower
            if self.vmax < upper:
                self.vmax = upper
        else:
            lower, upper = ax.get_xlim()
            if ax.xaxis_inverted():
                lower, upper = upper, lower
            if self.vmin > lower:
                self.vmin = lower
            if self.vmax < upper:
                self.vmax = upper

    def _setup_axes(self, ax):
        if self.is_vertical:
            despine(ax=ax, bottom=True)
            ax.tick_params(bottom=False, labelbottom=False)
        else:
            despine(ax=ax, left=True)
            ax.tick_params(left=False, labelleft=False)

    def _unify_lim(self, ax):
        if self.is_vertical:
            if ax.yaxis_inverted():
                ax.set_ylim(self.vmax, self.vmin)
            else:
                ax.set_ylim(self.vmin, self.vmax)
        else:
            if ax.xaxis_inverted():
                ax.set_xlim(self.vmax, self.vmin)
            else:
                ax.set_xlim(self.vmin, self.vmax)
