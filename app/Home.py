import matplotlib as mpl
import matplotlib.pyplot as plt
import streamlit as st

import heatgraphy as hg
from app.components.example_download import ExampleDownloader
from app.components.initialize import enable_nested_columns, inject_css
from app.components.layer_data import HeatmapData, GlobalConfig, \
    SizedHeatmapData, MarkerData
from app.components.saver import ChartSaver
from app.components.side_plots import side_plots_adder, split_plot
from app.components.state import init_state
from heatgraphy.plotter import ColorMesh, SizedMesh, MarkerMesh

# This make the nested columns available
# import components.nested_columns

# ===========SETUP THINGS=============

enable_nested_columns()

st.set_page_config(
    page_title="Heatmap",
    layout="centered",
    page_icon="🎨",
    initial_sidebar_state="collapsed"
)

inject_css()


@st.experimental_memo
def empty_figure():
    return plt.figure()


init_state(data_ready=False,
           main_data=None,
           render_plan=dict(top={}, bottom={}, left={}, right={}),
           dendrogram_row=None,
           dendrogram_col=None,
           figure=empty_figure(),
           split_row=None,
           split_col=None,

           heatmap_data=None,
           heatmap_raw_data=None,
           heatmap_transform=None,
           size_data=None,
           size_raw_data=None,
           size_transform=None,
           color_data=None,
           color_raw_data=None,
           color_transform=None,
           mark_data=None,
           )


# @st.experimental_singleton
def render_plot(global_options,
                heatmap_options,
                sizedheatmap_options,
                mark_options, ):
    fontsize = global_options['fontsize']
    fontfamily = global_options['fontfamily']

    with mpl.rc_context({"font.size": fontsize, "font.family": fontfamily}):
        fig = plt.figure()
        cluster_data_name = global_options["cluster_data_name"]
        cluster_data = st.session_state[cluster_data_name]
        h = hg.ClusterCanvas(cluster_data)

        heatmap_data = st.session_state["heatmap_data"]
        if heatmap_data is not None:
            heatmap = ColorMesh(heatmap_data, **heatmap_options)
            h.add_layer(heatmap, zorder=-100)

        size_data = st.session_state["size_data"]
        color_data = st.session_state["color_data"]
        if color_data is not None:
            sizedheatmap_options['color'] = color_data
        if size_data is not None:
            sized_heatmap = SizedMesh(
                size_data, **sizedheatmap_options
            )
            h.add_layer(sized_heatmap, zorder=1)

        mark_data = st.session_state["mark_data"]
        if mark_data is not None:
            marker = MarkerMesh(
                mark_data, **mark_options,
            )
            h.add_layer(marker, zorder=100)

        srow = st.session_state["split_row"]
        scol = st.session_state["split_col"]
        if srow is not None:
            h.split_row(cut=srow.cut, labels=srow.labels, order=srow.order)
        if scol is not None:
            h.split_col(cut=scol.cut, labels=scol.labels, order=scol.order)

        plans = st.session_state['render_plan']
        for side, actions in plans.items():
            actions = sorted(list(actions.values()), key=lambda x: x.key)
            for action in actions:
                action.apply(h)

        h.render(fig)
        st.session_state["figure"] = fig


# ===========UI PART=============

st.markdown("Try other tools: - [Upsetplot](/upset)")

st.header("Beautiful heatmap creator")
ExampleDownloader()

st.subheader("Data Input")
st.info("Select one or more layer to draw. "
        "Input data need to have same shape.", icon="🧐")
heat, sheat, mar = st.tabs(["Heatmap", "Sized Heatmap", "Mark"])

with heat:
    h_data = HeatmapData()

with sheat:
    sh_data = SizedHeatmapData()

with mar:
    m_data = MarkerData()

if st.session_state["data_ready"]:

    with st.expander("General Options"):
        tabs = st.tabs(["Heatmap Partition", "Configuration", "Export"])
        spliter, conf, saver = tabs

    fig = st.session_state["figure"]
    st.pyplot(fig)

    _, render_button, _ = st.columns([2, 2, 2])
    with render_button:
        render_request = st.button("Apply changes & Render",
                                   type="primary",
                                   help="Apply changes to your heatmap.")

    with spliter:
        split_plot()

    with conf:

        gconf = GlobalConfig()

    st.subheader("Add Side Plots")
    st.markdown("The side plots will add from inner to outer")
    side_plots_adder()

    if render_request:
        render_plot(gconf.get_conf(), h_data.get_styles(),
                    sh_data.get_styles(), m_data.get_styles())

        st.experimental_rerun()

    with saver:
        ChartSaver()
