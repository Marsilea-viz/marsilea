import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from components.data_input import FileUpload
from components.initialize import init_page
from components.initialize import inject_css
from components.resource import get_font_list, upset_showcase_data,\
    upset_example_data
from components.saver import ChartSaver
from components.state import State

from heatgraphy import UpsetData, Upset

init_page("Upsetplot")
inject_css()

s = State(key="upsetplot")
s.init_state(
    format="Sets",
    parse_success=False,
    upset_data=None,
    figure=None,
)

st.title("Upset Plot")

st.warning("Under construction", icon="🚧")

st.markdown("[What is upset plot?](https://upset.app/)")

c1, c2 = st.columns([1, 2])
with c1:
    format_options = ["Sets", "Memberships", "Binary Table"]
    format = st.radio("Your Set Format",
                      index=format_options.index(s['format']),
                      options=format_options)

with c2:
    showcase_data = upset_showcase_data()
    if format == "Sets":
        st.markdown("Items in each set.")
        st.markdown("**Example**")
        st.dataframe(showcase_data['sets'])

    elif format == "Memberships":
        st.markdown("Item belongs to which sets.")
        st.markdown("**Example**")
        st.dataframe(showcase_data['memberships'])

    else:
        st.markdown("If an item is in a set (1 or 0)")
        st.markdown("**Example**")
        st.dataframe(showcase_data['binary'])

user_input = FileUpload(key="upset",
                        use_header=True,
                        use_index=format == "Binary Table")
data = user_input.parse_dataframe()

load = st.button("Load Example")
if load:
    example = upset_example_data()
    s['upset_data'] = UpsetData(example.to_numpy(), items=example.index,
                                names=example.columns,)
    s["parse_success"] = True
    s['format'] = "Binary Table"


@st.cache_data(show_spinner=False)
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
        s["parse_success"] = True
        s['upset_data'] = upset_data
    except Exception as e:
        s["parse_success"] = False
        st.error("Failed to read set data, please select the correct"
                 "set format and check your input.", icon="🚨")

if s["parse_success"]:
    upset_data = s['upset_data']
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
            linewidth = st.number_input("Line Width", min_value=.5,
                                        value=1.5)
        with g2:
            shading = st.number_input("Shading", min_value=0.,
                                      value=.3, max_value=1.)
        with g3:
            grid_background = st.number_input("Background", min_value=0.,
                                              value=.1, max_value=1.)
        with g4:
            color = st.color_picker("Main Color", value="#111111")

        st.markdown("**Font**")
        f1, f2, f3 = st.columns(3)

        with f1:
            fontsize = st.number_input(
                "Font size", min_value=1, step=1, value=10)
        with f2:
            font_list = get_font_list()
            DEFAULT_FONT = font_list.index("Source Sans Pro")
            fontfamily = st.selectbox("Font Family", options=font_list,
                                      index=DEFAULT_FONT)
        with f3:
            fontcolor = st.color_picker("Font Color", value="#111111")

    with highlight:
        pass

    _, render_button, _ = st.columns(3)

    with render_button:
        render = st.button("Render", type="primary",
                           use_container_width=True)

    if render:
        with mpl.rc_context({'text.color': fontcolor,
                             'font.size': fontsize,
                             'font.family': fontfamily}):
            fig = plt.figure()
            up = Upset(upset_data,
                       min_size=size_range[0],
                       max_size=size_range[1],
                       min_degree=degree_range[0],
                       max_degree=degree_range[1],
                       color=color,
                       linewidth=linewidth,
                       shading=shading,
                       grid_background=grid_background
                       )
            up.render(fig)
            s['figure'] = fig

    if s['figure'] is not None:
        st.pyplot(s['figure'])

        with st.sidebar:
            ChartSaver(s['figure'])
