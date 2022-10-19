from __future__ import annotations

import warnings
from itertools import cycle
from typing import List

import numpy as np
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ._planner import Deformation
from ._plotter import Chart
from .layout import Grid
from .plotter import RenderPlan
from .utils import relative_luminance


def getaspect(ratio, w=None, h=None):
    canvas_size_min = np.array((4.0, 4.0))  # min length for width/height
    canvas_size_max = np.array((10.0, 10.0))  # max length for width/height

    set_w = w is not None
    set_h = h is not None

    canvas_height, canvas_width = None, None

    if set_w & set_h:
        canvas_height = h
    elif set_w:
        canvas_width = w
    else:
        canvas_height = 5

    if canvas_height is not None:
        newsize = np.array((canvas_height / ratio, canvas_height))
    else:
        newsize = np.array((canvas_width, canvas_width * ratio))

    newsize /= min(1.0, *(newsize / canvas_size_min))
    newsize /= max(1.0, *(newsize / canvas_size_max))
    newsize = np.clip(newsize, canvas_size_min, canvas_size_max)
    return newsize


class _Base:

    def __init__(self, w=None, h=None, data_aspect=1):
        w, h = getaspect(data_aspect, w=w, h=h)
        self.grid = Grid(w=w, h=h)
        self._side_count = {"right": 0, "left": 0, "top": 0, "bottom": 0}
        self._col_plan = []
        self._row_plan = []

    def _get_plot_name(self, name, side, chart):
        self._side_count[side] += 1
        if name is None:
            return f"{chart}-{side}-{self._side_count[side]}"
        else:
            return name

    def add_plot(self, plot: RenderPlan, side, name=None, size=1.,
                 no_split=False):
        plot_name = self._get_plot_name(name, side, type(plot))
        self.grid.add_ax(side, name=plot_name, size=size)
        if side in ["top", "bottom"]:
            plan = self._col_plan
        else:
            plan = self._row_plan
        plot.set(name=plot_name, side=side,
                 size=size, no_split=no_split)
        plan.append(plot)

    # def _add_plot(self, side, plot_type, data, name=None, size=1.,
    #               no_split=False,
    #               **kwargs):
    #     plot_name = self._get_plot_name(name, side, plot_type)
    #     self.grid.add_ax(side, name=plot_name, size=size)
    #     if side in ["top", "bottom"]:
    #         plan = self._col_plan
    #     else:
    #         plan = self._row_plan
    #     plan.append(
    #         plot(name=plot_name, orient=side,
    #                    data=data, size=size, chart=plot_type,
    #                    no_split=no_split,
    #                    options=kwargs,
    #                    )
    #     )

    # def add_labels(self, side, labels, name=None, size=.5, **options):
    #     """Add tick labels to the heatmap"""
    #     labels = np.asarray(labels)
    #     self._add_plot(side, Chart.Label, labels, name, size,
    #                    **options)

    # def add_chunks(self, side,
    #                labels=None,
    #                colors=None,
    #                bordercolor=None,
    #                borderwidth=None,
    #                borderstyle=None,
    #                name=None, size=.5, **options,
    #                ):
    #     if labels is None:
    #         labels = cycle([None])
    #     elif isinstance(labels, str):
    #         labels = [labels]
    #     if colors is None:
    #         colors = cycle([None])
    #     elif isinstance(colors, (str, tuple)):
    #         colors = [colors]
    #
    #     data = np.asarray([(text, c) for text, c in zip(labels, colors)],
    #                       dtype=object)
    #     self._add_plot(side, Chart.Chunk, data, name, size,
    #                    no_split=True,
    #                    bordercolor=bordercolor,
    #                    borderwidth=borderwidth,
    #                    borderstyle=borderstyle,
    #                    **options)

    # def add_colors(self,
    #                side,
    #                data,
    #                label=None,
    #                label_loc=None,
    #                name=None,
    #                size=0.25,
    #                ):
    #     if not isinstance(data, np.ndarray):
    #         data = np.array(data)
    #     if data.ndim < 2:
    #         if side in ["top", "bottom"]:
    #             data = data.reshape(1, -1)
    #         else:
    #             data = data.reshape(-1, 1)
    #     self._add_plot(side, Chart.Colors, data, name, size=size,
    #                    label=label, label_loc=label_loc)

    # def add_bar(self, side, data, name=None, size=1, **options):
    #     self._add_plot(side, Chart.Bar, data, name, size,
    #                    **options)
    #
    # def add_scatter(self):
    #     pass
    #
    # def add_violin(self):
    #     pass
    #
    # def add_custom(self):
    #     pass

    def set_title(self, row=None, col=None, main=None):
        pass

    def get_ax(self, name):
        """Get a specific axes by name when available"""
        pass

    def get_main_ax(self):
        """Return the main axes, like the heatmap axes"""
        pass


class MatrixBase(_Base):
    gird: Grid
    figure: Figure
    main_axes: Axes | List[Axes]
    _row_plan: List[RenderPlan]
    _col_plan: List[RenderPlan]

    # vmin = None
    # vmax = None
    # cmap = None
    # norm = None
    # annot_text = None
    # render_data = None

    def __init__(self, cluster_data, w=None, h=None, data_aspect=1):
        super().__init__(w=w, h=h, data_aspect=data_aspect)
        self._row_den = []
        self._col_den = []
        self._deform = Deformation(cluster_data)

    # def add_annotated_labels(self, side, labels, masks,
    #                          name=None, size=1, **options):
    #     """Mark specific tick labels on the heatmap"""
    #     annotated_labels = np.ma.masked_where(masks, labels)
    #     self._add_plot(side, Chart.AnnotatedLabel, annotated_labels,
    #                    name, size, **options)

    def add_dendrogram(self, side, name=None, method=None, metric=None,
                       linkage=None, show=True, size=0.5):
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
            self._deform.is_row_cluster = True
        else:
            self._col_den.append(
                dict(name=plot_name, show=show, pos="col",
                     side=side, method=method, metric=metric
                     )
            )
            self._deform.is_col_cluster = True

    def split_row(self, cut=None, labels=None, order=None, spacing=0.01):
        self._deform.hspace = spacing
        if cut is not None:
            self._deform.set_split_row(breakpoints=cut)

    def split_col(self, cut=None, labels=None, order=None, spacing=0.01):
        self._deform.wspace = spacing
        if cut is not None:
            self._deform.set_split_col(breakpoints=cut)

    def _setup_axes(self):
        deform = self._deform
        # split the main axes
        if deform.is_split:
            self.grid.split(
                "main",
                w_ratios=deform.col_ratios,
                h_ratios=deform.row_ratios,
                wspace=deform.wspace,
                hspace=deform.hspace
            )

        # split column axes
        if deform.is_col_split:
            for plan in self._col_plan:
                self.grid.split(
                    plan.name,
                    w_ratios=deform.col_ratios,
                    wspace=deform.wspace
                )

        # split row axes
        if deform.is_row_split:
            for plan in self._row_plan:
                self.grid.split(
                    plan.name,
                    h_ratios=deform.row_ratios,
                    hspace=deform.hspace
                )

    def _render_dendrogram(self):
        deform = self._deform
        for den in (self._row_den + self._col_den):
            if den['show']:
                ax = self.grid.get_ax(den['name'])
                ax.set_axis_off()
                spacing = deform.hspace
                den_obj = deform.get_row_dendrogram()
                if den['pos'] == "col":
                    spacing = deform.wspace
                    den_obj = deform.get_col_dendrogram()
                den_obj.draw(ax, orient=den['side'], spacing=spacing)

    def _render_plan(self):
        deform = self._deform
        for plan in self._col_plan:
            render_data = plan.data
            if not plan.no_split:
                render_data = deform.transform_col(plan.data)
            plan.set_render_data(render_data)
            axes = self.grid.get_canvas_ax(plan.name)
            plan.render(axes)

        # render other plots
        for plan in self._row_plan:
            # plan.data = plan.data.T
            render_data = plan.data
            if not plan.no_split:
                render_data = deform.transform_row(plan.data)
            plan.set_render_data(render_data)
            axes = self.grid.get_canvas_ax(plan.name)
            plan.render(axes)

    def get_deform(self):
        return self._deform

    def auto_legend(self, side):
        """Draw legend based on the order of annotation"""
        pass

    @property
    def row_cluster(self):
        return len(self._row_den) > 0

    @property
    def col_cluster(self):
        return len(self._col_den) > 0
