from __future__ import annotations

from copy import deepcopy
from typing import List
from uuid import uuid4

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ._deform import Deformation
from ._plotter import Chart
from .layout import CrossGrid
from .plotter import RenderPlan
from .utils import pairwise


def getaspect(ratio, w=None, h=None):
    canvas_size_min = np.array((2.0, 2.0))  # min length for width/height
    canvas_size_max = np.array((20.0, 20.0))  # max length for width/height

    set_w = w is not None
    set_h = h is not None

    canvas_height, canvas_width = None, None

    if set_w & set_h:
        canvas_height = h
    elif set_w:
        canvas_width = w
    else:
        if ratio >= 1:
            canvas_height = 4
        else:
            canvas_height = 2

    if canvas_height is not None:
        newsize = np.array((canvas_height / ratio, canvas_height))
    else:
        newsize = np.array((canvas_width, canvas_width * ratio))

    newsize /= min(1.0, *(newsize / canvas_size_min))
    newsize /= max(1.0, *(newsize / canvas_size_max))
    newsize = np.clip(newsize, canvas_size_min, canvas_size_max)
    return newsize


def reorder_index(arr, order=None):
    uniq = set(arr)
    indices = {x: [] for x in uniq}
    for ix, a in enumerate(arr):
        indices[a].append(ix)

    final_index = []
    if order is not None:
        for it in order:
            final_index += indices[it]
    else:
        for it in indices.values():
            final_index += it
    return final_index


def get_breakpoints(arr):
    breakpoints = []
    for ix, (a, b) in enumerate(pairwise(arr)):
        if a != b:
            breakpoints.append(ix + 1)
    return breakpoints


class _Base:
    gird: CrossGrid
    figure: Figure
    _row_plan: List[RenderPlan]
    _col_plan: List[RenderPlan]

    def __init__(self, w=None, h=None, data_aspect=1, name=None):
        w, h = getaspect(data_aspect, w=w, h=h)
        self.grid = CrossGrid(w=w, h=h, name=name)
        self.main_name = self.grid.main_name
        self._side_count = {"right": 0, "left": 0, "top": 0, "bottom": 0}
        self._col_plan = []
        self._row_plan = []

    def _get_plot_name(self, name, side, chart):
        self._side_count[side] += 1
        if name is None:
            return f"{chart}-{side}-{uuid4().hex}"
        else:
            return name

    def add_plot(self, side, plot: RenderPlan, name=None, size=None, pad=0.,
                 no_split=False):
        plot_name = self._get_plot_name(name, side, type(plot))

        add_ax_size = size if size is not None else 1.
        self.grid.add_ax(side, name=plot_name, size=add_ax_size, pad=pad)

        if side in ["top", "bottom"]:
            plan = self._col_plan
        else:
            plan = self._row_plan
        plot.set(name=plot_name, size=size, no_split=no_split)
        plot.set_side(side)

        if plot.canvas_size_unknown & (plot.size is None):
            s = plot.get_canvas_size()
            self.grid.set_render_size_inches(plot_name, s)

        plan.append(plot)

    def add_pad(self, side, size):
        self.grid.add_pad(side, size)

    def set_title(self, row=None, col=None, main=None):
        pass

    def get_ax(self, name):
        """Get a specific axes by name when available"""
        return self.grid.get_canvas_ax(name)

    def get_main_ax(self):
        """Return the main axes, like the heatmap axes"""
        return self.get_ax(self.main_name)


class MatrixBase(_Base):
    _row_reindex: List[int] = None
    _col_reindex: List[int] = None
    _allow_cluster: bool = True

    def __init__(self, cluster_data, w=None, h=None, data_aspect=1):
        super().__init__(w=w, h=h, data_aspect=data_aspect)
        self._row_den = []
        self._col_den = []
        self._cluster_data = cluster_data
        self._deform = Deformation(cluster_data)

    def add_dendrogram(self, side, name=None, method=None, metric=None,
                       show=True, size=0.5):
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
        show
        size

        Returns
        -------

        """
        if not self._allow_cluster:
            msg = f"Please specify cluster data when initialize " \
                  f"'{self.__class__.__name__}' class."
            raise ValueError(msg)
        plot_name = self._get_plot_name(name, side, Chart.Dendrogram)
        if show:
            self.grid.add_ax(side, name=plot_name, size=size)

        if side in ["right", "left"]:
            self._row_den.append(dict(name=plot_name, show=show,
                                      pos="row", side=side))
            self._deform.set_cluster(row=True)
            self._deform.set_row_cluster_params(method=method, metric=metric)
        else:
            self._col_den.append(dict(name=plot_name, show=show,
                                      pos="col", side=side))
            self._deform.set_cluster(col=True)
            self._deform.set_col_cluster_params(method=method, metric=metric)

    def split_row(self, cut=None, labels=None, order=None, spacing=0.01):
        self._deform.hspace = spacing
        if cut is not None:
            self._deform.set_split_row(breakpoints=cut)
        else:
            labels = np.asarray(labels)

            reindex = reorder_index(labels, order=order)
            self._deform.set_data_row_reindex(reindex)

            breakpoints = get_breakpoints(labels[reindex])
            self._deform.set_split_row(breakpoints=breakpoints)

    def split_col(self, cut=None, labels=None, order=None, spacing=0.01):
        self._deform.wspace = spacing
        if cut is not None:
            self._deform.set_split_col(breakpoints=cut)
        else:
            labels = np.asarray(labels)

            reindex = reorder_index(labels, order=order)
            self._deform.set_data_col_reindex(reindex)

            breakpoints = get_breakpoints(labels[reindex])
            self._deform.set_split_col(breakpoints=breakpoints)

    def _setup_axes(self):
        deform = self._deform
        # split the main axes
        if deform.is_split:
            self.grid.split(
                self.main_name,
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

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        # if add a number it will represent the size of the pad
        if isinstance(other, (int, float)):
            new_self = deepcopy(self)
            new_self.add_pad("right", other)
            return new_self
        return self.append_horizontal(other)

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        if isinstance(other, (int, float)):
            self.add_pad("bottom", other)
            return self
        return self.append_vertical(other)

    def append_horizontal(self, other: MatrixBase) -> MatrixList:
        new_grid = self.grid.append_horizontal(other.grid)
        new_list = MatrixList(new_grid)
        new_list.add_matrix(self)
        new_list.add_matrix(other)
        return new_list

    def append_vertical(self, other: MatrixBase) -> MatrixList:
        new_grid = self.grid.append_vertical(other.grid)
        new_list = MatrixList(new_grid)
        new_list.add_matrix(self)
        new_list.add_matrix(other)
        return new_list


class MatrixList:

    grid: CrossGrid
    figure: Figure

    def __init__(self, new_grid):
        self.grid = new_grid
        self._matrix_list = []

    def add_matrices(self, matrices):
        for m in matrices:
            new_m = deepcopy(m)
            self._matrix_list.append(new_m)

    def add_matrix(self, matrix):
        # make deepcopy so we don't change the previous one
        matrix = deepcopy(matrix)
        self._matrix_list.append(matrix)

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        if isinstance(other, (int, float)):
            self.grid.add_pad("right", other)
            return self
        return self.append_horizontal(other)

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        if isinstance(other, (int, float)):
            self.grid.add_pad("bottom", other)
            return self
        return self.append_vertical(other)

    def append_horizontal(self, other: MatrixBase) -> MatrixList:
        new_grid = self.grid.append_horizontal(other.grid)
        new_list = MatrixList(new_grid)
        new_list.add_matrices(self._matrix_list)
        new_list.add_matrix(other)
        return new_list

    def append_vertical(self, other: MatrixBase) -> MatrixList:
        new_grid = self.grid.append_vertical(other.grid)
        new_list = MatrixList(new_grid)
        new_list.add_matrices(self._matrix_list)
        new_list.add_matrix(other)
        return new_list

    def render(self, figure=None, aspect=1):
        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure

        for m in self._matrix_list:
            m.grid = self.grid
            m.render(figure=self.figure, aspect=aspect)

