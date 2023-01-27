from __future__ import annotations

from dataclasses import dataclass
from numbers import Number
from typing import List, Dict
from uuid import uuid4

import numpy as np
from icecream import ic
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from heatgraphy.exceptions import AppendLayoutError


# If not specify, we have few default setting
# 1. Size is inch unit
# 2. Origin point is left-bottom

# Axes is a rect, a rect can be recorded by a left-bottom anchor point
# and width and height. When other axes is added, the anchor point is aligned
# to either x-axis or y-axis, we could easily compute the final anchor point
# if we know the size of added axes

def _split(chunk_ratios, spacing=.05):
    """Return the relative anchor point, in ratio"""
    ratios = np.asarray(chunk_ratios) / np.sum(chunk_ratios)
    count = len(ratios)
    if isinstance(spacing, Number):
        spacing = [spacing for _ in range(count - 1)]

    canvas_size = 1 - np.sum(spacing)
    ratios = ratios * canvas_size

    start = 0
    anchors = []
    for ix, i in enumerate(ratios):
        anchors.append(start)
        start += i
        # If not the last one
        # Add space
        if ix != count - 1:
            start += spacing[ix - 1]
    return ratios, np.array(anchors)


def get_axes_rect(rect, figsize):
    cx, cy, cw, ch = rect
    fig_w, fig_h = figsize
    return cx / fig_w, cy / fig_h, cw / fig_w, ch / fig_h


class BaseCell:
    name: str
    side: str
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

    def hsplit(self, chunk_ratios, spacing=.05):
        """
        Parameters
        ----------
        chunk_ratios :
            The length of each chunk from top to bottom
        spacing :
            Relative to the cell size, the value should between 0~1
        """
        ratios, anchors = _split(chunk_ratios[::-1], spacing=spacing)
        self.h_ratios = ratios
        self.h_anchors = anchors

    def vsplit(self, chunk_ratios, spacing=.05):
        """
        Parameters
        ----------
        chunk_ratios :
            The length of each chunk from left to right
        spacing :
            Relative to the cell size, the value should between 0~1
        """
        ratios, anchors = _split(chunk_ratios, spacing=spacing)
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

    def get_cell_size(self):
        return self.width, self.height


@dataclass
class GridCell(BaseCell):
    name: str
    side: str
    size: float
    attach: MainCell
    is_canvas: bool = True

    def get_cell_size(self):
        """Get width, height of a cell"""
        if self.side in ['top', 'bottom']:
            return self.attach.width, self.size
        else:
            return self.size, self.attach.height


class CrossLayout:
    """
    The size is always in the unit of inches
    """

    # The left bottom anchor point of the layout
    anchor = None
    figsize = None
    figure = None

    def __init__(self, name, width, height, init_main=True) -> None:
        self._legend_ax_name = None
        self.main_cell = MainCell(name, width, height, is_canvas=init_main)
        self._side_cells = {'top': [], 'bottom': [], 'left': [], 'right': []}
        self.cells: Dict[str, BaseCell] = {name: self.main_cell}
        self._pads = {}

    def add_ax(self, side, name, size, pad=0.):
        # TODO: check the name
        new_cell = GridCell(name=name, side=side, size=size,
                            attach=self.main_cell)
        # Add pad before add canvas
        if pad > 0.:
            self.add_pad(side, pad)
        self._side_cells[side].append(new_cell)
        self.cells[name] = new_cell

    def add_pad(self, side, size):
        new_pad = GridCell(name=uuid4().hex, side=side, size=size,
                           is_canvas=False, attach=self.main_cell)
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

    def add_legend_ax(self, side, size, pad=0.):
        self._legend_ax_name = "-".join(
            [self.main_cell.name, "legend", uuid4().hex])
        self.add_ax(side, self._legend_ax_name, size, pad=pad)

    def get_legend_ax(self):
        return self.get_ax(self._legend_ax_name)

    def remove_legend_ax(self):
        self.remove_ax(self._legend_ax_name)

    def set_legend_size(self, size):
        self.cells[self._legend_ax_name].size = size

    def vsplit(self, name, chunk_ratios, spacing=.05):
        cell = self.cells[name]
        cell.is_split = True
        cell.vsplit(chunk_ratios, spacing=spacing)

    def hsplit(self, name, chunk_ratios, spacing=.05):
        cell = self.cells[name]
        cell.is_split = True
        cell.hsplit(chunk_ratios, spacing=spacing)

    def is_split(self, name):
        """Query if a cell is split"""
        return self.cells[name].is_split

    def get_side_size(self, side):
        return np.sum([c.size for c in self._side_cells[side]])

    def get_bbox_width(self):
        """Get the figure width in inches"""
        box_w = self.main_cell.width + self.get_side_size(
            'left') + self.get_side_size('right')
        return box_w

    def get_bbox_height(self):
        """Get the figure height in inches"""
        box_h = self.main_cell.height + self.get_side_size(
            'top') + self.get_side_size('bottom')
        return box_h

    def get_bbox_size(self):
        """Get the bbox size in inches (width, height)"""
        return self.get_bbox_width(), self.get_bbox_height()

    def get_figure_size(self):
        """Get the figsize in inches (width, height)"""
        if self.anchor is None:
            return self.get_bbox_size()
        else:
            ox, oy = self.anchor
            fig_w = ox + self.get_main_width() + self.get_side_size('right')
            fig_h = ox + self.get_main_height() + self.get_side_size('top')
            return fig_w, fig_h

    def get_main_anchor(self):
        """Get the main anchor point"""
        if self.anchor is None:
            x = self.get_side_size('left')
            y = self.get_side_size('bottom')
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

    def set_figsize(self, figsize):
        self.figsize = figsize

    def set_render_size(self, name, size):
        self.cells[name].size = size

    def initiate_axes(self, figure, _debug=False):
        figsize = figure.get_size_inches()
        clear_axes = figure == self.figure
        ic(clear_axes)
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
                        ax = figure.add_axes(rect)
                        axes.append(ax)
                        if _debug:
                            _debug_ax(ax, side=c.side, text=ix + 1)

                    c.set_ax(axes)
                else:
                    ax_rect = c.get_rect()
                    ax_rect = get_axes_rect(ax_rect, figsize)
                    ax = figure.add_axes(ax_rect)
                    c.set_ax(ax)
                    if _debug:
                        _debug_ax(ax, side=c.side, text=c.name)

    def freeze(self, figure=None, scale=1, _debug=False):
        """Freeze the current layout and draw on figure

        Freeze is safe to be called multiple times, it will update
        the layout if draw on the same figure

        Parameters
        ----------
        figure
        scale
        _debug

        Returns
        -------

        """
        if figure is None:
            if self.figsize is None:
                self.figsize = np.array(self.get_figure_size()) * scale
            figure = plt.figure(figsize=self.figsize)

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
        options['rotation'] = 90
    elif side == "right":
        options['rotation'] = -90

    if text is not None:
        ax.text(.5, .5, text, **options)


def _remove_axes(ax: Axes | List[Axes]):
    if ax is None:
        pass
    if isinstance(ax, Axes):
        ax.remove()
    else:
        for a in ax:
            a.remove()


def close_ticks(ax):
    ax.tick_params(bottom=False, top=False, left=False, right=False,
                   labelbottom=False, labeltop=False,
                   labelleft=False, labelright=False,
                   )


@dataclass
class _LegendAxes:
    side: str
    size: float
    pad: float
    ax = None

    def get_length(self):
        return self.size + self.pad


class CompositeCrossLayout:
    """A class to layout multiple Cross Layouts

    .. warn::
        This class are not supposed to be used directly by user

    Parameters
    ----------
    main_layout : CrossLayout
        The main cross layout

    """
    figure = None

    def __init__(self, main_layout) -> None:
        self.main_layout = main_layout
        self.main_cell_height = self.main_layout.get_main_height()
        self.main_cell_width = self.main_layout.get_main_width()
        self._side_layouts: Dict[str, List[CrossLayout]] = \
            {"top": [], "bottom": [], "right": [], "left": []}
        self._legend_axes = None

    @staticmethod
    def _reset_layout(layout):
        layout.set_anchor((0, 0))
        return layout

    def append(self, side, other):
        if isinstance(other, CompositeCrossLayout):
            raise AppendLayoutError

        elif isinstance(other, Number):
            other = CrossLayout(name=uuid4().hex,
                                width=self.main_cell_width,
                                height=other,
                                init_main=False)
            self._side_layouts[side].append(other)
        elif isinstance(other, CrossLayout):
            adjust = "height" if side in ["left", "right"] else "width"
            other = self._reset_layout(other)
            adjust_size = getattr(self, f"main_cell_{adjust}")
            getattr(other, f"set_main_{adjust}").__call__(adjust_size)
            self._side_layouts[side].append(other)
        else:
            raise TypeError(f"Cannot append object type of {type(other)}")

    def __truediv__(self, other: CrossLayout):
        self.append('bottom', other)

    def __add__(self, other: CrossLayout):
        self.append('right', other)

    def add_legend_ax(self, side, size, pad=0.):
        """Extend the layout

        This is used to draw legends after concatenation

        """
        self._legend_axes = _LegendAxes(side=side, size=size, pad=pad)

    def get_legend_ax(self):
        return self._legend_axes.ax

    def set_legend_size(self, size):
        self._legend_axes.size = size

    def get_side_size(self, side):
        """Get the max extend of a side, the center is the
        main cell of the main layout, not the whole main layout
        legend axes included"""
        # It's possible the left side of top x-layout
        # is longer than the left x-layout

        size = 0
        other_size = []
        size += self.main_layout.get_side_size(side)
        if side in ["left", "right"]:

            for g in self._side_layouts.get(side):
                size += g.get_bbox_width()

            for g in self._side_layouts['top'] + self._side_layouts['bottom']:
                other_size.append(g.get_side_size(side))
        else:

            for g in self._side_layouts.get(side):
                size += g.get_bbox_height()

            for g in self._side_layouts['left'] + self._side_layouts['right']:
                other_size.append(g.get_side_size(side))

        other_size = np.max(other_size, initial=0)
        legend_size = 0
        if self._legend_axes is not None:
            if self._legend_axes.side == side:
                legend_size = self._legend_axes.get_length()
        return max(size, other_size) + legend_size

    def get_bbox_width(self):
        return self.main_cell_width + self.get_side_size('left') + \
            self.get_side_size('right')

    def get_bbox_height(self):
        return self.main_cell_height + self.get_side_size('top') + \
            self.get_side_size('bottom')

    def get_bbox_size(self):
        """Get the minimum figsize that fits all layouts inside"""
        return self.get_bbox_width(), self.get_bbox_height()

    def get_figure_size(self):
        """Figure size should be the same as bbox size"""
        return self.get_bbox_size()

    def get_main_anchor(self):
        x = self.get_side_size('left')
        y = self.get_side_size('bottom')
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
        ic(mx, my)
        self.set_anchor((mx, my))

        self.main_layout.freeze(figure, _debug=_debug)

        # The left and right share the y
        offset_x = mx
        for g in self._side_layouts['left']:
            offset_x -= (g.get_side_size('right') + g.get_main_width())
            g.set_anchor((offset_x, my))
            g.set_figsize(figsize)
            g.freeze(figure, _debug=_debug)
            offset_x -= g.get_side_size('left')

        offset_x = (mx + self.main_cell_width +
                    self.main_layout.get_side_size('right'))
        for g in self._side_layouts['right']:
            offset_x += g.get_side_size('left')
            g.set_anchor((offset_x, my))
            g.set_figsize(figsize)
            g.freeze(figure, _debug=_debug)
            offset_x += (g.get_main_width() + g.get_side_size('right'))

        # The top and bottom share the x
        offset_y = my
        for g in self._side_layouts['bottom']:
            offset_y -= (g.get_side_size('top') + g.get_main_height())
            g.set_anchor((mx, offset_y))
            g.set_figsize(figsize)
            g.freeze(figure, _debug=_debug)
            offset_y -= g.get_side_size('bottom')

        offset_y = (my + self.main_cell_height +
                    self.main_layout.get_side_size('top'))
        for g in self._side_layouts['top']:
            offset_y += g.get_side_size('bottom')
            g.set_anchor((mx, offset_y))
            g.set_figsize(figsize)
            g.freeze(figure, _debug=_debug)
            offset_y += (g.get_main_height() + g.get_side_size('top'))

        # Add legend axes
        # The range is limited to the main_cell in each layout
        if self._legend_axes is not None:
            xmin, ymin, xmax, ymax = self._edge_main_point()
            legend_w, legend_h = xmax - xmin, ymax - ymin
            fig_w, fig_h = figsize
            bbox_w, bbox_h = fig_w, fig_h

            side = self._legend_axes.side
            size = self._legend_axes.size
            pad = self._legend_axes.pad
            if side in ["left", "right"]:
                bbox_w -= (size + pad)
            else:
                bbox_h -= (size + pad)

            ic(fig_w, fig_h)
            ic(bbox_w, bbox_h)

            if side == 'right':
                cx, cy = bbox_w + pad, ymin
                cw, ch = size, legend_h
            elif side == 'left':
                cx, cy = 0, ymin
                cw, ch = size, legend_h
            elif side == "top":
                cx, cy = xmin, bbox_h + pad
                cw, ch = legend_w, size
            elif side == "bottom":
                cx, cy = xmin, 0
                cw, ch = legend_w, size

            rect = get_axes_rect((cx, cy, cw, ch), figsize)
            ax = figure.add_axes(rect)
            if _debug:
                _debug_ax(ax, side=side, text="Legend Axes")
            self._legend_axes.ax = ax

        self.figure = figure

    def _edge_main_point(self):
        """This will return the edge point of all the main cell"""
        left_side = self._side_layouts['left']
        if len(left_side) > 0:
            xmin = left_side[-1].main_cell.anchor[0]
        else:
            xmin = self.main_layout.main_cell.anchor[0]

        right_side = self._side_layouts['right']
        if len(right_side) > 0:
            cell = right_side[-1].main_cell
        else:
            cell = self.main_layout.main_cell
        xmax = cell.anchor[0] + cell.width

        bottom_side = self._side_layouts['bottom']
        if len(bottom_side) > 0:
            ymin = bottom_side[-1].main_cell.anchor[1]
        else:
            ymin = self.main_layout.main_cell.anchor[1]

        top_side = self._side_layouts['top']
        if len(top_side) > 0:
            cell = top_side[-1].main_cell
        else:
            cell = self.main_layout.main_cell
        ymax = cell.anchor[1] + cell.height

        return xmin, ymin, xmax, ymax

    def plot(self, scale=1):
        self.freeze(scale=scale, _debug=True)
