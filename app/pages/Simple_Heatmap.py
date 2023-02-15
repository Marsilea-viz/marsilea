import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from components.initialize import enable_nested_columns
from components.state import State
from components.data_input import FileUpload
from components.cmap_selector import ColormapSelector
from components.font import FontFamily

import streamlit as st
import matplotlib as mpl
import heatgraphy as hg
from heatgraphy.plotter import Labels, Title, AnnoLabels

enable_nested_columns()

s = State(
    current_stage=0,
    data=None,
    cmap="coolwarm",
    datasets=[],
)

st.title("Simple Heatmap")

st.subheader("Prepare Your Data")
file = FileUpload(key="main", header=True, index=True)
user_data = file.parse()
if user_data is not None:
    s['data'] = user_data
load = st.button("Load Example")
if load:
    s['data'] = pd.DataFrame(np.random.randn(5, 5) + 10,
                             columns=["Apple", "Banana", "Orange",
                                      "Strawberry", "Coconut"],
                             index=["Red", "Blue", "Yellow", "Green", "Black"])
if s['data'] is not None:
    view_tab, trans_tab = st.tabs(["View", "Transform"])
    with view_tab:
        st.dataframe(s['data'])

if s['data'] is not None:
    st.markdown("---")
    st.subheader("Setup Your Heatmap")

    t1, t2, t3, t4 = st.columns(4)
    with t1:
        heatmap_title = st.text_input("Title")
    with t2:
        title_side = st.selectbox("Place title at",
                                  options=["top", "bottom", "left", "right"],
                                  format_func=lambda x: x.capitalize())
    with t3:
        options = {
            "top": ["center", "left", "right"],
            "bottom": ["center", "left", "right"],
            "left": ["center", "top", "bottom"],
            "right": ["center", "top", "bottom"],
        }
        title_align = st.selectbox("Title alignment",
                                   options=options[title_side],
                                   format_func=lambda x: x.capitalize())
    with t4:
        title_fontsize = st.number_input("Title font size",
                                         min_value=1, value=14)

    s1, s2 = st.columns(2)
    with s1:
        width = st.number_input("Width", min_value=0, value=5)
    with s2:
        height = st.number_input("Height", min_value=0, value=5)

    fonts = FontFamily().font_list
    font_family = st.selectbox("Font Family", options=fonts,
                               index=fonts.index("Noto Sans"))

    st.markdown("---")
    st.markdown("**Clustering**")
    cluster = st.radio("Cluster on", label_visibility="collapsed",
                       options=["No cluster", "Row", "Column", "Both"],
                       horizontal=True)
    s1, s2 = st.columns(2)
    methods = ["single", "complete", "average", "weighted",
               "centroid", "median", "ward"]
    metrics = ["euclidean", "minkowski", "cityblock",
               "sqeuclidean", "cosine", "correlation",
               "jaccard", "jensenshannon", "chebyshev",
               "canberra", "braycurtis", "mahalanobis"]
    with s1:
        method = st.selectbox("Method", options=methods)
    with s2:
        metric = st.selectbox("Distance Metrics", options=metrics)

    st.markdown("---")
    l1, l2 = st.columns(2)
    with l1:
        st.markdown("**Row Labels**")
        add_row_labels = st.checkbox("Add", key="row_add")
        row_marks = st.text_input("Show specific labels",
                                  help="Label a few important rows, "
                                       "eg. banana,apple",
                                  key="row_mark")
        row_rotation = st.number_input("Rotation", value=0, key="row_rotation")

    with l2:
        st.markdown("**Column Labels**")
        add_col_labels = st.checkbox("Add", key="col_add")
        col_marks = st.text_input("Show specific labels",
                                  help="Label a few important columns, "
                                       "eg. banana,apple",
                                  key="col_mark")
        col_rotation = st.number_input("Rotation", value=-45,
                                       key="col_rotation")

    font_size = st.number_input("Font size", min_value=1, value=10)

    st.markdown("---")
    cmap = ColormapSelector("simple")
    s['cmap'] = cmap.get_cmap()

    st.markdown("---")

    main_data = s['data'].to_numpy()
    row_labels = s['data'].index.astype(str).tolist()
    col_labels = s['data'].columns.astype(str).tolist()

    st.subheader("Result")

    with mpl.rc_context({"font.family": font_family, "font.size": font_size}):

        h = hg.Heatmap(data=main_data,
                       cmap=s['cmap'],
                       width=width, height=height)
        if cluster == "Row":
            h.add_dendrogram("left", method=method, metric=metric)
        elif cluster == "Column":
            h.add_dendrogram("top", method=method, metric=metric)
        elif cluster == "Both":
            h.add_dendrogram("left", method=method, metric=metric)
            h.add_dendrogram("top", method=method, metric=metric)

        if add_row_labels:
            if row_marks != "":
                marks = [i.strip() for i in row_marks.split(",")]
                row_label_plot = AnnoLabels(
                    row_labels, mark=marks, fontsize=font_size
                )
            else:
                row_label_plot = Labels(row_labels, text_pad=.1,
                                        rotation=row_rotation,
                                        fontsize=font_size)
            h.add_right(row_label_plot)
        if add_col_labels:
            kws = dict()
            if col_marks != "":
                marks = [i.strip() for i in col_marks.split(",")]
                col_label_plot = AnnoLabels(
                    col_labels, mark=marks, fontsize=font_size
                )
            else:
                col_label_plot = Labels(col_labels, text_pad=.1,
                                        rotation=col_rotation,
                                        fontsize=font_size)
            h.add_bottom(col_label_plot)
        if heatmap_title != "":
            h.add_plot(title_side,
                       Title(heatmap_title, align=title_align,
                             fontsize=title_fontsize), pad=.1)

        h.add_legends()
        h.render()
        st.pyplot(h.figure)
