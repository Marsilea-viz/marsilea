from __future__ import annotations

import logging

log = logging.getLogger("heatgraphy")

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import seaborn as sns
from seaborn import despine

from .layout import Grid


class Chart(Enum):
    Bar = "bar"
    Box = "box"
    Colors = "colors"
    Scatter = "scatter"
    Dendrogram = "dendrogram"
    Violin = "violin"
    Line = "line"


class Plot:
    ax: Any
    legend: Any


@dataclass
class PlotData:
    name: str
    side: str
    data: Any
    size: float
    chart: Chart


# TODO:
#  Separate the render logic for different plot
#  - Direction
#  - Split to axes

class Heatmap:
    gird: Grid
    figure: Figure
    heatmap_axes: Axes | List[Axes]

    def __init__(self,
                 data,
                 split=None,
                 ):

        self.grid = Grid()
        self.data = data[::-1]
        self._side_count = {"right": 0, "left": 0, "top": 0, "bottom": 0}
        self._render_plan = []  # {"right": [], "left": [], "top": [], "bottom": []}

        self._split_x = None
        self._split_y = None
        self._split_x_ratio = None
        self._split_y_ratio = None
        self._split_data = None

    def split(self, x=None, y=None, wspace=0.05, hspace=0.05):
        split_x = x is not None
        split_y = y is not None

        X, Y = self.data.shape
        if split_x:
            x = np.asarray(x)
            self._split_x = np.array([*x, X])
            self._split_x_ratio = np.sort(x) / X
        if split_y:
            y = np.asarray(y)
            self._split_y = np.array([*y, Y])
            self._split_y_ratio = np.sort(y) / Y
        self.grid.split("main", x=self._split_x_ratio, y=self._split_y_ratio,
                        wspace=wspace, hspace=hspace)

        self._split_data = []

        if split_x & split_y:
            # split x and y
            start_x = 0
            start_y = 0
            for iy in self._split_y:
                for ix in self._split_x:
                    self._split_data.append(
                        self.data[start_y:iy, start_x:ix]
                    )
                    start_x = ix
                start_y = iy
        else:
            if split_x:
                # split x
                start_x = 0
                for ix in self._split_x:
                    self._split_data.append(
                        self.data[:, start_x:ix]
                    )
                    start_x = ix
            if split_y:
                # split y
                start_y = 0
                for iy in self._split_y:
                    self._split_data.append(
                        self.data[start_y:iy]
                    )
                    start_y = iy

            log.debug(f"split_x: {split_x}\n"
                      f"split_y: {split_y}\n"
                      f"split_data: {len(self._split_data)}\n")

    def render(self,
               figure=None,
               wspace=0,
               hspace=0,
               ):
        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure
        self.grid.freeze(figure=self.figure, wspace=wspace, hspace=hspace)
        self.heatmap_axes = self.grid.get_ax("main")
        if isinstance(self.heatmap_axes, list):
            for hax, sdata in zip(self.heatmap_axes, self._split_data):
                hax.set_axis_off()
                hax.pcolormesh(sdata)
        else:
            self.heatmap_axes.set_axis_off()
            self.heatmap_axes.pcolormesh(self.data)
        for plan in self._render_plan:
            ax = self.grid.get_ax(plan.name)
            if plan.chart == Chart.Bar:
                # ax.xaxis.set_tick_params(labelbottom=False)
                if plan.side == "top":
                    ax = sns.barplot(x=np.arange(10), y=plan.data, ax=ax)
                    despine(ax=ax, top=True, bottom=False, right=True, left=True)
                    ax.set_xticks([])
                    ax.set_yticks([])
            elif plan.chart == Chart.Colors:
                if plan.side == "top":
                    ax.pcolormesh(plan.data, cmap="Set1")
                    ax.set_axis_off()

    def add_labels(self, side):
        """Add tick labels to the heatmap"""
        pass

    def set_title(self, row=None, col=None, main=None):
        pass

    def _get_plot_name(self, name, side, chart):
        self._side_count[side] += 1
        if name is None:
            return f"{chart}-{self._side_count[side]}"
        else:
            return name

    def add_colors(self, side, data, name=None, split=False, size=1):
        plot_name = self._get_plot_name(name, side, Chart.Colors)
        self.grid.add_ax(side, name=plot_name, size=size)
        self._render_plan.append(
            PlotData(name=plot_name, side=side,
                     data=data, size=size, chart=Chart.Colors)
        )

    def add_dendrogram(self):
        pass

    def add_category(self):
        pass

    def add_scatter(self):
        pass

    def add_bar(self, side, data, name=None, size=1):
        plot_name = self._get_plot_name(name, side, Chart.Bar)
        self.grid.add_ax(side, name=plot_name)
        self._render_plan.append(
            PlotData(name=plot_name, side=side,
                     data=data, size=size, chart=Chart.Bar))

    def add_violin(self):
        pass

    def add_annotation(self, side, name=None):
        """
        Add custom annotation to the plot

        Parameters
        ----------


        """
        pass

    def get_ax(self, name):
        """Get a specific axes by name when available"""
        pass

    def get_heatmap_ax(self):
        """Return the axes that draw heatmap"""
        pass

    def auto_legend(self, side):
        """Draw legend based on the order of annotation"""
        pass
