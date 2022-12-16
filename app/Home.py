import time

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib as mpl
import matplotlib.pyplot as plt

import heatgraphy as hg
from app.components.font import FontFamily

from components.nested_columns import register
from components.state import init_state
from components.data_input import FileUpload, PasteText
from components.transformation import transformation
from components.side_plots import side_plots_adder, split_plot
from components.saver import ChartSaver
from components.cmap_picker import colormap_viewer

# This make the nested columns available
# import components.nested_columns

register()

st.set_page_config(
    page_title="Heatmap",
    layout="centered",
    page_icon="🎨",
    initial_sidebar_state="collapsed"
)


@st.experimental_memo
def empty_figure():
    return plt.figure()


init_state(transform=None,
           render_plan=dict(top={}, bottom={}, left={}, right={}),
           dendrogram_row=None,
           dendrogram_col=None,
           data=None,
           raw_data=None,
           figure=empty_figure(),
           split_row=None,
           split_col=None,
           update=0,
           # a counter, if changed, the figure will rerender
           # use to improve performance
           )


# @st.experimental_singleton
def render_plot(**options):
    fontsize = options['fontsize']
    fontfamily = options['fontfamily']
    cmap = options['cmap']
    annot = options['annot']
    linewidth = options['linewidth']
    # try:
    with mpl.rc_context({"font.size": fontsize, 'font.family': fontfamily}):
        fig = plt.figure()
        h = hg.Heatmap(st.session_state['data'], cmap=cmap, annot=annot,
                       linewidth=linewidth)
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
                print(action)
                action.apply(h)

        h.render(fig)
        st.session_state["figure"] = fig
    # except Exception:
    #     raise Exception
    #     error.error("Failed to render the plot, please check your data input. "
    #                 "Or you may report this issue. "
    #                 "(Go to upper right menu -> Report a bug)", icon="🚨")


def apply_transform(action, data):
    try:
        if action is not None:
            st.session_state['data'] = action.apply(data)
            st.session_state['update'] += 1
    except Exception:
        st.error("Transformation failed", icon="🚨")

# Hack the style of elements in streamlit
st.markdown(f"""
<style>
    .main .block-container{{
        min-width: 800px;
        max-width: 1200px;
    }}
    
    div[data-testid="stImage"]>img {{
        max-height: 600px;
        object-fit: contain;
    }}
    
    .streamlit-expanderContent {{
        padding-right: 0rem;
        padding-left: 0rem;
    }}
    
    .streamlit-expanderHeader {{
        font-weight: bold;
        padding-right: 0rem;
        padding-left: 0rem;
    }}
    
    .streamlit-expander {{
        border-left: none;
        border-right: none;
        border-radius: 0rem;
    }}

</style>
""", unsafe_allow_html=True)

st.markdown("Try other tools: - [Upsetplot](/upset) - [Corrgram](/upset)")

st.header("Beautiful heatmap creator")

input_col, image_col = st.columns([1, 2])

with image_col:
    fig = st.session_state["figure"]
    st.pyplot(fig)

with input_col:
    data_input, data_transformation, data_viewer = st.tabs(
        ["Input Data", "Data Transformation", "Data Viewer"])

    with data_input:
        st.markdown("Input format: \n"
                    "   - Tab-seperated file (.tsv/.txt)\n"
                    "   - Comma-seperated file (.csv)\n"
                    "   - Excel file (.xlsx/.xls)")
        user_input = FileUpload(key="main-data")
    data = user_input.parse()

if data is not None:
    # TODO: Load example
    # load_example = st.button("Load example")
    st.session_state['data'] = data
    st.session_state['raw_data'] = data

    with data_viewer:
        data_anchor = st.empty()

    with data_transformation:
        transformation()

    _, render_button, _ = st.columns([2, 1, 2])
    with render_button:
        render_request = st.button("Apply changes & Render",
                                   type="primary",
                                   help="Apply changes to your heatmap.")

    with st.expander("Heatmap Options"):
        tabs = st.tabs(["Heatmap Partition", "Configuration", "Export"])
        spliter, conf, saver = tabs

    with spliter:
        split_plot()

    with conf:

        cmap = colormap_viewer()
        disable_text = data.size > 200
        annot = st.checkbox("Add Text", disabled=disable_text)
        fontsize = st.number_input("Font size", min_value=1, step=1,
                                   value=8)
        font_list = FontFamily().font_list
        fontfamily = st.selectbox("Font Family", options=font_list)
        grid_linewidth = st.number_input("Grid line", min_value=0.)

    st.subheader("Add Side Plots")
    st.markdown("The side plots will add from inner to outer")
    side_plots_adder()

    apply_transform(st.session_state['transform'],
                    st.session_state['data'])
    data_anchor.dataframe(st.session_state['data'])

    if render_request:
        render_plot(fontsize=fontsize, fontfamily=fontfamily,
                    cmap=cmap, annot=annot, linewidth=grid_linewidth)

        st.experimental_rerun()

    with saver:
        ChartSaver()
# chart.pyplot(fig)
