import matplotlib as mpl
import streamlit as st
from components.cmap_selector import ColormapSelector
from components.data_input import FileUpload
from components.initialize import enable_nested_columns
from components.initialize import init_page
from components.resource import simple_heatmap_example_data, get_font_list
from components.saver import ChartSaver
from components.state import State

import heatgraphy as hg
from heatgraphy.plotter import Labels, Title, AnnoLabels

init_page("Simple Heatmap")

enable_nested_columns()

s = State(key="simple_heatmap")
s.init_state(
    data=None,
    cmap="coolwarm",
    norm=None,
    datasets=[],
    figure=None,
)

st.title("Simple Heatmap")

st.header("Prepare Your Data")
file = FileUpload(key="main", header=True, index=True)
user_data = file.parse_dataframe()
if user_data is not None:
    s['data'] = user_data
load = st.button("Load Example")
if load:
    s['data'] = simple_heatmap_example_data()
if s['data'] is not None:
    view_tab, trans_tab = st.tabs(["View", "Transform"])
    with view_tab:
        st.dataframe(s['data'])

if s['data'] is not None:
    main_data = s['data'].to_numpy()
    row_labels = s['data'].index.astype(str).tolist()
    col_labels = s['data'].columns.astype(str).tolist()

    st.markdown("---")
    st.header("Setup Your Heatmap")

    general_tab, cluster_tab, label_tab, colormap_tab = \
        st.tabs(["General", "Cluster", "Labels", "Colormap"])

    with general_tab:
        t1, t2, t3, t4 = st.columns(4)
        with t1:
            heatmap_title = st.text_input("Title")
        with t2:
            title_side = st.selectbox(
                "Place title at",
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
            width = st.number_input("Heatmap Width", min_value=0, value=5)
        with s2:
            height = st.number_input("Heatmap Height", min_value=0, value=5)

        fonts = get_font_list()
        font_family = st.selectbox("Font Family", options=fonts,
                                   index=fonts.index("Noto Sans"))

    with cluster_tab:
        # st.markdown("**Clustering**")
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
            row_size = st.number_input(
                "Size of Row Dendrogram", min_value=0., value=1.)
        with s2:
            metric = st.selectbox("Distance Metrics", options=metrics)
            col_size = st.number_input(
                "Size of Column Dendrogram", min_value=0., value=1.)

    with label_tab:

        l1, l2 = st.columns(2)
        with l1:
            st.markdown("**Row Labels**")
            add_row_labels = st.checkbox("Add", key="row_add")
            row_marks = st.multiselect("Show only specified labels",
                                       options=row_labels,
                                       default=[],
                                       help="Label a few important rows",
                                       key="row_mark")
            row_rotation = st.number_input("Rotation", value=0,
                                           key="row_rotation")

        with l2:
            st.markdown("**Column Labels**")
            add_col_labels = st.checkbox("Add", key="col_add")
            col_marks = st.multiselect("Show only specified labels",
                                       options=col_labels,
                                       default=[],
                                       help="Label a few important columns",
                                       key="col_mark")
            col_rotation = st.number_input("Rotation", value=-45,
                                           key="col_rotation")

        font_size = st.number_input("Font size", min_value=1, value=10)

    with colormap_tab:
        cmap = ColormapSelector("simple")
        s['cmap'] = cmap.get_cmap()
        s['norm'] = cmap.get_norm()

    st.markdown("---")

    st.header("Result")

    _, render_button, _ = st.columns(3)

    with render_button:
        render = st.button("Render", type="primary", use_container_width=True)

    if render:
        with mpl.rc_context(
                {"font.family": font_family, "font.size": font_size}):

            h = hg.Heatmap(data=main_data,
                           cmap=s['cmap'],
                           norm=s['norm'],
                           width=width, height=height)
            if method == "ward":
                metric = "euclidean"
            if cluster == "Row":
                h.add_dendrogram(
                    "left", method=method, metric=metric, size=row_size)
            elif cluster == "Column":
                h.add_dendrogram(
                    "top", method=method, metric=metric, size=col_size)
            elif cluster == "Both":
                h.add_dendrogram(
                    "left", method=method, metric=metric, size=row_size)
                h.add_dendrogram(
                    "top", method=method, metric=metric, size=col_size)

            if add_row_labels:
                if len(row_marks) > 0:
                    row_label_plot = AnnoLabels(
                        row_labels, mark=row_marks, fontsize=font_size
                    )
                else:
                    row_label_plot = Labels(row_labels, text_pad=.1,
                                            rotation=row_rotation,
                                            fontsize=font_size)
                h.add_right(row_label_plot)
            if add_col_labels:
                kws = dict()
                if len(col_marks) > 0:
                    col_label_plot = AnnoLabels(
                        col_labels, mark=col_marks, fontsize=font_size
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
            s['figure'] = h.figure

    if s['figure'] is not None:
        st.pyplot(s['figure'])

        with st.sidebar:
            ChartSaver(s['figure'])
