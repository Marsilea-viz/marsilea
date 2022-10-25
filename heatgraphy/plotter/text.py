from __future__ import annotations

import warnings
from dataclasses import dataclass
from itertools import cycle
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
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
        print(s1, s2)
        s1.move_toward(s2, side="up")

    # adjust by reversed direction
    for s1, s2 in pairwise(reversed(segments)):
        s1.move_toward(s2, side="down")

    return segments


@dataclass
class TextConfig:
    ha: str
    va: str
    rotation: float
    connectionstyle: str
    relpos: tuple
    expand: tuple


side_mapper = {
    "top": TextConfig(va="bottom", ha="center", rotation=90,
                      connectionstyle="arc,angleA=-90,angleB=90,"
                                      "armA=30,armB=30,rad=0",
                      relpos=(0.5, 0), expand=(1.05, 1)),
    "bottom": TextConfig(va="top", ha="center", rotation=-90,
                         connectionstyle="arc,angleA=90,angleB=-90,"
                                         "armA=30,armB=30,rad=0",
                         relpos=(0.5, 1), expand=(1.05, 1)),
    "right": TextConfig(va="center", ha="left", rotation=0,
                        connectionstyle="arc,angleA=-180,angleB=0,"
                                        "armA=20,armB=20,rad=0",
                        relpos=(0, 0.5), expand=(1, 1.05)),
    "left": TextConfig(va="center", ha="right", rotation=0,
                       connectionstyle="arc,angleA=0,angleB=-180,"
                                       "armA=30,armB=30,rad=0",
                       relpos=(1, 0.5), expand=(1, 1.05)),
}


class AdjustableText:

    def __init__(self, x, y, text,
                 ax=None, renderer=None,
                 pointer=None,
                 expand=(1.05, 1.05),
                 va=None, ha=None, rotation=None,
                 connectionstyle=None, relpos=None,
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
                relpos=self.relpos),
        )


class _LabelBase(RenderPlan):
    va = None
    ha = None
    rotation = None
    connectionstyle = None
    relpos = None
    expand = None
    canvas_size = None
    canvas_size_unknown = True

    def set_side(self, side):
        self.side = side
        self._default_text_config()

    def _default_text_config(self):
        text_config = side_mapper[self.side]
        if self.va is None:
            self.va = text_config.va
        if self.ha is None:
            self.ha = text_config.ha
        if self.rotation is None:
            self.rotation = text_config.rotation
        if self.connectionstyle is None:
            self.connectionstyle = text_config.connectionstyle
        if self.relpos is None:
            self.relpos = text_config.relpos
        if self.expand is None:
            self.expand = text_config.expand

    @staticmethod
    def get_axes_coords(labels):
        coords = []
        use = False
        for i, c in enumerate(np.linspace(0, 1, len(labels) * 2 + 1)):
            if use:
                coords.append(c)
            use = not use
        return coords

    def silent_render(self):

        fig = plt.figure()
        renderer = fig.canvas.get_renderer()
        ax = fig.add_axes([0, 0, 1, 1])

        locs = self.get_axes_coords(self.data)
        sizes = []
        for s, c in zip(self.data, locs):
            x, y = (0, c) if self.h else (c, 0)
            t = ax.text(x, y, s=s, va=self.va, ha=self.ha,
                        rotation=self.rotation, transform=ax.transAxes)
            bbox = t.get_window_extent(renderer)  # .expanded(1.05, 1.05)
            if self.h:
                sizes.append(bbox.xmax - bbox.xmin)
            else:
                sizes.append(bbox.ymax - bbox.ymin)
        # matplotlib use 72 pixel per inch
        self.canvas_size = np.max(sizes) / 72
        plt.close(fig)


class AnnoLabels(_LabelBase):
    arrow_size = 0.4  # inches
    const_pos = cycle([0.4])

    def __init__(self,
                 mark_labels: np.ma.MaskedArray | List[np.ma.MaskedArray],
                 side="right",
                 va=None, ha=None, rotation=None, connectionstyle=None,
                 relpos=None,
                 **options,
                 ):
        self.data = mark_labels
        self.canvas_size = None
        self.side = side

        self.va = va
        self.ha = ha
        self.rotation = rotation
        self.connectionstyle = connectionstyle
        self.relpos = relpos
        self.options = options

    def get_canvas_size(self):
        self.silent_render()
        size = self.canvas_size + self.arrow_size
        self.const_pos = cycle([self.arrow_size / size])
        return size

    def render_ax(self, ax, labels):

        renderer = ax.get_figure().canvas.get_renderer()
        locs = self.get_axes_coords(labels)

        ax_bbox = ax.get_window_extent(renderer)

        if self.v:
            texts = []
            segments = []
            for x, y, s in zip(locs, self.const_pos, labels):
                if not np.ma.is_masked(s):
                    t = AdjustableText(x=x, y=y, text=s, ax=ax,
                                       pointer=(x, 0),
                                       renderer=renderer,
                                       va=self.va, ha=self.ha,
                                       rotation=self.rotation,
                                       connectionstyle=self.connectionstyle,
                                       relpos=self.relpos,
                                       expand=self.expand
                                       )
                    texts.append(t)
                    segments.append(t.get_segment_x())

            lim = Segment(ax_bbox.xmin, ax_bbox.xmax)
            adj_segments = adjust_segments(lim, segments)
            for t, s in zip(texts, adj_segments):
                t.set_display_x(s.mid)
                t.draw_annotate()
        else:
            texts = []
            segments = []
            for x, y, s in zip(self.const_pos, locs, labels):
                if not np.ma.is_masked(s):
                    t = AdjustableText(x=x, y=y, text=s, ax=ax,
                                       pointer=(0, y),
                                       renderer=renderer,
                                       va=self.va, ha=self.ha,
                                       rotation=self.rotation,
                                       connectionstyle=self.connectionstyle,
                                       relpos=self.relpos,
                                       expand=self.expand
                                       )
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


class Labels(_LabelBase):

    def __init__(self, labels, align=None, side="right",
                 va=None, ha=None, rotation=None,
                 **options):
        self.data = np.asarray(labels)
        self.align = align
        self.canvas_size = None
        self.va = va
        self.ha = ha
        self.rotation = rotation
        self.side = side
        self.options = options

    def get_canvas_size(self):
        self.silent_render()
        return self.canvas_size

    def render_ax(self, ax: Axes, data):
        ax.set_axis_off()
        coords = self.get_axes_coords(data)
        if self.h:
            coords = coords[::-1]
        for s, c in zip(data, coords):
            x, y = (0, c) if self.h else (c, 0)
            ax.text(x, y, s=s, va=self.va, ha=self.ha,
                    rotation=self.rotation, transform=ax.transAxes,
                    **self.options)
