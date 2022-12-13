import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


gradient = np.linspace(0, 1, 256)
gradient = np.vstack((gradient, gradient))

cmap_list = []
for i in mpl.colormaps:
    if not i.endswith("_r"):
        cmap_list.append(i)
cmap_list.sort()

default_cmap = cmap_list.index("coolwarm")


def colormap_viewer():

    cmap = st.selectbox("Colormap", options=cmap_list, index=default_cmap)
    fig, ax = plt.subplots(figsize=(10, .5))
    ax.imshow(gradient, aspect="auto", cmap=cmap)
    ax.set_axis_off()
    st.pyplot(fig)
    return cmap
