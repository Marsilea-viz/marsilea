import pandas as pd
import streamlit as st
import matplotlib as mpl
import matplotlib.pyplot as plt


import heatgraphy as hg

from components.state import init_state
from components.data_input import parse_text, parse_file
from components.transformation import transformation
from components.side_plots import side_plots_adder, split_plot
from components.saver import plot_saver
from components.cmap_picker import colormap_viewer
# This make the nested columns available
# import components.nested_columns

init_state(dict(
    transform=None,
    render_plan=dict(
        left={},
        right={},
        top={},
        bottom={},
    ),
    data=None,
    raw_data=None,
    figure=None,
    split_row=None,
    split_col=None
))

st.set_page_config(
    page_title="Heatmap",
    layout="centered",
    page_icon="🎨",
    initial_sidebar_state="collapsed"
)

st.markdown(f"""
<style>
    .main .block-container{{
        min-width: 800px;
        max-width: 1200px;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("Try other tools: - [Upsetplot](/upset) - [Corrgram](/upset)")

st.header("Beautiful heatmap creator")
error = st.empty()
mcol1, mcol2 = st.columns([1, 2])
with mcol2:
    chart = st.empty()

with mcol1:
    tb_file = st.file_uploader("Choose a table file",
                               key="table_reader",
                               accept_multiple_files=False,
                               type=["txt", "csv", "xlsx", "xls"])
    text = st.text_area("Paste data here")
    sep = st.text_input("Seperator", value="")

    data = None
    if text is not None:
        if sep == "":
            sep = ","
        data = parse_text(text, sep=sep)
    else:
        if tb_file is not None:
            data = parse_file(tb_file, sep)
    if data is None:
        load_example = st.button("Load example")
    else:
        with st.expander("View Data"):
            data_anchor = st.empty()

        st.session_state['data'] = data
        st.session_state['raw_data'] = data

        transformation()

        with st.expander("Configuration"):
            cmap = colormap_viewer()
            disable_text = data.size > 200
            annot = st.checkbox("Add Text", disabled=disable_text)
            fontsize = st.number_input("Font size", min_value=1, step=1,
                                       value=8)
            grid_linewidth = st.number_input("Grid line", min_value=0.)

        saver = st.expander("Save Your Plot")

if data is not None:

    split_plot()

    side_plots_adder()

    try:
        transform_action = st.session_state['transform']
        if transform_action is not None:
            st.session_state['data'] = transform_action.apply(st.session_state['data'])
        data_anchor.dataframe(st.session_state['data'])
    except Exception:
        error.error("Transformation failed", icon="🚨")

    #try:
    with mpl.rc_context({"font.size": fontsize}):
        fig = plt.figure()
        h = hg.Heatmap(st.session_state['data'], cmap=cmap, annot=annot,
                       linewidth=grid_linewidth)
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
        plot_saver(fig, anchor=saver)
        chart.pyplot(fig)
    # except Exception:
    #     raise Exception
    #     error.error("Failed to render the plot, please check your data input. "
    #                 "Or you may report this issue. "
    #                 "(Go to upper right menu -> Report a bug)", icon="🚨")

