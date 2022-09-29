from __future__ import annotations
import warnings
from dataclasses import dataclass
from typing import List
from itertools import tee, cycle
from enum import Enum

import matplotlib.pyplot as plt
from matplotlib.text import Text
import numpy as np

from ._base import _PlotBase


def pairwise(iterable):
    """This is not available in itertools until 3.10"""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class Relation(Enum):
    Right = 1
    Left = 2
    CrossRight = 3
    CrossLeft = 4
    Inside = 5
    Contain = 6


class Segment:
    up: float
    low: float

    def __repr__(self):
        return f"Segments({self.low:.2f} - {self.up:.2f})"

    def __init__(self, low, up):
        self.low = low
        self.up = up
        self.length = up - low
        self.side = None

    @property
    def mid(self):
        return self.length / 2 + self.low

    def overlap(self, other) -> (Relation, float):
        L = self.low - other.low
        U = self.up - other.up
        LU = self.low - other.up
        UL = self.up - other.low
        # print("L", L, "U", U, "LU", LU, "UL", UL)
        # Other is inside self
        if (L < 0) & (U > 0):
            return Relation.Inside, 0
        # Other contains self
        if (L > 0) & (U < 0):
            return Relation.Contain, 0
        # Other is on the right of self
        if UL < 0:
            return Relation.Right, -UL
        # Other is on the left of self
        if LU > 0:
            return Relation.Left, LU
        # Other is cross self on the right
        if (L < 0) & (UL > 0):
            return Relation.CrossRight, UL
        if (L > 0) & (LU < 0):
            return Relation.CrossLeft, -LU

    def set_side(self, point):
        if self.mid > point:
            self.side = 2  # Upper
        else:
            self.side = 1  # Lower

    def move_up(self, offset):
        self.up += offset
        self.low += offset

    def move_down(self, offset):
        self.up -= offset
        self.low -= offset

    def move(self, offset, relation):
        if (relation == Relation.CrossLeft) | (relation == Relation.Left):
            self.move_up(offset)
        elif (relation == Relation.CrossRight) | (relation == Relation.Right):
            self.move_down(offset)


def adjust_segments(lim: Segment, segments: List[Segment]):
    """segments must be sorted ascending"""

    # Ensure all segments are in the axes bbox
    total_length = 0
    length_collect = []
    for s in segments:
        relation, offset = lim.overlap(s)
        if offset > 0:
            s.move(offset, relation)
        length_collect.append(s.length)
        total_length += s.length

    if total_length > lim.length:
        warnings.warn("Too many labels to fit in, "
                      "try reducing the fontsize.")

    # Choose a good enough mid-point to perform adjust
    n = len(length_collect)
    mid_point = np.sum(np.asarray(length_collect)[0:int(n / 2)]) + lim.low
    for s in segments:
        s.set_side(mid_point)

    for s1, s2 in pairwise(segments):
        if s1.side == s2.side == 1:
            relation, offset = s1.overlap(s2)
            if offset > 0:
                if relation == Relation.CrossRight:
                    s2.move_up(offset)
                elif relation in [Relation.CrossLeft, Relation.Left]:
                    s2.move_up((s2.length - offset) + s1.length)
        else:
            break

    for s1, s2 in pairwise(segments[::-1]):
        if s1.side == s2.side == 2:
            relation, offset = s1.overlap(s2)
            if offset > 0:
                if relation == Relation.CrossLeft:
                    s2.move_down(offset)
                elif relation in [Relation.CrossRight, Relation.Right]:
                    s2.move_down((s2.length - offset) + s1.length)
        else:
            break

    return segments


@dataclass
class TextConfig:
    ha: str
    va: str
    rotation: float
    connectionstyle: str
    relpos: tuple


orient_mapper = {
    "top": TextConfig(va="bottom", ha="center", rotation=90,
                      connectionstyle="arc,angleA=-90,angleB=90,"
                                      "armA=30,armB=30,rad=0",
                      relpos=(0.5, 0)),
    "bottom": TextConfig(va="top", ha="center", rotation=-90,
                         connectionstyle="arc,angleA=90,angleB=-90,"
                                         "armA=30,armB=30,rad=0",
                         relpos=(0.5, 1)),
    "right": TextConfig(va="center", ha="left", rotation=0,
                        connectionstyle="arc,angleA=-180,angleB=0,"
                                        "armA=30,armB=30,rad=0",
                        relpos=(0, 0.5)),
    "left": TextConfig(va="center", ha="right", rotation=0,
                       connectionstyle="arc,angleA=0,angleB=-180,"
                                       "armA=30,armB=30,rad=0",
                       relpos=(1, 0.5)),
}


class AdjustableText:

    def __init__(self, x, y, text,
                 ax=None, renderer=None,
                 pointer=None,
                 expand=(1.05, 1.05),
                 orient="right",
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
        self.orient = orient

        orient_config = orient_mapper[orient]

        self.va = orient_config.va
        self.ha = orient_config.ha
        self.rotation = orient_config.rotation
        self.connectionstyle = orient_config.connectionstyle
        self.relpos = orient_config.relpos
        self.text_obj = Text(x, y, text, va=self.va, ha=self.ha,
                             rotation=self.rotation,
                             **kwargs)
        ax.add_artist(self.text_obj)
        self._bbox = self.text_obj.get_window_extent(self.renderer) \
            .expanded(*expand)

    def get_display_coordinate(self):
        return self.text_obj.get_transform().transform((self.x, self.y))

    def get_bbox(self):
        return self._bbox

    def get_segment_x(self):
        return Segment(self._bbox.xmin, self._bbox.xmax)

    def get_segment_y(self):
        return Segment(self._bbox.ymin, self._bbox.ymax)

    def set_display_coordinate(self, tx, ty):
        x, y = self.ax.transData.inverted().transform((tx, ty))
        self.x = x
        self.y = y

    def set_display_x(self, tx):
        x, _ = self.ax.transData.inverted().transform((tx, 0))
        self.x = x

    def set_display_y(self, ty):
        _, y = self.ax.transData.inverted().transform((0, ty))
        self.y = y

    def redraw(self):
        self.text_obj.set_position((self.x, self.y))

    def draw_annotate(self):
        self.text_obj.remove()
        self.ax.annotate(
            self.text,
            xy=self.pointer,
            xytext=(self.x, self.y),
            va=self.va,
            ha=self.ha,
            rotation=self.rotation,
            arrowprops=dict(
                arrowstyle="-",
                connectionstyle=self.connectionstyle,
                relpos=self.relpos),
        )


class AnnoLabel(_PlotBase):

    def __init__(self,
                 axes,
                 mark_labels: np.ma.MaskedArray | List[np.ma.MaskedArray],
                 **options,
                 ):
        self.axes = axes
        if self.is_whole():
            self.figure = self.axes.get_figure()
        else:
            self.figure = self.axes[0].get_figure()
        self.renderer = self.figure.canvas.get_renderer()
        self.mark_labels = mark_labels

    def render(self):
        if self.is_whole():
            self._add_labels(self.axes, self.mark_labels)
        else:
            for ax, chunk_labels in zip(self.axes, self.mark_labels):
                self._add_labels(ax, chunk_labels)

    def _add_labels(self, ax, labels):

        locs = np.arange(0.5, len(labels)+0.5, 1)
        const_pos = cycle([0.5])

        ax_bbox = ax.get_window_extent(self.renderer)
        if self.is_vertical:
            ax.set_ylim(0, 1.0)
            ax.set_xlim(0, locs[-1] + 0.5)

            texts = []
            for x, y, s in zip(locs, const_pos, labels):
                if not np.ma.is_masked(s):
                    t = AdjustableText(x=x, y=y, text=s, ax=ax,
                                       pointer=(x, 0), orient=self.orient,
                                       renderer=self.renderer)
                    texts.append(t)

            lim = Segment(ax_bbox.xmin, ax_bbox.xmax)
            segments = [t.get_segment_x() for t in texts]
            adj_segments = adjust_segments(lim, segments)
            for t, s in zip(texts, adj_segments):
                t.set_display_x(s.mid)
                t.draw_annotate()
        else:
            ax.set_xlim(0, 1.0)
            ax.set_ylim(0, locs[-1] + 0.5)
            texts = []
            for x, y, s in zip(const_pos, locs, labels):
                if not np.ma.is_masked(s):
                    t = AdjustableText(x=x, y=y, text=s, ax=ax,
                                       pointer=(0, y), orient=self.orient,
                                       renderer=self.renderer)
                    texts.append(t)

            lim = Segment(ax_bbox.ymin, ax_bbox.ymax)
            segments = [t.get_segment_y() for t in texts]
            adj_segments = adjust_segments(lim, segments)
            for t, s in zip(texts, adj_segments):
                t.set_display_y(s.mid)
                t.draw_annotate()

        ax.set_axis_off()
        if self.orient != "top":
            ax.invert_yaxis()
        if self.orient == "left":
            ax.invert_xaxis()


