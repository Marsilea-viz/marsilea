import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.colors import (
    LinearSegmentedColormap,
    Normalize,
    CenteredNorm,
    TwoSlopeNorm,
)


def get_colormap(cmap):
    try:
        return mpl.colormaps.get_cmap(cmap)
    except AttributeError:
        try:
            return mpl.colormaps.get(cmap)
        except AttributeError:
            return mpl.cm.get_cmap(cmap)


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

    fig = plt.figure(figsize=(6, 0.5), dpi=90)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(gradient, aspect="auto", cmap=cmap)
    ax.set_axis_off()
    plt.close(fig)
    return fig


def random_color():
    return "#" + "".join(np.random.choice(list("0123456789ABCDEF"), 6))


class ColormapSelector:
    def __init__(self, key, default="coolwarm", data_mapping=True):
        cmap_data = get_colormap_names()
        cmap_options = sorted(cmap_data.keys())
        default_index = cmap_options.index(default)
        self.reverse = False

        st.markdown("**Colormap**")

        radio_box, rev_box = st.columns(2)

        with radio_box:
            input_cmap = st.radio(
                label="cmap_input",
                label_visibility="collapsed",
                options=["Preset", "Create New"],
                horizontal=True,
                key=f"{key}-input-cmap",
            )
        with rev_box:
            self.reverse = st.checkbox("Reverse colormap", key=f"{key}-rev-cmap")

        if input_cmap == "Preset":
            color_box, cmap_box = st.columns(2)
            with color_box:
                cmap = st.selectbox(
                    "Select Preset Colormap",
                    label_visibility="collapsed",
                    key=f"{key}-preset-cmap",
                    options=cmap_options,
                    index=default_index,
                    format_func=lambda v: cmap_data[v],
                    help="The preset colormap are illuminated "
                    "compensated for best visual effect",
                )
                cmap = get_colormap(cmap)
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
                    label="Colormap Type",
                    key=f"{key}-select-gradient",
                    label_visibility="collapsed",
                    options=["One Gradient", "Two Gradient"],
                )
            _, c_lower, c_center, c_upper = st.columns([4, 1, 1, 1])
            with c_lower:
                lower = st.color_picker(
                    label="Lower",
                    value="#CB1B45",
                    key=f"{key}-lower-cmap-2",
                )
            with c_upper:
                upper = st.color_picker(
                    label="Upper",
                    value="#7B90D2",
                    key=f"{key}-upper-cmap-2",
                )

            if ncolors == "One Gradient":
                colors = [lower, upper]
            else:
                with c_center:
                    center = st.color_picker(
                        label="Center",
                        value="#BDC0BA",
                        key=f"{key}-center-cmap-3",
                    )
                colors = [lower, center, upper]
            self.cmap = LinearSegmentedColormap.from_list("user_cmap", colors)

            if self.reverse:
                self.cmap = self.cmap.reversed()

            with cmap_box:
                cmap_fig = get_colormap_images(self.cmap)
                st.pyplot(cmap_fig)

        if data_mapping:
            norm_strategy = st.selectbox(
                "Mapping Strategy",
                key=f"{key}-norm-selector",
                options=["Linear", "Min-Max", "Centered On", "Two Range"],
            )
            self.norm = None
            if norm_strategy == "Min-Max":
                st.caption("Value outside the min/max will be mapped to min/max")
                v1, v2 = st.columns(2)
                with v1:
                    vmin = st.number_input("Min", key=f"{key}-norm-vmin")
                with v2:
                    vmax = st.number_input("Max", key=f"{key}-norm-vmax")
                self.norm = Normalize(vmin=vmin, vmax=vmax)
            elif norm_strategy == "Centered On":
                st.caption("Center on a specific value and extend symmetrically")
                v1, v2 = st.columns(2)
                with v1:
                    vcenter = st.number_input(
                        "Center", key=f"{key}-center_norm-vcenter"
                    )
                with v2:
                    vhalf = st.number_input(
                        "Extend",
                        min_value=0.0,
                        value=1.0,
                        key=f"{key}-center_norm-vhalf",
                    )
                self.norm = CenteredNorm(vcenter=vcenter, halfrange=vhalf)
            elif norm_strategy == "Two Range":
                st.caption("Map to two range")
                v1, v2, v3 = st.columns(3)
                with v1:
                    vmin = st.number_input("Min", value=0.0, key=f"{key}-tsnorm-vmin")
                with v2:
                    vcenter = st.number_input(
                        "Center", value=vmin + 1, key=f"{key}-tsnorm-vcenter"
                    )
                with v3:
                    vmax = st.number_input(
                        "Max", value=vcenter + 1, key=f"{key}-tsnorm-vmax"
                    )
                if not ((vmin < vcenter) and (vcenter < vmax)):
                    st.error("Min, Center, Max must be ascending.", icon="📉")
                else:
                    self.norm = TwoSlopeNorm(vcenter=vcenter, vmin=vmin, vmax=vmax)

    def get_cmap(self):
        return self.cmap

    def get_norm(self):
        return self.norm
