from typing import Any

import numpy as np
import streamlit as st

from heatgraphy import ClusterBoard
from heatgraphy.plotter import ColorMesh, SizedMesh, MarkerMesh
from .cmap_selector import ColormapSelector

IMG_ROOT = "https://raw.githubusercontent.com/" \
           "Heatgraphy/heatgraphy/main/app/img/"


class MainPlotter:
    launch = False
    data = None
    label = None
    zorder = 0

    plot_explain = ""
    example_image = None

    def __init__(self, datastorage, key):
        self.datastorage = datastorage
        self.key = key

        self.showcase()

        self.select_panel()
        self.extra_options()

    def showcase(self):
        img_col, text_col, _ = st.columns([1, 4, 3], gap="large")

        if self.plot_explain is not None:
            with text_col:
                st.markdown(self.plot_explain)

        if self.example_image is not None:
            with img_col:
                st.image(f"{IMG_ROOT}/{self.example_image}", width=100)

    def select_panel(self):
        c1, c2 = st.columns([1, 2])
        with c1:
            self.label = st.text_input("Label", key=f"{self.key}-data-label")

        with c2:
            used_dataset = st.selectbox(
                "Select Dataset",
                key=f"{self.key}-data-select",
                options=[""] + self.datastorage.get_names(subset="2d"))
            if used_dataset != "":
                data = self.datastorage.get_datasets(used_dataset)
                self.launch = self.datastorage.align_main("main", data)
                self.data = data

    def extra_options(self):
        pass

    def apply(self, h):
        pass


class MainHeatmap(MainPlotter):
    annot: bool
    fontsize: int
    linewidth: float
    cmap: Any
    norm: Any

    plot_explain = "Heatmap reveal variation through color strength."
    example_image = "heatmap.png"

    def extra_options(self):
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            st.markdown("**Display value**")
        with c2:
            disabled = False
            if self.data is not None:
                disabled = self.data.size > 1000
            self.annot = st.checkbox("Display", value=False, disabled=disabled)
        with c3:
            self.fontsize = st.number_input("Font size", min_value=1,
                                            step=1, value=6)
        self.linewidth = st.number_input("Grid line", min_value=0.)

        cmap_selector = ColormapSelector(key=self.key, default="coolwarm")
        self.cmap = cmap_selector.get_cmap()
        self.norm = cmap_selector.get_norm()

    def apply(self, h: ClusterBoard):
        if self.launch:
            mesh = ColorMesh(data=self.data,
                             cmap=self.cmap,
                             norm=self.norm,
                             linewidth=self.linewidth,
                             annot=self.annot,
                             annot_kws=dict(fontsize=self.fontsize),
                             label=self.label,
                             )
            h.add_layer(mesh, zorder=self.zorder)


MARKER_OPTIONS = {
    "Triangle": "^",
    "Triangle Down": "v",
    "Triangle Left": "<",
    "Triangle Right": ">",
    "Circle": "o",
    "Square": "s",
    "Diamond": "D",
    "Thin Diamond": "d",
    "Pentagon": "p",
    "Hexagon": "h",
    "Octagon": "8",
    "Star": "*",
    "Plus": "P",
    "Plus (stroke)": "+",
    "Cross": "X",
    "Cross (stroke)": "x",

    "Point": ".",
    "Pixel": ",",
    "Tri Down": "1",
    "Tri Up": "2",
    "Tri Left": "3",
    "Tri Right": "4",
    "Vertical Line": "|",
    "Horizontal Line": "_",
}

MARKERS = list(MARKER_OPTIONS.keys())
CIRCLE_INDEX = MARKERS.index("Circle")
CROSS_INDEX = MARKERS.index("Cross (stroke)")


class MainSizedHeatmap(MainPlotter):
    cmap = "Greens"
    color = "#BF6766"
    edgecolor = "#91989F"
    marker = "o"
    linewidth = 0.
    size_data = None
    color_data = None
    norm = None

    def showcase(self):

        c1, c2, c3, _ = st.columns([1, 1, 2, 2])
        with c1:
            st.image(f"{IMG_ROOT}/sized_onlymap.png",
                     caption="Size Only",
                     width=100)
        with c2:
            st.image(f"{IMG_ROOT}/sized_heatmap.png",
                     caption="Color + Size",
                     width=100)
        with c3:
            st.markdown(
                "Sized Heatmap encodes size as extra information in heatmap")

    def select_panel(self):
        self.label = st.text_input("Label", key=f"{self.key}-data-label")

        c1, c2 = st.columns(2)
        with c1:
            sized_dataset = st.selectbox(
                "Select Sized Dataset",
                key=f"{self.key}-data-select-size",
                options=[""] + self.datastorage.get_names(subset="2d"))

        with c2:
            color_dataset = st.selectbox(
                "Select Color Dataset (Optional)",
                key=f"{self.key}-data-select-color",
                options=[""] + self.datastorage.get_names(subset="2d"))

        if sized_dataset != "":
            self.size_data = self.datastorage.get_datasets(sized_dataset)
            check_size = self.datastorage.align_main("main", self.size_data)
            if color_dataset != "":
                self.color_data = self.datastorage.get_datasets(color_dataset)
                check_color = self.datastorage.align_main(
                    "main", self.color_data)
                if check_color:
                    self.launch = True
            if check_size:
                self.launch = True

    def extra_options(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            marker = st.selectbox(label="Shape", options=MARKERS,
                                  index=CIRCLE_INDEX)

        with c2:
            self.linewidth = st.number_input(label="Stroke size",
                                             min_value=0., value=.5)

        with c3:
            self.edgecolor = st.color_picker(label="Stroke Color",
                                             value="#C1C1C1")

        with c4:
            self.color = st.color_picker(
                label="Fill Color",
                value="#BF6766",
                help="Only works when no color data is selected"
            )

        cmap_selector = ColormapSelector(key=f"{self.key}-cmap-select",
                                         default="Greens")
        self.cmap = cmap_selector.get_cmap()
        self.norm = cmap_selector.get_norm()

        self.marker = MARKER_OPTIONS[marker]

    def apply(self, h):
        if self.launch:
            if self.color_data is None:
                color = self.color
            else:
                color = self.color_data
            mesh = SizedMesh(self.size_data,
                             color=color,
                             norm=self.norm,
                             linewidth=self.linewidth,
                             marker=self.marker,
                             cmap=self.cmap,
                             edgecolor=self.edgecolor,
                             label=self.label,
                             )
            h.add_layer(mesh, zorder=self.zorder)


class MainMark(MainPlotter):
    color = "#CB4042"
    marker = "s"
    marker_size = 30

    plot_explain = "Use a mark to mark the cell on heatmap"
    example_image = "mark_map.png"

    def select_panel(self):
        c1, c2 = st.columns([1, 2])
        with c1:
            self.label = st.text_input("Label", key=f"{self.key}-data-label")

        with c2:
            used_dataset = st.selectbox(
                "Select Dataset",
                key=f"{self.key}-data-select",
                options=[""] + self.datastorage.get_names(subset="2d"))
            if used_dataset != "":
                data = self.datastorage.get_datasets(used_dataset)
                check_shape = self.datastorage.align_main("main", data)
                check_data_type = np.array_equal(data, data.astype(bool))
                if not check_data_type:
                    st.error("Selected data must contain only 0 and 1")
                if check_shape & check_data_type:
                    self.launch = True
                self.data = data

    def extra_options(self):
        c1, c2, c3 = st.columns(3)

        with c1:
            self.color = st.color_picker("Color", value="#CB4042")

        with c2:
            marker = st.selectbox(label="Mark Shape",
                                  options=MARKERS,
                                  index=CROSS_INDEX)
            self.marker = MARKER_OPTIONS[marker]

        with c3:
            self.marker_size = st.number_input(label="size",
                                               min_value=0, value=30)

    def apply(self, h):
        if self.launch:
            mesh = MarkerMesh(self.data,
                              color=self.color,
                              marker=self.marker,
                              size=self.marker_size,
                              label=self.label,
                              )
            legend = self.label != ""
            h.add_layer(mesh, zorder=self.zorder, legend=legend)
