import numpy as np
from matplotlib.axes import Axes


class _PlotBase:
    data = None
    axes = None
    orient = "top"
    is_vertical = None
    is_horizontal = None

    def render(self, *args, **kwargs):
        raise NotImplemented

    def get_legend(self, *args, **kwargs):
        """Return the legend instance of this plot"""
        raise NotImplemented

    def get_plot_data(self, *args, **kwargs):
        """Return the plot data of this plot"""
        raise NotImplemented

    def is_whole(self):
        return isinstance(self.axes, Axes)

    def set_orient(self, orient):
        self.orient = orient
        self.is_vertical = orient in ["top", "bottom"]
        self.is_horizontal = orient in ["right", "left"]

