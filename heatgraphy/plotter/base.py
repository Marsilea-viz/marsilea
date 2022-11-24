from __future__ import annotations

from typing import Any, List, Callable

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from seaborn import despine

from .._deform import Deformation


class RenderPlan:
    """The base class for every plot in Heatgraphy

    Attributes
    ----------
    name : str
        The name of the plot,
        can be used to retrieve the render axes and corresponding legend.
    data :
        The raw data input by user
    side : str, default: 'top'
        Which side to render this plot
    size : float, default: 1
    no_split : bool, default: False
        Use to mark if the RenderPlan can be split
    render_main : bool, default: False
        Use to mark if the RenderPlan can be rendered on main canvas
    canvas_size_unknown : bool, default: False
        Use to mark if the RenderPlan needs to be rendered to
        get the canvas size; If mark as True, :meth:`get_canvas_size()` must
        be implemented.
    zorder : int, default: 0
        This only works if the RenderPlan is rendered on main canvas

    """
    name: str = None
    data: Any
    size: float = 1.
    side: str = "top"
    # label if a render plan
    # can be used on split axes
    no_split: bool = False
    # label if a render plan need to calculate
    # canvas size before rendering
    canvas_size_unknown: bool = False
    zorder: int = 0

    deform: Deformation = None
    deform_func = None
    # If True, this RenderPlan can be rendered on main ax
    render_main = False

    def __repr__(self):
        side_str = f"side='{self.side}'"
        zorder_str = f"zorder={self.zorder}"

        if self.name is None:
            chunks = [side_str, zorder_str]
        else:
            chunks = [f"name='{self.name}'", side_str, zorder_str]
        return f"{self.__class__.__name__}" \
               f"({', '.join(chunks)})"

    def set(self, **kwargs):
        for k, v in kwargs.items():
            if k == "side":
                self.set_side(v)
            else:
                self.__setattr__(k, v)

    def set_side(self, side):
        self.side = side
        self._update_deform_func()

    def set_size(self, size):
        self.size = size

    def _update_deform_func(self):
        if self.is_deform:
            if self.h:
                trans = self.deform.transform_row
            elif self.v:
                trans = self.deform.transform_col
            else:
                trans = self.deform.transform
            self.deform_func = trans

    def set_deform(self, deform: Deformation):
        self.deform = deform
        self._update_deform_func()

    @property
    def is_deform(self):
        """If deform exist"""
        return self.deform is not None

    def get_render_data(self):
        """Define how render data is organized

        The render data could be different depends on following situations:

        #. Render at different sides: left, right, top, bottom and main canvas
        #. The canvas is split or not

        """
        if self.is_deform:
            return self.deform_func(self.data)
        else:
            return self.data

    @property
    def v(self):
        return self.side in ["top", "bottom"]

    @property
    def h(self):
        return self.side in ["right", "left"]

    def render_ax(self, ax: Axes, data):
        """The major rendering function
        Define how the plot is drawn
        """
        raise NotImplemented

    def render_axes(self, axes):
        """Use to render plots when the canvas is split

        By default, it will match each data chunk to each axes

        .. code-block:: python

            for ax, data in zip(axes, self.get_render_data()):
                self.render_ax(ax, data)

        """
        for ax, data in zip(axes, self.get_render_data()):
            self.render_ax(ax, data)

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
            self.render_axes(axes)
        else:
            self.render_ax(axes, self.get_render_data())

    def get_canvas_size(self) -> float:
        """
        If :attr:`canvas_size_unknown` is True, This function must be
        implemented to determine how to calculate the canvas size in inches.
        """
        raise NotImplementedError("Must be implemented in derived RenderPlan")

    @property
    def is_split(self):
        """
        For the RenderPlan to self-aware of whether its render canvas
        will be split. Useful to determine how to get render data.
        """
        if self.deform is not None:
            if self.v & self.deform.is_col_split:
                return True
            if self.h & self.deform.is_row_split:
                return True
            if (self.side == "main") & self.deform.is_split:
                return True
        return False

    def get_legends(self) -> List[Artist] | None:
        """
        This should define the legend return by the RenderPlan.

        The return object could be any :class:`matplotlib.artist.Artist`

        .. note::
            :class:`matplotlib.colorbar.Colorbar` is not an :class:`Artist`.
            Use :func:`legendkit.colorart`

        """
        return None

    def set_legends(self, *args, **kwargs):
        raise NotImplemented


class StatsBase(RenderPlan):
    axis_label: str = ""

    def _setup_axis(self, ax):
        if self.v:
            despine(ax=ax, bottom=True)
            ax.tick_params(left=True, labelleft=True,
                           bottom=False, labelbottom=False)
        else:
            despine(ax=ax, left=True)
            ax.tick_params(left=False, labelleft=False,
                           bottom=True, labelbottom=True)

    def align_lim(self, axes):
        if self.v:
            is_inverted = False
            ylim_low = []
            ylim_up = []
            for ax in axes:
                low, up = ax.get_ylim()
                if ax.yaxis_inverted():
                    is_inverted = True
                    low, up = up, low
                ylim_up.append(up)
                ylim_low.append(low)
            ylims = [np.min(ylim_low), np.max(ylim_up)]
            if is_inverted:
                ylims = ylims[::-1]
            for ax in axes:
                ax.set_ylim(*ylims)
        else:
            is_inverted = False
            xlim_low = []
            xlim_up = []
            for ax in axes:
                low, up = ax.get_xlim()
                if ax.xaxis_inverted():
                    is_inverted = True
                    low, up = up, low
                xlim_up.append(up)
                xlim_low.append(low)
            xlims = [np.min(xlim_low), np.max(xlim_up)]
            if is_inverted:
                xlims = xlims[::-1]
            for ax in axes:
                ax.set_xlim(*xlims)

    def render(self, axes):
        if self.is_split:
            self.render_axes(axes)
            self.align_lim(axes)
            for i, ax in enumerate(axes):
                # leave axis for the first ax
                if (i == 0) & self.v:
                    self._setup_axis(ax)
                    ax.set_ylabel(self.axis_label)
                # leave axis for the last ax
                elif (i == len(axes) - 1) & self.h:
                    self._setup_axis(ax)
                    ax.set_xlabel(self.axis_label)
                else:
                    ax.set_axis_off()
        else:
            # axes.set_axis_off()
            self.render_ax(axes, self.get_render_data())
            self._setup_axis(axes)
            if self.axis_label is not None:
                if self.v:
                    axes.set_ylabel(self.axis_label)
                else:
                    axes.set_xlabel(self.axis_label)