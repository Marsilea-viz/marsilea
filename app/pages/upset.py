import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from components.data_input import FileUpload
from components.initialize import inject_css
from components.layer_data import get_font_list
from components.state import init_state
from heatgraphy import UpsetData, Upset

st.set_page_config(
    page_title="Upset Plot",
    initial_sidebar_state="collapsed",
    page_icon="⚗️"
)

inject_css()


@st.experimental_memo
def empty_figure():
    return plt.figure(figsize=(1, 1))


init_state(
    upset_data=None,
    parse_success=False,
    figure=empty_figure()
)

st.header("Upset Plot")

st.markdown("[What is upset plot?](https://upset.app/)")

format = st.radio("Your Set Format",
                  options=["Sets", "Memberships", "Binary Table"],
                  horizontal=True)
if format == "Sets":
    st.markdown("The column records the items in a set.")
    st.markdown("**Example**")
    df = pd.DataFrame({"Set 1": ["Item 1", "Item 2", ""],
                       "Set 2": ["Item 4", "Item 2", "Item 3"],
                       "Set 3": ["Item 9", "", ""]})
    st.dataframe(df)

elif format == "Memberships":
    st.markdown("The column records the sets that an item belongs to.")
    st.markdown("**Example**")
    df = pd.DataFrame({"Item 1": ["Set 1", "Set 2", ""],
                       "Item 2": ["Set 4", "Set 2", "Set 3"],
                       "Item 3": ["Set 9", "", ""]})
    st.dataframe(df)

else:
    st.markdown("A binary table, columns are sets, rows are items, 1 indicates"
                "the item is in the set.")
    st.markdown("**Example**")
    df = pd.DataFrame(data=np.random.randint(0, 2, (3, 3)),
                      index=["Item 1", "Item 2", "Item 3"],
                      columns=["Set 1", "Set 2", "Set 3"])
    st.dataframe(df)

user_input = FileUpload()
data = user_input.parse_dataframe()


@st.experimental_memo(show_spinner=False)
def process_upset_data(format, data):
    if format == "Sets":
        sets = {}
        for name, col in data.items():
            sets[name] = col.dropna().values
        udata = UpsetData.from_sets(sets)
    elif format == "Memberships":
        items = {}
        for name, col in data.items():
            items[name] = col.dropna().values
        udata = UpsetData.from_memberships(items)
    else:
        udata = UpsetData(data)
    return udata


if data is not None:
    try:
        upset_data = process_upset_data(format, data)
        st.session_state["parse_success"] = True
    except Exception as e:
        st.session_state["parse_success"] = False
        st.error("Failed to read set data, please select the correct"
                 "set format and check your input.", icon="🚨")
        # raise e

    fig_container = st.empty()
    with fig_container:
        st.pyplot(st.session_state["figure"])

    if st.session_state["parse_success"]:
        st.session_state['upset_data'] = upset_data

        filter, highlight, styles = st.tabs(["Filter", "Highlight", "Styles"])

        with filter:
            sets_table = pd.DataFrame(upset_data.cardinality(),
                                      columns=["size"])
            sets_table["degree"] = sets_table.index.to_frame().sum(axis=1)

            size_upper = int(sets_table['size'].max())
            degree_upper = int(sets_table['degree'].max())

            c1, c2 = st.columns(2, gap="large")
            with c1:
                size_range = st.slider("Subset Size", min_value=0,
                                       value=(0, size_upper),
                                       max_value=size_upper)
            with c2:
                degree_range = st.slider("Degree", min_value=0,
                                         value=(0, degree_upper),
                                         max_value=degree_upper)

        with styles:
            st.markdown("**General**")
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                color = st.color_picker("Main Color", value="#111111")
            with g2:
                linewidth = st.number_input("Line Width", min_value=.5,
                                            value=1.5)
            with g3:
                shading = st.number_input("Shading", min_value=0.,
                                          value=.3, max_value=1.)
            with g4:
                grid_background = st.number_input("Background", min_value=0.,
                                                  value=.1, max_value=1.)

            st.markdown("**Font**")
            f1, f2, f3 = st.columns(3)
            with f1:
                fontcolor = st.color_picker("Font Color", value="#111111")
            with f2:
                fontsize = st.number_input(
                    "Font size", min_value=1, step=1, value=10)
            with f3:
                font_list = get_font_list()
                DEFAULT_FONT = font_list.index("Source Sans Pro")
                fontfamily = st.selectbox("Font Family", options=font_list,
                                          index=DEFAULT_FONT)

        with highlight:
            pass

        fig = plt.figure()
        up = Upset(upset_data, min_size=size_range[0],
                   max_size=size_range[1],
                   min_degree=degree_range[0], max_degree=degree_range[1],
                   color=color, linewidth=linewidth, shading=shading,
                   grid_background=grid_background
                   )
        up.render(fig, scale=1.5)
        fig_container.pyplot(fig)
        st.session_state["figure"] = fig
