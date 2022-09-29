from itertools import cycle

import numpy as np
from matplotlib.text import Text

from ._base import _PlotBase


def get_midpoint(lower, upper):
    return (upper - lower) / 2 + lower


class Label(_PlotBase):

    align_mapper = {
        "top": "bottom",
        "bottom": "top",
        "right": "left",
        "left": "right"
    }

    def __init__(self, axes, labels,
                 pos="edge",  # edge or center
                 draw_bbox=False,
                 **options):
        self.axes = axes
        self.labels = labels
        self.options = options
        self.pos = pos
        self.draw_bbox = draw_bbox

    def render(self):
        if self.is_whole():
            self._add_labels(self.axes, self.labels)
        else:
            for ax, chunk_labels in zip(self.axes, self.labels):
                self._add_labels(ax, chunk_labels)

    def _get_pos(self, midpoint):
        if self.pos == "edge":
            return midpoint / 8
        else:
            return midpoint

    def _add_labels(self, ax, labels):
        locs = np.arange(0.5, len(labels) + 0.5, 1)
        if self.draw_bbox:
            ax.tick_params(top=False, bottom=False, left=False, right=False,
                           labeltop=False, labelbottom=False,
                           labelleft=False, labelright=False)
        else:
            ax.set_axis_off()

        va = "center"
        ha = self.align_mapper[self.orient]
        if self.pos == "edge":
            const_pos = 1 / 16
        else:
            ha = "center"
            const_pos = 1 / 2
        xs = cycle([const_pos])
        ys = locs

        if self.is_vertical:
            va, ha = ha, va
            xs, ys = ys, xs
            ax.set_ylim(0, 1.0)
            ax.set_xlim(0, locs[-1] + 0.5)
        else:
            ax.set_xlim(0, 1.0)
            ax.set_ylim(0, locs[-1] + 0.5)

        options = {**dict(va=va, ha=ha), **self.options}
        for s, x, y in zip(labels, xs, ys):
            t = Text(x=x, y=y, text=s, **options)
            ax.add_artist(t)

        if self.orient != "top":
            ax.invert_yaxis()
        if self.orient == "left":
            ax.invert_xaxis()


