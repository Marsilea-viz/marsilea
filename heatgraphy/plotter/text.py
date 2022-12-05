from __future__ import annotations

import warnings
from dataclasses import dataclass
from itertools import cycle
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import is_color_like
from matplotlib.patches import Rectangle
from matplotlib.text import Text

from .base import RenderPlan
from ..utils import pairwise


class Segment:
    up: float
    low: float

    max: float = None
    min: float = None

    def __repr__(self):
        return f"Segments({self.label}: {self.low:.2f} - {self.up:.2f})"

    def __init__(self, low, up, label=""):
        self.low = low
        self.up = up

        self.side = None
        self.label = label

    @property
    def length(self):
        return self.up - self.low

    @property
    def mid(self):
        return self.length / 2 + self.low

    def overlap(self, other):
        # Other on the left
        if self.low >= other.up:
            return False
        # Other on the right
        elif other.low >= self.up:
            return False
        else:
            return True

    def move_toward(self, other: Segment, side="up"):
        """Move other to a side of self"""
        if not self.overlap(other):
            # Other on the left and move up
            if (self.low >= other.up) & (side == "up"):
                offset = self.length + other.length + (self.low - other.up)
                other.move_up(offset)

            if (other.low >= self.up) & (side == "down"):
                offset = self.length + other.length + (other.low - self.up)
                other.move_down(offset)

        if side == "up":
            if self.up >= other.up:
                offset = self.up - other.up + other.length
            else:
                offset = self.up - other.low
            other.move_up(offset)
        else:
            if self.low <= other.low:
                offset = other.low - self.low + other.length
            else:
                offset = other.up - self.low
            other.move_down(offset)

    def set_lim(self, lim: Segment):
        self.max = lim.up
        self.min = lim.low
        if self.low < self.min:
            self.low = self.min
        if self.up > self.max:
            self.up = self.max

    def move_up(self, offset):
        # check if move across lim
        final_up = self.up + offset
        if final_up <= self.max:
            self.up = final_up
            self.low += offset
        else:
            offset = self.max - self.up
            self.up = self.max
            self.low += offset

    def move_down(self, offset):
        # check if move across lim
        final_low = self.low - offset
        if final_low >= self.min:
            self.up -= offset
            self.low -= offset
        else:
            offset = self.low - self.min
            self.low = self.min
            self.up -= offset


def adjust_segments(lim: Segment, segments: List[Segment]):
    """segments must be pass in the render order"""

    # Ensure all segments are in the axes bbox
    total_length = 0
    for s in segments:
        s.set_lim(lim)
        total_length += s.length

    if total_length > lim.length:
        warnings.warn("Too many labels to fit in, "
                      "try reducing the fontsize.")

    # adjust by one direction
    for s1, s2 in pairwise(segments):
        # print(s1, s2, s1.overlap(s2))
        # if s1.overlap(s2):
        s1.move_toward(s2, side="up")

    # adjust by reversed direction
    for s1, s2 in pairwise(reversed(segments)):
        # print(s1, s2, s1.overlap(s2))
        # if s1.overlap(s2):
        s1.move_toward(s2, side="down")

    return segments


class AdjustableText:

    def __init__(self, x, y, text,
                 ax=None, renderer=None,
                 pointer=None,
                 expand=(1.05, 1.05),
                 va=None, ha=None, rotation=None,
                 connectionstyle=None, relpos=None,
                 linewidth=None,
                 **kwargs):
        if ax is None:
            ax = plt.gca()
        if renderer is None:
            fig = plt.gcf()
            renderer = fig.canvas.get_renderer()
        self.ax = ax
        self.renderer = renderer
        if pointer is None:
            pointer = (x, y)
        self.pointer = pointer
        self.x = x
        self.y = y
        self.text = text

        self.va = va
        self.ha = ha
        self.rotation = rotation
        self.connectionstyle = connectionstyle
        self.relpos = relpos
        self.linewidth = linewidth
        self.text_obj = Text(x, y, text, va=va, ha=ha,
                             rotation=rotation,
                             transform=self.ax.transAxes,
                             **kwargs)
        ax.add_artist(self.text_obj)
        self._bbox = self.text_obj.get_window_extent(self.renderer) \
            .expanded(*expand)
        self.annotation = None

    def get_display_coordinate(self):
        return self.text_obj.get_transform().transform((self.x, self.y))

    def get_bbox(self):
        return self._bbox

    def get_segment_x(self):
        return Segment(self._bbox.xmin, self._bbox.xmax, label=self.text)

    def get_segment_y(self):
        return Segment(self._bbox.ymin, self._bbox.ymax, label=self.text)

    def set_display_coordinate(self, tx, ty):
        x, y = self.ax.transAxes.inverted().transform((tx, ty))
        self.x = x
        self.y = y

    def set_display_x(self, tx):
        x, _ = self.ax.transAxes.inverted().transform((tx, 0))
        self.x = x

    def set_display_y(self, ty):
        _, y = self.ax.transAxes.inverted().transform((0, ty))
        self.y = y

    def redraw(self):
        self.text_obj.set_position((self.x, self.y))

    def draw_annotate(self):
        self.text_obj.remove()
        self.annotation = self.ax.annotate(
            self.text,
            xy=self.pointer,
            xytext=(self.x, self.y),
            va=self.va,
            ha=self.ha,
            rotation=self.rotation,
            transform=self.ax.transAxes,
            arrowprops=dict(
                arrowstyle="-",
                connectionstyle=self.connectionstyle,
                linewidth=self.linewidth,
                relpos=self.relpos),
        )


class _LabelBase(RenderPlan):
    canvas_size = None
    canvas_size_unknown = True

    def __init__(self, **text_options):
        self._update_params = set()
        self._user_options = {}
        self.ha = None
        self.va = None
        self.rotation = None
        for k, v in text_options.items():
            if hasattr(self, k):
                setattr(self, k, v)
                if v is None:
                    self._update_params.add(k)
            else:
                self._user_options[k] = v
        self._update_text_params()

    def set_side(self, side):
        self.side = side
        self._update_text_params()
        self._update_deform_func()

    def _update_text_params(self):
        raise NotImplemented

    @staticmethod
    def get_axes_coords(labels):
        coords = []
        use = False
        for i, c in enumerate(np.linspace(0, 1, len(labels) * 2 + 1)):
            if use:
                coords.append(c)
            use = not use
        return coords

    def silent_render(self, expand=(1., 1.)):

        fig = plt.figure()
        renderer = fig.canvas.get_renderer()
        ax = fig.add_axes([0, 0, 1, 1])

        locs = self.get_axes_coords(self.data)
        sizes = []
        for s, c in zip(self.data, locs):
            x, y = (0, c) if self.is_flank else (c, 0)
            t = ax.text(x, y, s=s, va=self.va, ha=self.ha,
                        rotation=self.rotation, transform=ax.transAxes)
            bbox = t.get_window_extent(renderer).expanded(*expand)
            if self.is_flank:
                sizes.append(bbox.xmax - bbox.xmin)
            else:
                sizes.append(bbox.ymax - bbox.ymin)
        # matplotlib use 72 pixel per inch
        self.canvas_size = np.max(sizes) / 72
        plt.close(fig)


@dataclass
class TextConfig:
    ha: str
    va: str
    rotation: float
    connectionstyle: str
    relpos: tuple


anno_side_params = {
    "top": TextConfig(va="bottom", ha="center", rotation=90,
                      connectionstyle="arc,angleA=-90,angleB=90,"
                                      "armA=10,armB=10,rad=0",
                      relpos=(0.5, 0)),
    "bottom": TextConfig(va="top", ha="center", rotation=-90,
                         connectionstyle="arc,angleA=90,angleB=-90,"
                                         "armA=10,armB=10,rad=0",
                         relpos=(0.5, 1)),
    "right": TextConfig(va="center", ha="left", rotation=0,
                        connectionstyle="arc,angleA=-180,angleB=0,"
                                        "armA=10,armB=10,rad=0",
                        relpos=(0, 0.5)),
    "left": TextConfig(va="center", ha="right", rotation=0,
                       connectionstyle="arc,angleA=0,angleB=-180,"
                                       "armA=10,armB=10,rad=0",
                       relpos=(1, 0.5)),
}


class AnnoLabels(_LabelBase):
    """Annotate a few rows or columns

    This is useful when your heatmap contains many rows/columns,
    and you only want to annotate a few of them.

    Parameters
    ----------
    mark_labels : np.ma.MaskedArray
        The length of the labels should match the main canvas side where
        it attaches to, the labels that won't be displayed should be masked.
    side : str
    text_pad : float
        Add padding around the text, relative to the fontsize
    pointer_length : float
        The size of the pointer
    linewidth : float
        The linewidth of the pointer
    va, ha, rotation :
        Text style
    connectionstyle :
    relpos :
    options :


    Examples
    --------

    If only shows values 4 and 5

    .. code-block:: python

        >>> texts = np.arange(10)
        >>> labels = np.ma.masked_where(~np.in1d(texts, [4, 5]), texts)

    .. plot::
        :context: close-figs

        >>> labels = np.arange(100)
        >>> labels = np.ma.masked_where(~np.in1d(labels, [3, 4, 5]), labels)

        >>> import heatgraphy as hg
        >>> from heatgraphy.plotter import AnnoLabels
        >>> matrix = np.random.randn(100, 10)
        >>> h = hg.Heatmap(matrix)
        >>> marks = AnnoLabels(labels)
        >>> h.add_right(marks)
        >>> h.render()

    """

    def __init__(self,
                 mark_labels: np.ma.MaskedArray | List[np.ma.MaskedArray],
                 side="right", text_pad=0.5, pointer_length=0.5,
                 linewidth=None, va=None, ha=None, rotation=None,
                 connectionstyle=None, relpos=None, **options):
        # if mark_labels.ndim > 1:
        #     mark_labels = mark_labels.flatten()
        self.data = mark_labels
        self.canvas_size = None
        self.side = side
        self.pointer_length = pointer_length
        self.linewidth = linewidth
        self.const_pos = 0.4
        self.expand = (1. + text_pad, 1. + text_pad)
        self.connectionstyle = None
        self.relpos = None

        super().__init__(va=va, ha=ha, rotation=rotation,
                         connectionstyle=connectionstyle,
                         relpos=relpos, **options)

    def _update_text_params(self):
        text_params = anno_side_params[self.side]
        for param in self._update_params:
            v = getattr(text_params, param)
            setattr(self, param, v)

    def get_canvas_size(self):
        self.silent_render(self.expand)
        size = self.canvas_size + self.pointer_length
        self.const_pos = self.pointer_length / size
        return size

    def render_ax(self, ax, labels):
        renderer = ax.get_figure().canvas.get_renderer()
        locs = self.get_axes_coords(labels)

        ax_bbox = ax.get_window_extent(renderer)

        text_options = dict(ax=ax, renderer=renderer, va=self.va,
                            ha=self.ha, rotation=self.rotation,
                            connectionstyle=self.connectionstyle,
                            relpos=self.relpos, expand=self.expand,
                            linewidth=self.linewidth,
                            **self._user_options)
        texts = []
        segments = []
        if self.is_body:
            y = self.const_pos
            for x, s in zip(locs, labels):
                if not np.ma.is_masked(s):
                    t = AdjustableText(x=x, y=y, text=s, pointer=(x, 0),
                                       **text_options)
                    texts.append(t)
                    segments.append(t.get_segment_x())

            lim = Segment(ax_bbox.xmin, ax_bbox.xmax)
            adj_segments = adjust_segments(lim, segments)
            for t, s in zip(texts, adj_segments):
                t.set_display_x(s.mid)
                t.draw_annotate()
        else:
            x = self.const_pos
            for y, s in zip(locs, labels):
                if not np.ma.is_masked(s):
                    t = AdjustableText(x=x, y=y, text=s, pointer=(0, y),
                                       **text_options)
                    texts.append(t)
                    segments.append(t.get_segment_y())

            lim = Segment(ax_bbox.ymin, ax_bbox.ymax)
            adj_segments = adjust_segments(lim, segments)
            for t, s in zip(texts, adj_segments):
                t.set_display_y(s.mid)
                t.draw_annotate()

        ax.set_axis_off()
        if self.side != "top":
            ax.invert_yaxis()
        if self.side == "left":
            ax.invert_xaxis()


side_align = {
    "right": "left",
    "left": "right",
    "top": "bottom",
    "bottom": "top"
}


class Labels(_LabelBase):
    """Add text labels

    Parameters
    ----------
    labels : array of str
    align : str
        Which side of the text to align
    text_pad : float
        Add padding around text, relative to the size of axes

    """

    def __init__(self, labels, align=None,
                 va=None, ha=None, rotation=None,
                 text_pad=0,
                 **options):
        self.data = np.asarray(labels)
        self.align = None
        self.pad = text_pad

        super().__init__(va=va, ha=ha, rotation=rotation, align=align,
                         **options)

    def _update_text_params(self):
        if 'align' in self._update_params:
            self.align = side_align[self.side]
        va, ha = self.align, "center"
        rotation = 90
        if self.is_flank:
            va, ha = ha, va
            rotation = 0
        if 'va' in self._update_params:
            self.va = va
        if 'ha' in self._update_params:
            self.ha = ha
        if 'rotation' in self._update_params:
            self.rotation = rotation

    def get_canvas_size(self):
        self.silent_render(expand=(1, 1))
        return self.canvas_size * (1 + self.pad)

    def render_ax(self, ax: Axes, data):
        ax.set_axis_off()
        coords = self.get_axes_coords(data)
        if self.is_flank:
            coords = coords[::-1]
        if self.align == "center":
            const = .5
        elif self.align in ["right", "top"]:
            const = 1 - self.pad / 2
        else:
            const = self.pad / 2
        for s, c in zip(data, coords):
            x, y = (const, c) if self.is_flank else (c, const)
            ax.text(x, y, s=s, va=self.va, ha=self.ha,
                    rotation=self.rotation, transform=ax.transAxes,
                    **self._user_options)


stick_pos = {
    "right": 0,
    "left": 1,
    "top": 0,
    "bottom": 1,
}

align_pos = {
    'right': 1,
    'left': 0,
    'top': 1,
    'bottom': 0,
    'center': 0.5
}


class Title(_LabelBase):

    def __init__(self, title, align="center", text_pad=0.5, va=None, ha=None,
                 fontsize=None, rotation=None, **options):
        self.data = title
        self.align = align
        if fontsize is None:
            fontsize = 12
        self.fontsize = fontsize
        self.expand = (1. + text_pad, 1. + text_pad)
        self.rotation = 0

        super().__init__(va=va, ha=ha, rotation=rotation, **options)

    def _update_text_params(self):
        va = side_align[self.side]
        ha = self.align
        rotation = 0
        if self.is_flank:
            va, ha = ha, va
            rotation = 90 if self.side == "left" else -90
        if 'va' in self._update_params:
            self.va = va
        if 'ha' in self._update_params:
            self.ha = ha
        if 'rotation' in self._update_params:
            self.rotation = rotation

    def get_render_data(self):
        return self.data

    def get_canvas_size(self):
        self.silent_render(expand=self.expand)
        return self.canvas_size

    def render_ax(self, ax: Axes, title):
        const = align_pos[self.align]
        pos = stick_pos[self.side]
        x, y = (const, pos) if self.is_body else (pos, const)
        ax.text(x, y, title, fontsize=self.fontsize, va=self.va, ha=self.ha,
                transform=ax.transAxes,
                rotation=self.rotation, **self._user_options)
        ax.set_axis_off()


_default_rotation = {
    "right": -90,
    "left": 90,
    "top": 0,
    "bottom": 0,
}


class Chunk(_LabelBase):

    def __init__(self, texts, rotation=None,
                 props=None, text_pad=0.5, fill_colors=None, bordercolor=None,
                 borderwidth=None, borderstyle=None, **options):
        super().__init__(rotation=rotation)
        self.data = texts
        self.props = props if props is not None else {}
        if is_color_like(fill_colors):
            fill_colors = [fill_colors for _ in range(len(self.data))]
        self.fill_colors = fill_colors
        self.bordercolor = bordercolor
        self.borderwidth = borderwidth
        self.borderstyle = borderstyle
        if self.fill_colors is not None:
            self._draw_bg = True
        else:
            self._draw_bg = False
        self.expand = (1. + text_pad, 1. + text_pad)
        self.va = "center"
        self.ha = "center"
        self.options = options

    def get_canvas_size(self):
        self.silent_render(expand=self.expand)
        return self.canvas_size

    def set_side(self, side):
        self.side = side
        if self.rotation is None:
            self.rotation = _default_rotation[self.side]
        self._update_deform_func()

    def _update_text_params(self):
        pass

    def render(self, axes):

        text_options = dict(va=self.va, ha=self.ha, rotation=self.rotation)
        text_options.update(self.props)

        for i, ax in enumerate(axes):
            ax.set_axis_off()
            if self._draw_bg:
                rect = Rectangle((0, 0), 1, 1,
                                 facecolor=self.fill_colors[i],
                                 edgecolor=self.bordercolor,
                                 linewidth=self.borderwidth,
                                 linestyle=self.borderstyle,
                                 transform=ax.transAxes)
                ax.add_artist(rect)

            ax.text(0.5, 0.5, self.data[i], fontdict=text_options,
                    transform=ax.transAxes, **self.options)
