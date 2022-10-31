import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from seaborn import barplot, despine

from .base import RenderPlan


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
                elif (i == len(axes)-1) & self.h:
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
               ax=None,
               orient="v",
               width=.8,
               show_values=None,
               ):
    if ax is None:
        ax = plt.gca()
    coords = np.arange(0, len(data)) + 0.5




class SimpleBar(RenderPlan):

    def __init__(self, data):
        self.data = data

