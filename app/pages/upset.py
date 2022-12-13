import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from heatgraphy import UpsetData, Upset
from components.state import init_state

st.set_page_config(
    page_title="Upset Plot",
    initial_sidebar_state="collapsed",
    page_icon="⚗️"
)

init_state(
    upset_data=None
)

st.header("Upload Files")

st.info("If you have many sets, "
        "it will be more convenient to upload it in a file.")

mode = st.selectbox("How to input your data?", options=["Upload File", "Text"])
format = st.radio("Set Format", options=["Sets", "Memberships", "Table"])
user_input = st.file_uploader("Choose a table file",
                              accept_multiple_files=False,
                              )

if user_input:
    sets = pd.read_csv(user_input, sep="\t")
    sets_names = sets.to_numpy().T
    items_names = sets.columns
    upset_data = UpsetData.from_memberships(
        sets_names, items_names=items_names)
    st.session_state['upset_data'] = upset_data

    sets_table = pd.DataFrame(upset_data.cardinality(), columns=["size"])
    sets_table["degree"] = sets_table.index.to_frame().sum(axis=1)

    size_upper = int(sets_table['size'].max())
    degree_upper = int(sets_table['degree'].max())

    with st.form("Options"):
        size_range = st.slider("Subset Size", min_value=0,
                               value=(0, size_upper), max_value=size_upper)
        degree_range = st.slider("Degree", min_value=0,
                                 value=(0, degree_upper),
                                 max_value=degree_upper)
        color = st.color_picker("Main Color", value="#111111")
        linewidth = st.number_input("Line Width", min_value=.5, value=1.5)
        shading = st.number_input("Shading", min_value=0.,
                                  value=.3, max_value=1.)
        grid_background = st.number_input("Background", min_value=0.,
                                          value=.1, max_value=1.)
        add = st.form_submit_button(label="Confirm")

    fig = plt.figure()
    Upset(upset_data, min_size=size_range[0], max_size=size_range[1],
          min_degree=degree_range[0], max_degree=degree_range[1],
          color=color, linewidth=linewidth, shading=shading,
          grid_background=grid_background
          ).render(fig, scale=1.5)
    st.pyplot(fig)

# st.header("Input text")
# sets_count = st.number_input("Number of sets", min_value=3, max_value=50)
# for i in range(sets_count):
#     st.text_area(f"Sets {i + 1}")
