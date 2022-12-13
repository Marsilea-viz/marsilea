import streamlit as st
from .cmap_picker import colormap_viewer


class Configuration:

    def __init__(self, data):
        cmap = colormap_viewer()
        disable_text = data.size > 200
        annot = st.checkbox("Add Text", disabled=disable_text)
        fontsize = st.number_input("Font size", min_value=1, step=1,
                                   value=8)
        grid_linewidth = st.number_input("Grid line", min_value=0.)