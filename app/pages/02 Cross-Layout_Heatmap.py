import matplotlib as mpl
import numpy as np
import streamlit as st
import textwrap
from components.data_input import FileUpload
from components.initialize import init_page
from components.main_plots import MainHeatmap, MainSizedHeatmap, MainMark
from components.resource import xlayout_example_data, get_font_list
from components.saver import ChartSaver
from components.side_plots import Splitter, SidePlotAdder
from components.state import State, DataStorage

import marsilea as hg

init_page("X-Layout Heatmap")

s = State(key="x-layout-heatmap")
s.init_state(figure=None, data_loaded=False, error=False, literal_codes=None)
ds = DataStorage(key="x-layout-heatmap")

st.title("X-Layout Visualization Creator")

st.warning(
    "We are still in beta stage, you may report to us " "if you encounter any bugs",
    icon="⚠️",
)

st.markdown(
    '<video controls width="250" autoplay="true" muted="true" loop="true" '
    'playsinline style="pointer-events: none;">'
    '<source src="https://raw.githubusercontent.com/Marsilea-viz'
    '/marsilea/main/app/img/V2.mp4" '
    'type="video/mp4" /></video>',
    unsafe_allow_html=True,
)

st.header("Step1: Prepare Datasets")

st.caption("Different datasets are used in different plots.")

file = FileUpload(key="x-layout", header=False, index=False)

data_name = st.text_input("Name", value=file.name)

c1, c2 = st.columns(2)
with c1:
    extract_row_label = st.checkbox("Extract row labels as a dataset")
with c2:
    extract_col_label = st.checkbox("Extract column labels as a dataset")

add = st.button("Add Dataset", type="primary")
if add:
    if file.name != "":
        process = True
        if data_name == "":
            st.error("Please give a name to your dataset", icon="✍️")
            process = False
        if data_name in ds.get_names():
            st.error("The name is already taken by other datasets")
            process = False

        if process:
            if extract_row_label or extract_col_label:
                data, row, col = file.parse_parts(
                    row_label=extract_row_label, col_label=extract_col_label
                )
                ds.add_dataset(data_name, data)
                if extract_row_label:
                    row_name = f"{data_name} (Row Labels)"
                    ds.add_dataset(row_name, row)
                if extract_col_label:
                    col_name = f"{data_name} (Column Labels)"
                    ds.add_dataset(col_name, col)
            else:
                data = file.parse()
                ds.add_dataset(data_name, data)
    else:
        st.error("Please upload a file", icon="📂")

load_example = st.button("Load Example")
if load_example:
    examples = xlayout_example_data()
    for d in examples:
        ds.add_dataset(d.name, d.data)

if len(ds.get_all_names()) == 0:
    st.warning("Please add at least one dataset to proceed", icon="🐣")

used_datasets = st.multiselect(
    "Select datasets to use",
    options=ds.get_all_names(),
    default=ds.get_all_names(),
    help=" Unselect the dataset that " "you don't want to use",
)
ds.set_visible_datasets(used_datasets)

if len(used_datasets) > 0:
    s["data_loaded"] = True

if (len(ds.get_all_names()) > 0) & (len(used_datasets) == 0):
    st.warning("Please select at least one dataset to proceed", icon="🐣")

with st.expander("View Dataset"):
    view_data_name = st.selectbox("Select a dataset", options=used_datasets)
    if s["data_loaded"]:
        view_data = ds.get_datasets(view_data_name)
        m1, m2, m3, m4 = st.columns(4)
        view_shape = view_data.shape
        with m1:
            if view_data.ndim == 2:
                st.metric("Row × Column", value=f"{view_shape[0]} × {view_shape[1]}")
            else:
                st.metric("Size", value=f"{view_data.size}")
        if np.issubdtype(view_data.dtype, np.number):
            with m2:
                st.metric("Min", value=view_data.min())
            with m3:
                st.metric("Max", value=view_data.max())
            with m4:
                st.metric("Mean", value=view_data.mean())

        st.dataframe(view_data)

# st.markdown("---")

if s["data_loaded"]:
    st.header("Step2: Draw on main canvas")
    st.caption("You can add multiple layers to main canvas")

    st.subheader("Step 2a: Select dataset for clustering")

    st.caption("The clustering data is used to generate dendrogram")

    cluster_data_name = st.selectbox(
        "Please select dataset used for clustering",
        label_visibility="collapsed",
        options=ds.get_names(subset="2d"),
    )
    ds.set_main_data(cluster_data_name)

    cluster_data = ds.get_datasets(cluster_data_name)
    cluster_data_shape = cluster_data.shape

    st.subheader("Step 2b: Add plots")

    heat, sized_heat, mark = st.tabs(["Heatmap", "Sized Heatmap", "Mark"])

    with heat:
        heatmap = MainHeatmap(ds, key="main-heatmap")

    with sized_heat:
        sized_heatmap = MainSizedHeatmap(ds, key="main-sized-heatmap")

    with mark:
        mark_heatmap = MainMark(ds, key="main-mark-heatmap")

    st.text("")
    st.text("")

    st.subheader("Step 2c: Adjust main canvas")
    width_col, height_col = st.columns(2)
    with width_col:
        width = st.number_input("Width", min_value=1.0, value=5.0, step=0.1)
    with height_col:
        height = st.number_input("Height", min_value=1.0, value=4.0, step=0.1)

    with st.expander("Partitioning main plot"):
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("**Horizontal**")
            hsplitter = Splitter("h", ds)
        with s2:
            st.markdown("**Vertical**")
            vsplitter = Splitter("v", ds)

    # ============================= STEP 3 ===================================

    st.header("Step 3: Add side plots")
    st.caption("Add plots on four sides to annotate the main plot")

    side_plotter = SidePlotAdder(ds, s)

    # ============================= STEP 4 ===================================

    st.header("Step 4: Result")
    st.caption("Save figure is in the left panel")

    f1, f2 = st.columns(2)
    with f1:
        fonts = get_font_list()
        font_family = st.selectbox(
            "Font Family", options=fonts, index=fonts.index("Noto Sans")
        )
    with f2:
        font_size = st.number_input("Font size", min_value=1, value=10)

    # TODO: How to adjust legend to be more intuitive
    # l1, l2, l3 = st.columns(3)
    # with l1:
    #     legend_side = st.selectbox(
    #         "Draw Legend",
    #         options=["right", "left", "top", "bottom", "No Legend"],
    #         format_func=lambda x: x.capitalize()
    #     )
    # with l2:
    #     legend_stack = st.selectbox("Legend Stack", options=["column", "row"])
    # with l3:
    #     legend_stack_size = st.number_input("Stack Size", min_value=1, value=3)

    _, render_button_c, _ = st.columns(3)
    with render_button_c:
        render = st.button(
            "Render",
            type="primary",
            use_container_width=True,
        )
    if render:
        literal_codes = (
            "import marsilea as ma\n"
            + "import marsilea.plotter as mp\n\n"
            + f"h = hg.ClusterBoard(cluster_data=cluster_data, width={width}, height={height})\n"
        )

        with mpl.rc_context({"font.family": font_family, "font.size": font_size}):
            h = hg.ClusterBoard(cluster_data=cluster_data, width=width, height=height)
            # apply main
            heatmap.apply(h)
            literal_codes += textwrap.dedent(heatmap.literal_code("h"))

            sized_heatmap.apply(h)
            literal_codes += textwrap.dedent(sized_heatmap.literal_code("h"))

            mark_heatmap.apply(h)
            literal_codes += textwrap.dedent(mark_heatmap.literal_code("h"))

            # apply split
            hsplitter.apply(h)
            literal_codes += textwrap.dedent(hsplitter.literal_code("h"))

            vsplitter.apply(h)
            literal_codes += textwrap.dedent(vsplitter.literal_code("h"))

            # Add Side plot
            side_plotter.apply(h)
            literal_codes += textwrap.dedent(side_plotter.literal_code("h"))

            h.add_legends()
            h.render()

            literal_codes += "\nh.add_legends()"
            literal_codes += "\nh.render()"
        s["figure"] = h.figure
        s["literal_codes"] = literal_codes

    if s["figure"] is not None:
        st.pyplot(s["figure"])

    if s["literal_codes"] is not None:
        with st.expander("Reference Code"):
            st.markdown(
                "The following code may not work directly. "
                "But it can be used to as a skeleton to reproduce the figure."
            )
            st.code(s["literal_codes"], language="python")

with st.sidebar:
    ChartSaver(s["figure"])
