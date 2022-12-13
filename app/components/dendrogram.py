import streamlit as st
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DendrogramAction:
    side: str
    size: float
    pad: float

    method: str
    metric: str
    add_divider: bool
    add_base: bool
    add_meta: bool
    meta_color: Any
    colors: Any

    def get_kws(self):
        return dict(
            method=self.method,
            metric=self.metric,
            add_divider=self.add_divider,
            add_base=self.add_base,
            add_meta=self.add_meta,
            meta_color=self.meta_color,
            colors=self.colors,
            size=self.size,
            pad=self.pad
        )

    def apply(self, h):
        h.add_dendrogram(self.side, **self.get_kws())


class Dendrogram:

    def __init__(self):
        with st.expander("Dendrogram"):
            with st.form("Add dendrogram"):
                direction = st.selectbox("Apply along",
                                         options=["Row", "Column", "Both"])
                self.row = direction != "Column"
                self.col = direction != "Row"

                methods = ["single", "complete", "average", "weighted",
                           "centroid", "median", "ward"]
                metrics = ["euclidean", "minkowski", "cityblock",
                           "sqeuclidean", "cosine", "correlation",
                           "jaccard", "jensenshannon", "chebyshev",
                           "canberra", "braycurtis", "mahalanobis"]
                self.method = st.selectbox("Method", options=methods)
                self.metric = st.selectbox("Metric", options=metrics)

                self.side = st.selectbox("Side",
                                         options=["right", "left",
                                                  "bottom", "top"],
                                         format_func=lambda x: x.capitalize())
                self.size = st.number_input("Size", min_value=0.1, value=1.)
                self.pad = st.number_input("Pad", min_value=0., value=.05)
                self.add_divider = st.checkbox("Add divide line")
                self.add_base = st.selectbox("Add base dendrogram")
                self.add_meta = st.selectbox("Add meta dendrogram")
                self.meta_color = st.color_picker("Color for meta dendrogram")
                self.colors = st.color_picker("Dendrogram base color")
                add = st.form_submit_button()
                if add:
                    self.write_action()

    def write_action(self):
        action = DendrogramAction(side=self.side,
                                  size=self.size,
                                  pad=self.pad,
                                  method=self.method,
                                  metric=self.metric,
                                  add_divider=self.add_divider,
                                  add_base=self.add_base,
                                  add_meta=self.add_meta,
                                  meta_color=self.meta_color,
                                  colors=self.colors,
                                  )
        st.session_state["dendrogram"] = action
