from __future__ import annotations

from copy import deepcopy
from typing import List, Dict
from uuid import uuid4

import numpy as np
from legendkit.layout import vstack, hstack
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.colors import is_color_like
from matplotlib.figure import Figure

from ._deform import Deformation
from .dendrogram import Dendrogram
from .exceptions import SplitTwice
from .layout import CrossLayout, CompositeCrossLayout
from .plotter import RenderPlan, Title
from .utils import pairwise, batched, get_plot_name


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


class LegendMaker:
    layout: CrossLayout | CompositeCrossLayout
    _legend_box: List[Artist] = None
    _legend_name: str = None

    def __init__(self) -> None:
        self._legend_grid_kws: Dict = {}
        self._legend_draw_kws: Dict = {}
        self._draw_legend: bool = False

    def get_legends(self) -> Dict:
        """To get legends in a dict

        Returns
        -------
        A dict of {name: legends}

        """
        raise NotImplementedError("Should be implemented in derived class")

    def add_legends(self, side="right", pad=0, order=None,
                    stack_by=None, stack_size=3,
                    align_legends=None,
                    align_stacks=None,
                    spacing=10,
                    ):
        """Draw legend based on the order of annotation

        .. note::
            If you want to concatenate plots, please add legend after
            concatenation, this will merge legends from every plots

        Parameters
        ----------
        side : str, default: 'left'
            Which side to draw legend
        pad : number, default: 0
        order : array of plot name
        stack_by :
        stack_size :
        align_legends :
        align_stacks :
        spacing :

        """
        self._draw_legend = True
        if stack_by is None:
            stack_by = "col" if side in ["right", "left"] else "row"
        if align_stacks is None:
            align_stacks = "baseline"
        if align_legends is None:
            align_legends = "left" if stack_by == "col" else "bottom"

        self._legend_grid_kws = dict(side=side, size=0.01, pad=pad)
        self._legend_draw_kws = dict(
            order=order, stack_by=stack_by, stack_size=stack_size,
            align_legends=align_legends, align_stacks=align_stacks,
            spacing=spacing)

    def remove_legends(self):
        self._draw_legend = False
        self.layout.remove_legend_ax()

    def _legends_drawer(self, ax):
        legends = self.get_legends()

        # force to remove all legends before drawing
        # In case some legends are added implicitly
        # This may not be a good solution
        for _, legs in legends.items():
            for leg in legs:
                try:
                    leg.remove()
                except Exception:
                    pass

        legend_order = self._legend_draw_kws['order']
        stack_by = self._legend_draw_kws['stack_by']
        stack_size = self._legend_draw_kws['stack_size']
        align_legends = self._legend_draw_kws['align_legends']
        align_stacks = self._legend_draw_kws['align_stacks']

        inner, outer = vstack, hstack
        if stack_by == "row":
            inner, outer = outer, inner

        all_legs = []
        if legend_order is None:
            for name, legs in legends.items():
                all_legs += legs
        else:
            for name in legend_order:
                all_legs += legends[name]

        bboxes = []
        for legs in batched(all_legs, stack_size):
            box = inner(legs, align=align_legends, spacing=10)
            bboxes.append(box)
        legend_box = outer(bboxes, align=align_stacks, loc="center left",
                           spacing=10)
        ax.add_artist(legend_box)
        # uncomment this to visualize legend ax
        # from matplotlib.patches import Rectangle
        # rect = Rectangle((0, 0), 1, 1,
        #                  fill=None,
        #                  edgecolor="r",
        #                  transform=ax.transAxes)
        # ax.add_artist(rect)
        return legend_box

    def _freeze_legend(self, figure):
        if self._draw_legend:
            self.layout.add_legend_ax(**self._legend_grid_kws)
            renderer = figure.canvas.get_renderer()
            legend_ax = figure.add_axes([0, 0, 1, 1])
            legends_box = self._legends_drawer(legend_ax)
            bbox = legends_box.get_window_extent(renderer)
            if self._legend_grid_kws['side'] in ["left", "right"]:
                size = bbox.xmax - bbox.xmin
            else:
                size = bbox.ymax - bbox.ymin
            print("Legend size inches", size / 72)
            self.layout.set_legend_size(size / 72)
            legend_ax.remove()

    def _render_legend(self):
        if self._draw_legend:
            legend_ax = self.layout.get_legend_ax()
            legend_ax.set_axis_off()
            legend_box = self._legends_drawer(legend_ax)
            self._legend_box = legend_box


class WhiteBoard(LegendMaker):
    """The base class that handle all rendering process

    """
    layout: CrossLayout
    figure: Figure
    _row_plan: List[RenderPlan]
    _col_plan: List[RenderPlan]
    _layer_plan: List[RenderPlan]

    def __init__(self, width=None, height=None, name=None):
        self.main_name = get_plot_name(name, "main", "board")
        width = 5 if width is None else width
        height = 5 if height is None else height
        self.layout = CrossLayout(name=self.main_name,
                                  width=width,
                                  height=height)

        # self._side_count = {"right": 0, "left": 0, "top": 0, "bottom": 0}
        self._col_plan = []
        self._row_plan = []
        self._layer_plan = []
        # use to mark if legend is enabled for a RenderPlan
        self._legend_switch = {}
        super().__init__()

    def add_plot(self, side, plot: RenderPlan, name=None,
                 size=None, pad=0., legend=True):
        plot_name = get_plot_name(name, side, plot.__class__.__name__)
        self._legend_switch[plot_name] = legend

        if size is not None:
            ax_size = size
        else:
            if plot.size is not None:
                ax_size = plot.size
            else:
                ax_size = 1.

        self.layout.add_ax(side, name=plot_name, size=ax_size, pad=pad)

        if side in ["top", "bottom"]:
            plan = self._col_plan
        else:
            plan = self._row_plan
        plot.set(name=plot_name, size=size)
        plot.set_side(side)

        plan.append(plot)

    def add_left(self, plot: RenderPlan, name=None,
                 size=None, pad=0., legend=True):
        self.add_plot("left", plot, name, size, pad, legend)

    def add_right(self, plot: RenderPlan, name=None,
                  size=None, pad=0., legend=True):
        self.add_plot("right", plot, name, size, pad, legend)

    def add_top(self, plot: RenderPlan, name=None,
                size=None, pad=0., legend=True):
        self.add_plot("top", plot, name, size, pad, legend)

    def add_bottom(self, plot: RenderPlan, name=None,
                   size=None, pad=0., legend=True):
        self.add_plot("bottom", plot, name, size, pad, legend)

    def _render_plan(self):
        for plan in self._col_plan:
            axes = self.layout.get_ax(plan.name)
            plan.render(axes)

        # render other plots
        for plan in self._row_plan:
            axes = self.layout.get_ax(plan.name)
            plan.render(axes)

        main_ax = self.get_main_ax()
        for plan in self._get_layers_zorder():
            plan.render(main_ax)

    def add_layer(self, plot: RenderPlan, zorder=None, name=None, legend=True):
        if name is None:
            name = plot.name
        plot_type = plot.__class__.__name__
        name = get_plot_name(name, side="main", chart=plot_type)
        self._legend_switch[name] = legend
        if not plot.render_main:
            msg = f"{plot_type} " \
                  f"cannot be rendered as another layer."
            raise TypeError(msg)
        if zorder is not None:
            plot.zorder = zorder
        plot.set(name=name)
        plot.set_side("main")
        self._layer_plan.append(plot)

    def _get_layers_zorder(self):
        return sorted(self._layer_plan, key=lambda p: p.zorder)

    def add_pad(self, side, size):
        self.layout.add_pad(side, size)

    def add_canvas(self, side, name, size, pad=0.):
        self.layout.add_ax(side, name, size, pad=pad)

    def add_title(self, top=None, bottom=None, left=None, right=None,
                  pad=.1, **props):
        if left is not None:
            self.add_plot("left", Title(left, **props), pad=pad)
        if right is not None:
            self.add_plot("right", Title(right, **props), pad=pad)
        if top is not None:
            self.add_plot("top", Title(top, **props), pad=pad)
        if bottom is not None:
            self.add_plot("bottom", Title(bottom, **props), pad=pad)

    def get_ax(self, name):
        """Get a specific axes by name when available

        If the axes is split, multiple axes will be returned

        .. note::
            This will not work before `render` is called

        """
        return self.layout.get_ax(name)

    def get_main_ax(self):
        """Return the main axes"""
        return self.layout.get_main_ax()

    def _extra_legends(self):
        """If there are legends that cannot get from RenderPlan

        Must be overridden in derived class

        """
        return {}

    def get_legends(self):
        legends = {}
        legends.update(self._extra_legends())
        for plan in self._layer_plan + self._col_plan + self._row_plan:
            # Not every render plan has legend
            if self._legend_switch[plan.name]:
                legs = plan.get_legends()
                if legs is not None:
                    if isinstance(legs, Artist):
                        legs = [legs]
                    legends[plan.name] = legs
        return legends

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        pass

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        pass

    def append(self, side, other):
        compose_board = CompositeBoard(self)
        compose_board.append(side, other)
        return compose_board

    def _freeze_flex_plots(self, figure):
        for plan in self._col_plan + self._row_plan:
            if plan.is_flex:
                self.layout.set_render_size(plan.name,
                                            plan.get_canvas_size(figure))

    def render(self, figure=None, scale=1, refreeze=True):
        """

        Parameters
        ----------
        figure
        scale
        refreeze : bool
            If True, recompute the Layout on render

        Returns
        -------

        """
        if figure is None:
            figure = plt.figure()
        self.figure = figure
        self._freeze_legend(figure)
        self._freeze_flex_plots(figure)

        # if refreeze:
        #     self.figure = self.layout.freeze(figure=figure, scale=scale)
        # else:
        #     self.figure = self.layout.figure
        self.layout.freeze(figure=figure, scale=scale)

        # render other plots
        self._render_plan()
        self._render_legend()


class CompositeBoard(LegendMaker):
    layout: CompositeCrossLayout
    figure: Figure

    def __init__(self, main_board: WhiteBoard):
        self.main_board = self.new_board(main_board)
        self.main_board.remove_legends()
        self.layout = CompositeCrossLayout(self.main_board.layout)
        self._board_list = [self.main_board]
        super().__init__()

    @staticmethod
    def new_board(board):
        board = deepcopy(board)
        board.remove_legends()
        return board

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        pass

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        pass

    def append(self, side, other):
        board = self.new_board(other)
        self._board_list.append(board)
        self.layout.append(side, board.layout)

    def render(self, figure=None, scale=1):
        if figure is None:
            figure = plt.figure()
        self._freeze_legend(figure)
        self.layout.freeze(figure=figure, scale=scale)
        self.figure = self.layout.figure

        for board in self._board_list:
            board.render(figure=self.figure)

        self._render_legend()

    def get_legends(self):
        legends = {}
        for m in self._board_list:
            legends.update(m.get_legends())
        return legends


class ClusterBoard(WhiteBoard):
    _row_reindex: List[int] = None
    _col_reindex: List[int] = None
    # If cluster data need to be defined by user
    _allow_cluster: bool = True
    _split_col: bool = False
    _split_row: bool = False
    _mesh = None
    square = False

    def __init__(self, cluster_data, width=None, height=None, name=None):
        super().__init__(width=width, height=height, name=name)
        self._row_den = []
        self._col_den = []
        self._cluster_data = cluster_data
        self._deform = Deformation(cluster_data)

    def add_dendrogram(self, side, method=None, metric=None,
                       add_meta=True, add_base=True, add_divider=True,
                       meta_color=None, linewidth=None, colors=None,
                       divider_style="--",
                       show=True, name=None, size=0.5, pad=0.):
        """Run cluster and add dendrogram

        .. note::

            #. method and metric only works when you
               add the first row/col dendrogram.
            #. If `add_meta=False` and `add_base=False`, the dendrogram
               axes will not be created.

        Parameters
        ----------
        side
        method : str
            See scipy's :meth:`linkage <scipy.cluster.hierarchy.linkage>`
        metric : str
            See scipy's :meth:`linkage <scipy.cluster.hierarchy.linkage>`
        add_meta : bool
            If the data is split, a meta dendrogram can be drawn for data
            chunks. The mean value of the data chunk is used to calculate
            linkage matrix for meta dendrogram.
        add_base : bool
            Draw the base dendrogram for each data chunk. You can turn this
            off if the base dendrogram is too crowded.
        add_divider : bool
            Draw a divide line that tells the difference between
            base and meta dendrogram.
        divider_style : str, default: "--"
            The line style of the divide line
        meta_color : color
            The color of the meta dendrogram
        linewidth : float
            The linewidth for every dendrogram and divide line
        colors : color, array of color
            If only one color is specified, it will be applied to
            every dendrogram. If an array of color is specified, it will
            be applied to each base dendrogram.
        show : bool
            If False, the dendrogram will not be drawn and the axes will
            not be created.
        name : str
            The name of the dendrogram axes
        size : float
        pad : float

        Examples
        --------

        You can change how the linkage matrix is calculated

        .. plot::
            :context: close-figs

            >>> data = np.random.rand(10, 11)
            >>> import heatgraphy as hg
            >>> h = hg.Heatmap(data)
            >>> h.add_dendrogram("left", method="ward", colors="green")
            >>> h.render()

        Only show the meta dendrogram to avoid crowded dendrogram

        .. plot::
            :context: close-figs

            >>> h = hg.Heatmap(data)
            >>> h.split_row(cut=[4, 8])
            >>> h.add_dendrogram("left", add_base=False)
            >>> h.render()

        Change color for each base dendrogram

        .. plot::
            :context: close-figs

            >>> h = hg.Heatmap(data)
            >>> h.split_row(cut=[4, 8])
            >>> h.add_dendrogram("left", colors=["#5470c6", "#91cc75", "#fac858"])
            >>> h.render()

        """
        if not self._allow_cluster:
            msg = f"Please specify cluster data when initialize " \
                  f"'{self.__class__.__name__}' class."
            raise ValueError(msg)
        plot_name = get_plot_name(name, side, "Dendrogram")

        # if only colors is passed
        # the color should be applied to all
        if (colors is not None) & (is_color_like(colors)) & (
                meta_color is None):
            meta_color = colors

        # if nothing is added
        # close the dendrogram
        if (not add_meta) & (not add_base):
            show = False

        if show:
            self.layout.add_ax(side, name=plot_name, size=size, pad=pad)

        den_options = dict(name=plot_name, show=show, side=side,
                           add_meta=add_meta, add_base=add_base,
                           add_divider=add_divider, meta_color=meta_color,
                           linewidth=linewidth, colors=colors,
                           divider_style=divider_style)

        deform = self.get_deform()
        if side in ["right", "left"]:
            den_options['pos'] = "row"
            self._row_den.append(den_options)
            deform.set_cluster(row=True, method=method, metric=metric)
        else:
            den_options['pos'] = "col"
            self._col_den.append(den_options)
            deform.set_cluster(col=True, method=method, metric=metric)

    def hsplit(self, cut=None, labels=None, order=None, spacing=0.01):
        if self._split_row:
            raise SplitTwice(axis="horizontally")
        self._split_row = True

        self._deform.hspace = spacing
        if cut is not None:
            self._deform.set_split_row(breakpoints=cut)
        else:
            labels = np.asarray(labels)

            reindex = reorder_index(labels, order=order)
            self._deform.set_data_row_reindex(reindex)

            breakpoints = get_breakpoints(labels[reindex])
            self._deform.set_split_row(breakpoints=breakpoints)

    def vsplit(self, cut=None, labels=None, order=None, spacing=0.01):
        if self._split_col:
            raise SplitTwice(axis="vertically")
        self._split_col = True

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
        deform = self.get_deform()
        w_ratios = deform.col_ratios
        h_ratios = deform.row_ratios
        wspace = deform.wspace
        hspace = deform.hspace

        # split the main axes
        if deform.is_split:
            if w_ratios is not None:
                self.layout.vsplit(self.main_name, w_ratios, wspace)
            if h_ratios is not None:
                self.layout.hsplit(self.main_name, h_ratios, hspace)

        # split column axes
        if deform.is_col_split:
            for plan in self._col_plan:
                if not plan.no_split:
                    self.layout.vsplit(plan.name, w_ratios, wspace)

        # split row axes
        if deform.is_row_split:
            for plan in self._row_plan:
                if not plan.no_split:
                    self.layout.hsplit(plan.name, h_ratios, hspace)

    def _render_dendrogram(self):
        deform = self.get_deform()
        for den in (self._row_den + self._col_den):
            if den['show']:
                ax = self.layout.get_ax(den['name'])
                ax.set_axis_off()
                spacing = deform.hspace
                den_obj = deform.get_row_dendrogram()
                if den['pos'] == "col":
                    spacing = deform.wspace
                    den_obj = deform.get_col_dendrogram()
                if isinstance(den_obj, Dendrogram):
                    color = den['colors']
                    if (color is not None) & (not is_color_like(color)):
                        color = color[0]
                    den_obj.draw(ax, orient=den['side'], color=color,
                                 linewidth=den['linewidth'])
                else:
                    den_obj.draw(ax, orient=den['side'],
                                 spacing=spacing,
                                 add_meta=den['add_meta'],
                                 add_base=den['add_base'],
                                 base_colors=den['colors'],
                                 meta_color=den['meta_color'],
                                 linewidth=den['linewidth'],
                                 divide=den['add_divider'],
                                 divide_style=den['divider_style'],
                                 )

    def _render_plan(self):
        deform = self.get_deform()
        for plan in self._col_plan:
            if not plan.no_split:
                plan.set_deform(deform)
            axes = self.layout.get_ax(plan.name)
            plan.render(axes)

        # render other plots
        for plan in self._row_plan:
            if not plan.no_split:
                plan.set_deform(deform)
            axes = self.layout.get_ax(plan.name)
            plan.render(axes)

        main_ax = self.get_main_ax()
        for plan in self._get_layers_zorder():
            plan.set_deform(deform)
            plan.render(main_ax)

    def get_deform(self):
        return self._deform

    @property
    def row_cluster(self):
        return len(self._row_den) > 0

    @property
    def col_cluster(self):
        return len(self._col_den) > 0

    def render(self, figure=None, scale=1, refreeze=True):
        if figure is None:
            figure = plt.figure()
        self.figure = figure
        self._freeze_legend(figure)
        self._freeze_flex_plots(figure)

        # Make sure all axes is split
        self._setup_axes()
        # Place axes
        # if refreeze:
        #     self.figure = self.layout.freeze(figure=figure, scale=scale)
        # else:
        #     self.figure = self.layout.figure
        self.layout.freeze(figure=figure, scale=scale)
        # render other plots
        self._render_plan()
        # add row and col dendrogram
        self._render_dendrogram()
        self._render_legend()
