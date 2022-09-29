from __future__ import annotations

import logging
from collections import namedtuple
from dataclasses import dataclass
from itertools import cycle
from typing import Any, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import cm
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import seaborn

from ._planner import SplitPlan
from ._plotter import ColorMesh, Chart, RenderPlan
from .dendrogram import Dendrogram, GroupDendrogram
from .layout import Grid
from .base import MatrixBase

log = logging.getLogger("heatgraphy")


@dataclass
class ChunkData:
    label: str
    color: str


class Plot:
    ax: Any
    legend: Any


def _handle_ax(ax, side):
    if side == "left":
        ax.invert_xaxis()
    if side == "bottom":
        ax.invert_yaxis()


class Heatmap(MatrixBase):

    def __init__(self,
                 data: np.ndarray,
                 vmin=None,
                 vmax=None,
                 cmap=None,
                 center=None,
                 robust=None,
                 mask=None,
                 ):
        if mask is not None:
            data = np.ma.masked_where(np.asarray(mask), data).filled(np.nan)
        self.render_data = data
        self._process_cmap(data, vmin, vmax, cmap, center, robust)
        self._split_plan = SplitPlan(self.render_data)
        super().__init__()

    def split_row(self, cut=None, labels=None, order=None, spacing=0.01):
        self._split_plan.hspace = spacing
        if cut is not None:
            self._split_plan.set_split_index(row=cut)

    def split_col(self, cut=None, labels=None, order=None, spacing=0.01):
        self._split_plan.wspace = spacing
        if cut is not None:
            self._split_plan.set_split_index(col=cut)

    def _data_cluster(self):
        split_plan = self._split_plan
        col_den = None
        row_den = None

        # If add dendrogram on column
        if self.col_cluster:
            if split_plan.split_col:
                split_col_data = split_plan. \
                    get_split_col_data(reorder=False)
                dens = [Dendrogram(chunk.T) for chunk in
                        split_col_data]
                gd = GroupDendrogram(dens)
                split_plan.set_order(
                    col=[d.reorder_index for d in dens],
                    col_chunk=gd.reorder_index)
                col_den = gd
            else:
                dg = Dendrogram(self.render_data.T)
                self.render_data = self.render_data[:, dg.reorder_index]
                col_den = dg

        if self.row_cluster:
            if split_plan.split_row:
                split_row_data = split_plan. \
                    get_split_row_data(reorder=False)
                dens = [Dendrogram(chunk) for chunk in split_row_data]
                gd = GroupDendrogram(dens)
                split_plan.set_order(
                    row=[d.reorder_index for d in dens],
                    row_chunk=gd.reorder_index)
                row_den = gd
            else:
                dg = Dendrogram(self.render_data)
                self.render_data = self.render_data[dg.reorder_index]
                row_den = dg
        return col_den, row_den

    def _setup_axes(self):
        split_plan = self._split_plan
        if split_plan.split:
            self.grid.split(
                "main",
                w_ratios=split_plan.col_segments,
                h_ratios=split_plan.row_segments,
                wspace=split_plan.wspace,
                hspace=split_plan.hspace
            )

        if split_plan.split_col:
            for plan in self._col_plan:
                self.grid.split(
                    plan.name,
                    w_ratios=split_plan.col_segments,
                    wspace=split_plan.wspace
                )

        if split_plan.split_row:
            for plan in self._row_plan:
                self.grid.split(
                    plan.name,
                    h_ratios=split_plan.row_segments,
                    hspace=split_plan.hspace
                )

    def render(self,
               figure=None,
               wspace=0,
               hspace=0,
               ):
        if figure is None:
            self.figure = plt.figure(figsize=(8, 8))
        else:
            self.figure = figure

        split_plan = self._split_plan

        # If dendrogram is added, perform the cluster and set the order
        if self.row_cluster or self.col_cluster:
            col_den, row_den = self._data_cluster()

        # If split, get the split data
        if split_plan.split:
            self.render_data = split_plan.get_split_data()
        # Otherwise, use the original render data

        # Make sure all axes is split
        self._setup_axes()
        # Place axes
        self.grid.freeze(figure=self.figure,
                         wspace=wspace,
                         hspace=hspace)
        self.main_axes = self.grid.get_canvas_ax("main")
        ColorMesh(self.main_axes,
                  self.render_data,
                  cmap=self.cmap,
                  vmin=self.vmin,
                  vmax=self.vmax
                  )

        # add row and col dendrogram
        for den in (self._row_den + self._col_den):
            if den['show']:
                ax = self.grid.get_ax(den['name'])
                ax.set_axis_off()
                spacing = split_plan.hspace
                den_obj = row_den
                if den['pos'] == "col":
                    spacing = split_plan.wspace
                    den_obj = col_den
                den_obj.draw(ax, orient=den['side'], spacing=spacing)

        # render other plots
        for plan in self._col_plan:
            if not plan.no_split:
                if split_plan.split_col:
                    plan.set_render_data(split_plan.split_by_col(plan.data))
                elif self.col_cluster:
                    plan.set_render_data(plan.data[:, col_den.reorder_index])
            else:
                plan.set_render_data(plan.data)
            axes = self.grid.get_canvas_ax(plan.name)
            plan.render(axes)

        # render other plots
        for plan in self._row_plan:
            # plan.data = plan.data.T
            if not plan.no_split:
                if split_plan.split_row:
                    plan.set_render_data(split_plan.split_by_row(plan.data))
                elif self.row_cluster:
                    plan.set_render_data(plan.data[row_den.reorder_index])
            else:
                plan.set_render_data(plan.data)
            axes = self.grid.get_canvas_ax(plan.name)
            plan.render(axes)


class DotHeatmap(MatrixBase):

    def __init__(self, dot_sizes, dot_colors=None, matrix=None, sizes=(1, 200),
                 dot_patch="circle", dot_outline=True, outline_color=".7",
                 dot_alpha=1.0, dot_cmap=None, matrix_cmap=None):
        super().__init__()


class CatHeatmap(MatrixBase):
    pass
