from __future__ import annotations

from dataclasses import dataclass
from numbers import Number
from typing import List, Dict, Literal
from uuid import uuid4

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from .exceptions import AppendLayoutError, DuplicateName
from .utils import _check_side


# If not specify, we have few default setting
# 1. Size is inch unit
# 2. Origin point is left-bottom

# Axes is a  rect, a rect can be recorded by a left-bottom anchor point
# and width and height. When other axes is added, the anchor point is aligned
# to either x-axis or y-axis, we could easily compute the final anchor point
# if we know the size of added axes

# It's unlikely to return axes right after being added, the split operation
# is unknown, this will create more than one axes.


def _split(chunk_ratios, spacing=0.05, group_ratios=None):
    """Return the relative anchor point, in ratio"""

    ratios = np.asarray(chunk_ratios) / np.sum(chunk_ratios)
    count = len(ratios)
    if isinstance(spacing, Number):
        spacing = [spacing for _ in range(count - 1)]
    spacing = np.asarray(spacing)

    canvas_size = 1 - np.sum(spacing)
    ratios = ratios * canvas_size
    assert np.sum(spacing) + np.sum(ratios) - 1 <= 0.00001

    if group_ratios is not None:
        c = np.asarray(group_ratios)
        groups = (c / c.sum() * count).astype(int)
        if np.sum(groups) != count:
            raise ValueError(f"Cannot group the split with ratios of {group_ratios}")

        regroup_ratios = []
        anchors = [0]

        start_anchor = 0
        start_ix = 0
        last_ix = len(groups) - 1
        for i, g in enumerate(groups):
            if g == 1:
                gratio = ratios[start_ix]
            else:
                mr = ratios[start_ix : start_ix + g].sum()
                ms = spacing[start_ix : start_ix + g - 1].sum()
                gratio = mr + ms

            if i < last_ix:
                gspacing = spacing[start_ix + g - 1]
                start_anchor += gratio + gspacing
                anchors.append(start_anchor)
            else:
                start_anchor += gratio
            regroup_ratios.append(gratio)
            start_ix += g
        ratios = regroup_ratios
    else:
        start = 0
        anchors = []
        last_ix = len(ratios) - 1
        for ix, i in enumerate(ratios):
            anchors.append(start)
            start += i
            # If not the last one
            # Add space
            if ix < last_ix:
                start += spacing[ix]
    return np.array(ratios), np.array(anchors)


def get_axes_rect(rect, figsize):
    cx, cy, cw, ch = rect
    fig_w, fig_h = figsize
    return cx / fig_w, cy / fig_h, cw / fig_w, ch / fig_h


class BaseCell:
    name: str
    side: str
    projection: str = None
    ax = None
    anchor = None

    is_split: bool = False
    h_anchors: np.ndarray = None
    h_ratios: np.ndarray = None
    v_anchors: np.ndarray = None
    v_ratios: np.ndarray = None

    is_canvas: bool = True

    def set_ax(self, ax):
        self.ax = ax

    def set_anchor(self, anchor):
        self.anchor = anchor

    def get_cell_size(self) -> (float, float):
        raise NotImplementedError

    def get_rect(self):
        cx, cy = self.anchor
        cw, ch = self.get_cell_size()

        return cx, cy, cw, ch

    def hsplit(self, chunk_ratios, spacing=0.05, group_ratios=None):
        """
        Parameters
        ----------
        chunk_ratios :
            The length of each chunk from top to bottom
        spacing :
            Relative to the cell size, the value should between 0~1
        group_ratios :
            Regroup the split chunks

        """
        ratios, anchors = _split(
            chunk_ratios[::-1], spacing=spacing, group_ratios=group_ratios
        )
        self.h_ratios = ratios
        self.h_anchors = anchors

    def vsplit(self, chunk_ratios, spacing=0.05, group_ratios=None):
        """
        Parameters
        ----------
        chunk_ratios :
            The length of each chunk from left to right
        spacing :
            Relative to the cell size, the value should between 0~1
        group_ratios :
            Regroup the split chunks

        """
        ratios, anchors = _split(
            chunk_ratios, spacing=spacing, group_ratios=group_ratios
        )
        self.v_ratios = ratios
        self.v_anchors = anchors

    def get_rects(self):
        cx, cy = self.anchor
        cw, ch = self.get_cell_size()

        if self.v_anchors is not None:
            w_anchors = self.v_anchors * cw + cx
            w_sizes = self.v_ratios * cw
        else:
            w_anchors = [cx]
            w_sizes = [cw]

        if self.h_anchors is not None:
            h_anchors = self.h_anchors * ch + cy
            h_sizes = self.h_ratios * ch
        else:
            h_anchors = [cy]
            h_sizes = [ch]

        # Make sure the order of split axes is
        # from top-left to bottom-right
        h_anchors = h_anchors[::-1]
        h_sizes = h_sizes[::-1]

        rects = []
        for ay, ay_size in zip(h_anchors, h_sizes):
            for ax, ax_size in zip(w_anchors, w_sizes):
                rects.append((ax, ay, ax_size, ay_size))
        return rects


@dataclass
class MainCell(BaseCell):
    name: str
    width: float
    height: float
    side: str = "main"
    is_canvas: bool = True
    projection: str = None

    def get_cell_size(self):
        return self.width, self.height


@dataclass
class GridCell(BaseCell):
    name: str
    side: str
    size: float
    attach: MainCell
    is_canvas: bool = True
    projection: str = None

    def get_cell_size(self):
        """Get width, height of a cell"""
        if self.side in ["top", "bottom"]:
            return self.attach.width, self.size
        else:
            return self.size, self.attach.height


@dataclass
class Margin:
    top: float
    right: float
    bottom: float
    left: float


class _MarginMixin:
    margin = Margin(0, 0, 0, 0)

    def set_margin(self, margin):
        if isinstance(margin, Number):
            self.margin = Margin(margin, margin, margin, margin)
        else:
            if len(margin) == 4:
                self.margin = Margin(*margin)
            else:
                msg = (
                    "margin must be one number or a tuple with 4 numbers"
                    "(top, right, bottom, left)"
                )
                raise ValueError(msg)

    def get_margin_w(self):
        return self.margin.left + self.margin.right

    def get_margin_h(self):
        return self.margin.top + self.margin.bottom


class CrossLayout(_MarginMixin):
    """The cross-layout engine

    This class implements the cross-layout. The axes are added
    incrementally to the main axes.

    - The size is always in the unit of inches


    Parameters
    ----------
    name : str
        The name of the main canvas
    width : float
        The width of the main canvas
    height : float
        The height of the main canvas
    init_main : bool
        Add the main canvas as axes
    projection : str
        The projection of the main canvas

    Attributes
    ----------
    is_composite : bool
        Use to indicate the current position of CrossLayout.
        Whether it's in a CompositeCrossLayout.

    """

    def __init__(
        self, name, width, height, init_main=True, projection=None, margin=0.2
    ):
        self._legend_ax_name = None
        self.main_cell = MainCell(
            name, width, height, is_canvas=init_main, projection=projection
        )
        self._side_cells = {"top": [], "bottom": [], "left": [], "right": []}
        self.cells: Dict[str, BaseCell] = {name: self.main_cell}
        self._pads = {}

        self.is_composite = False
        self.figure = None
        self.figsize = None
        # The left bottom anchor point of the layout
        self.anchor = None
        # (top, right, bottom, left)
        self.set_margin(margin)

    def _get_cell(self, name):
        cell = self.cells.get(name)
        if cell is None:
            raise ValueError(f"Axes with name {name} not exist")
        return cell

    def add_ax(self, side, name, size, pad=0.0, projection=None):
        """Add an axes to the layout

        Parameters
        ----------
        side
        name
        size
        pad
        projection

        Returns
        -------

        """
        _check_side(side)
        if self.cells.get(name) is not None:
            raise DuplicateName(name)

        new_cell = GridCell(
            name=name,
            side=side,
            size=size,
            attach=self.main_cell,
            projection=projection,
        )
        # Add pad before add canvas
        if pad > 0.0:
            self.add_pad(side, pad)
        self._side_cells[side].append(new_cell)
        self.cells[name] = new_cell

    def add_pad(self, side, size):
        """Add padding between axes

        Parameters
        ----------
        side
        size

        Returns
        -------

        """
        _check_side(side)
        new_pad = GridCell(
            name=uuid4().hex,
            side=side,
            size=size,
            is_canvas=False,
            attach=self.main_cell,
        )
        self._side_cells[side].append(new_pad)

    def remove_ax(self, name):
        cell = self.cells.pop(name, None)
        if cell is not None:
            # remove from self._side_cells
            side = cell.side
            self._side_cells[side].remove(cell)
            # remove its pad
            pad = self._pads.pop(name, None)
            if pad is not None:
                self._side_cells[side].remove(pad)

    def get_ax(self, name):
        return self.cells[name].ax

    def get_main_ax(self):
        return self.main_cell.ax

    def add_legend_ax(self, side, size, pad=0.0):
        """Add a legend axes

        Parameters
        ----------
        side
        size
        pad

        Returns
        -------

        """
        # TODO: Ensure the legend axes always add at last
        self._legend_ax_name = "-".join([self.main_cell.name, "legend", uuid4().hex])
        self.add_ax(side, self._legend_ax_name, size, pad=pad)

    def get_legend_ax(self):
        if self._legend_ax_name is not None:
            return self.get_ax(self._legend_ax_name)

    def remove_legend_ax(self):
        self.remove_ax(self._legend_ax_name)

    def set_legend_size(self, size):
        legend_cell = self._get_cell(self._legend_ax_name)
        legend_cell.size = size

    def vsplit(self, name, chunk_ratios, spacing=0.05, group_ratios=None):
        cell = self._get_cell(name)
        cell.is_split = True
        cell.vsplit(chunk_ratios, spacing=spacing, group_ratios=group_ratios)

    def hsplit(self, name, chunk_ratios, spacing=0.05, group_ratios=None):
        cell = self._get_cell(name)
        cell.is_split = True
        cell.hsplit(chunk_ratios, spacing=spacing, group_ratios=group_ratios)

    def is_split(self, name):
        """Query if a cell is split"""
        return self._get_cell(name).is_split

    def get_side_size(self, side):
        return np.sum([c.size for c in self._side_cells[side]])

    def get_bbox_width(self):
        """Get the bbox width in inches"""
        box_w = (
            self.main_cell.width
            + self.get_side_size("left")
            + self.get_side_size("right")
        )
        return box_w

    def get_bbox_height(self):
        """Get the bbox height in inches"""
        box_h = (
            self.main_cell.height
            + self.get_side_size("top")
            + self.get_side_size("bottom")
        )
        return box_h

    def get_bbox_size(self):
        """Get the bbox size in inches (width, height)"""
        return self.get_bbox_width(), self.get_bbox_height()

    def get_figure_size(self):
        """Get the figsize in inches (width, height)"""
        if self.anchor is None:
            if self.is_composite:
                return self.get_bbox_size()
            w, h = self.get_bbox_size()
            return w + self.get_margin_w(), h + self.get_margin_h()

        else:
            ox, oy = self.anchor
            fig_w = ox + self.get_main_width() + self.get_side_size("right")
            fig_h = ox + self.get_main_height() + self.get_side_size("top")
            if self.is_composite:
                return fig_w, fig_h
            return fig_w + self.get_margin_w(), fig_h + self.get_margin_h()

    def get_main_anchor(self):
        """Get the main anchor point"""
        if self.anchor is None:
            x = self.get_side_size("left")
            y = self.get_side_size("bottom")
            if self.is_composite:
                return x, y
            x += self.margin.left
            y += self.margin.bottom
            return x, y
        else:
            return self.anchor

    def set_layout(self, main_anchor):
        """Set the layout of all cell

        Parameters
        ----------
        main_anchor : point
            The anchor point of the main cell

        """
        self.main_cell.set_anchor(main_anchor)
        ax, ay = main_anchor
        for side, cells in self._side_cells.items():
            if side == "top":
                cell_y = ay + self.main_cell.height
                for c in cells:
                    c.set_anchor((ax, cell_y))
                    cell_y += c.size
            elif side == "bottom":
                cell_y = ay
                for c in cells:
                    cell_y -= c.size
                    c.set_anchor((ax, cell_y))
            elif side == "left":
                cell_x = ax
                for c in cells:
                    cell_x -= c.size
                    c.set_anchor((cell_x, ay))
            else:
                cell_x = ax + self.main_cell.width
                for c in cells:
                    c.set_anchor((cell_x, ay))
                    cell_x += c.size

    def get_main_height(self):
        return self.main_cell.height

    def set_main_height(self, height):
        self.main_cell.height = height

    def get_main_width(self):
        return self.main_cell.width

    def set_main_width(self, width):
        self.main_cell.width = width

    def set_anchor(self, anchor):
        self.anchor = anchor

    def set_bbox_anchor(self, anchor):
        xoff = self.margin.left + self.get_side_size("left")
        yoff = self.margin.bottom + self.get_side_size("bottom")
        self.anchor = anchor[0] + xoff, anchor[1] + yoff

    def set_figsize(self, figsize):
        self.figsize = figsize

    def set_render_size(self, name, size):
        self._get_cell(name).size = size

    def initiate_axes(self, figure, _debug=False):
        figsize = self.figsize
        clear_axes = figure == self.figure
        # add axes
        for c in list(self.cells.values()):
            # Previous axes will be removed
            if clear_axes:
                _remove_axes(c.ax)
            # only add if it's a canvas
            if c.is_canvas:
                # check if it's split
                if c.is_split:
                    ax_rects = c.get_rects()
                    ax_rects = [get_axes_rect(r, figsize) for r in ax_rects]
                    axes = []
                    for ix, rect in enumerate(ax_rects):
                        ax = figure.add_axes(rect, projection=c.projection)
                        axes.append(ax)
                        if _debug:
                            _debug_ax(ax, side=c.side, text=ix + 1)

                    c.set_ax(axes)
                else:
                    ax_rect = c.get_rect()
                    print(ax_rect)
                    ax_rect = get_axes_rect(ax_rect, figsize)
                    print(ax_rect)
                    ax = figure.add_axes(ax_rect, projection=c.projection)
                    c.set_ax(ax)
                    if _debug:
                        _debug_ax(ax, side=c.side, text=f"{c.name}{c.get_cell_size()}")

    def freeze(
        self,
        figure=None,
        scale=1,
        _debug=False,
    ):
        """Freeze the current layout and draw on figure

        Freeze is safe to be called multiple times, it will update
        the layout if draw on the same figure

        Parameters
        ----------
        figure : :class:`matplotlib.figure.Figure`
            A matplotlib figure instance
        scale : float
            To scale the size of figure
        _debug : bool
            Not a public parameter, for internal debug use,
            the information display on the canvas
            is not guarantee to be consistent.

        Returns
        -------

        """
        # If not composed, update the figsize
        if not self.is_composite:
            self.figsize = np.array(self.get_figure_size())
        figsize = self.figsize * scale
        if figure is None:
            figure = plt.figure(figsize=figsize)
        else:
            if not self.is_composite:
                figure.set_size_inches(*figsize)

        main_anchor = self.get_main_anchor()
        self.set_layout(main_anchor)

        self.initiate_axes(figure, _debug=_debug)
        self.figure = figure

    def plot(self, scale=1):
        self.freeze(scale=scale, _debug=True)

    def _append_check(self, other):
        if isinstance(other, CompositeCrossLayout):
            raise AppendLayoutError
        if isinstance(other, (CrossLayout, Number)):
            c = CompositeCrossLayout(main_layout=self)
            return c

    def append(self, side, other):
        c = self._append_check(other)
        c.append(side, other)

    def __truediv__(self, other):
        return self.append("bottom", other)

    def __add__(self, other):
        return self.append("right", other)


def _debug_ax(ax, side, text=None):
    close_ticks(ax)
    options = dict(transform=ax.transAxes, va="center", ha="center")
    if side == "left":
        options["rotation"] = 90
    elif side == "right":
        options["rotation"] = -90

    if text is not None:
        ax.text(0.5, 0.5, text, **options)


def _remove_axes(ax: Axes | List[Axes]):
    if ax is None:
        return
    if isinstance(ax, Axes):
        ax.remove()
    else:
        for a in ax:
            a.remove()


def close_ticks(ax):
    ax.tick_params(
        bottom=False,
        top=False,
        left=False,
        right=False,
        labelbottom=False,
        labeltop=False,
        labelleft=False,
        labelright=False,
    )


def _reset_layout(layout: CrossLayout):
    layout.set_anchor((0, 0))
    layout.is_composite = True
    return layout


@dataclass
class _LegendAxes:
    side: str
    size: float
    pad: float
    ax = None

    def get_length(self):
        return self.size + self.pad


class CompositeCrossLayout(_MarginMixin):
    """A class to layout multiple Cross Layouts

    .. warning::
        This class are not supposed to be used directly by user

    Parameters
    ----------
    main_layout : CrossLayout
        The main cross layout

    """

    figure = None

    def __init__(self, main_layout, margin=0, align_main=True) -> None:
        self.main_layout = _reset_layout(main_layout)
        self.main_cell_height = self.main_layout.get_main_height()
        self.main_cell_width = self.main_layout.get_main_width()
        self._side_layouts: Dict[str, List[CrossLayout]] = {
            "top": [],
            "bottom": [],
            "right": [],
            "left": [],
        }
        self._legend_axes = None
        self.layouts = {self.main_layout.main_cell.name: self.main_layout}
        self.set_margin(margin)
        self.align_main = align_main

    def append(self, side, other):
        _check_side(side)
        if isinstance(other, CompositeCrossLayout):
            raise AppendLayoutError

        elif isinstance(other, Number):
            if side in ["left", "right"]:
                width, height = other, self.main_cell_height
            else:
                width, height = self.main_cell_height, other
            other = CrossLayout(
                name=uuid4().hex, width=width, height=height, init_main=False
            )
            other.is_composite = True
            self._side_layouts[side].append(other)
        elif isinstance(other, CrossLayout):
            other = _reset_layout(other)
            if self.align_main:
                adjust = "height" if side in ["left", "right"] else "width"
                adjust_size = getattr(self, f"main_cell_{adjust}")
                getattr(other, f"set_main_{adjust}").__call__(adjust_size)
            self._side_layouts[side].append(other)
            self.layouts[other.main_cell.name] = other
        else:
            raise TypeError(f"Cannot append object type of {type(other)}")

    def __truediv__(self, other: CrossLayout):
        self.append("bottom", other)

    def __add__(self, other: CrossLayout):
        self.append("right", other)

    def add_legend_ax(self, side, size, pad=0.0):
        """Extend the layout

        This is used to draw legends after concatenation

        """
        self._legend_axes = _LegendAxes(side=side, size=size, pad=pad)

    def get_legend_ax(self):
        if self._legend_axes is not None:
            return self._legend_axes.ax

    def set_legend_size(self, size):
        self._legend_axes.size = size

    def get_side_size(self, side):
        """Get the max extend of a side, the center is the
        main cell of the main layout, not the whole main layout
        legend axes included"""
        # It's possible the left side of top cross-layout
        # is longer than the left cross-layout

        size = 0
        other_size = []
        size += self.main_layout.get_side_size(side)
        if side in ["left", "right"]:
            for g in self._side_layouts.get(side):
                size += g.get_bbox_width()

            for g in self._side_layouts["top"] + self._side_layouts["bottom"]:
                other_size.append(g.get_side_size(side))
        else:
            for g in self._side_layouts.get(side):
                size += g.get_bbox_height()

            for g in self._side_layouts["left"] + self._side_layouts["right"]:
                other_size.append(g.get_side_size(side))

        other_size = np.max(other_size, initial=0)
        legend_size = 0
        if self._legend_axes is not None:
            if self._legend_axes.side == side:
                legend_size = self._legend_axes.get_length()
        return max(size, other_size) + legend_size

    def get_bbox_width(self):
        return (
            self.main_cell_width
            + self.get_side_size("left")
            + self.get_side_size("right")
        )

    def get_bbox_height(self):
        return (
            self.main_cell_height
            + self.get_side_size("top")
            + self.get_side_size("bottom")
        )

    def get_bbox_size(self):
        """Get the minimum figsize that fits all layouts inside"""
        return self.get_bbox_width(), self.get_bbox_height()

    def get_figure_size(self):
        """Figure size is bbox size + margin"""
        fig_w = self.get_bbox_width() + self.get_margin_w()
        fig_h = self.get_bbox_height() + self.get_margin_h()
        return fig_w, fig_h

    def get_main_anchor(self):
        x = self.get_side_size("left") + self.margin.left
        y = self.get_side_size("bottom") + self.margin.bottom
        return x, y

    def set_anchor(self, anchor):
        self.main_layout.set_anchor(anchor)

    def freeze(self, figure=None, scale=1, _debug=False):
        figsize = np.asarray(self.get_figure_size()) * scale

        if figure is None:
            figure = plt.figure(figsize=figsize)
        else:
            figure.set_size_inches(figsize)

        # To freeze all the layouts
        # We only need to compute the anchor point for main layouts
        # And then the location will be automatically derived

        # compute the anchor point for the main layout
        mx, my = self.get_main_anchor()
        self.main_layout.set_anchor((mx, my))
        self.main_layout.set_figsize(figsize)

        self.main_layout.freeze(figure, _debug=_debug)

        # The left and right share the y
        offset_x = mx - self.main_layout.get_side_size("left")
        for g in self._side_layouts["left"]:
            offset_x -= g.get_side_size("right") + g.get_main_width()
            g.set_anchor((offset_x, my))
            g.set_figsize(figsize)
            g.freeze(figure, _debug=_debug)
            offset_x -= g.get_side_size("left")

        offset_x = mx + self.main_cell_width + self.main_layout.get_side_size("right")
        for g in self._side_layouts["right"]:
            offset_x += g.get_side_size("left")
            g.set_anchor((offset_x, my))
            g.set_figsize(figsize)
            g.freeze(figure, _debug=_debug)
            offset_x += g.get_main_width() + g.get_side_size("right")

        # The top and bottom share the x
        offset_y = my - self.main_layout.get_side_size("bottom")
        for g in self._side_layouts["bottom"]:
            offset_y -= g.get_side_size("top") + g.get_main_height()
            g.set_anchor((mx, offset_y))
            g.set_figsize(figsize)
            g.freeze(figure, _debug=_debug)
            offset_y -= g.get_side_size("bottom")

        offset_y = my + self.main_cell_height + self.main_layout.get_side_size("top")
        for g in self._side_layouts["top"]:
            offset_y += g.get_side_size("bottom")
            g.set_anchor((mx, offset_y))
            g.set_figsize(figsize)
            g.freeze(figure, _debug=_debug)
            offset_y += g.get_main_height() + g.get_side_size("top")

        # Add legend axes
        # The range is limited to the main_cell in each layout
        if self._legend_axes is not None:
            xmin, ymin, xmax, ymax = self._edge_main_point()
            legend_w, legend_h = xmax - xmin, ymax - ymin
            fig_w, fig_h = figsize

            side = self._legend_axes.side
            size = self._legend_axes.size

            if side == "right":
                cx, cy = fig_w - size - self.margin.right, ymin
                cw, ch = size, legend_h
            elif side == "left":
                cx, cy = self.margin.left, ymin
                cw, ch = size, legend_h
            elif side == "top":
                cx, cy = xmin, fig_h - self.margin.top - size
                cw, ch = legend_w, size
            elif side == "bottom":
                cx, cy = xmin, self.margin.bottom
                cw, ch = legend_w, size

            rect = get_axes_rect((cx, cy, cw, ch), figsize)
            ax = figure.add_axes(rect)
            if _debug:
                _debug_ax(ax, side=side, text="Legend Axes")
            self._legend_axes.ax = ax

        self.figure = figure

    def _edge_main_point(self):
        """This will return the edge point of all the main cell"""
        left_side = self._side_layouts["left"]
        if len(left_side) > 0:
            xmin = left_side[-1].main_cell.anchor[0]
        else:
            xmin = self.main_layout.main_cell.anchor[0]

        right_side = self._side_layouts["right"]
        if len(right_side) > 0:
            cell = right_side[-1].main_cell
        else:
            cell = self.main_layout.main_cell
        xmax = cell.anchor[0] + cell.width

        bottom_side = self._side_layouts["bottom"]
        if len(bottom_side) > 0:
            ymin = bottom_side[-1].main_cell.anchor[1]
        else:
            ymin = self.main_layout.main_cell.anchor[1]

        top_side = self._side_layouts["top"]
        if len(top_side) > 0:
            cell = top_side[-1].main_cell
        else:
            cell = self.main_layout.main_cell
        ymax = cell.anchor[1] + cell.height

        return xmin, ymin, xmax, ymax

    def plot(self, scale=1):
        self.freeze(scale=scale, _debug=True)

    def get_ax(self, layout_name, ax_name):
        return self.layouts[layout_name].get_ax(ax_name)

    def get_main_ax(self, layout_name):
        return self.layouts[layout_name].get_main_ax()


class StackCrossLayout(_MarginMixin):
    """A stack of cross layouts

    This class allow users to stack multiple cross layouts
    either horizontally or vertically

    Multiple StackCrossLayout can also be stacked

    .. warning::
        This class are not supposed to be used directly by user

    Parameters
    ----------
    layouts : list of :class:`CrossLayout`, :class:`StackCrossLayout`
        The layouts to be stacked
    direction : {"horizontal", "vertical"}
        The direction of the stack, horizontal will stack from left to right
        vertical will stack from top to bottom
    align : {"center", "bottom", "top", "left", "right"}
        The alignment of the stack, the default is center

    """

    _direction_align = {
        "horizontal": {"center", "top", "bottom"},
        "vertical": {"center", "left", "right"},
    }

    def __init__(
        self,
        layouts: List[CrossLayout | StackCrossLayout],
        direction="horizontal",
        align: Literal["center", "bottom", "top", "left", "right"] = "center",
        spacing=0,
        margin=0,
        name=None,
    ):
        # Check the direction and align
        if direction not in self._direction_align:
            raise ValueError(f"Invalid direction {direction}")
        if align not in self._direction_align[direction]:
            raise ValueError(
                f"When setting direction={direction}, "
                f"align must be one of {self._direction_align[direction]}"
            )

        self.layouts = []
        self._layouts_mapper = {}
        for layout in layouts:
            layout = _reset_layout(layout)
            self.layouts.append(layout)
            if hasattr(layout, "name"):
                self._layouts_mapper[layout.name] = layout
            else:
                self._layouts_mapper[layout.main_cell.name] = layout
        self.direction = direction
        self.align = align
        self.spacing = spacing
        if name is None:
            name = uuid4().hex
        self.name = name
        self.set_margin(margin)
        self.is_composite = False
        self.figure = None
        self.figsize = None
        # The left bottom anchor point of the layout
        self.anchor = None
        self._legend_axes = None

    def remove_legend_ax(self):
        self._legend_axes = None
        for layout in self.layouts:
            layout.remove_legend_ax()

    def _get_layout_widths(self):
        return [layout.get_bbox_width() for layout in self.layouts]

    def _get_layout_heights(self):
        return [layout.get_bbox_height() for layout in self.layouts]

    def _get_spacing_widths(self):
        return self.spacing * (len(self.layouts) - 1)

    def _get_spacing_heights(self):
        return self.spacing * (len(self.layouts) - 1)

    def get_bbox_width(self):
        ws = self._get_layout_widths()
        if self.direction == "horizontal":
            return np.sum(ws) + self._get_spacing_widths()
        else:
            if self.align == "center":
                return np.max(ws)
            elif self.align == "left":
                left_sides = np.asarray(
                    [layout.get_side_size("left") for layout in self.layouts]
                )
                right_leftover = ws - left_sides
                return np.max(left_sides) + np.max(right_leftover)
            else:
                right_sides = np.asarray(
                    [layout.get_side_size("right") for layout in self.layouts]
                )
                left_leftover = ws - right_sides
                return np.max(right_sides) + np.max(left_leftover)

    def get_bbox_height(self):
        hs = self._get_layout_heights()
        if self.direction == "vertical":
            return np.sum(hs) + self._get_spacing_heights()
        else:
            if self.align == "center":
                return np.max(hs)
            elif self.align == "top":
                top_sides = np.asarray(
                    [layout.get_side_size("top") for layout in self.layouts]
                )
                bottom_leftover = hs - top_sides
                return np.max(top_sides) + np.max(bottom_leftover)
            else:
                bottom_sides = np.asarray(
                    [layout.get_side_size("bottom") for layout in self.layouts]
                )
                top_leftover = hs - bottom_sides
                return np.max(bottom_sides) + np.max(top_leftover)

    def get_bbox_size(self):
        return self.get_bbox_width(), self.get_bbox_height()

    def get_figure_size(self):
        fig_w = self.get_bbox_width() + self.get_margin_w()
        fig_h = self.get_bbox_height() + self.get_margin_h()
        return fig_w, fig_h

    def set_figsize(self, figsize):
        self.figsize = figsize
        for layout in self.layouts:
            layout.set_figsize(figsize)

    # Mimic the CrossLayoutAPI
    def get_side_size(self, side):
        legend_size = 0
        if self._legend_axes is not None:
            if self._legend_axes.side == side:
                legend_size = self._legend_axes.get_length()
        return self._get_layouts_offset(side) + legend_size

    # Mimic the CrossLayoutAPI
    def get_main_height(self):
        return (
            self.get_bbox_height()
            - self._get_layouts_offset("bottom")
            - self._get_layouts_offset("top")
        )

    # Mimic the CrossLayoutAPI
    def get_main_width(self):
        return (
            self.get_bbox_width()
            - self._get_layouts_offset("left")
            - self._get_layouts_offset("right")
        )

    def _get_layouts_offset(self, side):
        if self.direction == "horizontal":
            if side in {"bottom", "top"}:
                return np.max([layout.get_side_size(side) for layout in self.layouts])
            elif side == "left":
                return self.layouts[0].get_side_size("left")
            else:
                return self.layouts[-1].get_side_size("right")
        else:
            if side in {"left", "right"}:
                return np.max([layout.get_side_size(side) for layout in self.layouts])
            elif side == "bottom":
                return self.layouts[-1].get_side_size("bottom")
            else:
                return self.layouts[0].get_side_size("top")

    def get_layout_anchors(self):
        """Get the anchor points of all layouts assume the layout is not composite"""
        base_x, base_y = self.margin.left, self.margin.bottom
        xs, ys = [], []
        if self.direction == "horizontal":
            # x is always the same regardless of the alignment
            for layout in self.layouts:
                base_x += layout.get_side_size("left")
                xs.append(base_x)
                base_x += (
                    layout.get_main_width()
                    + layout.get_side_size("right")
                    + self.spacing
                )
            # only y is different
            if self.align == "bottom":
                base_y = self.margin.bottom + self._get_layouts_offset("bottom")
                ys = [base_y for _ in range(len(self.layouts))]
            elif self.align == "top":
                base_y = (
                    self.margin.bottom
                    + self.get_bbox_height()
                    - self._get_layouts_offset("top")
                )
                ys = [base_y - layout.get_main_height() for layout in self.layouts]
            else:
                center_y = self.margin.bottom + self.get_bbox_height() / 2
                ys = [
                    center_y - layout.get_main_height() / 2 for layout in self.layouts
                ]
        else:
            # y is always the same regardless of the alignment
            for layout in self.layouts[::-1]:
                base_y += layout.get_side_size("bottom")
                ys.append(base_y)
                base_y += (
                    layout.get_main_height()
                    + layout.get_side_size("top")
                    + self.spacing
                )
            # only x is different
            if self.align == "left":
                base_x = self.margin.left + self._get_layouts_offset("left")
                xs = [base_x for _ in range(len(self.layouts))]
            elif self.align == "right":
                base_x = (
                    self.margin.left
                    + self.get_bbox_width()
                    - self._get_layouts_offset("right")
                )
                xs = [base_x - layout.get_main_width() for layout in self.layouts]
            else:
                center_x = self.margin.left + self.get_bbox_width() / 2
                xs = [center_x - layout.get_main_width() / 2 for layout in self.layouts]
            ys = ys[::-1]

        return np.array(list(zip(xs, ys)))

    def set_layout_anchors(self, anchors):
        for layout, a in zip(self.layouts, anchors):
            layout.set_anchor(a)

    def set_anchor(self, anchor):
        self.anchor = anchor

    def add_legend_ax(self, side, size, pad=0.0):
        """Extend the layout

        This is used to draw legends after concatenation

        """
        self._legend_axes = _LegendAxes(side=side, size=size, pad=pad)

    def get_legend_ax(self):
        if self._legend_axes is not None:
            return self._legend_axes.ax

    def set_legend_size(self, size):
        self._legend_axes.size = size

    def freeze(self, figure=None, scale=1, _debug=False):
        # If not composed, update the figsize
        if not self.is_composite:
            self.figsize = np.array(self.get_figure_size())
        figsize = self.figsize * scale
        if figure is None:
            figure = plt.figure(figsize=figsize)
        else:
            if not self.is_composite:
                figure.set_size_inches(*figsize)

        # Compute the anchor points for all sub layouts
        anchors = self.get_layout_anchors()
        # Offset the anchor point by the main anchor
        main_anchor = np.min(anchors, axis=0)
        if self.anchor is not None:
            xoff = self.anchor[0] - main_anchor[0]
            yoff = self.anchor[1] - main_anchor[1]
            anchors = [(x + xoff, y + yoff) for x, y in anchors]
        self.set_layout_anchors(anchors)

        for layout in self.layouts:
            layout.set_figsize(figsize)
            layout.freeze(figure, _debug=_debug)

        if self._legend_axes is not None:
            bbox_w, bbox_h = self.get_bbox_size()
            ax, ay = main_anchor

            side = self._legend_axes.side
            size = self._legend_axes.size

            if side == "right":
                cx, cy = ax + bbox_w, ay
                cw, ch = size, bbox_h
            elif side == "left":
                cx, cy = ax - size, ay
                cw, ch = size, bbox_h
            elif side == "top":
                cx, cy = ax, ay + bbox_h
                cw, ch = bbox_w, size
            elif side == "bottom":
                cx, cy = ax, ay - size
                cw, ch = bbox_w, size

            rect = get_axes_rect((cx, cy, cw, ch), figsize)
            ax = figure.add_axes(rect)
            if _debug:
                _debug_ax(ax, side=side, text="Legend Axes")
            self._legend_axes.ax = ax

        self.figure = figure

    def get_ax(self, layout_name, ax_name):
        return self._layouts_mapper[layout_name].get_ax(ax_name)

    def get_main_ax(self, layout_name):
        return self._layouts_mapper[layout_name].get_main_ax()
