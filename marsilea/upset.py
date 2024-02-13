# The API design of upsetplot is highly inspired from UpsetPlot
# https://github.com/jnothman/UpSetPlot

from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd
from itertools import cycle
from legendkit import ListLegend
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle, Patch
from typing import List, Set, Mapping

from .base import WhiteBoard
from .plotter import Numbers, Labels, StackBar, Bar, Box, \
    Boxen, Violin, Point, Strip, Swarm
from .utils import get_canvas_size_by_data


def _get_sets_table(binary_table):
    cardinality = binary_table.groupby(list(binary_table.columns),
                                       observed=True).size()
    sets_table = pd.DataFrame(cardinality, columns=["cardinality"])
    sets_table["degree"] = sets_table.index.to_frame().sum(axis=1)
    return sets_table


class UpsetData:
    """Handle multiple sets

    Normally, the construction methods are used to create a UpsetData

    Terminology that you might not be familiar with:
        - set: a collection of unique items
        - subset: intersection of sets
        - degree: The number of sets that intersect with each other
        - cardinality: The number of items in the subset

    Parameters
    ----------
    data : bool matrix
        A one-hot encode matrix indicates if an item is in a set.
        Columns are sets and rows are items
    sets_names : optional, array
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

        from marsilea.upset import UpsetData
        sets = [[1,2,3,4], [3,4,5,6]]
        data = UpsetData.from_sets(sets)


    """

    def __repr__(self):
        nitems, nsets = self._binary_table.shape
        return f"UpsetData: {nsets} sets, {nitems} items"

    def __init__(self, data, sets_names=None, items=None,
                 sets_attrs=None, items_attrs=None):
        if isinstance(data, pd.DataFrame):
            if sets_names is None:
                sets_names = data.columns.tolist()
            if items is None:
                items = data.index.tolist()
            data = data.to_numpy()
        if sets_names is None:
            raise ValueError("The name of sets must be provided")
        if items is None:
            raise ValueError("The name of items must be provided")

        assert len(sets_names) == len(set(sets_names)), \
            "Duplicates in set names"
        assert len(items) == len(set(items)), "Duplicates in items"

        if sets_attrs is not None:
            sets_attrs = sets_attrs.loc[list(sets_names)]
        self._sets_attrs = sets_attrs

        if items_attrs is not None:
            items_attrs = items_attrs.loc[list(items)]
        self._items_attrs = items_attrs

        self._binary_table = pd.DataFrame(columns=sets_names, index=items,
                                          data=data)
        self._sets_table = _get_sets_table(self._binary_table)

    def filter(self,
               min_degree=None,
               max_degree=None,
               min_cardinality=None,
               max_cardinality=None,
               ):
        """Filter by degree or cardinality

        Parameters
        ----------
        min_degree : int
            The minimum degree
        max_degree : int
            The maximum degree
        min_cardinality : int
            The minimum cardinality
        max_cardinality : int
            The maximum cardinality

        """
        sets_table = self._sets_table
        if min_degree is not None:
            sets_table = sets_table[sets_table["degree"] >= min_degree]
        if max_degree is not None:
            sets_table = sets_table[sets_table["degree"] <= max_degree]
        if min_cardinality is not None:
            sets_table = sets_table[
                sets_table["cardinality"] >= min_cardinality]
        if max_cardinality is not None:
            sets_table = sets_table[
                sets_table["cardinality"] <= max_cardinality]
        self._sets_table = sets_table
        return self

    def sort_subsets(self, by="degree", ascending=False):
        """Sort the subsets by degree or cardinality

        Parameters
        ----------
        by : str
            Sort by either `degree` or `cardinality`
        ascending : bool
            Sort in ascending order if True


        """
        if by not in ["degree", "cardinality"]:
            raise ValueError("Sort by either `degree` or `cardinality`")
        if by == "cardinality":
            self._sets_table.sort_values(by=by, ascending=not ascending,
                                         inplace=True, kind="stable")
        else:
            matrix = self._sets_table.index.to_frame().reset_index(drop=True)
            _, num = matrix.shape

            matrix['SUM'] = matrix.sum(axis=1)

            reorder_ix = []
            for n, df in matrix.groupby('SUM'):
                del df['SUM']
                rows = df.to_numpy()
                c_rows = []
                for row in rows:
                    str_digit = row[::-1].astype(str)
                    str_row = "".join(str_digit)
                    c_rows.append(int(str_row))
                ix = np.argsort(c_rows)
                rix = df.index[ix].to_list()
                if not ascending:
                    rix = rix[::-1]
                reorder_ix += rix

            if ascending:
                reorder_ix = reorder_ix[::-1]
            self._sets_table = self._sets_table.iloc[reorder_ix, :]

        return self

    def sort_sets(self, ascending=False, order=None):
        """Control the order of sets

        Parameters
        ----------
        ascending : bool
            Sort in ascending order if True
        order : list
            Explicitly specify the order of sets

        """
        if order is not None:
            sets_names = order
        else:
            sets_sizes = self.sets_size().sort_values(ascending=ascending,
                                                      kind="stable")
            sets_names = sets_sizes.index.to_list()
        self._binary_table = self._binary_table.loc[:, sets_names]
        self._sets_table = self._sets_table.reorder_levels(order=sets_names)
        if self._sets_attrs is not None:
            self._sets_attrs = self._sets_attrs.loc[sets_names]
        return self

    def mark(self,
             present=None,
             absent=None,
             min_cardinality=None,
             max_cardinality=None,
             min_degree=None,
             max_degree=None
             ):
        sets_table = self._sets_table
        marks = np.ones(len(sets_table), dtype=int)

        if isinstance(present, str):
            present = [present]
        if isinstance(absent, str):
            absent = [absent]
        if present is not None:
            for cat in present:
                marks = marks & (sets_table.index.get_level_values(cat) == 1)
        if absent is not None:
            for cat in absent:
                marks = marks & (sets_table.index.get_level_values(cat) == 0)

        if min_cardinality is not None:
            marks = marks & (sets_table["cardinality"] >= min_cardinality)
        if max_cardinality is not None:
            marks = marks & (sets_table["cardinality"] <= max_cardinality)
        if min_degree is not None:
            marks = marks & (sets_table["degree"] >= min_degree)
        if min_degree is not None:
            marks = marks & (sets_table["degree"] >= max_degree)
        return marks

    def reset(self):
        self._sets_table = _get_sets_table(self._binary_table)
        return self

    @classmethod
    def from_sets(cls, sets: List[Set], sets_names=None,
                  sets_attrs: pd.DataFrame = None,
                  items_attrs: pd.DataFrame = None) -> UpsetData:
        """Create UpsetData from a series of sets

        Parameters
        ----------
        sets : array of sets, dict
            The sets data
        sets_names : optional
            The name of sets, if name is not provided, it will
            be automatically named as "Set 1, Set 2, ..."
        sets_attrs : optional, pd.DataFrame
            The attributes of sets, the input index should be the
            same as sets_names
        items_attrs : optional, pd.DataFrame
            The attributes of items, the input index should be the
            same as items

        
        """
        items = set()
        new_sets = []
        new_names = []
        sets_total = {}

        if isinstance(sets, Mapping):
            it = sets.items()
        else:
            if sets_names is None:
                sets_names = [f"Set {i + 1}" for i in range(len(sets))]
            it = zip(sets_names, sets)

        for name, s in it:
            s = set(s)
            new_sets.append(s)
            new_names.append(name)
            items.update(s)
            sets_total[name] = len(s)

        items = np.array(list(items))
        data = []
        for name, s in zip(new_names, new_sets):
            d = [i in s for i in items]
            data.append(d)
        data = np.array(data, dtype=int).T
        container = cls(data, sets_names=new_names, items=items,
                        sets_attrs=sets_attrs,
                        items_attrs=items_attrs)
        return container

    @classmethod
    def from_memberships(cls, items, items_names=None,
                         sets_attrs: pd.DataFrame = None,
                         items_attrs: pd.DataFrame = None):
        """Describe the sets an item are in

        Parameters
        ----------
        items : array of array of sets_names, dict
            The data of items
        items_names : optional
            The name of items, if name is not provided, it will
            be automatically named as "Item 1, Item 2, ..."
        sets_attrs : optional, pd.DataFrame
            The attributes of sets, the input index should be the
            same as sets_names
        items_attrs : optional, pd.DataFrame
            The attributes of items, the input index should be the
            same as items

        """

        sets = []
        new_items_names = []

        if isinstance(items, Mapping):
            for name, ss in items.items():
                new_items_names.append(name)
                sets.append({s: True for s in ss})
        else:
            for i, ss in enumerate(items):
                new_items_names.append(f"Item {i + 1}")
                sets.append({s: True for s in ss})

        if items_names is not None:
            new_items_names = items_names

        df = pd.DataFrame(sets).fillna(False).astype(int)
        container = cls(df.to_numpy(), sets_names=df.columns,
                        items=new_items_names, sets_attrs=sets_attrs,
                        items_attrs=items_attrs)
        return container

    def has_item(self, item):
        """Return a list of sets' name the item is in"""
        item_data = self._binary_table.loc[item]
        return item_data.loc[item_data == 1].index.tolist()

    def intersection(self, sets_name):
        """Return the items that are shared in different sets"""
        expr = "&".join([f"(`{s}`==1)" for s in sets_name])
        return self._binary_table.query(expr).index.tolist()

    def intersection_count(self):
        """The item has occurred in how many sets"""
        return self._binary_table.sum(axis=1)

    def binary_table(self):
        return self._binary_table

    def sets_table(self) -> pd.DataFrame:
        return self._sets_table

    def cardinality(self):
        """The number of items in intersections"""
        return self._sets_table['cardinality']

    def degree(self):
        """Intersection between how many sets"""
        return self._sets_table['degree']

    def sets_size(self):
        return self._binary_table.sum()[self.sets_names]

    @property
    def sets_names(self):
        return self._sets_table.index.names

    @property
    def items(self):
        return self._binary_table.index

    @property
    def sets_attrs(self):
        return self._sets_attrs

    @property
    def items_attrs(self):
        return self._items_attrs

    def get_items_attr(self, attr):
        """Return the attribute of items in the order of plotting

        Parameters
        ----------
        attr : key in items_attrs
            Retrieve the attribute of items

        Returns
        -------
            array of attribute

        """
        items_attrs = self._items_attrs
        sets_names = np.asarray(self.sets_names)

        data_collector = []

        for ix, row in self.sets_table().iterrows():
            s = sets_names[np.array(ix).astype(bool)]
            items = self.intersection(s)
            attr_data = items_attrs.loc[items][attr]
            data_collector.append(attr_data)
        return data_collector


class Upset(WhiteBoard):
    """Upset Plot

    Parameters
    ----------
    data : :class:`UpsetData`
        Upset data
    orient : str
        The orientation of the Upset plot
    sets_order : array of str
        The order of sets
    sets_color : array of color
        The color for each set, this will also change the bar color
        in set size
    sort_sets : {'ascending', 'descending'}
        The sorting order of sets
    sort_subsets : {'cardinality', 'degree'}
        How to sort the subset, 'size' will sort by intersection size,
        'degree' will sort by the number of intersected sets.
    min_degree, max_degree : int
        Select a fraction of subset to render by degree
    min_cardinality, max_cardinality : int
        Select a fraction of subset to render by cardinality
    color : color
        The main color to use
    shading : float
        The value to dilute the main color
    radius : float
        The size of the dot
    linewidth : float
        The width of lines that connect the dots
    grid_background : float
        The value to dilute the main color for background
    fontsize : int
        Set the fontsize for the plot
    add_intersections : bool, str, default: True
        Whether or which side to add the intersection size.
    add_sets_size : bool, str, default: True
        Whether or which side to add the sets size.
    add_labels : bool, str, default: True
        Whether or which side to add the label.
    width : float
    height : float
    ratio : float

    Examples
    --------

    .. plot::
        :context: close-figs

        >>> from marsilea.upset import UpsetData, Upset
        >>> data = UpsetData.from_sets([[1, 2, 3, 4],
        >>>                             [3, 4, 5, 6],
        >>>                             [1, 6, 10, 11]])
        >>> Upset(data).render()
    

    """

    def __init__(self, data: UpsetData,
                 orient="h",
                 sort_sets=None,  # ascending, descending
                 sets_order=None,
                 sets_color=None,
                 sort_subsets="cardinality",  # cardinality, degree
                 min_degree=None,
                 max_degree=None,
                 min_cardinality=None,
                 max_cardinality=None,
                 color=".1",
                 shading=.3,
                 radius=50,
                 linewidth=1.5,
                 grid_background=0.1,
                 fontsize=None,
                 add_intersections=True,
                 add_sets_size=True,
                 add_labels=True,
                 width=None,
                 height=None,
                 ):
        # The modification happens inplace
        upset_data = data
        upset_data.filter(min_degree=min_degree,
                          max_degree=max_degree,
                          min_cardinality=min_cardinality,
                          max_cardinality=max_cardinality)

        ascending = sort_subsets.startswith("-")
        if ascending:
            sort_subsets = sort_subsets[1:]
        upset_data.sort_subsets(by=sort_subsets, ascending=ascending)

        ascending = sort_sets == "ascending"
        upset_data.sort_sets(order=sets_order, ascending=ascending)

        sets_size = upset_data.sets_size()
        sets_table = upset_data.sets_table()

        self.sets_size = sets_size
        self.sets_table = sets_table

        self.data = upset_data
        self.color = color
        self.shading = shading
        self.linewidth = linewidth
        self.grid_background = grid_background
        self.fontsize = fontsize
        self.height = height
        self.width = width
        self.radius = radius
        if sets_color is None:
            sets_color = [self.color for _ in range(len(sets_size))]
        self.sets_color = np.asarray(sets_color)

        self._subset_styles = {}
        self._subset_line_styles = {}
        self._legend_entries = []
        self._add_intersections = add_intersections
        self._intersection_bar = None
        self._sets_size_bar = None

        if orient not in ["h", "v"]:
            raise ValueError("orient must be 'h' or 'v'")

        main_shape = sets_table.index.to_frame().shape
        if orient == "h":
            main_shape = main_shape[::-1]
        self.orient = orient

        width, height = get_canvas_size_by_data(
            main_shape, scale=.3, width=width, height=height, aspect=1)

        super().__init__(width=width, height=height)
        if add_intersections:
            if isinstance(add_intersections, str):
                side = add_intersections
            else:
                side = "top" if orient == "h" else "right"
            self.add_intersections(side)
        if add_labels:
            if isinstance(add_labels, str):
                side = add_labels
            else:
                side = "right" if orient == "h" else "bottom"
            self.add_sets_label(side)
        if add_sets_size:
            if isinstance(add_sets_size, str):
                side = add_sets_size
            else:
                side = "left" if orient == "h" else "top"
            self.add_sets_size(side, color=self.sets_color)

    def highlight_subsets(self, present=None, absent=None,
                          min_cardinality=None, max_cardinality=None,
                          min_degree=None, max_degree=None,
                          facecolor=None, edgecolor=None,
                          edgewidth=None, hatch=None, edgestyle=None,
                          label=None,
                          ):
        """Highlight a subset of the data.

        Notice that the color of hatch is determined by the edgecolor.

        Parameters
        ----------
        present :
            The sets that present in the subset
        absent :
            The sets that absent in the subset
        min_cardinality :
            The minimum cardinality of the subset
        max_cardinality :
             The maximum cardinality of the subset
        min_degree :
            The minimum degree of the subset
        max_degree :
            The maximum degree of the subset
        facecolor :
            The facecolor to decorate the subset
        edgecolor :
            The color of the edge line
        edgewidth :
            The edgewidth of the edge line
        hatch :
            The fill pattern
        edgestyle :
            The style of edge line
        label :
            The label for the highlighting

        """
        marks = self.data.mark(present=present, absent=absent,
                               min_cardinality=min_cardinality,
                               max_cardinality=max_cardinality,
                               min_degree=min_degree,
                               max_degree=max_degree)

        def _label(name, value):
            if value is not None:
                return f"{name}={value}"
            else:
                return ""

        if label is None:
            present = _label("present", present)
            absent = _label("absent", absent)
            min_cardinality = _label("min_cardinality", min_cardinality)
            max_cardinality = _label("max_cardinality", max_cardinality)
            min_degree = _label("min_degree", min_degree)
            max_degree = _label("max_degree", max_degree)

            label = ", ".join([s for s in [present, absent, min_cardinality,
                                           max_cardinality, min_degree,
                                           max_degree] if s])

        styles = dict(facecolor=facecolor, edgecolor=edgecolor,
                      linestyle=edgestyle, linewidth=edgewidth,
                      hatch=hatch, label=label)
        styles = {k: v for k, v in styles.items() if v is not None}

        line_styles = dict()
        linecolor = facecolor if facecolor is not None else None
        linecolor = edgecolor if edgecolor is not None else linecolor
        line_styles.update(color=linecolor)

        for i, m in enumerate(marks):
            if m:
                current_styles = styles.copy()
                sub_set_style = self._subset_styles.get(i)
                if sub_set_style is not None:
                    sub_set_style.update(current_styles)
                    self._subset_line_styles[i].update(line_styles)
                else:
                    self._subset_styles[i] = current_styles
                    self._subset_line_styles[i] = {**line_styles}

        if 'facecolor' not in styles.keys():
            styles['facecolor'] = 'none'
        if 'edgecolor' not in styles.keys():
            styles['edgecolor'] = 'none'
        self._legend_entries.append(styles)

    def _check_side(self, side, chart_name, allow):
        options = allow[self.orient]
        if side not in options:
            msg = f"{chart_name} cannot be placed at '{side}', " \
                  f"try {' ,'.join(options)}"
            raise ValueError(msg)

    def add_intersections(self, side, pad=.1, size=1.):
        self._check_side(side, 'Intersections',
                         dict(h=["top", "bottom"], v=["left", "right"]))
        data = self.data.cardinality()
        self._intersection_bar = Numbers(data, color=self.color)
        self.add_plot(side, self._intersection_bar, size=size, pad=pad)

    def add_sets_size(self, side, pad=.1, size=1., **props):
        self._check_side(side, 'Sets size',
                         dict(h=["left", "right"], v=["top", "bottom"]))
        data = self.sets_size
        options = dict(color=self.color)
        options.update(props)
        self._sets_size_bar = Numbers(data, **options)
        self.add_plot(side, self._sets_size_bar, size=size, pad=pad)

    def add_sets_label(self, side, pad=.1, size=None, **props):
        self._check_side(side, 'Sets label',
                         dict(h=["left", "right"], v=["top", "bottom"]))
        data = self.data.sets_names
        self.add_plot(side, Labels(data, **props), pad=pad, size=size)

    def get_intersection_ax(self):
        return self.get_ax('Intersections')

    def get_sets_size_ax(self):
        return self.get_ax('Sets size')

    def get_sets_label_ax(self):
        return self.get_ax('Sets label')

    def get_data(self):
        return self.data

    _attr_plotter = {
        'bar': Bar,
        'box': Box,
        'boxen': Boxen,
        'violin': Violin,
        'point': Point,
        'strip': Strip,
        'swarm': Swarm,
        'stack_bar': StackBar,
        'number': Numbers,
    }

    @classmethod
    def update_attr_plotter(cls, attr_plotter):
        """Update the global upset plot for attr plotter"""
        cls._attr_plotter.update(attr_plotter)

    def add_sets_attr(self, side, attr_name, plot,
                      name=None, pad=.1, size=None, plot_kws=None):
        """Add a plot for the sets attribute

        Parameters
        ----------
        side : str
            The side to add the plot, can be 'left', 'right', 'top', 'bottom'
        attr_name : str
            The name of the attribute
        plot : str
            The type of plot, can be 'bar', 'box', 'boxen', 'violin', 'point',
            'strip', 'swarm', 'stack_bar', 'number'
        name : str, optional
            The name of the plot
        pad : float, optional
            The padding between the plot and the axis
        size : float, optional
            The size of the plot
        plot_kws : dict, optional
            The keyword arguments for the plot

        """
        data = self.data.sets_attrs
        attr = data[attr_name]
        plot = self._attr_plotter[plot]
        kws = {'label': attr_name}
        if plot_kws is not None:
            kws.update(plot_kws)
        self.add_plot(side, plot(attr, **plot_kws),
                      name=name, pad=pad, size=size)

    def add_items_attr(self, side, attr_name, plot,
                       name=None, pad=.1, size=None, plot_kws=None):
        """Add a plot for the items attribute

        Parameters
        ----------
        side : str
            The side to add the plot, can be 'left', 'right', 'top', 'bottom'
        attr_name : str
            The name of the attribute
        plot : str
            The type of plot, can be 'bar', 'box', 'boxen', 'violin', 'point',
            'strip', 'swarm', 'stack_bar', 'number'
        name : str, optional
            The name of the plot
        pad : float, optional
            The padding between the plot and the axis
        size : float, optional
            The size of the plot
        plot_kws : dict, optional
            The keyword arguments for the plot

        """

        data_collector = self.data.get_items_attr(attr_name)

        construct = pd.DataFrame(data_collector).T

        if plot == StackBar:
            collect = [Counter(col) for col in data_collector]
            construct = pd.DataFrame(collect).T
            construct = ((construct.loc[~pd.isnull(construct.index)])
                         .fillna(0)
                         .astype(int))

        plot = self._attr_plotter[plot]
        kws = {'label': attr_name}
        if plot_kws is not None:
            kws.update(plot_kws)
        self.add_plot(side, plot(construct, **kws),
                      name=name, pad=pad, size=size)

    def _render_matrix(self, ax):
        ax.set_axis_off()

        bg_circles = []
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
            ax.scatter(xv, yv, s=self.radius, facecolor=self.color,
                       alpha=self.shading, edgecolor="none")

        for ix1, chunk in enumerate(matrix):
            custom_style = self._subset_styles.get(ix1)
            custom_line_style = self._subset_line_styles.get(ix1)
            if custom_style is None:
                custom_style = {}
                custom_line_style = {}

            cy = np.nonzero(chunk)[0]
            cx = np.repeat(ix1, len(cy))
            if len(cy) > 0:
                line_low, line_up = np.min(cy), np.max(cy)
                if (self.linewidth > 0) & (line_up - line_low > 0):
                    line_style = {'color': self.color, 'lw': self.linewidth,
                                  **custom_line_style}
                    xs, ys = ix1, (line_low, line_up)
                    liner = ax.vlines if self.orient == "h" else ax.hlines
                    liner(xs, *ys, **line_style)
                scatter_colors = self.sets_color[cy]
                if self.orient == "v":
                    cx, cy = cy, cx
                current_style = {'facecolor': scatter_colors, 'zorder': 100,
                                 'alpha': 1, **custom_style}
                ax.scatter(cx, cy, s=self.radius, **current_style)

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
        handles = [Patch(**entry) for entry in self._legend_entries]
        highlight_legend = ListLegend(handles=handles, handlelength=2)
        highlight_legend.figure = None
        return {'highlight_subsets': [highlight_legend]}

    def render(self, figure=None, scale=1):
        super().render(figure=figure, scale=scale)
        main_ax = self.get_main_ax()
        self._render_matrix(main_ax)
        # apply highlight style to bar
        if self._add_intersections:
            for ix, rect in enumerate(self._intersection_bar.bars):
                bar_style = self._subset_styles.get(ix)
                if bar_style is not None:
                    rect.set(**bar_style)
