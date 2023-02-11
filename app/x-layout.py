import heatgraphy as hg
import matplotlib as mpl
import matplotlib.pyplot as plt
import streamlit as st
from components.example_download import ExampleDownloader
from components.initialize import enable_nested_columns, inject_css
from components.layer_data import HeatmapData, GlobalConfig, \
    SizedHeatmapData, MarkerData
from components.saver import ChartSaver
from components.side_plots import side_plots_adder, split_plot
from components.state import init_state
from heatgraphy.plotter import ColorMesh, SizedMesh, MarkerMesh
from matplotlib.image import imread

# This make the nested columns available
# import components.nested_columns

# ===========SETUP THINGS=============

enable_nested_columns()

st.set_page_config(
    page_title="Heatgraphy",
    layout="centered",
    page_icon=imread("app/img/favicon.png"),
    initial_sidebar_state="collapsed",
    menu_items={
        'Report a bug': 'https://github.com/heatgraphy/heatgraphy/issues/new/choose',
        'About': 'A web interface for Heatgraphy'
    }
)

inject_css()


@st.cache_data
def empty_figure():
    return plt.figure()


init_state(data_ready=False,
           main_data=None,
           render_plan=dict(top={}, bottom={}, left={}, right={}),
           dendrogram_row=None,
           dendrogram_col=None,
           figure=empty_figure(),
           split_h=None,
           split_v=None,

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
    add_legends = global_options['add_legends']
    width = global_options['width']
    height = global_options['height']

    with mpl.rc_context({"font.size": fontsize, "font.family": fontfamily}):
        fig = plt.figure()
        cluster_data_name = global_options["cluster_data_name"]
        cluster_data = st.session_state[cluster_data_name]
        h = hg.ClusterBoard(cluster_data, width=width, height=height)

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

        srow = st.session_state["split_h"]
        scol = st.session_state["split_v"]
        if srow is not None:
            h.hsplit(cut=srow.cut, labels=srow.labels, order=srow.order)
        if scol is not None:
            h.vsplit(cut=scol.cut, labels=scol.labels, order=scol.order)

        plans = st.session_state['render_plan']
        for side, actions in plans.items():
            actions = sorted(list(actions.values()), key=lambda x: x.key)
            for action in actions:
                action.apply(h)

        if add_legends:
            h.add_legends()

        h.render(fig)
        st.session_state["figure"] = fig


# ===========UI PART=============

st.markdown("Try other tools: - [Upsetplot](/upset)")

st.header("x-layout visualization creator")

st.warning("Beta stage: Only heatmap variants are available",
           icon="⚠️")
ExampleDownloader()

st.markdown("Before you start you may want to read [Manual](/Manual).")

st.subheader("Data Input")
st.info("Select one or more layer to draw.", icon="😉")
st.markdown("Data Requirements: \n" \
            "- Format: .txt/.csv/.xlsx\n" \
            "- Data must be number, " \
            "if label is presented, add it with side plot.\n"\
            " - Data must have same shape."
            )
heat, sheat, mar = st.tabs(["Heatmap", "Sized Heatmap", "Mark"])

with heat:
    st.markdown("Heatmap reveal variation through color strength.")
    st.image("app/img/heatmap.png", width=100)
    h_data = HeatmapData()

with sheat:
    st.markdown("Sized Heatmap encodes size as extra information in heatmap")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("Size Only")
        st.image("app/img/sized_onlymap.png", width=100)
    with c2:
        st.markdown("Color + Size")
        st.image("app/img/sized_heatmap.png", width=100)

    sh_data = SizedHeatmapData()

with mar:
    st.markdown("Use a mark to mark the cell on heatmap")
    st.image("app/img/mark_map.png", width=100)
    m_data = MarkerData()

if st.session_state["data_ready"]:

    with st.expander("General Options"):
        tabs = st.tabs(["Configuration", "Heatmap Partition", "Export"])
        conf, spliter, saver = tabs

    button_name = "Apply changes & Render"
    st.info(f"Remember to click **{button_name}** after any changes.",
            icon="😝")
    _, render_button, _ = st.columns([2, 2, 2])
    with render_button:

        render_request = st.button(button_name,
                                   type="primary",
                                   help="Apply changes to your heatmap.")

    fig = st.session_state["figure"]
    st.pyplot(fig)

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
