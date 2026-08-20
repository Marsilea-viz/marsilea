from __future__ import annotations

import copy
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

from ._normalize import check_plot_data, densify
from ._sources import accepts_source, resolve, resolve_group
from ._deform import Deformation
from .dendrogram import Dendrogram
from .exceptions import SplitTwice, DuplicatePlotter, LayerConflict
from .layout import CrossLayout, CompositeCrossLayout, StackCrossLayout
from .plotter import RenderPlan, Title, SizedMesh
from .plotter._seaborn import _SeabornBase
from .plotter.base import _DeferredPlot
from .plotter.mesh import MeshBase
from .utils import pairwise, batched, caller_location, get_plot_name, _check_side


# Attributes whose container must not be shared with the source board,
# but whose contents are. Plotters are shared on purpose: a render does
# not mutate them in a way the copy cares about, and copying one would
# drag in the live matplotlib artists it keeps after a render (a Bar
# plotter holds its BarContainer). The layout classes solve the same
# problem one level down with their own __deepcopy__.
# `_source` is deliberately in neither this tuple nor the deepcopy block below:
# copy.copy(board) already shares it, which is what we want. Copying an AnnData
# per board would duplicate the matrix, and it defines no __copy__ anyway.
_COPY_SHALLOW = (
    "_user_legends",
    "_legend_switch",
    "_col_plan",
    "_row_plan",
    "_layer_plan",
    "_row_den",
    "_col_den",
)


def _copy_board(board, layout=None):
    """Shallow-copy a board but deep-copy layout and plan metadata.

    Everything that controls axes geometry and legend state is
    deep-copied so the copy is independent of the original.

    `layout` is passed when copying the boards held by a group board, so
    each child is bound to the sub-layout that already lives in the
    parent's copied layout tree. Deep-copying the tree and the children
    separately leaves the children pointing at layouts that nothing
    positions, and they then draw at the wrong place.
    """
    new = copy.copy(board)
    new.layout = deepcopy(board.layout) if layout is None else layout
    new._legend_grid_kws = deepcopy(board._legend_grid_kws)
    new._legend_draw_kws = deepcopy(board._legend_draw_kws)
    for attr in _COPY_SHALLOW:
        if hasattr(board, attr):
            setattr(new, attr, copy.copy(getattr(board, attr)))

    # ClusterBoard-specific
    if hasattr(board, "_deform"):
        new._deform = deepcopy(board._deform)

    # StackBoard/CompositeBoard hold other boards
    if hasattr(board, "_board_list"):
        sub_layouts = new.layout.layouts
        if isinstance(sub_layouts, dict):  # CompositeCrossLayout keys by name
            sub_layouts = list(sub_layouts.values())
        new._board_list = [
            _copy_board(child, layout=sub)
            for child, sub in zip(board._board_list, sub_layouts, strict=True)
        ]
        if hasattr(board, "main_board"):
            new.main_board = new._board_list[0]

    return new


def _render_with_context(plan, axes):
    """Render one plan, tagging any failure with where the plan came from.

    A board is built lazily, so the only user frame in a render traceback is
    ``render()`` itself. Notes keep the original exception intact, its type,
    its message and its traceback, and add the two things it cannot know:
    which plotter blew up, and the ``add_*`` line that put it there.
    """
    try:
        plan.render(axes)
    except Exception as e:
        e.add_note(f"  while rendering {type(plan).__name__} on '{plan.side}'")
        if plan._added_at is not None:
            e.add_note(f"  added at {plan._added_at}")
        raise


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

    layout: CrossLayout | CompositeCrossLayout | StackCrossLayout
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
        return self

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
                    # Try to detach legend from figure
                    leg.remove()
                    # For matplotlib >= 3.10.0
                    if hasattr(leg, "_parent_figure"):
                        setattr(leg, "_parent_figure", None)
                    # For matplotlib < 3.10.0
                    if hasattr(leg, "figure"):
                        setattr(leg, "figure", None)
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
    #: Optional data container (an AnnData) that data references resolve against.
    #: Shared, never copied -- see the note above `_COPY_SHALLOW`.
    _source = None
    #: Which board axis each container axis maps to, e.g. {"obs": "row"}.
    _axis_map = None

    @accepts_source
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
        # Left/right plots index rows, top/bottom index columns -- the same split
        # that picks _row_plan vs _col_plan below.
        plot = self._build_deferred(
            plot, "col" if side in ("top", "bottom") else "row", side
        )
        if plot._registered:
            raise DuplicatePlotter(plot)
        # Before the layout is touched: a rejected plot must not leave an
        # orphan axes behind for the next render to trip over.
        check_plot_data(plot, side, plot.data_axis(side), self._board_shape())
        plot._added_at = caller_location()
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
        plot._registered = True

        plan.append(plot)
        return self

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
        return self.add_plot("left", plot, name, size, pad, legend)

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
        return self.add_plot("right", plot, name, size, pad, legend)

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
        return self.add_plot("top", plot, name, size, pad, legend)

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
        return self.add_plot("bottom", plot, name, size, pad, legend)

    def _render_plan(self):
        for plan in self._col_plan + self._row_plan:
            axes = self.layout.get_ax(plan.name)
            _render_with_context(plan, axes)

        main_ax = self.get_main_ax()
        for plan in self._get_layers_zorder():
            _render_with_context(plan, main_ax)

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
        plot = self._build_deferred(plot, "main")
        if plot._registered:
            raise DuplicatePlotter(plot)
        if name is None:
            name = plot.name
        plot_type = plot.__class__.__name__
        name = get_plot_name(name, side="main", chart=plot_type)
        self._legend_switch[name] = legend
        if not plot.render_main:
            msg = f"{plot_type} cannot be rendered as another layer."
            raise TypeError(msg)
        self._check_layer_conflict(plot)
        check_plot_data(plot, "main", plot.data_axis("main"), self._board_shape())
        plot._added_at = caller_location()
        if zorder is not None:
            plot.zorder = zorder
        plot.set(name=name)
        plot.set_side("main")
        plot._registered = True
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
        return self

    def _board_shape(self):
        """(nrow, ncol) if this board has a fixed grid, else None."""
        deform = getattr(self, "_deform", None)
        return None if deform is None else deform.get_data().shape

    def _build_deferred(self, plot, axis, side=None):
        """Turn a :class:`_DeferredPlot` into a real plotter for `axis`.

        Everything downstream in ``add_plot``/``add_layer`` -- ``_registered``,
        ``__class__.__name__``, ``_check_layer_conflict`` -- needs a real plotter,
        so this has to happen first.
        """
        if not isinstance(plot, _DeferredPlot):
            return plot
        shape = self._board_shape()
        return plot.build(
            lambda v: resolve(v, self._source, axis, self._axis_map, shape, side)
        )

    def _check_layer_conflict(self, plot):
        """Reject layers whose axes conventions cannot coexist.

        A seaborn plot places categories at ``0 .. n - 1`` and scales the other
        axis to the data values; a mesh draws cells over ``0 .. n`` on both.
        Sharing the same Axes leaves the categories half a cell off and
        overwrites the mesh's limits, so refuse the combination rather than
        render a figure that is silently wrong.
        """
        if isinstance(plot, _SeabornBase):
            clashes_with, adding_seaborn = MeshBase, True
        elif isinstance(plot, MeshBase):
            clashes_with, adding_seaborn = _SeabornBase, False
        else:
            return
        for existing in self._layer_plan:
            if isinstance(existing, clashes_with):
                # report the same way round however the two were added
                seaborn_plot, mesh_plot = (
                    (plot, existing) if adding_seaborn else (existing, plot)
                )
                raise LayerConflict(seaborn_plot, mesh_plot)

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
        return self

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
        return self

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

        return self

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

    def get_plot_names(self) -> List[str]:
        """Return the names of all registered plotters in order

        Useful for passing to :meth:`~marsilea.base.LegendMaker.add_legends`
        to control legend ordering.

        Returns
        -------
        list of str
            Names of all plotters: layers first, then col (top/bottom) and row (left/right) plans.

        """
        return [p.name for p in self._layer_plan + self._col_plan + self._row_plan]

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
        self : :class:`~marsilea.base.WhiteBoard`
            The current instance

        """
        if figure is None:
            figure = plt.figure()
        self._freeze_legend(figure)
        self._freeze_flex_plots(figure)

        self.layout.freeze(figure=figure, scale=scale)

        self._draw(figure)
        return self

    def _draw(self, figure):
        """Draw on the axes of an already frozen layout.

        Split out of :meth:`render` so a group board can freeze the whole
        layout tree once and then only draw, instead of every child
        re-freezing its own layout and re-creating its axes.
        """
        self.figure = figure
        self._render_plan()
        self._render_legend()

    def save(self, fname, **kwargs):
        """Save the figure to a file

        Save the current opened figure to a file, if no figure is open,
        a render will be performed first.

        Parameters
        ----------
        fname : str, path-like
            The file name to save
        kwargs : dict
            Additional options for saving the figure, will be passed to :meth:`~matplotlib.pyplot.savefig`

        """
        if self.figure is None:
            self.render()
        save_options = dict(bbox_inches="tight")
        save_options.update(kwargs)
        self.figure.savefig(fname, **save_options)
        return self

    def set_margin(self, margin: float | tuple[float, float, float, float]):
        """Set margin of the main canvas

        Parameters
        ----------
        margin : float, 4-tuple
            The margin of the main canvas in inches

        """
        self.layout.set_margin(margin)
        return self


class ZeroWidth(WhiteBoard):
    """A utility class to initialize a canvas \
    with zero width

    This is useful when you try to stack many plots

    Parameters
    ----------
    height : float
        The height of the canvas in inches
    name : str
    margin : float

    """

    @accepts_source
    def __init__(self, height, name=None, margin=0.2):
        super().__init__(
            width=0, height=height, name=name, margin=margin, init_main=False
        )


class ZeroHeight(WhiteBoard):
    """A utility class to initialize a canvas \
    with zero height

    This is useful when you try to stack many plots

    """

    @accepts_source
    def __init__(self, width, name=None, margin=0.2):
        super().__init__(
            width=width, height=0, name=name, margin=margin, init_main=False
        )


class _GroupBoard(LegendMaker):
    """Shared behavior for boards that render a list of other boards.

    A group board owns the whole layout tree: it freezes it once and then
    asks every board in it to draw, instead of letting each child freeze
    its own layout again.
    """

    figure: Figure = None
    keep_legends: bool = False
    _board_list: List

    def new_board(self, board):
        board = _copy_board(board)
        if not self.keep_legends and isinstance(board, LegendMaker):
            board.remove_legends()
        return board

    # To mimic the board API
    def _freeze_flex_plots(self, figure):
        for board in self._board_list:
            board._freeze_flex_plots(figure)

    def _freeze_legend(self, figure):
        super()._freeze_legend(figure)
        # With keep_legends=True a board draws its own legend, so its
        # legend axes must be sized and registered before the tree is
        # frozen: _draw needs the axes to exist, and the legend is a side
        # cell, so the stack only leaves room for it if it is there first.
        for board in self._board_list:
            board._freeze_legend(figure)

    def remove_legends(self):
        super().remove_legends()
        # Keep the boards in step with the layout tree, whose legend
        # axes we just dropped
        for board in self._board_list:
            board.remove_legends()

    def render(self, figure=None, scale=1):
        if figure is None:
            figure = plt.figure()
        self._freeze_legend(figure)
        self._freeze_flex_plots(figure)
        self.layout.freeze(figure=figure, scale=scale)
        self._draw(figure)
        return self

    def _draw(self, figure):
        self.figure = figure
        for board in self._board_list:
            board._draw(figure)
        self._render_legend()

    def save(self, fname, **kwargs):
        if self.figure is None:
            self.render()
        save_options = dict(bbox_inches="tight")
        save_options.update(kwargs)
        self.figure.savefig(fname, **save_options)
        return self

    def get_legends(self):
        legends = {}
        for m in self._board_list:
            legends.update(m.get_legends())
        return legends

    def get_ax(self, board_name, ax_name):
        return self.layout.get_ax(board_name, ax_name)

    def get_main_ax(self, name):
        return self.layout.get_main_ax(name)

    def set_margin(self, margin):
        self.layout.set_margin(margin)
        return self


class CompositeBoard(_GroupBoard):
    """Layout multiple canvas

    Parameters
    ----------
    main_board : :class:`WhiteBoard` or :class:`ClusterBoard`
        The main canvas
    keep_legends : bool, default: False
        Whether to keep the legends in each canvas
        If False, you can group all legends with `.add_legends()`
    align_main : bool, default: True
        Whether to force the size of other canvas to align with the main canvas
    margin : float, default: 0
        The margin space reserved around the whole canvas

    """

    layout: CompositeCrossLayout = None

    def __init__(
        self,
        main_board: WhiteBoard,
        keep_legends=False,
        align_main=True,
        margin=0,
    ):
        self.keep_legends = keep_legends

        self.main_board = self.new_board(main_board)
        if not keep_legends:
            self.main_board.remove_legends()
        self.layout = CompositeCrossLayout(
            self.main_board.layout, align_main=align_main, margin=margin
        )
        self._board_list = [self.main_board]

        super().__init__()

    def __add__(self, other):
        """Define behavior that horizontal appends two grid"""
        return self.append("right", other)

    def __truediv__(self, other):
        """Define behavior that vertical appends two grid"""
        return self.append("bottom", other)

    def append(self, side, other, pad=0):
        if isinstance(other, Number):
            self.layout.append(side, other)
        else:
            board = self.new_board(other)
            self._board_list.append(board)
            self.layout.append(side, board.layout)

        if pad > 0:
            self.layout.append(side, pad)
        return self


class StackBoard(_GroupBoard):
    """Stack multiple boards

    Parameters
    ----------
    boards : list of :class:`WhiteBoard`, :class:`StackBoard`
        The boards to stack, a :class:`StackBoard` may be stacked itself
    direction : {"horizontal", "vertical"}, default: "horizontal"
        Stack from left to right, or from top to bottom
    align : {"center", "top", "bottom", "left", "right"}, default: "center"
        How to align the boards on the other axis, relative to their
        main canvas. Only "center", "top" and "bottom" are valid for
        `direction="horizontal"`, and only "center", "left" and "right"
        for `direction="vertical"`.
    spacing : float, default: 0.2
        The space between two boards in inches
    margin : float, 4-tuple, default: 0
        The margin space reserved around the whole canvas in inches
    keep_legends : bool, default: False
        Whether to keep the legends in each board.
        If False, you can group all legends with `.add_legends()`

    """

    layout: StackCrossLayout = None

    def __init__(
        self,
        boards: List[WhiteBoard | StackBoard],
        direction="horizontal",
        align="center",
        spacing=0.2,
        margin=0,
        keep_legends=False,
    ):
        if len(boards) == 0:
            raise ValueError("Cannot stack an empty list of boards")
        self.keep_legends = keep_legends
        board_list = []
        layouts = []
        for board in boards:
            board = self.new_board(board)
            board_list.append(board)
            layouts.append(board.layout)

        self.layout = StackCrossLayout(
            layouts, margin=margin, direction=direction, align=align, spacing=spacing
        )

        self._board_list = board_list
        super().__init__()


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

    @accepts_source
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
        # np.asarray on a sparse matrix returns a 0-d object array rather than
        # failing, so densify first or the error below is deeply confusing.
        cluster_data = np.asarray(densify(cluster_data))
        if cluster_data.ndim != 2:
            raise ValueError("Cluster data must be 2D array")
        if cluster_data.dtype.kind in "US":
            # Text reaches numpy's reductions and dies as a ufunc loop error
            # that names neither marsilea nor the data.
            msg = (
                f"{self.__class__.__name__} needs numbers, but this data is "
                f"text (dtype {cluster_data.dtype}). Use `ma.CatHeatmap` for "
                f"categories, or pass `cluster_data=` to cluster on something "
                f"numeric."
            )
            raise ValueError(msg)
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
        height_scale=None,
        height_transform=None,
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
            The size of meta dendrogram relative to the base dendrogram.
            Exact when `height_scale` is not the default "minmax".
        height_scale : {"minmax", "group", "shared"}, default: "minmax"
            What the merge heights are measured against.

            - "minmax" stretches each group's own range over the full height,
              so every group's dendrogram ends up the same height no matter
              how tightly its rows actually cluster.
            - "group" scales each group by its own tallest merge, keeping the
              proportions inside a group honest.
            - "shared" scales every group by the tallest merge anywhere, so
              heights can be compared between groups and a tight group draws
              genuinely short. Use this when the meta dendrogram looks
              unbalanced against dense base dendrograms.
        height_transform : {None, "sqrt", "log", "rank"} or callable
            Bend the heights without reordering them, to spread out merges
            that bunch up near the leaves. Worth reaching for with
            ``method="ward"``, which is strongly bottom-heavy, and best left
            alone with the default "single". A callable takes and returns an
            array in [0, 1]. Requires `height_scale` other than "minmax", and
            gives up readable distances in exchange for legibility.
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
            height_scale=height_scale,
            height_transform=height_transform,
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
        return self

    def group_rows(self, group, order=None, spacing=0.01):
        """Group rows into chunks

        Parameters
        ----------
        group : array-like
            The group of each row. May be a data reference, e.g.
            ``A.obs["leiden"]``.
        order : array-like, optional
            The order of the unique groups. If omitted and `group` is categorical,
            its category order is used; otherwise the groups are sorted.
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

        labels, cat_order = resolve_group(
            group, self._source, "row", self._axis_map, self._board_shape()
        )
        if order is None:
            order = cat_order
        reindex, order = reorder_index(labels, order=order)
        deform.set_data_row_reindex(reindex)

        breakpoints = get_breakpoints(labels[reindex])
        deform.set_split_row(breakpoints=breakpoints, order=order)
        return self

    def group_cols(self, group, order=None, spacing=0.01):
        """Group columns into chunks

        Parameters
        ----------
        group : array-like
            The group of each column. May be a data reference, e.g.
            ``A.var["gene_group"]``.
        order : array-like, optional
            The order of the unique groups. If omitted and `group` is categorical,
            its category order is used; otherwise the groups are sorted.
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

        labels, cat_order = resolve_group(
            group, self._source, "col", self._axis_map, self._board_shape()
        )
        if order is None:
            order = cat_order
        reindex, order = reorder_index(labels, order=order)
        deform.set_data_col_reindex(reindex)

        breakpoints = get_breakpoints(labels[reindex])
        deform.set_split_col(breakpoints=breakpoints, order=order)
        return self

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
        return self

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
        return self

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
                        height_scale=den["height_scale"],
                        height_transform=den["height_transform"],
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
                        height_scale=den["height_scale"],
                        height_transform=den["height_transform"],
                    )

    def _render_plan(self):
        deform = self.get_deform()
        for plan in self._col_plan + self._row_plan:
            if plan.allow_split:
                plan.set_deform(deform)
            axes = self.layout.get_ax(plan.name)
            _render_with_context(plan, axes)

        main_ax = self.get_main_ax()
        for plan in self._get_layers_zorder():
            plan.set_deform(deform)
            _render_with_context(plan, main_ax)

    def get_deform(self):
        """Return the deformation object of the cluster data"""
        return self._deform

    def get_row_linkage(self):
        """Return the linkage matrix of row dendrogram

        If the canvas is not split, the linkage matrix will be returned;
        otherwise, a dictionary of linkage matrix will be returned, the key is either
        index or the name of each chunk. A chunk with a single row has nothing
        to merge and maps to None.

        """
        return self._deform.get_row_linkage()

    def get_col_linkage(self):
        """Return the linkage matrix of column dendrogram

        If the canvas is not split, the linkage matrix will be returned;
        otherwise, a dictionary of linkage matrix will be returned, the key is either
        index or the name of each chunk. A chunk with a single column has nothing
        to merge and maps to None.

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

    def _freeze_flex_plots(self, figure):
        if self._deform is None:
            raise ValueError("No layer is added to the plot")
        super()._freeze_flex_plots(figure)
        # Make sure all axes is split before the layout is frozen
        self._setup_axes()

    def _draw(self, figure):
        self.figure = figure
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

    @accepts_source
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

    @accepts_source
    def __init__(self, cluster_data, width, name=None, margin=0.2):
        super().__init__(
            cluster_data=cluster_data,
            width=width,
            height=0,
            name=name,
            margin=margin,
            init_main=False,
        )
