from __future__ import annotations

import logging
from typing import Any, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import cm
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.figure import Figure
# from sklearn.preprocessing import RobustScaler

from ._planner import SplitPlan, RenderPlan
from ._plotter import ColorMesh, Chart
from .dendrogram import Dendrogram, GroupDendrogram
from .layout import Grid

log = logging.getLogger("heatgraphy")


class Plot:
    ax: Any
    legend: Any


def _handle_ax(ax, side):
    if side == "left":
        ax.invert_xaxis()
    if side == "bottom":
        ax.invert_yaxis()


class Heatmap:
    gird: Grid
    figure: Figure
    heatmap_axes: Axes | List[Axes]
    _row_plan: List[RenderPlan]
    _col_plan: List[RenderPlan]
    vmin = None
    vmax = None

    def __init__(self,
                 data: np.ndarray,
                 vmin=None,
                 vmax=None,
                 cmap=None,
                 center=None,
                 robust=None,
                 mask=None,
                 ):

        self.render_data = self._transform_data(data, vmin, vmax, robust)

        self._row_index = None  # if pandas
        self._col_index = None  # if pandas
        self._process_cmap(cmap, center)

        self._row_den = []
        self._col_den = []

        self.grid = Grid()
        self._split_plan = SplitPlan(self.render_data)
        self._side_count = {"right": 0, "left": 0, "top": 0, "bottom": 0}
        self._col_plan = []
        self._row_plan = []

    def _transform_data(self, raw_data, vmin, vmax, robust):

        if isinstance(raw_data, pd.DataFrame):
            data = raw_data.to_numpy()
        else:
            try:
                # try to transform to ndarray
                raw_data = np.asarray(raw_data)
                data = raw_data
            except Exception:
                msg = f"Don't know how to process input data with type " \
                      f"{type(raw_data)}"
                raise TypeError(msg)
        return data
        # If vmin and vmax is set
        # Perform regular normalize
        orig_shape = data.shape
        data = data.flatten()

        if not robust:
            # Perform min max normalize
            dmin = np.nanmin(data)
            dmax = np.nanmax(data)
            self.vmin = dmin if vmin is None else vmin
            self.vmax = dmax if vmax is None else vmax
            #
            # vrange = self.vmax - self.vmin
            # std = data - dmin / (dmax - dmin)
            # scaled = std * vrange + self.vmin

            trans_data = data
        #
        # else:
        #     # Use robust scale
        #     if isinstance(robust, bool):
        #         # Use seaborn default
        #         robust = (2., 98.)
        #     else:
        #         # User input quantile range, eg. (5., 95.)
        #         robust = robust
        #     transformer = RobustScaler(quantile_range=robust)
        #     transformer.fit(data)
        #     trans_data = transformer.transform(data)
        #     self.vmin = np.nanmin(trans_data)
        #     self.vmax = np.nanmax(trans_data)
        #     self.center = transformer.center_
        # Map to origin shape
        # Flip to match origin style of dataframe
        return trans_data.reshape(orig_shape)

    # Copy from seaborn/matrix.py
    def _process_cmap(self, cmap, center):
        if cmap is None:
            self.cmap = cm.get_cmap('RdBu')
        elif isinstance(cmap, str):
            self.cmap = cm.get_cmap(cmap)
        elif isinstance(cmap, list):
            self.cmap = mcolors.ListedColormap(cmap)
        else:
            self.cmap = cmap

        if center is not None:

            # Copy bad values
            # in mpl<3.2 only masked values are honored with "bad" color spec
            # (see https://github.com/matplotlib/matplotlib/pull/14257)
            bad = self.cmap(np.ma.masked_invalid([np.nan]))[0]

            # under/over values are set for sure when cmap extremes
            # do not map to the same color as +-inf
            under = self.cmap(-np.inf)
            over = self.cmap(np.inf)
            under_set = under != self.cmap(0)
            over_set = over != self.cmap(self.cmap.N - 1)

            vrange = max(self.vmax - center, center - self.vmin)
            normlize = mcolors.Normalize(center - vrange, center + vrange)
            cmin, cmax = normlize([self.vmin, self.vmax])
            cc = np.linspace(cmin, cmax, 256)
            self.cmap = mcolors.ListedColormap(self.cmap(cc))
            self.cmap.set_bad(bad)
            if under_set:
                self.cmap.set_under(under)
            if over_set:
                self.cmap.set_over(over)

    def split_row(self, cut=None, labels=None, order=None, spacing=0.01):
        self._split_plan.hspace = spacing
        if cut is not None:
            self._split_plan.set_split_index(row=cut)

    def split_col(self, cut=None, labels=None, order=None, spacing=0.01):
        self._split_plan.wspace = spacing
        if cut is not None:
            self._split_plan.set_split_index(col=cut)

    def add_labels(self, side):
        """Add tick labels to the heatmap"""
        pass

    def set_title(self, row=None, col=None, main=None):
        pass

    def _get_plot_name(self, name, side, chart):
        # TODO: check duplicate names
        self._side_count[side] += 1
        if name is None:
            return f"{chart}-{side}-{self._side_count[side]}"
        else:
            return name

    def _add_plot(self, side, plot_type, data, name=None, size=1):
        plot_name = self._get_plot_name(name, side, plot_type)
        self.grid.add_ax(side, name=plot_name, size=size)
        self._render_plan.append(
            RenderPlan(name=plot_name, side=side,
                       data=data, size=size, chart=plot_type)
        )

    def add_colors(self, side, data, name=None, size=1):
        self._add_plot(side, Chart.Colors, data, name, size)

    def add_dendrogram(
            self,
            side,
            name=None,
            method=None,
            metric=None,
            linkage=None,
            show=True,
            size=0.5,
    ):
        """

        .. notes::
            Notice that we only use method and metric
            when you add the first dendrogram.

        Parameters
        ----------
        side
        name
        method
        metric
        linkage
        show
        size

        Returns
        -------

        """
        plot_name = self._get_plot_name(name, side, Chart.Dendrogram)
        if show:
            self.grid.add_ax(side, name=plot_name, size=size)

        if side in ["right", "left"]:
            self._row_den.append(
                dict(
                    name=plot_name,
                    show=show,
                    pos="row",
                    side=side,
                    method=method,
                    metric=metric
                )
            )
        else:
            self._col_den.append(
                dict(
                    name=plot_name,
                    show=show,
                    pos="col",
                    side=side,
                    method=method,
                    metric=metric
                )
            )

    def add_heatmap(self, data):
        pass

    def add_category(self):
        pass

    def add_scatter(self):
        pass

    def add_bar(self, side, data, name=None, size=1):
        plot_name = self._get_plot_name(name, side, Chart.Bar)
        self.grid.add_ax(side, name=plot_name)
        self._render_plan.append(
            RenderPlan(name=plot_name, side=side,
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

    def _data_cluster(self):
        split_plan = self._split_plan
        col_den = None
        row_den = None

        # If add dendrogram on column
        if len(self._col_den) > 0:
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

        if len(self._row_den) > 0:
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
            self.figure = plt.figure()
        else:
            self.figure = figure

        split_plan = self._split_plan

        # If dendrogram is added, perform the cluster and set the order
        if (len(self._row_den) > 0) or (len(self._col_den) > 0):
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
        self.heatmap_axes = self.grid.get_canvas_ax("main")
        ColorMesh(self.heatmap_axes,
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
