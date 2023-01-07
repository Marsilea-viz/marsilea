import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


@st.experimental_memo
def get_colormap_names():
    cmap_mapper = {}
    for i in mpl.colormaps:
        cmap_name = i
        if i.endswith("_r"):
            cmap_name = f"{i[:-2]} (Reversed)"
        cmap_mapper[i] = cmap_name.capitalize()
    return cmap_mapper


@st.experimental_memo
def get_colormap_images(cmap):
    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))

    fig = plt.figure(figsize=(2.5, .5), dpi=90)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(gradient, aspect="auto", cmap=cmap)
    ax.set_axis_off()
    plt.close(fig)
    return fig


class ColormapSelector:

    def __init__(self, default="coolwarm"):
        cmap_data = get_colormap_names()
        cmap_options = sorted(cmap_data.keys())
        default_index = cmap_options.index(default)
        self.cmap = st.selectbox("Select Colormap",
                                 options=cmap_options,
                                 index=default_index,
                                 format_func=lambda v: cmap_data[v]
                                 )
        cmap_fig = get_colormap_images(self.cmap)
        st.pyplot(cmap_fig)

    def get_cmap(self):
        return self.cmap
