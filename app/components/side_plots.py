from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from heatgraphy.base import ClusterBoard
from heatgraphy.plotter import (Bar, Box, Boxen, Colors, Count, Strip, Violin,
                                Point, Swarm, ColorMesh, AnnoLabels, Labels,
                                Title)
from heatgraphy.plotter import RenderPlan
from .data_input import FileUpload
from .state import init_state

IMG_ROOT = "https://raw.githubusercontent.com/" \
           "Heatgraphy/heatgraphy/main/app/img/"


@dataclass
class RenderAction:
    key: int
    side: str
    plotter: RenderPlan
    data: Any
    size: float = None
    pad: float = None
    kwargs: dict = field(default_factory=dict)

    def __hash__(self):
        return hash((self.side, self.key))

    def __eq__(self, other):
        cmp_side = self.side == other.side
        cmp_key = self.key == other.key
        return cmp_key & cmp_side

    def apply(self, h: ClusterBoard):
        p = self.plotter(self.data, **self.kwargs)
        h.add_plot(self.side, p, size=self.size, pad=self.pad)


@dataclass
class DendrogramAction(RenderAction):

    def apply(self, h):
        h.add_dendrogram(self.side,
                         **self.kwargs, size=self.size, pad=self.pad, )


class PlotAdder:
    init_size = 1.0
    init_pad = .05
    side: str
    size: float
    pad: float
    no_data: bool = False
    is_numeric: bool = True

    user_input: Any
    plotter: RenderPlan = None

    name: str = ""
    input_help: str = None
    plot_explain: str = None
    example_image: str = None

    def __repr__(self):
        return f"Draw at {self.side} with size {self.size} and {self.pad}"

    def __init__(self, key, side, datasets, main_data):
        self.key = key
        self.side = side
        self.plot_key = f"Add side plotter-{key}-{side}"
        self.data = None
        self.pass_check = False
        self.datasets = datasets
        self.main_data = main_data

        if self.plot_explain is not None:
            st.markdown(self.plot_explain)

        if self.example_image is not None:
            st.image(f"{IMG_ROOT}/{self.example_image}", width=150)

        if not self.no_data:
            self.input_panel()
        self.base_elements()

        # with st.expander("More Options"):
        self.extra_options()

        # if add:
        #     # rerender figure
        #     # TODO: Check the data input and tips prompt
        #     if not self.no_data:
        #         self.data = self.get_data()
        #         main_data = st.session_state["main_data"]
        #         if self.side in ["left", "right"]:
        #             match_num = main_data.shape[0]
        #         else:
        #             match_num = main_data.shape[1]
        #         if self.data.ndim == 1:
        #             if len(self.data) > match_num:
        #                 st.error("Your input data is more than required.")
        #             if len(self.data) < match_num:
        #                 st.error("Your input data is less than required.")
        #     self.write_action()

    def form(self):
        return st.form(self.plot_key)

    def base_elements(self):
        st.markdown("**Plot Options**")
        c1, c2, _ = st.columns([1, 1, 1])
        self.size = c1.number_input("Size", min_value=0.1,
                                    key=f"{self.plot_key}_size",
                                    value=self.init_size,
                                    help="Adjust the size of this plot")
        self.pad = c2.number_input("Pad", min_value=0.,
                                   key=f"{self.plot_key}_pad",
                                   value=self.init_pad,
                                   help="Adjust the space between this plot"
                                        " and the adjacent plot.")

    def input_panel(self):
        used_dataset = st.selectbox("Select Dataset",
                                    key=f"{self.plot_key}_datasets",
                                    options=[""] + self.datasets)
        if used_dataset != "":
            data = st.session_state['datasets'][used_dataset]
            main_shape = self.main_data.shape
            match_to = main_shape[0] if self.side in ["left", "right"] else \
                main_shape[1]
            axis = "row" if self.side in ["left", "right"] else "column"
            # TODO: Check this logic
            if data.shape[1] == 1:
                if data.size != match_to:
                    st.error(f"Selected dataset with size ({data.size}) "
                             f"must match to the number of {axis} of "
                             f"cluster data ({match_to})")
            else:
                if data.shape[1] != match_to:
                    st.error(f"The column of selected dataset {data.shape[1]} "
                             f"does not match to the number of {axis} of "
                             f"cluster data ({match_to})")

    def extra_options(self):
        pass

    def get_options(self):
        return {}

    def write_action(self):
        if self.data is not None:
            action = RenderAction(key=self.key, side=self.side,
                                  data=self.data, size=self.size,
                                  pad=self.pad, plotter=self.plotter,
                                  kwargs=self.get_options())
            return action


class LabelAdder(PlotAdder):
    name = "Labels"
    plotter = Labels


class ColorsAdder(PlotAdder):
    name = "Color Strip"
    plotter = Colors
    example_image = "colors.png"


class TitleAdder(PlotAdder):
    name = "Title"
    plotter = Title
    no_data = True

    color: str
    fontsize = 10
    fontweight = "regular"
    fontstyle = "normal"

    plot_explain = "Add a title component to your plot"

    def input_panel(self):
        self.data = st.text_input("Title")

    def extra_options(self):
        self.color = st.color_picker("Title color")
        self.fontsize = st.number_input("Title font size", value=10,
                                        min_value=5, max_value=20)
        fontstyle = st.selectbox("Title font style",
                                 options=["regular", "Bold", "Italic",
                                          "Bold + Italic"],
                                 help="Style is not available for some font"
                                 )
        if fontstyle != "regular":
            if fontstyle != "Italic":
                self.fontweight = "bold"
            if fontstyle != "Bold":
                self.fontstyle = "italic"

    def get_options(self):
        return dict(color=self.color,
                    fontdict=dict(fontweight=self.fontweight,
                                  fontstyle=self.fontstyle,
                                  fontsize=self.fontsize, )
                    )


class DendrogramAdder(PlotAdder):
    name = "Hierarchical clustering dendrogram"
    init_size = .5
    no_data = True

    method: str
    metric: str
    add_divider: bool
    add_base: bool
    add_meta: bool
    meta_color: Any
    colors: Any
    linewidth: float

    methods = ["single", "complete", "average", "weighted",
               "centroid", "median", "ward"]
    metrics = ["euclidean", "minkowski", "cityblock",
               "sqeuclidean", "cosine", "correlation",
               "jaccard", "jensenshannon", "chebyshev",
               "canberra", "braycurtis", "mahalanobis"]

    plot_explain = "Perform hierarchy clustering and draw the dendrogram " \
                   "that represents the clustering result."
    example_image = "dendrogram.svg"

    def input_panel(self):
        pass

    def extra_options(self):
        self.method = st.selectbox("Method", options=self.methods,
                                   key=f"{self.plot_key}_dendrogram_method", )
        self.metric = st.selectbox("Metric", options=self.metrics,
                                   key=f"{self.plot_key}_dendrogram_metric", )
        self.add_divider = st.checkbox("Add divide line",
                                       key=f"{self.plot_key}_add_divider", )
        self.add_base = st.checkbox("Add base dendrogram", value=True,
                                    key=f"{self.plot_key}_add_base", )
        self.add_meta = st.checkbox("Add meta dendrogram", value=True,
                                    key=f"{self.plot_key}_add_meta", )
        self.meta_color = st.color_picker("Color for meta dendrogram",
                                          key=f"{self.plot_key}_meta_color", )
        self.colors = st.color_picker("Dendrogram base color",
                                      key=f"{self.plot_key}_dendrogram_colors")
        self.linewidth = st.number_input("Line Width", min_value=0., value=.5,
                                         key=f"{self.plot_key}_lw", )

    def get_options(self):
        if self.method == "ward":
            self.metric = "euclidean"
        return dict(method=self.method,
                    metric=self.metric,
                    add_divider=self.add_divider,
                    add_base=self.add_base,
                    add_meta=self.add_meta,
                    meta_color=self.meta_color,
                    colors=self.colors,
                    linewidth=self.linewidth
                    )

    def write_action(self):
        action = DendrogramAction(key=self.key, side=self.side,
                                  data=None, size=self.size,
                                  pad=self.pad, plotter=self.plotter,
                                  kwargs=self.get_options())
        st.session_state[f"render_plan"][self.side][self.plot_key] = action


STATS_INPUT_HELP = "Table data: Each column corresponds to the row or column " \
                   "of the heatmap, depends on your side."


class BarAdder(PlotAdder):
    name = "Bar"
    plotter = Bar
    color: str
    errcolor: str
    errwidth: float
    capsize: float
    bar_width: float
    show_value: bool

    input_help = STATS_INPUT_HELP
    plot_explain = "Bar plot use rectangles to show data, " \
                   "For multiple observations, estimates and errors " \
                   "will be shown as error bar."
    example_image = "bar.png"

    def extra_options(self):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            self.color = st.color_picker("Color", value="#00b796")
        with c2:
            self.errcolor = st.color_picker("Error Bar Color", value="#555555")
        with c3:
            self.errwidth = st.number_input("Error Bar Width", value=1.,
                                            min_value=0., max_value=5.)
        with c4:
            self.capsize = st.number_input("Error Cap Size", value=.15,
                                           min_value=.1, max_value=1.)
        with c5:
            self.bar_width = st.number_input("Bar Width", value=.8,
                                             min_value=.1, max_value=1.)

    def get_options(self):
        return dict(color=self.color, errcolor=self.errcolor,
                    errwidth=self.errwidth, capsize=self.capsize,
                    width=self.bar_width
                    )


class BoxAdder(PlotAdder):
    name = "Box"
    plotter = Box
    color: str
    linewidth: float
    box_width: float

    input_help = STATS_INPUT_HELP
    plot_explain = "Box plot shows the distribution of your data"
    example_image = "box.png"

    def extra_options(self):
        c1, c2, c3 = st.columns(3)
        with c1:
            self.color = st.color_picker("Color", value="#00b796")
        with c2:
            self.linewidth = st.number_input("Line Width", value=1.,
                                             min_value=0., max_value=5.)
        with c3:
            self.box_width = st.number_input("Box Width", value=.8,
                                             min_value=.1, max_value=1.)

    def get_options(self):
        return dict(color=self.color,
                    linewidth=self.linewidth,
                    width=self.box_width
                    )


class BoxenAdder(PlotAdder):
    name = "Boxen"
    plotter = Boxen
    color: str
    linewidth: float
    box_width: float
    flier_size: float

    input_help = STATS_INPUT_HELP
    plot_explain = "An enhanced variant of box plot"
    example_image = "boxen.png"

    def extra_options(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            self.color = st.color_picker("Color", value="#00b796")
        with c2:
            self.linewidth = st.number_input("Line Width", value=1.,
                                             min_value=0., max_value=5.)
        with c3:
            self.box_width = st.number_input("Box Width", value=.8,
                                             min_value=.1, max_value=1.)
        with c4:
            self.flier_size = st.number_input("Flier Size", value=20,
                                              min_value=1)

    def get_options(self):
        return dict(color=self.color,
                    linewidth=self.linewidth,
                    width=self.box_width,
                    flier_kws=dict(s=self.flier_size)
                    )


class PointAdder(PlotAdder):
    name = "Point"
    plotter = Point
    color: str
    linestyle: str
    errwidth: float
    capsize: float

    ls = {
        "No Line": "",
        "Straight": "-",
        "Dashed": "--"
    }

    input_help = STATS_INPUT_HELP
    plot_explain = "Similar to box plot, but use point."
    example_image = "point.png"

    def extra_options(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            self.color = st.color_picker("Color", value="#00b796")
        with c2:
            linestyle = st.selectbox(
                "Line", options=["No Line", "Straight", "Dashed"])
            self.linestyle = self.ls[linestyle]
        with c3:
            self.errwidth = st.number_input("Error Bar Width", value=1.,
                                            min_value=0., max_value=5.)
        with c4:
            self.capsize = st.number_input("Error Cap Size", value=.3,
                                           min_value=.1, max_value=1.)

    def get_options(self):
        return dict(color=self.color,
                    linestyles=self.linestyle,
                    errwidth=self.errwidth,
                    capsize=self.capsize
                    )


class ViolinAdder(PlotAdder):
    name = "Violin"
    plotter = Violin
    scale: str | None
    color: str
    inner: str | None
    linewidth: float

    input_help = STATS_INPUT_HELP
    plot_explain = "Violin plot is a combination of boxplot " \
                   "and kernel density estimate."
    example_image = "violin.png"

    def extra_options(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            self.color = st.color_picker("Color", value="#00b796")
        with c2:
            self.scale = st.selectbox("Scale Method",
                                      options=["area", "count", "width"],
                                      help="The method used to scale the "
                                           "width of each violin. If area, "
                                           "each violin will have "
                                           "the same area.If count, the width "
                                           "of the violins will be scaled by "
                                           "the number of observations "
                                           "in that bin. If width, "
                                           "each violin will have "
                                           "the same width.")
        with c3:
            self.inner = st.selectbox("Violin Interior", options=[
                "box", "quartile", "point", "stick"])
        with c4:
            self.linewidth = st.number_input("Line Width", value=1.,
                                             min_value=0., max_value=5.)

    def get_options(self):
        return dict(color=self.color,
                    scale=self.scale, inner=self.inner,
                    linewidth=self.linewidth,
                    )


# For Strip and Swarm
class StripAdder(PlotAdder):
    name = "Strip"
    plotter = Strip
    color: str
    marker_size: float

    input_help = STATS_INPUT_HELP
    plot_explain = "Showing the underlying distribution of your data point"
    example_image = "strip.png"

    def extra_options(self):
        c1, c2 = st.columns(2)
        with c1:
            self.color = st.color_picker("Point Color", value="#00b796")
        with c2:
            self.marker_size = st.number_input("Marker Size", value=1.,
                                               min_value=0., max_value=5.)

    def get_options(self):
        return dict(color=self.color,
                    size=self.marker_size,
                    )


class SwarmAdder(StripAdder):
    name = "Swarm"
    plotter = Swarm
    example_image = "swarm.png"


class CountAdder(PlotAdder):
    name = "Count"
    plotter = Count
    color: str

    plot_explain = "Show the counts of observations in each categorical."
    example_image = "count.svg"

    def extra_options(self):
        self.color = st.color_picker("Color", value="#00b796")

    def get_options(self):
        return dict(color=self.color)


class AnnoLabelsAdder(PlotAdder):
    name = "Annotated specific labels"
    plotter = AnnoLabels
    plot_explain = "Annotate a few rows or columns."
    example_image = "annolabels.png"

    def input_panel(self):
        super().input_panel()
        self.anno_texts = st.text_input(
            "The label to show, seperated by comma(,)")
        self.anno_texts = self.anno_texts.split(",")

    def get_data(self):
        texts = self.user_input.parse()
        return np.ma.masked_where(~np.in1d(texts, self.anno_texts), texts)


PLOTTERS = [
    DendrogramAdder,
    ColorsAdder,
    LabelAdder,
    AnnoLabelsAdder,
    BarAdder,
    BoxAdder,
    BoxenAdder,
    ViolinAdder,
    # CountAdder,
    PointAdder,
    StripAdder,
    SwarmAdder,
]
plot_options = dict(zip([p.name for p in PLOTTERS], PLOTTERS))


def plot_panel(key, side, datasets, main_data):
    with st.expander(f"{side.capitalize()} plot {key + 1}", expanded=False):
        selector, _ = st.columns([1, 1])
        adder = selector.selectbox(f"Plot type",
                                   options=list(plot_options.keys()),
                                   label_visibility="collapsed",
                                   key=f"{key}-{side}")
        adder_func = plot_options[adder]
        adder_func(key, side, datasets, main_data)


def side_plots_adder(datasets, main_data, storage):
    side_options = ["right", "top", "left", "bottom"]
    tabs = st.tabs([s.capitalize() for s in side_options])
    for side in side_options:
        state_key = f"{side}_plot_counts"
        storage.add_state(state_key, 0)
    for ix, (t, side) in enumerate(zip(tabs, side_options)):
        state_key = f"{side}_plot_counts"

        def add_callback(state_key):
            storage[state_key] += 1

        def delete_callback(state_key):
            if storage[state_key] > 0:
                storage[state_key] -= 1

        with t:
            adder, deleter, _ = st.columns([1, 2, 2.5])
            with adder:
                st.button(f"➕ Add One",
                          use_container_width=True,
                          key=f"{side}_{ix}_add",
                          on_click=partial(add_callback, state_key))
            with deleter:
                st.button(f"❌ Remove Last Added",
                          use_container_width=True,
                          key=f"{side}_{ix}_delete",
                          on_click=partial(delete_callback, state_key),
                          disabled=storage[state_key] == 0,
                          )
            for i in range(storage[state_key]):
                plot_panel(i, side, datasets, main_data)


@dataclass
class SplitAction:
    orient: str
    cut: list = field(default=None)
    labels: list = field(default=None)
    order: list = field(default=None)
    spacing: float = 0.01


def spliter(orient, datastorage):

    how = st.selectbox("How to partition",
                       options=["By Position", "By Data"],
                       key=f"{orient}-how-to-partition"
                       )
    space = st.number_input("Gap", value=1, min_value=0, max_value=100,
                            key=f"{orient}-partition-space",
                            help="Percentage of the canvas size")
    if how == "By Position":
        cut = st.text_input("Example: 10,15",
                            key=f"{orient}-partition-by-position")
        if cut != "":
            cut = [int(c.strip()) for c in cut.split(",")]
            return SplitAction(orient=orient, cut=cut, spacing=space/100)
    else:
        dataset_name = st.selectbox("Which dataset",
                                    key=f"{orient}-partition-select-dataset",
                                    options=[""] + datastorage.get_names())
        order = st.text_input("Order", help="eg. a,b",
                              key=f"{orient}-partition-order")
        if dataset_name != "":
            if order != "":
                order = [str(o.strip()) for o in order.split(",")]
            else:
                order = None
            return SplitAction(orient=orient,
                               labels=datastorage.get_datasets(dataset_name),
                               order=order, spacing=space/100)

