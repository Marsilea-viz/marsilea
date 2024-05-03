from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Iterable, Sequence, Dict

import numpy as np
import pandas as pd
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.offsetbox import AnchoredText
from seaborn import despine

from .._deform import Deformation
from ..exceptions import DataError, SplitConflict


class DataLoader:
    """Handle user data"""

    def __init__(self, data, target="2d", plotter: str = None):
        self.plotter = plotter
        self.data = self.from_any(data, target=target)

    def get_array(self):
        if np.ma.isMaskedArray(self.data):
            return self.data
        return np.asarray(self.data)

    def from_any(self, data, target="2d"):
        if isinstance(data, pd.DataFrame):
            return self.from_dataframe(data, target=target)
        elif isinstance(data, np.ndarray):
            return self.from_ndarray(data, target=target)
        elif isinstance(data, Iterable):
            return self.from_iterable(data, target=target)
        else:
            raise TypeError(f"Your input data with type {type(data)} is not supported.")

    def from_dataframe(self, data: pd.DataFrame, target="2d"):
        ndata = data.to_numpy()
        if target == "1d":
            self._check_1d_compat(ndata)
            ndata = ndata.flatten()
        return ndata

    def from_ndarray(self, data: np.ndarray, target="2d"):
        ndata = data
        if target == "1d":
            self._check_1d_compat(ndata)
            ndata = ndata.flatten()
        if (target == "2d") & (ndata.ndim == 1):
            ndata = ndata.reshape(1, -1)
        return ndata

    def from_iterable(self, data: Iterable, target="2d"):
        try:
            ndata = np.asarray(data)
        except Exception:
            msg = f"Cannot handle your data with type {type(data)}"
            if self.plotter is not None:
                msg += f" for {self.plotter}."
            raise DataError(msg)
        return self.from_ndarray(ndata, target=target)

    def _check_1d_compat(self, data: np.ndarray):
        if data.ndim == 2:
            row, col = data.shape
            if not (row == 1) or (col == 1):
                if self.plotter is not None:
                    msg = f"{self.plotter} requires 1D data as input."
                else:
                    msg = "Require 1D data as input."
                raise DataError(msg)


@dataclass(repr=False)
class RenderSpec:
    """The container class that holds the \
    rendering data and parameters for each axes

    Attributes
    ----------
    data : Any
        The data to be rendered
    params : List[Dict]
        The parameters for each data
    group_data : Any
        The group data
    group_params : Any
        The group parameters
    current_ix : int
        The current index of the axes
    total : int
        The total number of axes


    """
    ax: Axes

    data: Any
    params: List[Dict] = None
    group_data: Any = None
    group_params: Any = None

    current_ix: int = 0

    total: int = 1

    def __repr__(self):
        return f"{self.__class__.__name__}({self.current_ix} -> {self.total})"

    @property
    def is_first(self):
        return self.current_ix == 0

    @property
    def is_last(self):
        return self.current_ix == self.total - 1


class RenderPlanLabel:
    label_props = {
        "left": dict(loc="center right", bbox_to_anchor=(0, 0.5)),
        "right": dict(loc="center left", bbox_to_anchor=(1, 0.5)),
        "top": dict(
            loc="lower center", bbox_to_anchor=(0.5, 1), prop=dict(rotation=90)
        ),
        "bottom": dict(
            loc="upper center", bbox_to_anchor=(0.5, 0), prop=dict(rotation=90)
        ),
    }

    label_loc = {
        "top": "right",
        "bottom": "right",
        "left": "bottom",
        "right": "bottom",
    }

    def __init__(self, label, loc=None, props=None):
        self.label = label
        self.loc = loc
        self.props = {} if props is None else props

    def add(self, axes, side):
        if side != "main":
            if isinstance(axes, Sequence):
                if self.loc in ["top", "left"]:
                    label_ax = axes[0]
                else:
                    label_ax = axes[-1]
            else:
                label_ax = axes

            if self.loc is None:
                loc = self.label_loc[side]
            else:
                loc = self.loc
            label_props = self.label_props[loc]
            bbox_loc = label_props["loc"]
            bbox_to_anchor = label_props["bbox_to_anchor"]
            prop = label_props.get("prop", {})
            if self.props is not None:
                prop.update(self.props)

            title = AnchoredText(
                self.label,
                loc=bbox_loc,
                bbox_to_anchor=bbox_to_anchor,
                prop=prop,
                pad=0.3,
                borderpad=0,
                bbox_transform=label_ax.transAxes,
                frameon=False,
            )
            label_ax.add_artist(title)


class MetaRenderPlan(type):
    """Metaclass for RenderPlan"""

    def __init__(cls, name, bases, attrs):
        allow_labeling = attrs.get("allow_labeling", False)
        if allow_labeling:

            def new_render(self, axes):
                attrs["render"](self, axes)
                self._plan_label.add(axes, self.side)

            setattr(cls, "render", new_render)


class RenderPlan:
    """The base class for every plotter in Marsilea

    Attributes
    ----------
    name : str
        The name of the plot,
        can be used to retrieve the render axes and corresponding legend.
    side : str, default: 'top'
        Which side to render this plot
    size : float
    allow_split : bool, default: True
        Use to mark if the RenderPlan can be split
    render_main : bool, default: False
        Use to mark if the RenderPlan can be rendered on main canvas
    zorder : int, default: 0
        This only works if the RenderPlan is rendered on main canvas

    """

    name: str = None
    size: float = None
    side: str = "top"
    # label if a render plan
    # can be used on split axes
    allow_split: bool = True
    zorder: int = 0
    deform: Deformation = None
    # If True, this RenderPlan can be rendered on main ax
    render_main = False
    label: str = ""
    allow_labeling: bool = True

    _data: Sequence[np.ndarray] = None
    _is_datasets: bool = False
    _params: List[Dict[str, Any]] = None
    _group_data: List = None
    _group_params: List[Dict[str, Any]] = None
    _plan_label: RenderPlanLabel = None
    _split_regroup: Sequence[float] = None

    def __repr__(self):
        side_str = f"side='{self.side}'"
        zorder_str = f"zorder={self.zorder}"

        if self.name is None:
            chunks = [side_str, zorder_str]
        else:
            chunks = [f"name='{self.name}'", side_str, zorder_str]
        return f"{self.__class__.__name__}" f"({', '.join(chunks)})"

    def set(self, **kwargs):
        for k, v in kwargs.items():
            if k == "side":
                self.set_side(v)
            else:
                self.__setattr__(k, v)

    def set_side(self, side):
        self.side = side

    def set_size(self, size):
        self.size = size

    def set_label(self, label, loc=None, props=None):
        self.label = label
        self._plan_label = RenderPlanLabel(label, loc=loc, props=props)

    def get_deform_func(self):
        if self.has_deform:
            if self.side == "main":
                return self.deform.transform
            elif self.is_flank:
                return self.deform.transform_row
            else:
                return self.deform.transform_col

    def reindex_by_chunk(self, group_data):
        if group_data is not None:
            if self.has_deform:
                group_data = np.asarray(group_data)
                if (self.deform.is_col_split
                        & (self.is_body | (self.side == "main"))
                        & self.deform.is_col_cluster
                ):
                    return group_data[self.deform.col_chunk_index]
                elif (
                    self.deform.is_row_split
                    & (self.is_flank | (self.side == "main"))
                    & self.deform.is_row_cluster
                ):
                    return group_data[self.deform.row_chunk_index]
            return group_data

    def set_deform(self, deform: Deformation):
        self.deform = deform

    def get_data(self):
        return self._data

    def set_data(self, *data):
        self._data = data

    def get_params(self):
        return self._params

    def set_params(self, params: Dict[str, List]):
        params_names = params.keys()
        spec_params = []
        for d in zip(*params.values()):
            spec_params.append(dict(zip(params_names, d)))
        self._params = spec_params

    def set_group_data(self, group_data):
        self._group_data = group_data

    def get_group_data(self):
        return self._group_data

    def set_group_params(self, group_params: Dict[str, List]):
        params_names = group_params.keys()
        spec_params = []
        for d in zip(*group_params.values()):
            spec_params.append(dict(zip(params_names, d)))
        self._group_params = spec_params

    def get_group_params(self):
        return self._group_params

    def data_validator(self, data, target="2d"):
        name = self.__class__.__name__
        loader = DataLoader(data, target=target, plotter=name)
        return loader.get_array()

    # def get_render_data(self):
    #
    #     data = self.get_data()
    #
    #     if self.has_deform:
    #         self.get_deform_func()
    #
    #     else:
    #         if len(data) == 1:
    #             return data[0]
    #         else:
    #             return data

    def _get_split_render_spec(self, axes):
        datasets = self.get_data()
        params = self.get_params()
        group_params = self.get_group_params()
        deform_func = self.get_deform_func()
        if len(datasets) == 1:
            spec_data = deform_func(datasets[0])
        else:
            datasets = [deform_func(d) for d in datasets]
            spec_data = [d for d in zip(*datasets)]

        n = len(spec_data)
        if params is not None:
            params = deform_func(np.asarray(params, dtype=object))
        else:
            params = [None for _ in range(n)]

        if group_params is not None:
            group_params = self.reindex_by_chunk(group_params)
        else:
            group_params = [None for _ in range(n)]

        spec_list = []
        total = len(axes)
        dispatch = zip(axes, spec_data, params, group_params)
        for i, (ax, d, p, gp) in enumerate(dispatch):
            spec = RenderSpec(
                ax=ax, data=d, params=p, group_params=gp, current_ix=i, total=total
            )
            spec_list.append(spec)
        return spec_list

    def _get_intact_render_spec(self, ax):
        datasets = self.get_data()
        params = self.get_params()

        if self.has_deform:
            deform_func = self.get_deform_func()
            if datasets is None:
                spec_data = None
            elif len(datasets) == 1:
                spec_data = deform_func(datasets[0])
            else:
                spec_data = [deform_func(d) for d in datasets]
            if params is not None:
                params = deform_func(np.asarray(params, dtype=object))
        else:
            spec_data = datasets[0] if len(datasets) == 1 else datasets
        return RenderSpec(ax=ax, data=spec_data, params=params)

    def get_render_spec(self, axes):
        try:
            if self.is_split:
                return self._get_split_render_spec(axes)
            else:
                return self._get_intact_render_spec(axes)
        except Exception as _:
            raise DataError(
                f"Please check your data input with {self.__class__.__name__}"
            )

    # def get_render_data(self):
    #     """Define how render data is organized
    #
    #     The render data could be different depends on following situations:
    #
    #     #. Render at different sides: left, right, top, bottom and main canvas
    #     #. The canvas is split or not
    #
    #     """
    #     deform_func = self.get_deform_func()
    #     data = self.get_data()
    #     datasets = self.get_datasets()
    #     if deform_func is None:
    #         if data is not None:
    #             return data
    #         else:
    #             return datasets
    #     else:
    #         if data is not None:
    #             return deform_func(data)
    #         elif datasets is not None:
    #             return self.create_render_datasets(*datasets)

    # def create_render_datasets(self, deform_func, *datasets):
    #     datasets = [deform_func(d) for d in datasets]
    #     if self.is_split:
    #         return [d for d, in zip(*datasets)]
    #     else:
    #         return datasets

    @property
    def has_deform(self):
        """If the RenderPlan has Deformation"""
        return self.deform is not None

    @property
    def is_body(self):
        """Draw on top and bottom"""
        return self.side in ["top", "bottom"]

    @property
    def is_flank(self):
        """Draw on left and right"""
        return self.side in ["right", "left"]

    @property
    def is_split(self):
        """
        For the RenderPlan to self-aware of whether its render canvas
        will be split. Useful to determine how to get render data.
        """
        if self.deform is not None:
            if self.is_body & self.deform.is_col_split:
                return True
            if self.is_flank & self.deform.is_row_split:
                return True
            if (self.side == "main") & self.deform.is_split:
                return True
        return False

    def render_ax(self, spec: RenderSpec):
        """The major rendering function
        Define how the plot is drawn
        """
        pass

    # def render_axes(self, axes):
    #     """Use to render plots when the canvas is split
    #
    #     By default, it will match each data chunk to each axes
    #
    #     .. code-block:: python
    #
    #         for ax, data in zip(axes, self.get_render_data()):
    #             self.render_ax(ax, data)
    #
    #     """
    #     total = len(axes)
    #     for ix, (ax, data) in enumerate(
    #             zip_longest(axes, self.get_render_data())):
    #         self.render_ax(RenderSpec(ax=ax, data=data,
    #                                   current_ix=ix, total=total))

    def render(self, axes):
        """
        This function will be call when render a plot

        - If the canvas is split, :meth:`render_axes` will be called.
        - If only one ax is passed, :meth:`render_ax` will be called.

        .. code-block:: python

            if self.is_split:
                self.render_axes(axes)
            else:
                self.render_ax(axes, self.get_render_data())

        """
        if self.is_split:
            for spec in self.get_render_spec(axes):
                self.render_ax(spec)
        else:
            self.render_ax(self.get_render_spec(axes))

        if self.allow_labeling:
            if self._plan_label is not None:
                self._plan_label.add(axes, self.side)

    def get_canvas_size(self, figure) -> float:
        """
        If the size is unknown before rendering, this function must be
        implemented to return the canvas size in inches.
        """
        return self.size

    def get_legends(self) -> List[Artist] | None:
        """
        This should define the legend return by the RenderPlan.

        The return object could be any :class:`matplotlib.artist.Artist`

        .. note::
            :class:`matplotlib.colorbar.Colorbar` is not an :class:`Artist`.
            Use :class:`legendkit.colorart`

        """
        return None

    def set_legends(self, *args, **kwargs):
        raise NotImplementedError

    def update_main_canvas_size(self):
        pass

    def set_split_regroup(self, ratio):
        self._split_regroup = ratio

    def get_split_regroup(self):
        return self._split_regroup


class AxisOption:
    inverted: bool
    label: str
    visibility: bool
    ticklabels: bool


class StatsBase(RenderPlan):
    """A base class for rendering statistics plot"""

    render_main = True
    orient = None
    axis_options = None

    def get_orient(self):
        if self.orient is None:
            return "h" if self.is_flank else "v"
        return self.orient

    def get_deform_func(self):
        if self.has_deform:
            orient = self.get_orient()
            if self.side == "main":
                orient_mapper = {"h": "horizontally", "v": "vertically"}

                if ((orient == "v") & self.deform.is_row_split) or (
                    (orient == "h") & self.deform.is_col_split
                ):
                    plot_dir = orient_mapper[self.get_orient()]
                    msg = (
                        f"{self.__class__.__name__} is oriented "
                        f"{plot_dir} should only be split {plot_dir}"
                    )
                    raise SplitConflict(msg)

            if self.get_orient() == "v":
                return self.deform.transform_col
            else:
                return self.deform.transform_row

    def _setup_axis(self, ax):
        if self.get_orient() == "h":
            despine(ax=ax, left=True)
            ax.tick_params(left=False, labelleft=False, bottom=True, labelbottom=True)
        else:
            despine(ax=ax, bottom=True)
            ax.tick_params(left=True, labelleft=True, bottom=False, labelbottom=False)

    def align_lim(self, axes):
        is_inverted = False
        lim_low = []
        lim_up = []

        is_h = self.get_orient() == "h"
        for ax in axes:
            if is_h:
                low, up = ax.get_xlim()
                if ax.xaxis_inverted():
                    is_inverted = True
                    low, up = up, low
            else:
                low, up = ax.get_ylim()
                if ax.yaxis_inverted():
                    is_inverted = True
                    low, up = up, low
            lim_up.append(up)
            lim_low.append(low)
        lims = [np.min(lim_low), np.max(lim_up)]
        if is_inverted:
            lims = lims[::-1]
        for ax in axes:
            ax.set_xlim(*lims) if is_h else ax.set_ylim(*lims)

    def render(self, axes):
        # check if self._plan_label.loc is None
        is_loc = False
        props = None
        if self._plan_label is not None:
            if self._plan_label.loc is not None:
                is_loc = True
            props = self._plan_label.props
        if self.is_split:
            for spec in self.get_render_spec(axes):
                self.render_ax(spec)
            self.align_lim(axes)

            for i, ax in enumerate(axes):
                # leave axis for the first ax
                if (i == 0) & (self.get_orient() == "v"):
                    self._setup_axis(ax)
                    if not is_loc:
                        ax.set_ylabel(self.label, fontdict=props)
                # leave axis for the last ax
                elif (i == len(axes) - 1) & (self.get_orient() == "h"):
                    self._setup_axis(ax)
                    if not is_loc:
                        ax.set_xlabel(self.label, fontdict=props)
                else:
                    ax.set_axis_off()
        else:
            # axes.set_axis_off()
            self.render_ax(self.get_render_spec(axes))
            self._setup_axis(axes)
            if self.label is not None:
                if self.get_orient() == "v":
                    if not is_loc:
                        axes.set_ylabel(self.label, fontdict=props)
                else:
                    if not is_loc:
                        axes.set_xlabel(self.label, fontdict=props)

        if self.allow_labeling & is_loc:
           self._plan_label.add(axes, self.side)
