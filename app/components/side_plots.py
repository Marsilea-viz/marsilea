from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from heatgraphy.base import MatrixBase
from heatgraphy.plotter import RenderPlan
from heatgraphy.plotter import Bar, Colors


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


plotter_mapper = dict(
    Bar=Bar,
    Colros=Colors,
)


def plot_adder(key):
    plot_key = f"Add side plotter-{key}"
    with st.form(plot_key):
        c1, c2, c3, c4, c5 = st.columns([3, 3, 3, 3, 1])
        side = c1.selectbox("Side", options=["right", "left", "bottom", "top"],
                            format_func=lambda x: x.capitalize())
        plotter = c2.selectbox("Plot type", options=["Bar", "Colors"])
        size = c3.number_input("Size", min_value=0.)
        pad = c4.number_input("Pad", min_value=0.)
        color = c5.color_picker("Color")

        st.markdown("**Add your data**")
        input1, input2 = st.columns(2)
        paste_data = input1.text_area("1️⃣ ️️Paste here")
        tb_file = input2.file_uploader("2️⃣️ Choose a table file",
                                       accept_multiple_files=False,
                                       type=["txt", "csv", "xlsx", "xls"]
                                       )

        add = st.form_submit_button("Confirm")
        if add:
            size = None if size == 0 else size
            if tb_file is not None:
                data = pd.read_csv(tb_file)
            else:
                rows = paste_data.split("\n")
                raw_data = [[float(r) for r in row.split(",")] for row in rows]
                data = np.array(raw_data)
            st.session_state[f"render_plan"][side][plot_key] = (
                RenderAction(
                    key=key,
                    side=side, plotter=plotter_mapper[plotter],
                    data=data, size=size, pad=pad, kwargs=dict(color=color)
                )
            )


def side_plots_adder():
    _, space, _ = st.columns([1, 2, 1])
    space.subheader("Add Side Plots")
    add_plots = space.number_input("Add plots", min_value=0, max_value=50)
    for i in range(add_plots):
        plot_adder(i)


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
    with st.expander("Split plot?"):
        col1, col2 = st.columns(2)
        with col1:
            spliter("row")
        with col2:
            spliter("col")
