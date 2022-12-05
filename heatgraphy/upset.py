# The API design of upsetplot is highly inspired from UpsetPlot
# https://github.com/jnothman/UpSetPlot

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import cycle
from typing import List, Set

import numpy as np
import pandas as pd
from legendkit import ListLegend
from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

from .base import Base
from .plotter import Numbers, Labels, StackBar


@dataclass
class UpSetAttr:
    name: str
    data: np.ndarray


class UpsetData:
    """Handle multiple sets

    Normally, the construction methods are used to create a UpsetData

    Parameters
    ----------
    data : bool matrix
        A one-hot encode matrix indicates if an item is in a set.
        Columns are sets and rows are items
    names : optional, array
        The name of sets
    items : optional, array
        The name of items
    sets_attrs : optional, pd.DataFrame
        The attributes of sets, the input index should be the
        same as names
    items_attrs : optional, pd.DataFrame
        The attributes of items, the input index should be the
        same as items

    Examples
    --------

    .. plot::
        :context: close-figs

        from heatgraphy.upset import UpsetData
        sets = [[1,2,3,4], [3,4,5,6]]
        data = UpsetData.from_sets(sets)


    """

    def __init__(self, data, names=None, items=None,
                 sets_attrs=None, items_attrs=None):
        assert len(names) == len(set(names)), "Duplicates in names"
        assert len(items) == len(set(items)), "Duplicates in items"
        self.names = list(names)  # columns
        self.items = list(items)  # row
        self._data = data  # one-hot encode matrix

        if sets_attrs is not None:
            sets_attrs = sets_attrs.loc[self.names]
        self._sets_attrs = sets_attrs

        if items_attrs is not None:
            items_attrs = items_attrs.loc[self.items]
        self._items_attrs = items_attrs

        self._sets_table = pd.DataFrame(columns=names, index=items,
                                        data=data)

    @classmethod
    def from_sets(cls, sets: List[Set], names=None,
                  sets_attrs: pd.DataFrame = None,
                  items_attrs: pd.DataFrame = None) -> UpsetData:
        if names is None:
            names = [f"Set {i + 1}" for i in range(len(sets))]
        items = set()
        new_sets = []
        sets_total = {}
        for name, s in zip(names, sets):
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
        container = cls(data, names=names, items=items,
                        sets_attrs=sets_attrs,
                        items_attrs=items_attrs)
        return container

    @classmethod
    def from_memberships(cls, sets_names, items_names=None,
                         sets_attrs: pd.DataFrame = None,
                         items_attrs: pd.DataFrame = None):
        """Describe the sets an item are in"""
        df = (pd.DataFrame([{name: True for name in names}
                            for names in sets_names])
              ).fillna(False).astype(int)
        container = cls(df.to_numpy(), names=df.columns,
                        items=items_names, sets_attrs=sets_attrs,
                        items_attrs=items_attrs)
        return container

    def has_item(self, item):
        """Return the sets name the item is in"""
        item_data = self._sets_table.loc[item]
        return item_data.loc[item_data == 1].index.tolist()

    def intersection(self, sets_name):
        """Return the items that appears in sets"""
        expr = "&".join([f"(`{s}`==1)" for s in sets_name])
        return self._sets_table.query(expr).index.tolist()

    def intersection_count(self):
        """The number of sets an item has occurred"""
        return self._sets_table.sum(axis=1)

    def sets_table(self):
        return self._sets_table

    def cardinality(self):
        return self._sets_table.groupby(self.names).size()

    def degree(self):
        return self._sets_table.groupby(self.names).sum(axis=1)

    def sets_size(self):
        return self._sets_table.sum()

    @property
    def sets_attrs(self):
        return self._sets_attrs

    @property
    def items_attrs(self):
        return self._items_attrs


class Upset(Base):
    """Upset Plot

    Parameters
    ----------
    data : :class:`UpsetData`
        Upset data
    orient : str
        The orientation of the Upset plot
    sets_order : array of str
        The order of sets
    sort_subset : {'size', 'degree'}
        How to sort the subset, 'size' will sort by intersection size,
        'degree' will sort by the number of intersected sets.
    ascending : bool, default: True
        The sorting order
    min_degree, max_degree : int
        Select a fraction of subset to render by degree
    min_size, max_size :


    """

    def __init__(self, data: UpsetData,
                 orient="h",
                 sets_order=None,
                 sort_subset="size",  # size, degree
                 ascending=False,
                 min_degree=None,
                 max_degree=None,
                 min_size=None,
                 max_size=None,
                 color=".1",
                 shading=.3,
                 radius=.25,
                 linewidth=1.5,
                 grid_background=0.1,
                 fontsize=None,
                 add_intersections=True,
                 add_sets_size=True,
                 add_labels=True,
                 width=None,
                 height=None,
                 ratio=1
                 ):

        sets_table = pd.DataFrame(data.cardinality(), columns=["size"])
        sets_table["degree"] = sets_table.index.to_frame().sum(axis=1)
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

        self.data = data
        self.orient = orient
        self.color = color
        self.shading = shading
        self.radius = radius
        self.linewidth = linewidth
        self.grid_background = grid_background
        self.fontsize = fontsize

        self.sets_table = sets_table
        self.sets_size = sets_size
        self._subset_styles = {}
        self._subset_line_styles = {}
        self._legend_entries = []
        self._add_intersections = add_intersections
        self._intersection_bar = None
        self._sets_size_bar = None

        h = len(self.sets_table)
        w = len(self.sets_table.index)

        if orient == "h":
            h, w = w, h
        super().__init__(w=width, h=height, main_aspect=h / w * ratio)
        if add_intersections:
            side = "top" if orient == "h" else "right"
            self.add_intersections(side)
        if add_labels:
            side = "right" if orient == "h" else "bottom"
            self.add_sets_label(side)
        if add_sets_size:
            side = "left" if orient == "h" else "top"
            self.add_sets_size(side)

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
                      hatch=hatch, label=label)
        styles = {k: v for k, v in styles.items() if v is not None}

        line_styles = dict()
        linecolor = facecolor if facecolor is not None else None
        linecolor = edgecolor if edgecolor is not None else linecolor
        line_styles.update(color=linecolor)

        self._legend_entries.append(styles)

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
        # TODO: add method to get specific axes
        self._check_side(side, 'Intersections',
                         dict(h=["top", "bottom"], v=["left", "right"]))
        data = self.sets_table["size"]
        self._intersection_bar = Numbers(data, color=self.color)
        size = min(self.height, self.width) * .4
        self.add_plot(side, self._intersection_bar, size=size, pad=pad)

    def add_sets_size(self, side, pad=.1):
        self._check_side(side, 'Sets size',
                         dict(h=["left", "right"], v=["top", "bottom"]))
        data = self.sets_size
        self._sets_size_bar = Numbers(data, color=self.color)
        size = min(self.height, self.width) * .4
        self.add_plot(side, self._sets_size_bar, size=size, pad=pad)

    def add_sets_label(self, side, pad=.1):
        self._check_side(side, 'Sets label',
                         dict(h=["left", "right"], v=["top", "bottom"]))
        data = self.sets_table.index.names
        self.add_plot(side, Labels(data), pad=pad)

    def add_sets_attrs(self, side, attr_names, plot=None):
        # TODO: Auto detect side, more options
        data = self.data.sets_attrs
        attr = data[attr_names]
        self.add_plot(side, plot(attr), pad=.1)

    def add_items_attrs(self, side, attr_names, plot=None, name=None, pad=0,
                        **kwargs):
        items_attrs = self.data.items_attrs
        sets_names = np.array(self.sets_table.index.names)

        data_collector = []

        for ix, row in self.sets_table.iterrows():
            s = sets_names[np.array(ix).astype(bool)]
            items = self.data.intersection(s)
            attr_data = items_attrs.loc[items][attr_names]
            data_collector.append(attr_data)

        construct = pd.DataFrame(data_collector).T

        if plot == StackBar:
            collect = [Counter(col) for _, col in construct.items()]
            construct = pd.DataFrame(collect).T
            construct = (construct.loc[~pd.isnull(construct.index)]
            ).fillna(0).astype(int).to_numpy()

        self.add_plot(side, plot(construct, **kwargs), name=name, pad=pad)

    def _render_matrix(self, ax):
        ax.set_axis_off()

        bg, bg_circles = [], []
        lines, circles = [], []
        matrix = self.sets_table.index.to_frame().to_numpy()
        X, Y = matrix.shape
        xticks = np.arange(X)
        yticks = np.arange(Y)
        xv, yv = np.meshgrid(xticks, yticks)

        # draw bg
        if self.shading > 0:
            if self.orient == "v":
                xv, yv = yv, xv
            ax.scatter(xv, yv, facecolor=self.color, alpha=self.shading,
                       edgecolor="none")

        for ix1, chunk in enumerate(matrix):
            custom_style = self._subset_styles.get(ix1)
            custom_line_style = self._subset_line_styles.get(ix1)
            if custom_style is None:
                custom_style = {}
                custom_line_style = {}

            cy = np.nonzero(chunk)[0]
            cx = np.repeat(ix1, len(cy))
            line_low, line_up = np.min(cy), np.max(cy)
            if (self.linewidth > 0) & (line_up - line_low > 1):
                line_style = {'color': self.color, 'lw': self.linewidth,
                              **custom_line_style}
                xs, ys = ix1, (line_low, line_up)
                liner = ax.vlines
                if self.orient == "v":
                    xs, ys = ys, xs
                    liner = ax.hlines
                liner(xs, *ys, **line_style)

            if self.orient == "v":
                cx, cy = cy, cx
            current_style = {'facecolor': self.color, 'zorder': 100,
                             'alpha': 1, **custom_style}
            ax.scatter(cx, cy, **current_style)

        xlow, xup = 0 - 0.5, np.max(xv) + 0.5
        ylow, yup = np.max(yv) + 0.5, 0 - 0.5
        ax.set_xlim(xlow, xup)
        ax.set_ylim(ylow, yup)

        if self.orient == "h":
            bg_coords = zip(cycle([xlow]), np.arange(yup, ylow))
            height = 1
            width = xup - xlow
        else:
            bg_coords = zip(np.arange(xlow, xup), cycle([yup]))
            width = 1
            height = ylow - yup
        for i, coord in enumerate(bg_coords):
            if i % 2 == 0:
                rect = Rectangle(xy=coord, height=height, width=width,
                                 facecolor=self.color,
                                 alpha=self.grid_background)
                bg_circles.append(rect)
        # add bg_circles
        bg_circles = PatchCollection(bg_circles, match_original=True)
        ax.add_collection(bg_circles)

        # add lines
        for line in lines:
            ax.add_artist(line)

        # add circles
        circles = PatchCollection(circles, match_original=True)
        ax.add_collection(circles)

    def _extra_legends(self):
        legend_items = [('rect', entry['label'], entry) \
                        for entry in self._legend_entries]
        highlight_legend = ListLegend(legend_items=legend_items)
        highlight_legend.figure = None
        return {'highlight_subsets': [highlight_legend]}

    def render(self, figure=None, aspect=1, scale=1.1):

        self._freeze_legend()

        if figure is None:
            self.figure = plt.figure()
        else:
            self.figure = figure

        if not self.grid.is_freeze:
            self.grid.freeze(figure=self.figure, aspect=aspect, scale=scale)
        main_axes = self.get_main_ax()
        self._render_matrix(main_axes)
        self._render_plan()
        # apply highlight style to bar
        if self._add_intersections:
            for ix, rect in enumerate(self._intersection_bar.bars):
                bar_style = self._subset_styles.get(ix)
                if bar_style is not None:
                    rect.set(**bar_style)
        self._render_legend()
