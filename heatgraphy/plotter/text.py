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
        print(s1, s2, s1.overlap(s2))
        # if s1.overlap(s2):
        s1.move_toward(s2, side="up")

    # adjust by reversed direction
    for s1, s2 in pairwise(reversed(segments)):
        print(s1, s2, s1.overlap(s2))
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
    canvas_size = None
    canvas_size_unknown = True
    _update_params = []
    _user_options = {}
    ha = None
    va = None
    rotation = None

    def __init__(self, **text_options):
        for k, v in text_options.items():
            if hasattr(self, k):
                setattr(self, k, v)
                if v is None:
                    self._update_params.append(k)
            else:
                self._user_options[k] = v

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


@dataclass
class TextConfig:
    ha: str
    va: str
    rotation: float
    connectionstyle: str
    relpos: tuple
    expand: tuple


anno_side_params = {
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


class AnnoLabels(_LabelBase):
    arrow_size = 0.4  # inches
    const_pos = 0.4

    # text params we need to take control of
    va = None
    ha = None
    rotation = None
    connectionstyle = None
    relpos = None
    expand = (1.2, 1.2)

    def __init__(self,
                 mark_labels: np.ma.MaskedArray | List[np.ma.MaskedArray],
                 side="right", arrow_size=0.4,
                 va=None, ha=None, rotation=None,
                 connectionstyle=None, relpos=None, **options):
        self.data = mark_labels
        self.canvas_size = None
        self.side = side
        self.arrow_size = arrow_size

        super().__init__(va=va, ha=ha, rotation=rotation,
                         connectionstyle=connectionstyle,
                         relpos=relpos, **options)

    def _update_text_params(self):
        text_params = anno_side_params[self.side]
        for param in self._update_params:
            v = getattr(text_params, param)
            setattr(self, param, v)

    def get_canvas_size(self):
        self.silent_render()
        size = self.canvas_size + self.arrow_size
        self.const_pos = self.arrow_size / size
        return size

    def render_ax(self, ax, labels):

        renderer = ax.get_figure().canvas.get_renderer()
        locs = self.get_axes_coords(labels)

        ax_bbox = ax.get_window_extent(renderer)

        text_options = dict(ax=ax, renderer=renderer, va=self.va,
                            ha=self.ha, rotation=self.rotation,
                            connectionstyle=self.connectionstyle,
                            relpos=self.relpos, expand=self.expand,
                            **self._user_options)
        texts = []
        segments = []
        if self.v:
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

align_pos = {
    'right': 1,
    'left': 0,
    'top': 1,
    'bottom': 0,
    'center': 0.5
}


class Labels(_LabelBase):
    # text params we need to take control of
    va = None
    ha = None
    rotation = None

    def __init__(self, labels, align=None,
                 va=None, ha=None, rotation=None,
                 **options):
        self.data = np.asarray(labels)
        self.align = align

        super().__init__(va=va, ha=ha, rotation=rotation, **options)

    def _update_text_params(self):
        if self.align is None:
            self.align = side_align[self.side]
        va, ha = self.align, "center"
        rotation = 90
        if self.h:
            va, ha = ha, va
            rotation = 0
        if 'va' in self._update_params:
            self.va = va
        if 'ha' in self._update_params:
            self.ha = ha
        if 'rotation' in self._update_params:
            self.rotation = rotation

    def get_canvas_size(self):
        self.silent_render()
        return self.canvas_size

    def render_ax(self, ax: Axes, data):
        ax.set_axis_off()
        coords = self.get_axes_coords(data)
        if self.h:
            coords = coords[::-1]
        const = align_pos[self.align]
        for s, c in zip(data, coords):
            x, y = (const, c) if self.h else (c, const)
            ax.text(x, y, s=s, va=self.va, ha=self.ha,
                    rotation=self.rotation, transform=ax.transAxes,
                    **self._user_options)


stick_pos = {
    "right": 0,
    "left": 1,
    "top": 0,
    "bottom": 1,
}


class Title(_LabelBase):
    no_split = True
    canvas_size_unknown = True

    va = None
    ha = None
    rotation = 0

    def __init__(self, title, align="center", va=None, ha=None,
                 fontsize=None, rotation=None, **options):
        self.data = title
        self.align = align
        if fontsize is None:
            fontsize = 12
        self.fontsize = fontsize

        super().__init__(va=va, ha=ha, rotation=rotation, **options)

    def _update_text_params(self):
        va = side_align[self.side]
        ha = self.align
        rotation = 0
        if self.h:
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
        self.silent_render()
        return self.canvas_size

    def render_ax(self, ax: Axes, title):
        const = align_pos[self.align]
        pos = stick_pos[self.side]
        x, y = (const, pos) if self.v else (pos, const)
        ax.text(x, y, title, fontsize=self.fontsize, va=self.va, ha=self.ha,
                transform=ax.transAxes,
                rotation=self.rotation, **self._user_options)
        ax.set_axis_off()
