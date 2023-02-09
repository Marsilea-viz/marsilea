import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import get_cmap


@st.experimental_memo
def get_colormap_names():
    cmap_mapper = {}
    for i in mpl.colormaps:
        if not i.endswith("_r"):
            cmap_name = i
            cmap_mapper[i] = cmap_name.capitalize()
    return cmap_mapper


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
        self.reverse = False

        st.markdown("")
        st.markdown("**Choose colormap**")

        radio_box, select_box = st.columns(2)
        color_box, cmap_box = st.columns(2)

        with radio_box:
            input_cmap = st.radio(label="cmap_input",
                                  label_visibility="hidden",
                                  options=["Preset", "Customize"],
                                  horizontal=True,
                                  )
            self.reverse = st.checkbox("Reverse colormap")

        if input_cmap == "Preset":
            with select_box:
                cmap = st.selectbox("Select Preset Colormap",
                                    options=cmap_options,
                                    index=default_index,
                                    format_func=lambda v: cmap_data[v],
                                    help="The preset colormap are illuminated"
                                         "compensated for best visual effect"
                                    )
                cmap = get_cmap(cmap)
                if self.reverse:
                    cmap = cmap.reversed()
                self.cmap = cmap
            with cmap_box:
                cmap_fig = get_colormap_images(self.cmap)
                st.pyplot(cmap_fig)
        else:
            with select_box:
                ncolors = st.selectbox(
                    label="Colormap Type",
                    options=["One Gradient", "Two Gradient"])

            with color_box:
                if ncolors == "One Gradient":
                    c1, c2 = st.columns(2)
                    with c1:
                        lower = st.color_picker(label="Lower")
                    with c2:
                        upper = st.color_picker(label="Upper")
                    self.cmap = (LinearSegmentedColormap
                                 .from_list("user_cmap", [lower, upper]))
                else:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        lower = st.color_picker(label="Lower")
                    with c2:
                        center = st.color_picker(label="Center")
                    with c3:
                        upper = st.color_picker(label="Upper")
                    self.cmap = (LinearSegmentedColormap
                                 .from_list("user_cmap",
                                            [lower, center, upper]))

            if self.reverse:
                self.cmap = self.cmap.reversed()

            with cmap_box:
                cmap_fig = get_colormap_images(self.cmap)
                st.pyplot(cmap_fig)

    def get_cmap(self):
        return self.cmap
