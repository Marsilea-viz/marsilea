from __future__ import annotations

import warnings
from copy import deepcopy
from numbers import Number
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
from .exceptions import SplitTwice, DuplicatePlotter
from .layout import CrossLayout, CompositeCrossLayout
from .plotter import RenderPlan, Title, SizedMesh
from .utils import pairwise, batched, get_plot_name, _check_side


def reorder_index(arr, order=None):
    uniq = set(arr)
    indices = {x: [] for x in uniq}
    for ix, a in enumerate(arr):
        indices[a].append(ix)

    if order is None:
        order = sorted(uniq)

    final_index = []
    for it in order:
        final_index += indices[it]
    return final_index, order


def get_breakpoints(arr):
    breakpoints = []
    for ix, (a, b) in enumerate(pairwise(arr)):
        if a != b:
            breakpoints.append(ix + 1)
    return breakpoints


class LegendMaker:
    """The factory class to handle legends"""

    layout: CrossLayout | CompositeCrossLayout
    _legend_box: List[Artist] = None
    _legend_name: str = None

    def __init__(self) -> None:
        self._legend_grid_kws: Dict = {}
        self._legend_draw_kws: Dict = {}
        self._user_legends = {}
        self._draw_legend: bool = False

    def get_legends(self) -> Dict:
        """To get legends in a dict

        Returns
        -------
        A dict of {name: legends}

        """
        raise NotImplementedError("Should be implemented in derived class")

    def custom_legend(self, legend_func, name=None):
        """Add a custom legend

        Parameters
        ----------

        legend_func : Callable
            A function that return the legend object,
            the legend must be an `Artist <matplotlib.artist.Artists>`
        name : str, optional
            The name of the legend

        """
        if name is None:
            name = str(uuid4())
        self._user_legends[name] = legend_func

    def add_legends(
        self,
        side="right",
        pad=0.0,
        order=None,
        stack_by=None,
        stack_size=3,
        align_legends=None,
        align_stacks=None,
        legend_spacing=10,
        stack_spacing=10,
        box_padding=2,
    ):
        """Draw legend based on the order of annotation

        .. note::
            If you want to concatenate plots, please add legend after
            concatenation, this will merge legends from every plots

        Stack is a pack of legends

        Parameters
        ----------
        side : {'right', 'left', 'top', 'bottom'}, default: 'right'
            Which side to draw legend
        pad : number, default: 0
            The padding of the legend in inches
        order : array of plot name
            The order of the legend, if None, the order will be the same as the order when adding plotters.
            You need to set name for each plotter when adding them, and specify the order here.
        stack_by : {'row', 'col'}
            The direction to stack legends
        stack_size : int, default: 3
            The number of legends in a stack
        align_legends : {'left', 'right', 'top', 'bottom'}
            The side to align legends in a stack
        align_stacks : {'left', 'right', 'top', 'bottom'}
            The side to align stacks
        legend_spacing : float, default: 10
            The space between legends
        stack_spacing : float, default: 10
            The space between stacks
        box_padding : float, default: 2
            Add pad around the whole legend box

        """
        # TODO: Allow user to control where to add legends,
        #       relative to the main canvas or the whole figure
        # TODO: Allow user to add stack_size as a list
        #       Each stack can contain different number of legends
        _check_side(side)
        self._draw_legend = True
        if stack_by is None:
            stack_by = "col" if side in ["right", "left"] else "row"
        if align_stacks is None:
            align_stacks = "baseline"
        if align_legends is None:
            align_legends = "left" if stack_by == "col" else "bottom"

        self._legend_grid_kws = dict(side=side, size=0.01, pad=pad)
        self._legend_draw_kws = dict(
            order=order,
            stack_by=stack_by,
            stack_size=stack_size,
            align_legends=align_legends,
            align_stacks=align_stacks,
            legend_spacing=legend_spacing,
            stack_spacing=stack_spacing,
            box_padding=box_padding,
        )

    def remove_legends(self):
        self._draw_legend = False
        self.layout.remove_legend_ax()

    def _legends_drawer(self, ax):
        user_legends = {k: [v()] for k, v in self._user_legends.items()}
        legends = {**self.get_legends(), **user_legends}

        # force to remove all legends before drawing
        # In case some legends are added implicitly
        # This may not be a good solution
        for _, legs in legends.items():
            for leg in legs:
                try:
                    leg.remove()
                except Exception:
                    pass

        legend_order = self._legend_draw_kws["order"]
        stack_by = self._legend_draw_kws["stack_by"]
        stack_size = self._legend_draw_kws["stack_size"]
        align_legends = self._legend_draw_kws["align_legends"]
        align_stacks = self._legend_draw_kws["align_stacks"]
        legend_spacing = self._legend_draw_kws["legend_spacing"]
        stack_spacing = self._legend_draw_kws["stack_spacing"]
        box_padding = self._legend_draw_kws["box_padding"]

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
            box = inner(legs, align=align_legends, spacing=legend_spacing)
            bboxes.append(box)
        legend_box = outer(
            bboxes,
            align=align_stacks,
            loc="center left",
            spacing=stack_spacing,
            padding=box_padding,
        )
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
            if self.layout.get_legend_ax() is None:
                self.layout.add_legend_ax(**self._legend_grid_kws)
            renderer = figure.canvas.get_renderer()
            legend_ax = figure.add_axes([0, 0, 1, 1])
            legends_box = self._legends_drawer(legend_ax)
            bbox = legends_box.get_window_extent(renderer)
            if self._legend_grid_kws["side"] in ["left", "right"]:
                size = bbox.xmax - bbox.xmin
            else:
                size = bbox.ymax - bbox.ymin
            self.layout.set_legend_size(size / figure.get_dpi())
            legend_ax.remove()

    def _render_legend(self):
        if self._draw_legend:
            legend_ax = self.layout.get_legend_ax()
            legend_ax.set_axis_off()
            legend_box = self._legends_drawer(legend_ax)
            self._legend_box = legend_box


class WhiteBoard(LegendMaker):
    """The base class that handle all rendering process

    Parameters
    ----------
    width : float, optional
        The width of the main canvas in inches
    height : float, optional
        The height of the main canvas in inches
    name : str, optional
        The name of the main canvas
    margin : float, 4-tuple, optional
        The margin of the main canvas in inches
    init_main : bool, optional
        If True, the main canvas will be initialized


    See Also
    --------
    :class:`~marsilea.base.ClusterBoard`


    Attributes
    ----------
    layout : CrossLayout
        The layout manager
    figure : Figure
        The matplotlib figure object

    Examples
    --------
    Create a violin plot in white board

    .. plot::
        :context: close-figs

        >>> import numpy as np
        >>> import marsilea as ma
        >>> data = np.random.rand(10, 10)
        >>> h = ma.WhiteBoard(height=2)
        >>> h.add_layer(ma.plotter.Violin(data))
        >>> h.render()


    """

    layout: CrossLayout
    figure: Figure = None
    _row_plan: List[RenderPlan]
    _col_plan: List[RenderPlan]
    _layer_plan: List[RenderPlan]

    def __init__(self, width=None, height=None, name=None, margin=0.2, init_main=True):
        self.main_name = get_plot_name(name, "main", "board")
        self._main_size_updatable = (width is None) & (height is None)
        width = 4 if width is None else width
        height = 4 if height is None else height
        self.layout = CrossLayout(
            name=self.main_name,
            width=width,
            height=height,
            margin=margin,
            init_main=init_main,
        )

        # self._side_count = {"right": 0, "left": 0, "top": 0, "bottom": 0}
        self._col_plan = []
        self._row_plan = []
        self._layer_plan = []
        # use to mark if legend is enabled for a RenderPlan
        self._legend_switch = {}
        super().__init__()

    def add_plot(
        self, side, plot: RenderPlan, name=None, size=None, pad=0.0, legend=True
    ):
        """Add a plotter to the board

        Parameters
        ----------
        side : {"left", "right", "top", "bottom"}
            Which side to add the plotter
        plot : RenderPlan
            The plotter to add
        name : str, optional
            The name of the plot
        size : float, optional
            The size of the plot in inches
        pad : float, optional
            The padding of the plot in inches
        legend : bool, optional
            If True, the legend will be included when calling :meth:`~marsilea.base.LegendMaker.add_legends`

        """
        if plot.name is not None:
            raise DuplicatePlotter(plot)
        plot_name = get_plot_name(name, side, plot.__class__.__name__)
        self._legend_switch[plot_name] = legend

        if size is not None:
            ax_size = size
        else:
            if plot.size is not None:
                ax_size = plot.size
            else:
                ax_size = 1.0

        self.layout.add_ax(side, name=plot_name, size=ax_size, pad=pad)

        if side in ["top", "bottom"]:
            plan = self._col_plan
        else:
            plan = self._row_plan
        plot.set(name=plot_name, size=size)
        plot.set_side(side)

        plan.append(plot)

    def add_left(self, plot: RenderPlan, name=None, size=None, pad=0.0, legend=True):
        """Add a plotter to the left-side of main canvas

        Parameters
        ----------
        plot : RenderPlan
            The plotter to add
        name : str, optional
            The name of the plot
        size : float, optional
            The size of the plot in inches
        pad : float, optional
            The padding of the plot in inches
        legend : bool, optional
            If True, the legend will be included when calling :meth:`~marsilea.base.LegendMaker.add_legends`

        """
        self.add_plot("left", plot, name, size, pad, legend)

    def add_right(self, plot: RenderPlan, name=None, size=None, pad=0.0, legend=True):
        """Add a plotter to the right-side of main canvas

        Parameters
        ----------
        plot : RenderPlan
            The plotter to add
        name : str, optional
            The name of the plot
        size : float, optional
            The size of the plot in inches
        pad : float, optional
            The padding of the plot in inches
        legend : bool, optional
            If True, the legend will be included when calling :meth:`~marsilea.base.LegendMaker.add_legends`

        """
        self.add_plot("right", plot, name, size, pad, legend)

    def add_top(self, plot: RenderPlan, name=None, size=None, pad=0.0, legend=True):
        """Add a plotter to the top-side of main canvas

        Parameters
        ----------
        plot : RenderPlan
            The plotter to add
        name : str, optional
            The name of the plot
        size : float, optional
            The size of the plot in inches
        pad : float, optional
            The padding of the plot in inches
        legend : bool, optional
            If True, the legend will be included when calling :meth:`~marsilea.base.LegendMaker.add_legends`

        """
        self.add_plot("top", plot, name, size, pad, legend)

    def add_bottom(self, plot: RenderPlan, name=None, size=None, pad=0.0, legend=True):
        """Add a plotter to the bottom-side of main canvas

        Parameters
        ----------
        plot : RenderPlan
            The plotter to add
        name : str, optional
            The name of the plot
        size : float, optional
            The size of the plot in inches
        pad : float, optional
            The padding of the plot in inches
        legend : bool, optional
            If True, the legend will be included when calling :meth:`~marsilea.base.LegendMaker.add_legends`

        """
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
        """Add a plotter to the main canvas

        .. note::

            Not every plotter can be added as a layer.

        Parameters
        ----------
        plot : RenderPlan
            The plotter to add
        zorder : int, optional
            The zorder of the plot
        name : str, optional
            The name of the plot
        legend : bool, optional
            If True, the legend will be included when calling :meth:`~marsilea.base.LegendMaker.add_legends`

        """
        if name is None:
            name = plot.name
        plot_type = plot.__class__.__name__
        name = get_plot_name(name, side="main", chart=plot_type)
        self._legend_switch[name] = legend
        if not plot.render_main:
            msg = f"{plot_type} " f"cannot be rendered as another layer."
            raise TypeError(msg)
        if zorder is not None:
            plot.zorder = zorder
        plot.set(name=name)
        plot.set_side("main")
        self._layer_plan.append(plot)

        # SizedMesh will update the main canvas size
        if self._main_size_updatable:
            if isinstance(plot, SizedMesh):
                w, h = plot.update_main_canvas_size()
                self.layout.set_main_width(w)
                self.layout.set_main_height(h)
                # only update once,
                # if we have more plot in the future
                # that will change canvas size
                self._main_size_updatable = False

    def _get_layers_zorder(self):
        return sorted(self._layer_plan, key=lambda p: p.zorder)

    def add_pad(self, side, size):
        """Add padding to the main canvas

        Parameters
        ----------
        side : {"left", "right", "top", "bottom"}
            Which side to add padding
        size : float
            The size of padding in inches

        """
        self.layout.add_pad(side, size)

    def add_canvas(self, side, name, size, pad=0.0):
        """Add an axes to the main canvas

        Parameters
        ----------
        side : {"left", "right", "top", "bottom"}
            Which side to add the axes
        name : str
            The name of the axes
        size : float
            The size of the axes in inches
        pad : float, optional
            The padding of the axes in inches

        """
        self.layout.add_ax(side, name, size, pad=pad)

    def add_title(self, top=None, bottom=None, left=None, right=None, pad=0, **props):
        """A shortcut to add title to the main canvas

        Parameters
        ----------
        top : str, optional
            The title of the top side
        bottom : str, optional
            The title of the bottom side
        left : str, optional
            The title of the left side
        right : str, optional
            The title of the right side
        pad : float, optional
            The padding of the title in inches
        props : dict
            The properties of the title

        Returns
        -------

        """
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
        """Get all legends from the main canvas"""
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
        return self.append("right", other)

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        return self.append("bottom", other)

    def append(self, side, other):
        """Append two :class:`~marsilea.base.CrossLayout` together"""
        compose_board = CompositeBoard(self)
        compose_board.append(side, other)
        return compose_board

    def _freeze_flex_plots(self, figure):
        main_cell = self.layout.main_cell
        main_width = main_cell.width
        main_height = main_cell.height

        for plan in self._col_plan + self._row_plan:
            if plan.size is None:
                render_size = plan.get_canvas_size(
                    figure, main_width=main_width, main_height=main_height
                )
                if render_size is not None:
                    self.layout.set_render_size(plan.name, render_size)

    def render(self, figure=None, scale=1):
        """Finalize the layout and render all plots

        Parameters
        ----------
        figure : :class:`~matplotlib.figure.FigureBase`, optional
            The matplotlib figure object
        scale : float, optional
            The scale value of the figure size. You can use this to
            adjust the overall size of the figure

        Returns
        -------

        """
        if figure is None:
            figure = plt.figure()
        self.figure = figure
        self._freeze_legend(figure)
        self._freeze_flex_plots(figure)

        self.layout.freeze(figure=figure, scale=scale)

        # render other plots
        self._render_plan()
        self._render_legend()

    def save(self, fname, **kwargs):
        """Save the figure to a file

        This will force a re-render of the figure

        Parameters
        ----------
        fname : str, path-like
            The file name to save
        kwargs : dict
            Additional options for saving the figure, will be passed to :meth:`~matplotlib.pyplot.savefig`

        """
        self.render()
        save_options = dict(bbox_inches="tight")
        save_options.update(kwargs)
        self.figure.savefig(fname, **save_options)

    def set_margin(self, margin: float | tuple[float, float, float, float]):
        """Set margin of the main canvas

        Parameters
        ----------
        margin : float, 4-tuple
            The margin of the main canvas in inches

        """
        self.layout.set_margin(margin)


class ZeroWidth(WhiteBoard):
    """A utility class to initialize a canvas \
    with zero width

    This is useful when you try to stack many plots

    Parameters
    ----------
    height : float
        The
    name : str
    margin : float

    """

    def __init__(self, height, name=None, margin=0.2):
        super().__init__(
            width=0, height=height, name=name, margin=margin, init_main=False
        )


class ZeroHeight(WhiteBoard):
    """A utility class to initialize a canvas \
    with zero height

    This is useful when you try to stack many plots

    """

    def __init__(self, width, name=None, margin=0.2):
        super().__init__(
            width=width, height=0, name=name, margin=margin, init_main=False
        )


class CompositeBoard(LegendMaker):
    layout: CompositeCrossLayout = None
    figure: Figure = None

    def __init__(self, main_board: WhiteBoard):
        self.main_board = self.new_board(main_board)
        # self.main_board.remove_legends()
        self.layout = CompositeCrossLayout(self.main_board.layout)
        self._board_list = [self.main_board]
        super().__init__()

    @staticmethod
    def new_board(board):
        board = deepcopy(board)
        if isinstance(board, LegendMaker):
            board.remove_legends()
        return board

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        return self.append("right", other)

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        return self.append("bottom", other)

    def append(self, side, other):
        if isinstance(other, Number):
            self.layout.append(side, other)
        else:
            board = self.new_board(other)
            self._board_list.append(board)
            self.layout.append(side, board.layout)
        return self

    def render(self, figure=None, scale=1):
        if figure is None:
            figure = plt.figure()
        self._freeze_legend(figure)
        for board in self._board_list:
            board._freeze_flex_plots(figure)
        self.layout.freeze(figure=figure, scale=scale)
        self.figure = figure
        for board in self._board_list:
            board.render(figure=self.figure)

        self._render_legend()

    def save(self, fname, **kwargs):
        if self.figure is not None:
            save_options = dict(bbox_inches="tight")
            save_options.update(kwargs)
            self.figure.savefig(fname, **save_options)
        else:
            warnings.warn(
                "Figure does not exist, " "please render it before saving as file."
            )

    def get_legends(self):
        legends = {}
        for m in self._board_list:
            legends.update(m.get_legends())
        return legends

    def get_ax(self, board_name, ax_name):
        return self.layout.get_ax(board_name, ax_name)

    def set_margin(self, margin):
        self.layout.set_margin(margin)


class ClusterBoard(WhiteBoard):
    """A main canvas class that can handle cluster data

    Parameters
    ----------
    cluster_data : ndarray
        The cluster data
    width : float, optional
        The width of the main canvas in inches
    height : float, optional
        The height of the main canvas in inches
    name : str, optional
        The name of the main canvas
    margin : float, 4-tuple, optional
        The margin of the main canvas in inches
    init_main : bool, optional
        If True, the main canvas will be initialized


    See Also
    --------
    :class:`~marsilea.base.WhiteBoard`


    """

    _row_reindex: List[int] = None
    _col_reindex: List[int] = None
    # If cluster data need to be defined by user
    _allow_cluster: bool = True
    _split_col: bool = False
    _split_row: bool = False
    _mesh = None

    def __init__(
        self,
        cluster_data,
        width=None,
        height=None,
        name=None,
        margin=0.2,
        init_main=True,
    ):
        super().__init__(
            width=width, height=height, name=name, margin=margin, init_main=init_main
        )
        self._row_den = []
        self._col_den = []
        cluster_data = np.asarray(cluster_data)
        if cluster_data.ndim != 2:
            raise ValueError("Cluster data must be 2D array")
        self._cluster_data = cluster_data
        self._deform = Deformation(cluster_data)

    def add_dendrogram(
        self,
        side,
        method=None,
        metric=None,
        linkage=None,
        meta_linkage=None,
        add_meta=True,
        add_base=True,
        add_divider=True,
        meta_color=None,
        linewidth=None,
        colors=None,
        divider_style="--",
        meta_ratio=0.2,
        show=True,
        name=None,
        size=0.5,
        pad=0.0,
        get_meta_center=None,
        rasterized=False,
    ):
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
        linkage : ndarray
            Precomputed linkage matrix.
            See scipy's :meth:`linkage <scipy.cluster.hierarchy.linkage>` for
            specific format.
        meta_linkage : ndarray
            Precomputed chunk-level linkage matrix.
            See scipy's :meth:`linkage <scipy.cluster.hierarchy.linkage>` for
            specific format.
        add_meta : None | bool
            By default, add_meta is set to False if the linkage is provided, otherwise True.
            If the data is split, a meta dendrogram can be drawn for data
            chunks. The mean value of the data chunk is used to calculate
            linkage matrix for meta dendrogram.
        add_base : None | bool
            By default, add_meta is set to False if the linkage is provided, otherwise True.
            Draw the base dendrogram for each data chunk. You can turn this
            off if the base dendrogram is too crowded.
        add_divider : bool
            Draw a divide line that tells the difference between
            base and meta dendrogram.
        divider_style : str, default: "--"
            The line style of the divide line
        meta_color : color
            The color of the meta dendrogram
        meta_ratio : float
            The size of meta dendrogram relative to the base dendrogram
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
        get_meta_center: callable
            A function to calculate the centroid of data. It should accept a 2D numpy
            array as input and return a 1D numpy array of the same length as the number
            of columns in the input, representing the centroid. The default will use the
            mean values.
        rasterized : bool
            If True, the dendrogram will be rasterized

        Examples
        --------

        You can change how the linkage matrix is calculated

        .. plot::
            :context: close-figs

            >>> data = np.random.rand(10, 11)
            >>> import marsilea as ma
            >>> h = ma.Heatmap(data)
            >>> h.add_dendrogram("left", method="ward", colors="green")
            >>> h.render()

        Only show the meta dendrogram to avoid crowded dendrogram

        .. plot::
            :context: close-figs

            >>> h = ma.Heatmap(data)
            >>> h.cut_rows(cut=[4, 8])
            >>> h.add_dendrogram("left", add_base=False)
            >>> h.render()

        Change color for each base dendrogram

        .. plot::
            :context: close-figs

            >>> h = ma.Heatmap(data)
            >>> h.cut_rows(cut=[4, 8])
            >>> h.add_dendrogram("left", colors=["#5470c6", "#91cc75", "#fac858"])
            >>> h.render()

        """
        if not self._allow_cluster:
            msg = (
                f"Please specify cluster data when initialize "
                f"'{self.__class__.__name__}' class."
            )
            raise ValueError(msg)
        plot_name = get_plot_name(name, side, "Dendrogram")

        # if only colors is passed
        # the color should be applied to all
        if (colors is not None) & (is_color_like(colors)) & (meta_color is None):
            meta_color = colors

        # if nothing is added
        # close the dendrogram
        if (not add_meta) & (not add_base):
            show = False

        if show:
            self.layout.add_ax(side, name=plot_name, size=size, pad=pad)

        den_options = dict(
            name=plot_name,
            show=show,
            side=side,
            add_meta=add_meta,
            add_base=add_base,
            add_divider=add_divider,
            meta_color=meta_color,
            linewidth=linewidth,
            colors=colors,
            divider_style=divider_style,
            meta_ratio=meta_ratio,
            rasterized=rasterized,
        )

        deform = self.get_deform()
        if side in ["right", "left"]:
            den_options["pos"] = "row"
            self._row_den.append(den_options)
            deform.set_cluster(
                row=True,
                method=method,
                metric=metric,
                linkage=linkage,
                meta_linkage=meta_linkage,
                use_meta=add_meta,
                get_meta_center=get_meta_center,
                rasterized=rasterized,
            )
        else:
            den_options["pos"] = "col"
            self._col_den.append(den_options)
            deform.set_cluster(
                col=True,
                method=method,
                metric=metric,
                linkage=linkage,
                meta_linkage=meta_linkage,
                use_meta=add_meta,
                get_meta_center=get_meta_center,
                rasterized=rasterized,
            )

    def hsplit(self, cut=None, labels=None, order=None, spacing=0.01):
        """Split the main canvas horizontally

        .. deprecated:: 0.5.0
            Use :meth:`~marsilea.base.ClusterBoard.cut_rows` \
            or :meth:`~marsilea.base.ClusterBoard.group_rows` instead

        Parameters
        ----------
        cut : array-like, optional
            The index of your data to specify where to split the canvas
        labels : array-like, optional
            The labels of your data, must be the same length as the data
        order : array-like, optional
            The order of the unique labels
        spacing : float, optional
            The spacing between each split chunks, default is 0.01

        Examples
        --------
        Split the canvas by the unique labels

        .. plot::
            :context: close-figs

            >>> data = np.random.rand(10, 11)
            >>> import marsilea as ma
            >>> h = ma.Heatmap(data)
            >>> labels = ["A", "B", "C", "A", "B", "C", "A", "B", "C", "A"]
            >>> h.hsplit(labels=labels, order=["A", "B", "C"])
            >>> h.add_left(ma.plotter.Labels(labels), pad=.1)
            >>> h.render()


        Split the canvas by the index

        .. plot::
            :context: close-figs

            >>> h = ma.Heatmap(data)
            >>> h.hsplit(cut=[4, 8])
            >>> h.render()


        """
        warnings.warn(
            DeprecationWarning(
                "`hsplit` will be deprecated in v0.5.0, use `cut_rows` or `group_rows` instead"
            ),
            stacklevel=2,
        )
        if self._split_row:
            raise SplitTwice(axis="horizontally")
        self._split_row = True

        deform = self.get_deform()
        deform.hspace = spacing
        if cut is not None:
            deform.set_split_row(breakpoints=cut)
        else:
            labels = np.asarray(labels)

            reindex, order = reorder_index(labels, order=order)
            deform.set_data_row_reindex(reindex)

            breakpoints = get_breakpoints(labels[reindex])
            deform.set_split_row(breakpoints=breakpoints, order=order)

    def vsplit(self, cut=None, labels=None, order=None, spacing=0.01):
        """Split the main canvas vertically

        .. deprecated:: 0.5.0
            Use :meth:`~marsilea.base.ClusterBoard.cut_cols` \
            or :meth:`~marsilea.base.ClusterBoard.group_cols` instead

        Parameters
        ----------
        cut : array-like, optional
            The index of your data to specify where to split the canvas
        labels : array-like, optional
            The labels of your data, must be the same length as the data
        order : array-like, optional
            The order of the unique labels
        spacing : float, optional
            The spacing between each split chunks, default is 0.01

        Examples
        --------
        Split the canvas by the unique labels

        .. plot::
            :context: close-figs

            >>> data = np.random.rand(10, 11)
            >>> import marsilea as ma
            >>> h = ma.Heatmap(data)
            >>> labels = ["A", "B", "C", "A", "B", "C", "A", "B", "C", "A", "B"]
            >>> h.vsplit(labels=labels, order=["A", "B", "C"])
            >>> h.add_top(ma.plotter.Labels(labels), pad=.1)
            >>> h.render()


        Split the canvas by the index

        .. plot::
            :context: close-figs

            >>> h = ma.Heatmap(data)
            >>> h.vsplit(cut=[4, 8])
            >>> h.render()


        """
        warnings.warn(
            DeprecationWarning(
                "`vsplit` will be deprecated in v0.5.0, use `cut_cols` or `group_cols` instead"
            ),
            stacklevel=2,
        )
        if self._split_col:
            raise SplitTwice(axis="vertically")
        self._split_col = True

        deform = self.get_deform()
        deform.wspace = spacing
        if cut is not None:
            deform.set_split_col(breakpoints=cut)
        else:
            labels = np.asarray(labels)

            reindex, order = reorder_index(labels, order=order)
            deform.set_data_col_reindex(reindex)

            breakpoints = get_breakpoints(labels[reindex])
            deform.set_split_col(breakpoints=breakpoints, order=order)

    def group_rows(self, group, order=None, spacing=0.01):
        """Group rows into chunks

        Parameters
        ----------
        group : array-like
            The group of each row
        order : array-like, optional
            The order of the unique groups
        spacing : float, optional
            The spacing between each split chunks, default is 0.01

        Examples
        --------
        Group rows by the unique labels

        .. plot::
            :context: close-figs

            >>> data = np.random.rand(10, 11)
            >>> import marsilea as ma
            >>> h = ma.Heatmap(data)
            >>> labels = ["A", "B", "C", "A", "B", "C", "A", "B", "C", "A"]
            >>> h.group_rows(labels, order=["A", "B", "C"])
            >>> h.add_left(ma.plotter.Labels(labels), pad=0.1)
            >>> h.render()

        """
        if self._split_row:
            raise SplitTwice(axis="rows")
        self._split_row = True

        deform = self.get_deform()
        deform.hspace = spacing

        labels = np.asarray(group)
        reindex, order = reorder_index(labels, order=order)
        deform.set_data_row_reindex(reindex)

        breakpoints = get_breakpoints(labels[reindex])
        deform.set_split_row(breakpoints=breakpoints, order=order)

    def group_cols(self, group, order=None, spacing=0.01):
        """Group columns into chunks

        Parameters
        ----------
        group : array-like
            The group of each column
        order : array-like, optional
            The order of the unique groups
        spacing : float, optional
            The spacing between each split chunks, default is 0.01

        Examples
        --------
        Group columns by the unique labels

        .. plot::
            :context: close-figs

            >>> data = np.random.rand(11, 10)
            >>> import marsilea as ma
            >>> h = ma.Heatmap(data)
            >>> labels = ["A", "B", "C", "A", "B", "C", "A", "B", "C", "A"]
            >>> h.group_cols(labels, order=["A", "B", "C"])
            >>> h.add_top(ma.plotter.Labels(labels), pad=0.1)
            >>> h.render()

        """
        if self._split_col:
            raise SplitTwice(axis="columns")
        self._split_col = True

        deform = self.get_deform()
        deform.wspace = spacing

        labels = np.asarray(group)
        reindex, order = reorder_index(labels, order=order)
        deform.set_data_col_reindex(reindex)

        breakpoints = get_breakpoints(labels[reindex])
        deform.set_split_col(breakpoints=breakpoints, order=order)

    def cut_rows(self, cut, spacing=0.01):
        """Cut the main canvas by rows

        Parameters
        ----------
        cut : array-like
            The index of your data to specify where to cut the canvas
        spacing : float, optional
            The spacing between each cut, default is 0.01

        Examples
        --------
        Cut the canvas by the index

        .. plot::
            :context: close-figs

            >>> data = np.random.rand(10, 11)
            >>> import marsilea as ma
            >>> h = ma.Heatmap(data)
            >>> h.cut_rows([4, 8])
            >>> h.render()

        """
        if self._split_row:
            raise SplitTwice(axis="horizontally")
        self._split_row = True

        deform = self.get_deform()
        deform.hspace = spacing
        deform.set_split_row(breakpoints=cut)

    def cut_cols(self, cut, spacing=0.01):
        """Cut the main canvas by columns

        Parameters
        ----------
        cut : array-like
            The index of your data to specify where to cut the canvas
        spacing : float, optional
            The spacing between each cut, default is 0.01

        Examples
        --------
        Cut the canvas by the index

        .. plot::
            :context: close-figs

            >>> data = np.random.rand(10, 11)
            >>> import marsilea as ma
            >>> h = ma.Heatmap(data)
            >>> h.cut_cols([4, 8])
            >>> h.render()

        """
        if self._split_col:
            raise SplitTwice(axis="vertically")
        self._split_col = True

        deform = self.get_deform()
        deform.wspace = spacing
        deform.set_split_col(breakpoints=cut)

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
                if plan.allow_split:
                    # if deform.is_col_cluster:
                    #     group_ratios = None
                    # else:
                    group_ratios = plan.get_split_regroup()
                    self.layout.vsplit(plan.name, w_ratios, wspace, group_ratios)

        # split row axes
        if deform.is_row_split:
            for plan in self._row_plan:
                if plan.allow_split:
                    # if deform.is_row_cluster:
                    #     group_ratios = None
                    # else:
                    group_ratios = plan.get_split_regroup()
                    self.layout.hsplit(plan.name, h_ratios, hspace, group_ratios)

    def _render_dendrogram(self):
        deform = self.get_deform()
        for den in self._row_den + self._col_den:
            if den["show"]:
                ax = self.layout.get_ax(den["name"])
                ax.set_axis_off()
                spacing = deform.hspace
                den_obj = deform.get_row_dendrogram()
                if den["pos"] == "col":
                    spacing = deform.wspace
                    den_obj = deform.get_col_dendrogram()
                if isinstance(den_obj, Dendrogram):
                    color = den["colors"]
                    if (color is not None) & (not is_color_like(color)):
                        color = color[0]
                    den_obj.draw(
                        ax,
                        orient=den["side"],
                        color=color,
                        linewidth=den["linewidth"],
                        rasterized=den["rasterized"],
                    )
                else:
                    den_obj.draw(
                        ax,
                        orient=den["side"],
                        spacing=spacing,
                        add_meta=den["add_meta"],
                        add_base=den["add_base"],
                        base_colors=den["colors"],
                        meta_color=den["meta_color"],
                        linewidth=den["linewidth"],
                        divide=den["add_divider"],
                        divide_style=den["divider_style"],
                        meta_ratio=den["meta_ratio"],
                        rasterized=den["rasterized"],
                    )

    def _render_plan(self):
        deform = self.get_deform()
        for plan in self._col_plan:
            if plan.allow_split:
                plan.set_deform(deform)
            axes = self.layout.get_ax(plan.name)
            plan.render(axes)

        # render other plots
        for plan in self._row_plan:
            if plan.allow_split:
                plan.set_deform(deform)
            axes = self.layout.get_ax(plan.name)
            plan.render(axes)

        main_ax = self.get_main_ax()
        for plan in self._get_layers_zorder():
            plan.set_deform(deform)
            plan.render(main_ax)

    def get_deform(self):
        """Return the deformation object of the cluster data"""
        return self._deform

    def get_row_linkage(self):
        """Return the linkage matrix of row dendrogram

        If the canvas is not split, the linkage matrix will be returned;
        otherwise, a dictionary of linkage matrix will be returned, the key is either
        index or the name of each chunk.

        """
        return self._deform.get_row_linkage()

    def get_col_linkage(self):
        """Return the linkage matrix of column dendrogram

        If the canvas is not split, the linkage matrix will be returned;
        otherwise, a dictionary of linkage matrix will be returned, the key is either
        index or the name of each chunk.

        """
        return self._deform.get_col_linkage()

    @property
    def row_cluster(self):
        """If row dendrogram is added"""
        return len(self._row_den) > 0

    @property
    def col_cluster(self):
        """If column dendrogram is added"""
        return len(self._col_den) > 0

    def render(self, figure=None, scale=1):
        if self._deform is None:
            raise ValueError("No layer is added to the plot")
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


class ZeroWidthCluster(ClusterBoard):
    """
    A utility class to initialize a canvas \
    with zero width and cluster data

    Parameters
    ----------
    cluster_data : ndarray
        The cluster data
    height : float
        The height of the main canvas in inches
    name : str
        The name of the main canvas
    margin : float, 4-tuple
        The margin of the main canvas in inches

    """

    def __init__(self, cluster_data, height, name=None, margin=0.2):
        super().__init__(
            cluster_data=cluster_data,
            width=0,
            height=height,
            name=name,
            margin=margin,
            init_main=False,
        )


class ZeroHeightCluster(ClusterBoard):
    """
    A utility class to initialize a canvas \
    with zero height and cluster data

    Parameters
    ----------
    cluster_data : ndarray
        The cluster data
    width : float
        The width of the main canvas in inches
    name : str
        The name of the main canvas
    margin : float, 4-tuple
        The margin of the main canvas in inches


    """

    def __init__(self, cluster_data, width, name=None, margin=0.2):
        super().__init__(
            cluster_data=cluster_data,
            width=width,
            height=0,
            name=name,
            margin=margin,
            init_main=False,
        )
