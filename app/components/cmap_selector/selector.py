import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.cm import get_cmap
from matplotlib.colors import LinearSegmentedColormap


@st.cache_data
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

    fig = plt.figure(figsize=(6, .5), dpi=90)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(gradient, aspect="auto", cmap=cmap)
    ax.set_axis_off()
    plt.close(fig)
    return fig


def random_color():
    return "#" + "".join(np.random.choice(list('0123456789ABCDEF'), 6))


class ColormapSelector:

    def __init__(self, key, default="coolwarm"):
        cmap_data = get_colormap_names()
        cmap_options = sorted(cmap_data.keys())
        default_index = cmap_options.index(default)
        self.reverse = False

        st.markdown("**Colormap**")

        radio_box, rev_box = st.columns(2)

        with radio_box:
            input_cmap = st.radio(label="cmap_input",
                                  label_visibility="collapsed",
                                  options=["Preset", "Create New"],
                                  horizontal=True,
                                  key=f'{key}-input-cmap'
                                  )
        with rev_box:
            self.reverse = st.checkbox("Reverse colormap",
                                       key=f'{key}-rev-cmap')

        if input_cmap == "Preset":
            color_box, cmap_box = st.columns(2)
            with color_box:
                cmap = st.selectbox("Select Preset Colormap",
                                    label_visibility="collapsed",
                                    key=f'{key}-preset-cmap',
                                    options=cmap_options,
                                    index=default_index,
                                    format_func=lambda v: cmap_data[v],
                                    help="The preset colormap are illuminated "
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
            select_box, cmap_box = st.columns(2)
            with select_box:
                ncolors = st.selectbox(
                    label="Colormap Type", key=f'{key}-select-gradient',
                    label_visibility="collapsed",
                    options=["One Gradient", "Two Gradient"])
            _, c_lower, c_center, c_upper = st.columns([4, 1, 1, 1])
            with c_lower:
                lower = st.color_picker(label="Lower",
                                        value="#CB1B45",
                                        key=f'{key}-lower-cmap-2', )
            with c_upper:
                upper = st.color_picker(label="Upper",
                                        value="#7B90D2",
                                        key=f'{key}-upper-cmap-2', )

            if ncolors == "One Gradient":
                colors = [lower, upper]
            else:
                with c_center:
                    center = st.color_picker(label="Center",
                                             value="#BDC0BA",
                                             key=f'{key}-center-cmap-3', )
                colors = [lower, center, upper]
            self.cmap = (LinearSegmentedColormap
                         .from_list("user_cmap", colors))

            if self.reverse:
                self.cmap = self.cmap.reversed()

            with cmap_box:
                cmap_fig = get_colormap_images(self.cmap)
                st.pyplot(cmap_fig)

    def get_cmap(self):
        return self.cmap
