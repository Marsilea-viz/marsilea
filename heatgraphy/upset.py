# The API design of upsetplot is highly inspired from UpsetPlot
# https://github.com/jnothman/UpSetPlot

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Circle, Rectangle

from . import CrossGrid
from .base import _Base
from .plotter import Numbers, Labels


@dataclass
class UpSetAttr:
    name: str
    data: np.ndarray


class UpsetData:
    names: np.ndarray  # columns
    items: np.ndarray  # row
    data: np.ndarray  # one-hot encode matrix
    attrs: UpSetAttr = None

    def __init__(self, names, data, items=None, attrs=None):
        self.names = names
        self.items = items
        self.data = data
        self.attrs = attrs

        self._sets_table = pd.DataFrame(columns=names, index=items,
                                        data=data)
        self._sets_size = None

    @staticmethod
    def from_sets(sets: Dict) -> UpsetData:
        names = []
        items = set()
        new_sets = []
        sets_total = {}
        for name, s in sets.items():
            names.append(name)
            s = set(s)
            new_sets.append(s)
            items.update(s)
            sets_total[name] = len(s)
        items = np.array(list(items))
        data = []
        for name, s in zip(names, new_sets):
            d = [i in s for i in items]
            data.append(d)
        data = np.array(data, dtype=int).T
        container = UpsetData(names, data, items=items)
        container._sets_size = sets_total
        return container

    def from_dataframe(self, data):
        pass

    def isin(self, item):
        """Return the sets name the item is in"""
        pass

    def overlap_items(self, sets_name):
        """Return the items that appears in sets"""
        pass

    def overlap_count(self, count, up=None, low=None):
        """Return the item that has overlap at exactly number of sets"""
        pass

    def sets_table(self):
        result = self._sets_table.groupby(self.names).size()
        result = pd.DataFrame(result, columns=["size"])
        result["degree"] = result.index.to_frame().sum(axis=1)
        return result

    def sets_size(self):
        total = pd.DataFrame(data=self._sets_size, index=["size"])
        # reorder based on names order
        return total[self.names].T

    def sets_attrs(self):
        pass


class Upset(_Base):

    def __init__(self, data: UpsetData, orient="h",
                 sets_order=None,
                 sort_subset="size",  # size, degree
                 ascending=True,
                 min_degree=None,
                 max_degree=None,
                 min_size=None,
                 max_size=None,
                 color=".1",
                 shading=.3,
                 radius=.25,
                 linewidth=1.5,
                 grid_background=0.1,
                 add_intersections=True,
                 add_sets_size=True,
                 add_labels=True,
                 ):
        sets_table = data.sets_table()
        sets_size = data.sets_size()

        if sets_order is not None:
            sets_table = sets_table.reorder_levels(sets_order)
        if sort_subset is not None:
            sets_table = sets_table.sort_values(sort_subset,
                                                ascending=ascending)
        if min_degree is not None:
            sets_table = sets_table[sets_table["degree"] >= min_degree]
        if max_degree is not None:
            sets_table = sets_table[sets_table["degree"] <= max_degree]
        if min_size is not None:
            sets_table = sets_table[sets_table["size"] >= min_size]
        if max_size is not None:
            sets_table = sets_table[sets_table["size"] >= max_size]

        self.orient = orient
        self.color = color
        self.shading = shading
        self.radius = radius
        self.linewidth = linewidth
        self.grid_background = grid_background

        self.sets_table = sets_table
        self.sets_size = sets_size
        self._matrix = sets_table.index.to_frame().to_numpy()
        self._subset_styles = {}
        self._subset_line_styles = {}
        self._intersection_bar = None
        self._sets_size_bar = None

        if orient == "h":
            if add_intersections:
                self._interactions = "top"
            if add_sets_size:
                self._sets_size = "left"
            if add_labels:
                self._labels = "right"
        else:
            if add_intersections:
                self._interactions = "right"
            if add_sets_size:
                self._sets_size = "top"
            if add_labels:
                self._labels = "bottom"

        h, w = sets_table.index.to_frame().shape

        if orient == "h":
            h, w = w, h
        super().__init__(main_aspect=h / w)
        if add_intersections:
            self.add_intersections(self._interactions)
        if add_labels:
            self.add_sets_label(self._labels)
        if add_sets_size:
            self.add_sets_size(self._sets_size)

    def _mark_subsets(self, present=None, absent=None,
                      min_size=None, max_size=None,
                      min_degree=None, max_degree=None):
        sets_table = self.sets_table.copy()
        if isinstance(present, str):
            present = [present]
        if isinstance(absent, str):
            absent = [absent]
        conds = np.ones(len(sets_table), dtype=int)
        if present is not None:
            for cat in present:
                conds = conds & (sets_table.index.get_level_values(cat) == 1)
        if absent is not None:
            for cat in absent:
                conds = conds & (sets_table.index.get_level_values(cat) == 0)
        if min_size is not None:
            conds = conds & (sets_table["size"] >= min_size)
        if max_size is not None:
            conds = conds & (sets_table["size"] <= max_size)
        if min_degree is not None:
            conds = conds & (sets_table["degree"] >= min_degree)
        if min_degree is not None:
            conds = conds & (sets_table["degree"] >= max_degree)
        return conds

    def highlight_subsets(self, present=None, absent=None,
                          min_size=None, max_size=None,
                          min_degree=None, max_degree=None,
                          facecolor=None, edgecolor=None,
                          edgewidth=None, hatch=None, edgestyle=None,
                          label=None,
                          ):
        marks = self._mark_subsets(present=present, absent=absent,
                                   min_size=min_size, max_size=max_size,
                                   min_degree=min_degree,
                                   max_degree=max_degree)
        styles = dict(facecolor=facecolor, edgecolor=edgecolor,
                      linestyle=edgestyle, linewidth=edgewidth,
                      hatch=hatch)
        styles = {k: v for k, v in styles.items() if v is not None}

        line_styles = dict()
        if facecolor is not None:
            line_styles.update(color=facecolor)

        for i, m in enumerate(marks):
            if m:
                style = self._subset_styles.get(i)
                if style is not None:
                    style.update(styles)
                    if label is not None:
                        if 'label' in style.keys():
                            style['label'] += f"; {label}"
                        else:
                            style['label'] = label
                    self._subset_line_styles[i].update(line_styles)
                else:
                    self._subset_styles[i] = styles
                    self._subset_styles[i]['label'] = label
                    self._subset_line_styles[i] = line_styles

    def _check_side(self, side, chart_name, allow):
        options = allow[self.orient]
        if side not in options:
            msg = f"{chart_name} cannot be placed at '{side}', " \
                  f"try {' ,'.join(options)}"
            raise ValueError(msg)

    def add_intersections(self, side, pad=.1):
        self._check_side(side, 'Intersections',
                         dict(h=["top", "bottom"], v=["left", "right"]))
        data = self.sets_table["size"]
        self._intersection_bar = Numbers(data, color=self.color)
        self.add_plot(side, self._intersection_bar, size=2, pad=pad)

    def add_sets_size(self, side, pad=.1):
        self._check_side(side, 'Sets size',
                         dict(h=["left", "right"], v=["top", "bottom"]))
        data = self.sets_size["size"]
        self._sets_size_bar = Numbers(data, color=self.color)
        self.add_plot(side, self._sets_size_bar, size=2, pad=pad)

    def add_sets_label(self, side, pad=.1):
        self._check_side(side, 'Sets label',
                         dict(h=["left", "right"], v=["top", "bottom"]))
        data = self.sets_table.index.names
        self.add_plot(side, Labels(data), pad=pad)

    def _render_matrix(self, ax):
        ax.set_axis_off()

        bg, bg_circles = [], []
        lines, circles = [], []
        last_ix1, last_ix2 = 0, 0
        matrix = self._matrix

        for ix1, chunk in enumerate(matrix):
            custom_style = self._subset_styles.get(ix1)
            custom_line_style = self._subset_line_styles.get(ix1)
            if custom_style is None:
                custom_style = {}
                custom_line_style = {}

            lines_coords = []
            for ix2, ele in enumerate(chunk):
                cx, cy = ix1, ix2
                if self.orient == "v":
                    cx, cy = cy, cx
                if ele:
                    lines_coords.append(ix2)
                    current_style = {'facecolor': self.color,
                                     'alpha': 1, **custom_style}
                    c = Circle((cx, cy), self.radius, **current_style)
                    circles.append(c)
                else:
                    if self.shading > 0:
                        # background circle
                        c = Circle((cx, cy), self.radius,
                                   facecolor=self.color,
                                   alpha=self.shading)
                        bg_circles.append(c)
                last_ix2 = ix2
            if (self.linewidth > 0) & (len(lines_coords) > 1):
                # draw line
                low, up = np.min(lines_coords), np.max(lines_coords)
                line_style = {'color': self.color, 'lw': self.linewidth,
                              **custom_line_style}
                xs, ys = (ix1, ix1), (low, up)
                if self.orient == "v":
                    xs, ys = ys, xs
                line = Line2D(xs, ys, **line_style)
                lines.append(line)
            last_ix1 = ix1
        if self.orient == "v":
            last_ix1, last_ix2 = last_ix2, last_ix1
        xlow, xup = 0 - 0.5, last_ix1 + 0.5
        ylow, yup = last_ix2 + 0.5, 0 - 0.5
        ax.set_xlim(xlow, xup)
        ax.set_ylim(ylow, yup)

        if self.orient == "h":
            bg_coords = np.arange(yup, ylow)
            for iy, coord in enumerate(bg_coords):
                if iy % 2 == 0:
                    bg_circles.append(Rectangle(xy=(xlow, coord),
                                                height=1,
                                                width=xup - xlow,
                                                facecolor=self.color,
                                                alpha=self.grid_background
                                                ))
        else:
            bg_coords = np.arange(xlow, xup)
            for ix, coord in enumerate(bg_coords):
                if ix % 2 == 0:
                    bg_circles.append(Rectangle(xy=(coord, yup),
                                                width=1,
                                                height=ylow - yup,
                                                facecolor=self.color,
                                                alpha=self.grid_background
                                                ))
        # add bg_circles
        bg_circles = PatchCollection(bg_circles, match_original=True)
        ax.add_collection(bg_circles)

        # add lines
        for line in lines:
            ax.add_artist(line)

        # add circles
        circles = PatchCollection(circles, match_original=True)
        ax.add_collection(circles)

    def render(self, figure=None, aspect=1):
        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure

        if not self.grid.is_freeze:
            self.grid.freeze(figure=self.figure, aspect=aspect)
        main_axes = self.get_main_ax()
        self._render_matrix(main_axes)
        self._render_plan()
        # apply highlight style to bar
        if self._interactions:
            for ix, rect in enumerate(self._intersection_bar.bars):
                bar_style = self._subset_styles.get(ix)
                if bar_style is not None:
                    rect.set(**bar_style)

        # TODO: legend entries
