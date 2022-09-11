import numpy as np

from ._base import _PlotBase
from seaborn import barplot


class Bar(_PlotBase):

    def __init__(self,
                 axes,
                 data,
                 ):
        self.axes = axes
        self.data = data
        pass

    def render(self, orient="top"):
        if isinstance(axes, list):
            for ax, arr in zip(self.axes, self.data):
                x = [0 for _ in range(len(arr))]
                y = arr
                if orient in ["left", "right"]:
                    x, y = y, x
                barplot(x=x, y=y, ax=ax)
                if orient == ""