from dataclasses import dataclass, field
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from .data_input import FileUpload, PasteText
from heatgraphy.base import MatrixBase
from heatgraphy.plotter import (Bar, Box, Boxen, Colors, Count, Strip, Violin,
                                Point, Swarm, ColorMesh, Labels, Title)
from heatgraphy.plotter import RenderPlan


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

    def apply(self, h: MatrixBase):
        p = self.plotter(self.data, **self.kwargs)
        h.add_plot(self.side, p, size=self.size, pad=self.pad)


@dataclass
class DendrogramAction(RenderAction):

    def apply(self, h):
        h.add_dendrogram(self.side,
                         **self.kwargs, size=self.size, pad=self.pad, )


plotter_mapper = dict(
    bar=Bar,
    box=Box,
    boxen=Boxen,
    colors=Colors,
    colormesh=ColorMesh,
    count=Count,
    strip=Strip,
    swarm=Swarm,
    violin=Violin,
    point=Point,
    labels=Labels,
    dendrogram=None,
    title=Title,
)

raw_plotter = ['labels', 'colors']


class PlotAdder:
    init_size = 1.0
    init_pad = .05
    side: str
    size: float
    pad: float
    no_data: bool = False
    is_numeric: bool = True

    user_input: Any

    def __repr__(self):
        return f"Draw at {self.side} with size {self.size} and {self.pad}"

    def __init__(self, key, side, plot_name):
        self.key = key
        self.side = side
        self.plot_key = f"Add side plotter-{key}-{side}"
        self.plotter = plotter_mapper[plot_name]
        self.data = None

        with self.form():
            self.input_panel()
            self.base_elements()

            with st.expander("More Options"):
                self.extra_options()
            add = st.form_submit_button(label="Add plot")

        if add:
            # rerender figure
            # TODO: Check the data input and tips prompt
            if not self.no_data:
                self.data = self.user_input.parse()
                print(self.data)
                main_data = st.session_state["data"]
                if self.side in ["left", "right"]:
                    match_num = main_data.shape[0]
                else:
                    match_num = main_data.shape[1]
                if self.data.ndim == 1:
                    if len(self.data) > match_num:
                        st.error("Your input data is more than required.")
                    if len(self.data) < match_num:
                        st.error("Your input data is less than required.")
            self.write_action()

    def form(self):
        return st.form(self.plot_key)

    def base_elements(self):
        st.markdown("**Plot Options**")
        c1, c2, _ = st.columns([1, 1, 3])
        self.size = c1.number_input("Size", min_value=0.1,
                                    value=self.init_size)
        self.pad = c2.number_input("Pad", min_value=0., value=self.init_pad)

    def input_panel(self):
        st.markdown("**Input data**")
        self.user_input = FileUpload(key=self.plot_key)

    def extra_options(self):
        st.markdown("No more options.")

    def get_options(self):
        return {}

    def write_action(self):
        if self.data is not None:
            action = RenderAction(key=self.key, side=self.side,
                                  data=self.data, size=self.size,
                                  pad=self.pad, plotter=self.plotter,
                                  kwargs=self.get_options())
            st.session_state[f"render_plan"][self.side][self.plot_key] = action


class TitleAdder(PlotAdder):
    no_data = True
    color: str
    fontsize = 10
    fontweight = "regular"
    fontstyle = "normal"

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

    def input_panel(self):
        pass

    def handle_input(self):
        pass

    def extra_options(self):
        methods = ["single", "complete", "average", "weighted",
                   "centroid", "median", "ward"]
        metrics = ["euclidean", "minkowski", "cityblock",
                   "sqeuclidean", "cosine", "correlation",
                   "jaccard", "jensenshannon", "chebyshev",
                   "canberra", "braycurtis", "mahalanobis"]
        self.method = st.selectbox("Method", options=methods)
        self.metric = st.selectbox("Metric", options=metrics)
        self.add_divider = st.checkbox("Add divide line")
        self.add_base = st.checkbox("Add base dendrogram", value=True)
        self.add_meta = st.checkbox("Add meta dendrogram", value=True)
        self.meta_color = st.color_picker("Color for meta dendrogram")
        self.colors = st.color_picker("Dendrogram base color")
        self.linewidth = st.number_input("Line Width", min_value=0., value=.5)

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


class BarAdder(PlotAdder):
    color: str
    errcolor: str
    errwidth: float
    capsize: float
    width: float
    show_value: bool

    def extra_options(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            self.color = st.color_picker("Color", value="#00b796")
        with c2:
            self.errcolor = st.color_picker("Error Bar Color", value="#555555")
        with c3:
            self.errwidth = st.number_input("Error Bar Width", value=1.,
                                            min_value=0., max_value=5.)
        with c4:
            self.capsize = st.number_input("Error Cap Size", value=.3,
                                           min_value=.1, max_value=1.)
        # self.width = st.slider("Bar Width", value=.8,
        #                        min_value=.1, max_value=1.)

    def get_options(self):
        return dict(color=self.color, errcolor=self.errcolor,
                    errwidth=self.errwidth, capsize=self.capsize,
                    )


plotter_adder = dict(bar=BarAdder,
                     dendrogram=DendrogramAdder,
                     title=TitleAdder,
                     )


def plot_panel(key, side):
    with st.expander(f"Side plot {key + 1}", expanded=True):
        selector, _ = st.columns([1, 4])
        plot_type = selector.selectbox(f"Plot type",
                                       options=plotter_mapper.keys(),
                                       format_func=lambda x: x.capitalize(),
                                       label_visibility="collapsed",
                                       key=f"{key}-{side}")
        adder = plotter_adder.get(plot_type)

        if adder is None:
            PlotAdder(key, side, plot_type)
        else:
            adder(key, side, plot_type)


def side_plots_adder():
    side_options = ["right", "top", "left", "bottom"]
    tabs = st.tabs([s.capitalize() for s in side_options])
    for ix, (t, side) in enumerate(zip(tabs, side_options)):
        with t:
            adder, _ = st.columns([1, 4])
            add_plots = adder.number_input(f"Add plots", key=ix,
                                           min_value=0, max_value=50)
            for i in range(add_plots):
                plot_panel(key=i, side=side)


@dataclass
class SplitAction:
    orient: str
    cut: list = field(default=None)
    labels: list = field(default=None)
    order: list = field(default=None)


def spliter(orient):
    st.subheader(f"Split {orient.capitalize()}")
    with st.form(f"Split {orient}"):
        cut = st.text_input("Where to split",
                            help="Use number seperated by comma to indicate "
                                 "where to split the heatmap eg. 10,15"
                            )
        labels = st.text_input("Labels",
                               help="Labels should be seperated by comma,"
                                    "eg. a,a,b,b"
                               )
        order = st.text_input("Order", help="eg. a,b")
        submit = st.form_submit_button("Confirm")
        if submit:
            cut = [int(c) for c in cut.split(",")]
            labels = [str(label) for label in labels.split(",")]
            order = [str(o) for o in order]
            st.session_state[f"split_{orient}"] = (
                SplitAction(orient=orient, cut=cut,
                            labels=labels, order=order))


def split_plot():
    col1, col2 = st.columns(2)
    with col1:
        spliter("row")
    with col2:
        spliter("col")
