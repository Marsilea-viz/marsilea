import numpy as np
import pandas as pd
import streamlit as st
import heatgraphy as hg

from components.data_input import FileUpload
from components.state import State, DataStorage
from components.cmap_selector import ColormapSelector

from components.side_plots import spliter, side_plots_adder

from heatgraphy.plotter import ColorMesh

s = State(figure=None, data_loaded=False, )
ds = DataStorage()

st.title("X-Layout Visualization Creator")

st.header("Step1: Prepare Datasets")

file = FileUpload(key="x-layout", header=False, index=False)

data_name = st.text_input("Name", value=file.name)

add = st.button("Add Dataset")
if add:
    if file is not None:
        process = True
        if data_name == "":
            st.error("Please give a name to your dataset")
            process = False
        if data_name in ds.get_names():
            st.error("The name is already taken by other datasets")
            process = False

        if process:
            data = file.parse()
            ds.add_dataset(data_name, data)

load_example = st.button("Load Example")
if load_example:
    name = "Example: Main Data"
    fake_data = np.random.randint(0, 100, (10, 10))
    ds.add_dataset(name, fake_data)

    name = "Example: Unmatched Main Data"
    fake_data = np.random.randint(0, 100, (9, 9))
    ds.add_dataset(name, fake_data)

    name = "Example: Side Data"
    fake_data = np.random.randint(0, 100, 10)
    ds.add_dataset(name, fake_data)

    name = "Example: Unmatched Side Data"
    fake_data = np.random.randint(0, 100, 9)
    ds.add_dataset(name, fake_data)

if len(ds.get_names()) == 0:
    st.warning("Please add at least one dataset to proceed", icon="🐣")

used_datasets = st.multiselect("Added Datasets",
                               options=ds.get_names(),
                               default=ds.get_names(),
                               help="Select datasets for plotting"
                               )

if len(used_datasets) > 0:
    s['data_loaded'] = True

if (len(ds.get_names()) > 0) & (len(used_datasets) == 0):
    st.warning("Please select at least one dataset to proceed", icon="🐣")

with st.expander("View Dataset"):
    view_data_name = st.selectbox("Select a dataset", options=used_datasets)
    if s['data_loaded']:
        view_data = ds.get_datasets(view_data_name)
        m1, m2, m3, m4 = st.columns(4)
        view_shape = view_data.shape
        with m1:
            st.metric("Row × Column",
                      value=f"{view_shape[0]} × {view_shape[1]}")
        with m2:
            st.metric("Min", value=view_data.min())
        with m3:
            st.metric("Max", value=view_data.max())
        with m4:
            st.metric("Mean", value=view_data.mean())

        st.dataframe(view_data)

# st.markdown("---")

if s['data_loaded']:

    st.header("Step2: Main Plot")
    st.caption("You can add multiple layer to main plot")

    cluster_data_name = \
        st.selectbox("Which dataset used for cluster", options=used_datasets)

    cluster_data = ds.get_datasets(cluster_data_name)
    cluster_data_shape = cluster_data.shape

    heat, sheat, mar, partition = st.tabs(["Heatmap", "Sized Heatmap",
                                           "Mark", "Partition"])

    with heat:
        LAUNCH_HEAT = False
        c1, c2 = st.columns([1, 2])
        with c1:
            heatmap_label = st.text_input("Label", key=f"heatmap-data-label")

        with c2:
            heatmap_name = st.selectbox("Select Dataset",
                                        options=[""] + used_datasets)

        if heatmap_name != "":
            heatmap_data = ds.get_datasets(heatmap_name)
            LAUNCH_HEAT = True
            if heatmap_name != cluster_data_name:
                if heatmap_data.shape != cluster_data_shape:
                    st.error(f"Selected dataset {heatmap_data.shape} "
                             f"does not match cluster data {cluster_data_shape}")
                    LAUNCH_HEAT = False

        st.markdown("**Annotate Text**")
        annot = st.checkbox("Add Text")
        fontsize = st.number_input("Font size", min_value=1,
                                   step=1, value=6)
        grid_linewidth = st.number_input("Grid line", min_value=0.)

        cmap_selector = ColormapSelector(key="heatmap", default="coolwarm")

        cmap_selector.get_cmap()

    with partition:
        st.subheader("Partition the heatmap")
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("**Horizontal**")
            hsplit_action = spliter("horizontal", ds)
        with s2:
            st.markdown("**Vertical**")
            vsplit_action = spliter("vertical", ds)

    st.header("Step 3: Side Plots")

    side_plots_adder(used_datasets, cluster_data, s)

    st.header("Step 4: Result")

    _, render_button_c, _ = st.columns(3)
    with render_button_c:
        render = st.button("Render", type="primary", use_container_width=True)
    if render:
        h = hg.ClusterBoard(cluster_data=cluster_data)
        if LAUNCH_HEAT:
            heatmap = ColorMesh(heatmap_data)
            h.add_layer(heatmap, zorder=-100)

        if hsplit_action is not None:
            hs = hsplit_action
            h.hsplit(cut=hs.cut, labels=hs.labels, order=hs.order,
                     spacing=hs.spacing)
        if vsplit_action is not None:
            vs = vsplit_action
            h.vsplit(cut=vs.cut, labels=vs.labels, order=vs.order,
                     spacing=vs.spacing)

        h.render()
        s['figure'] = h.figure

    if s['figure'] is not None:
        st.pyplot(s['figure'])
