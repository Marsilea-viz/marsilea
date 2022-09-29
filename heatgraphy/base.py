from __future__ import annotations

from itertools import cycle
from typing import List
from uuid import uuid4

import numpy as np
from matplotlib import cm
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ._planner import SplitPlan
from ._plotter import RenderPlan, Chart
from .layout import Grid
from .utils import relative_luminance


class SplitBase:
    _split_plan: SplitPlan

    def split_row(self, cut=None, labels=None, order=None, spacing=0.01):
        self._split_plan.hspace = spacing
        if cut is not None:
            self._split_plan.set_split_index(row=cut)

    def split_col(self, cut=None, labels=None, order=None, spacing=0.01):
        self._split_plan.wspace = spacing
        if cut is not None:
            self._split_plan.set_split_index(col=cut)


class MatrixBase:
    gird: Grid
    figure: Figure
    main_axes: Axes | List[Axes]
    _row_plan: List[RenderPlan]
    _col_plan: List[RenderPlan]
    vmin = None
    vmax = None
    cmap = None
    annot_text = None
    render_data = None

    def __init__(self):
        self._row_den = []
        self._col_den = []
        self.grid = Grid()
        self._side_count = {"right": 0, "left": 0, "top": 0, "bottom": 0}
        self._col_plan = []
        self._row_plan = []

    # Copy from seaborn/matrix.py
    def _process_cmap(self, data, vmin, vmax,
                      cmap, center, robust):
        """Use some heuristics to set good defaults for colorbar and range."""

        if vmin is None:
            if robust:
                vmin = np.nanpercentile(data, 2)
            else:
                vmin = np.nanmin(data)
        if vmax is None:
            if robust:
                vmax = np.nanpercentile(data, 98)
            else:
                vmax = np.nanmax(data)
        self.vmin, self.vmax = vmin, vmax

        # Choose default colormaps if not provided
        # if cmap is None:
        #     if center is None:
        #         self.cmap = cm.rocket
        #     else:
        #         self.cmap = cm.icefire
        if isinstance(cmap, str):
            self.cmap = cm.get_cmap(cmap)
        elif isinstance(cmap, list):
            self.cmap = mcolors.ListedColormap(cmap)
        elif cmap is None:
            self.cmap = "coolwarm"
        else:
            self.cmap = cmap

        # Recenter a divergent colormap
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

            vrange = max(vmax - center, center - vmin)
            normlize = mcolors.Normalize(center - vrange, center + vrange)
            cmin, cmax = normlize([vmin, vmax])
            cc = np.linspace(cmin, cmax, 256)
            self.cmap = mcolors.ListedColormap(self.cmap(cc))
            self.cmap.set_bad(bad)
            if under_set:
                self.cmap.set_under(under)
            if over_set:
                self.cmap.set_over(over)

    def _annotate_text(self, ax, mesh, **annot_kws):
        """Add textual labels with the value in each cell."""
        mesh.update_scalarmappable()
        height, width = self.annot_text.shape
        xpos, ypos = np.meshgrid(np.arange(width) + .5, np.arange(height) + .5)
        for x, y, m, color, val in zip(xpos.flat, ypos.flat,
                                       mesh.get_array(), mesh.get_facecolors(),
                                       self.annot_text.flat):
            if m is not np.ma.masked:
                lum = relative_luminance(color)
                text_color = ".15" if lum > .408 else "w"
                annotation = ("{:" + self.fmt + "}").format(val)
                text_kwargs = dict(color=text_color, ha="center", va="center")
                text_kwargs.update(annot_kws)
                ax.text_obj(x, y, annotation, **text_kwargs)

    def _get_plot_name(self, name, side, chart: Chart):
        self._side_count[side] += 1
        if name is None:
            return f"{chart.value}-{side}-{self._side_count[side]}"
        else:
            return name

    def _add_plot(self, side, plot_type, data, name=None, size=1.,
                  no_split=False,
                  **kwargs):
        plot_name = self._get_plot_name(name, side, plot_type)
        self.grid.add_ax(side, name=plot_name, size=size)
        if side in ["top", "bottom"]:
            plan = self._col_plan
        else:
            plan = self._row_plan
        plan.append(
            RenderPlan(name=plot_name, orient=side,
                       data=data, size=size, chart=plot_type,
                       no_split=no_split,
                       options=kwargs,
                       )
        )

    def add_labels(self, side, labels, name=None, size=.5, **options):
        """Add tick labels to the heatmap"""
        labels = np.asarray(labels)
        self._add_plot(side, Chart.Label, labels, name, size,
                       **options)

    def add_annotated_labels(self, side, labels, masks,
                             name=None, size=1, **options):
        """Mark specific tick labels on the heatmap"""
        annotated_labels = np.ma.masked_where(masks, labels)
        self._add_plot(side, Chart.AnnotatedLabel, annotated_labels,
                       name, size, **options)

    def add_chunks(self, side,
                   labels=None,
                   colors=None,
                   bordercolor=None,
                   borderwidth=None,
                   borderstyle=None,
                   name=None, size=.5, **options,
                   ):
        if labels is None:
            labels = cycle([None])
        elif isinstance(labels, str):
            labels = [labels]
        if colors is None:
            colors = cycle([None])
        elif isinstance(colors, (str, tuple)):
            colors = [colors]

        data = np.asarray([(text, c) for text, c in zip(labels, colors)],
                          dtype=object)
        self._add_plot(side, Chart.Chunk, data, name, size,
                       no_split=True,
                       bordercolor=bordercolor,
                       borderwidth=borderwidth,
                       borderstyle=borderstyle,
                       **options)

    def add_colors(self,
                   side,
                   data,
                   label=None,
                   label_loc=None,
                   name=None,
                   size=0.25,
                   ):
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        if data.ndim < 2:
            if side in ["top", "bottom"]:
                data = data.reshape(1, -1)
            else:
                data = data.reshape(-1, 1)
        self._add_plot(side, Chart.Colors, data, name, size=size,
                       label=label, label_loc=label_loc)

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
                dict(name=plot_name, show=show, pos="row",
                     side=side, method=method, metric=metric)
            )
        else:
            self._col_den.append(
                dict(name=plot_name, show=show, pos="col",
                     side=side, method=method, metric=metric
                     )
            )

    def add_bar(self, side, data, name=None, size=1, **options):
        self._add_plot(side, Chart.Bar, data, name, size,
                       **options)

    def add_scatter(self):
        pass

    def add_violin(self):
        pass

    def add_custom(self):
        pass

    def set_title(self, row=None, col=None, main=None):
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

    @property
    def row_cluster(self):
        return len(self._row_den) > 0

    @property
    def col_cluster(self):
        return len(self._col_den) > 0
