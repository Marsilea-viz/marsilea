from __future__ import annotations

from typing import Any, List

import numpy as np
import streamlit as st

from marsilea.base import ClusterBoard
from marsilea.plotter import (
    Bar,
    Box,
    Boxen,
    Colors,
    Chunk,
    Strip,
    Violin,
    Point,
    Swarm,
    AnnoLabels,
    Labels,
    Title,
)
from marsilea.plotter import RenderPlan
from .cmap_selector import ColormapSelector

IMG_ROOT = "https://raw.githubusercontent.com/" "Marsilea-viz/marsilea/main/app/img/"


class PlotAdder:
    init_size = 1.0
    init_pad = 0.05
    side: str
    size: float
    pad: float
    no_data: bool = False
    is_numeric: bool = True

    plotter: RenderPlan = None

    name: str = ""
    plot_explain: str = None
    example_image: str = None
    launch = False
    subset = None

    def __repr__(self):
        return f"Draw at {self.side} with size {self.size} and {self.pad}"

    def __init__(self, key, side, datastorage):
        self.key = key
        self.side = side
        self.plot_key = f"Add side plotter-{key}-{side}"
        self.data = None
        self.datastorage = datastorage

        if self.example_image is not None:
            img_col, text_col, _ = st.columns([1, 4, 3], gap="large")
            with img_col:
                st.image(f"{IMG_ROOT}/{self.example_image}", width=100)
            if self.plot_explain is not None:
                with text_col:
                    st.markdown(self.plot_explain)
        else:
            if self.plot_explain is not None:
                st.markdown(self.plot_explain)

        if not self.no_data:
            self.input_panel()
        self.base_elements()

        # with st.expander("More Options"):
        self.extra_options()

    def form(self):
        return st.form(self.plot_key)

    def base_elements(self):
        c1, c2, _ = st.columns([1, 1, 1])
        self.size = c1.number_input(
            "Size",
            min_value=0.1,
            key=f"{self.plot_key}_size",
            value=self.init_size,
            help="Adjust the size of this plot",
        )
        self.pad = c2.number_input(
            "Pad",
            min_value=0.0,
            key=f"{self.plot_key}_pad",
            value=self.init_pad,
            help="Adjust the space between this plot" " and the adjacent plot.",
        )

    def input_panel(self):
        used_dataset = st.selectbox(
            "Select Dataset",
            key=f"{self.plot_key}_datasets",
            options=[""] + self.datastorage.get_names(subset=self.subset),
        )

        if used_dataset != "":
            data = self.datastorage.get_datasets(used_dataset)
            self.launch = self.datastorage.align_main(self.side, data)
            self.data = data

    def extra_options(self):
        pass

    def get_options(self):
        return {}

    def apply(self, h):
        if self.launch:
            p = self.plotter(self.data, **self.get_options())
            h.add_plot(self.side, p, size=self.size, pad=self.pad)


class LabelAdder(PlotAdder):
    name = "Labels"
    plotter = Labels
    subset = "1d"

    align: str
    color: str
    pad: float

    align_options = {
        "left": ["right", "left", "center"],
        "right": ["left", "center", "right"],
        "top": ["bottom", "center", "top"],
        "bottom": ["top", "center", "bottom"],
    }

    def extra_options(self):
        c1, c2, c3 = st.columns(3)
        with c1:
            self.color = st.color_picker(
                "Text Color", key=f"{self.plot_key}_label_color"
            )
        with c2:
            self.align = st.selectbox(
                "Alignment",
                options=self.align_options[self.side],
                key=f"{self.plot_key}_label_align",
            )
        with c3:
            self.pad = st.number_input(
                "Space around text",
                min_value=0.0,
                value=0.1,
                max_value=1.0,
                key=f"{self.plot_key}_label_pad",
            )

    def get_options(self):
        return dict(align=self.align, padding=self.pad, color=self.color)


class ColorsAdder(PlotAdder):
    name = "Color Strip"
    plotter = Colors
    example_image = "colors.png"
    plot_explain = "Use colors to annotate your categorical variable"

    label: str
    cmap: Any

    def extra_options(self):
        self.label = st.text_input("Label", key=f"{self.plot_key}_colors_label")
        cmap = ColormapSelector(key=self.plot_key, default="Dark2", data_mapping=False)
        self.cmap = cmap.get_cmap()

    def get_options(self):
        return dict(label=self.label, cmap=self.cmap)


class TitleAdder(PlotAdder):
    name = "Title"
    plotter = Title
    no_data = True

    color: str
    fontsize = 10
    fontweight = "regular"
    fontstyle = "normal"

    plot_explain = "Add a title component to your plot"

    def extra_options(self):
        c1, c2, c3 = st.columns(3)
        with c1:
            self.color = st.color_picker("Title color")
        with c2:
            self.fontsize = st.number_input(
                "Title font size",
                value=10,
                min_value=5,
                max_value=20,
                key=f"{self.plot_key}_title_fontsize",
            )
        with c3:
            fontstyle = st.selectbox(
                "Title font style",
                options=["regular", "Bold", "Italic", "Bold + Italic"],
                help="Style is not available for some font",
                key=f"{self.plot_key}_title_fontstyle",
            )
        if fontstyle != "regular":
            if fontstyle != "Italic":
                self.fontweight = "bold"
            if fontstyle != "Bold":
                self.fontstyle = "italic"

    def get_options(self):
        return dict(
            color=self.color,
            fontdict=dict(
                fontweight=self.fontweight,
                fontstyle=self.fontstyle,
                fontsize=self.fontsize,
            ),
        )


class DendrogramAdder(PlotAdder):
    name = "Hierarchical clustering dendrogram"
    init_size = 0.5
    no_data = True

    method: str
    metric: str
    add_divider: bool
    add_base: bool
    add_meta: bool
    meta_color: Any
    colors: Any
    linewidth: float

    methods = [
        "single",
        "complete",
        "average",
        "weighted",
        "centroid",
        "median",
        "ward",
    ]
    metrics = [
        "euclidean",
        "minkowski",
        "cityblock",
        "sqeuclidean",
        "cosine",
        "correlation",
        "jaccard",
        "jensenshannon",
        "chebyshev",
        "canberra",
        "braycurtis",
        "mahalanobis",
    ]

    plot_explain = (
        "Perform hierarchy clustering and draw the dendrogram "
        "that represents the clustering result."
    )
    example_image = "dendrogram.svg"

    def input_panel(self):
        pass

    def extra_options(self):
        c1, c2 = st.columns(2)

        with c1:
            self.method = st.selectbox(
                "Method", options=self.methods, key=f"{self.plot_key}_dendrogram_method"
            )

        with c2:
            self.metric = st.selectbox(
                "Metric", options=self.metrics, key=f"{self.plot_key}_dendrogram_metric"
            )

        a1, a2, a3 = st.columns(3)
        with a1:
            self.add_base = st.checkbox(
                "Add base dendrogram", value=True, key=f"{self.plot_key}_add_base"
            )

        with a2:
            self.add_meta = st.checkbox(
                "Add meta dendrogram", value=True, key=f"{self.plot_key}_add_meta"
            )
        with a3:
            self.add_divider = st.checkbox(
                "Add divide line", key=f"{self.plot_key}_add_divider"
            )

        c1, c2, c3 = st.columns(3)
        with c1:
            self.colors = st.color_picker(
                "Dendrogram base color", key=f"{self.plot_key}_dendrogram_colors"
            )
        with c2:
            self.meta_color = st.color_picker(
                "Color for meta dendrogram",
                value="#113285",
                key=f"{self.plot_key}_meta_color",
            )
        with c3:
            self.linewidth = st.number_input(
                "Line Width", min_value=0.0, value=0.5, key=f"{self.plot_key}_lw"
            )

    def apply(self, h: ClusterBoard):
        h.add_dendrogram(
            self.side,
            method=self.method,
            metric=self.metric,
            add_base=self.add_base,
            add_meta=self.add_meta,
            meta_color=self.meta_color,
            colors=self.colors,
            linewidth=self.linewidth,
            add_divider=self.add_divider,
        )


STATS_INPUT_HELP = (
    "Table data: Each column corresponds to the row or column "
    "of the heatmap, depends on your side."
)


class BarAdder(PlotAdder):
    name = "Bar"
    plotter = Bar
    color: str
    errcolor: str
    errwidth: float
    capsize: float
    bar_width: float
    show_value: bool

    input_help = STATS_INPUT_HELP
    plot_explain = (
        "Bar plot use rectangles to show data, "
        "For multiple observations, estimates and errors "
        "will be shown as error bar."
    )
    example_image = "bar.png"

    def extra_options(self):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            self.color = st.color_picker(
                "Color", value="#00b796", key=f"{self.plot_key}_bar_color"
            )
        with c2:
            self.errcolor = st.color_picker(
                "Error Bar Color", value="#555555", key=f"{self.plot_key}_bar_errcolor"
            )
        with c3:
            self.errwidth = st.number_input(
                "Error Bar Width",
                value=1.0,
                min_value=0.0,
                max_value=5.0,
                key=f"{self.plot_key}_bar_errwidth",
            )
        with c4:
            self.capsize = st.number_input(
                "Error Cap Size",
                value=0.15,
                min_value=0.1,
                max_value=1.0,
                key=f"{self.plot_key}_bar_errcapsize",
            )
        with c5:
            self.bar_width = st.number_input(
                "Bar Width",
                value=0.8,
                min_value=0.1,
                max_value=1.0,
                key=f"{self.plot_key}_bar_width",
            )

    def get_options(self):
        return dict(
            color=self.color,
            errcolor=self.errcolor,
            errwidth=self.errwidth,
            capsize=self.capsize,
            width=self.bar_width,
        )


class BoxAdder(PlotAdder):
    name = "Box"
    plotter = Box
    color: str
    linewidth: float
    box_width: float

    input_help = STATS_INPUT_HELP
    plot_explain = "Box plot shows the distribution of your data"
    example_image = "box.png"

    def extra_options(self):
        c1, c2, c3 = st.columns(3)
        with c1:
            self.color = st.color_picker(
                "Color", value="#00b796", key=f"{self.plot_key}_box_color"
            )
        with c2:
            self.linewidth = st.number_input(
                "Line Width",
                value=1.0,
                min_value=0.0,
                max_value=5.0,
                key=f"{self.plot_key}_box_lw",
            )
        with c3:
            self.box_width = st.number_input(
                "Box Width",
                value=0.8,
                min_value=0.1,
                max_value=1.0,
                key=f"{self.plot_key}_box_width",
            )

    def get_options(self):
        return dict(color=self.color, linewidth=self.linewidth, width=self.box_width)


class BoxenAdder(PlotAdder):
    name = "Boxen"
    plotter = Boxen
    color: str
    linewidth: float
    box_width: float
    flier_size: float

    input_help = STATS_INPUT_HELP
    plot_explain = "An enhanced variant of box plot"
    example_image = "boxen.png"

    def extra_options(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            self.color = st.color_picker(
                "Color", value="#00b796", key=f"{self.plot_key}_boxen_color"
            )
        with c2:
            self.linewidth = st.number_input(
                "Line Width",
                value=1.0,
                min_value=0.0,
                max_value=5.0,
                key=f"{self.plot_key}_boxen_lw",
            )
        with c3:
            self.box_width = st.number_input(
                "Box Width",
                value=0.8,
                min_value=0.1,
                max_value=1.0,
                key=f"{self.plot_key}_boxen_width",
            )
        with c4:
            self.flier_size = st.number_input(
                "Flier Size", value=20, min_value=1, key=f"{self.plot_key}_flier_size"
            )

    def get_options(self):
        return dict(
            color=self.color,
            linewidth=self.linewidth,
            width=self.box_width,
            flier_kws=dict(s=self.flier_size),
        )


class PointAdder(PlotAdder):
    name = "Point"
    plotter = Point
    color: str
    linestyle: str
    errwidth: float
    capsize: float

    ls = {"No Line": "", "Straight": "-", "Dashed": "--"}

    input_help = STATS_INPUT_HELP
    plot_explain = "Similar to box plot, but use point."
    example_image = "point.png"

    def extra_options(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            self.color = st.color_picker(
                "Color", value="#00b796", key=f"{self.plot_key}_point_color"
            )
        with c2:
            linestyle = st.selectbox(
                "Line",
                options=["No Line", "Straight", "Dashed"],
                key=f"{self.plot_key}_point_linestyle",
            )
            self.linestyle = self.ls[linestyle]
        with c3:
            self.errwidth = st.number_input(
                "Error Bar Width",
                value=1.0,
                min_value=0.0,
                max_value=5.0,
                key=f"{self.plot_key}_point_errwidth",
            )
        with c4:
            self.capsize = st.number_input(
                "Error Cap Size",
                value=0.3,
                min_value=0.1,
                max_value=1.0,
                key=f"{self.plot_key}_point_capsize",
            )

    def get_options(self):
        return dict(
            color=self.color,
            linestyles=self.linestyle,
            errwidth=self.errwidth,
            capsize=self.capsize,
        )


class ViolinAdder(PlotAdder):
    name = "Violin"
    plotter = Violin
    scale: str | None
    color: str
    inner: str | None
    linewidth: float

    input_help = STATS_INPUT_HELP
    plot_explain = (
        "Violin plot is a combination of boxplot " "and kernel density estimate."
    )
    example_image = "violin.png"

    def extra_options(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            self.color = st.color_picker(
                "Color", value="#00b796", key=f"{self.plot_key}_violin_color"
            )
        with c2:
            self.scale = st.selectbox(
                "Scale Method",
                options=["area", "count", "width"],
                help="The method used to scale the width of each violin. "
                "If area, each violin will have the same area. "
                "If count, the width of the violins will be scaled by "
                "the number of observations in that bin. "
                "If width, each violin will have the same width.",
                key=f"{self.plot_key}_violin_scale",
            )
        with c3:
            self.inner = st.selectbox(
                "Violin Interior",
                options=["box", "quartile", "point", "stick"],
                key=f"{self.plot_key}_violin_inner",
            )
        with c4:
            self.linewidth = st.number_input(
                "Line Width",
                value=1.0,
                min_value=0.0,
                max_value=5.0,
                key=f"{self.plot_key}_violin_linewidth",
            )

    def get_options(self):
        return dict(
            color=self.color,
            scale=self.scale,
            inner=self.inner,
            linewidth=self.linewidth,
        )


# For Strip and Swarm
class StripAdder(PlotAdder):
    name = "Strip"
    plotter = Strip
    color: str
    marker_size: float

    input_help = STATS_INPUT_HELP
    plot_explain = "Showing the underlying distribution of your data point"
    example_image = "strip.png"

    def extra_options(self):
        c1, c2 = st.columns(2)
        with c1:
            self.color = st.color_picker(
                "Point Color", value="#00b796", key=f"{self.plot_key}_strip_color"
            )
        with c2:
            self.marker_size = st.number_input(
                "Marker Size",
                value=1.0,
                min_value=0.0,
                max_value=5.0,
                key=f"{self.plot_key}_strip_marker_size",
            )

    def get_options(self):
        return dict(
            color=self.color,
            size=self.marker_size,
        )


class SwarmAdder(StripAdder):
    name = "Swarm"
    plotter = Swarm
    example_image = "swarm.png"


# class CountAdder(PlotAdder):
#     name = "Count"
#     plotter = Count
#     color: str
#
#     plot_explain = "Show the counts of observations in each categorical."
#     example_image = "count.svg"
#
#     def extra_options(self):
#         self.color = st.color_picker("Color", value="#00b796")
#
#     def get_options(self):
#         return dict(color=self.color)


class AnnoLabelsAdder(PlotAdder):
    name = "Annotated specific labels"
    plotter = AnnoLabels
    plot_explain = "Annotate a few rows or columns."
    example_image = "annolabels.png"

    anno_texts: List[str]

    def input_panel(self):
        super().input_panel()
        options = []
        if self.data is not None:
            options = self.data.flatten()
        self.anno_texts = st.multiselect(
            "Select label to show",
            options=options,
            default=[],
            help="Label a few important columns",
            key=f"{self.plot_key}_annolabels_select",
        )

    def apply(self, h):
        p = AnnoLabels(self.data, mark=self.anno_texts, **self.get_options())
        h.add_plot(self.side, p, size=self.size, pad=self.pad)


class ChunkAdder(PlotAdder):
    name = "Chunk"
    plotter = Chunk
    plot_explain = "Annotate each of your partition"

    text_pad = 0.1
    labels = []
    colors = []

    def input_panel(self):
        current_chunks = self.datastorage.get_chunk(self.side)

        self.labels = []
        self.colors = []

        color_cols = st.columns(current_chunks)
        for ix, ccol in enumerate(color_cols):
            with ccol:
                color = st.color_picker(
                    f"Color {ix + 1}",
                    value="#fff",
                    key=f"{self.plot_key}_chunk_color_{ix}",
                )
                self.colors.append(color)

        label_cols = st.columns(current_chunks)
        for ix, lcol in enumerate(label_cols):
            with lcol:
                label = st.text_input(
                    f"Label {ix + 1}", key=f"{self.plot_key}_chunk_label_{ix}"
                )
                self.labels.append(label)

        filter_labels = [i != "" for i in self.labels]
        self.launch = np.sum(filter_labels) == current_chunks

    def extra_options(self):
        self.text_pad = st.number_input(
            "Space around text",
            min_value=0.0,
            value=0.2,
            key=f"{self.plot_key}_chunk_text_pad",
        )

    def apply(self, h):
        p = Chunk(texts=self.labels, fill_colors=self.colors, padding=self.text_pad)
        h.add_plot(self.side, p, size=self.size, pad=self.pad)


PLOTTERS = [
    DendrogramAdder,
    ColorsAdder,
    LabelAdder,
    AnnoLabelsAdder,
    TitleAdder,
    ChunkAdder,
    BarAdder,
    BoxAdder,
    BoxenAdder,
    ViolinAdder,
    # CountAdder,
    PointAdder,
    StripAdder,
    SwarmAdder,
]

PLOTTER_OPTIONS = dict(zip([p.name for p in PLOTTERS], PLOTTERS))


class SidePlotAdder:
    def __init__(self, datastorage, storage):
        self.side_options = ["right", "top", "left", "bottom"]
        tabs = st.tabs([s.capitalize() for s in self.side_options])
        for side in self.side_options:
            state_key = f"{side}_plot_counts"
            storage.add_state(state_key, 0)
        self.storage = storage
        self.datastorage = datastorage

        self.side_plotter = {}

        for side, tab in zip(self.side_options, tabs):
            self.side_plotter[side] = self.create_tab(side, tab)

    def create_tab(self, side, tab):
        state_key = f"{side}_plot_counts"

        def add_callback():
            self.storage[state_key] += 1

        def delete_callback():
            if self.storage[state_key] > 0:
                self.storage[state_key] -= 1

        with tab:
            adder, deleter, _ = st.columns([1, 2, 2.5])
            with adder:
                st.button(
                    "➕ Add One",
                    use_container_width=True,
                    key=f"{side}_add",
                    on_click=add_callback,
                )
            with deleter:
                st.button(
                    "❌ Remove Last Added",
                    use_container_width=True,
                    key=f"{side}_delete",
                    on_click=delete_callback,
                    disabled=self.storage[state_key] == 0,
                )
            plotter = []
            for i in range(self.storage[state_key]):
                p = self.add_plotter(i, side)
                plotter.append(p)
        return plotter

    def add_plotter(self, key, side):
        with st.expander(f"{side.capitalize()} plot {key + 1}", expanded=False):
            selector, _ = st.columns([1, 1])
            plot = selector.selectbox(
                "Plot type",
                options=list(PLOTTER_OPTIONS.keys()),
                label_visibility="collapsed",
                key=f"__{key}-{side}-plotter",
            )
            plotter = PLOTTER_OPTIONS[plot]
            return plotter(key, side, self.datastorage)

    def apply(self, h: ClusterBoard):
        for side in self.side_options:
            for plotter in self.side_plotter[side]:
                plotter.apply(h)


class Splitter:
    ready = False

    def __init__(self, orient, datastorage):
        self.orient = orient
        self.datastorage = datastorage
        self.how = st.selectbox(
            "How to partition",
            options=["By Position", "By Data"],
            key=f"{orient}-how-to-partition",
        )
        self.space = st.number_input(
            "Gap",
            value=1,
            min_value=0,
            max_value=100,
            key=f"{orient}-partition-space",
            help="Percentage of the canvas size",
        )

        self.cut = []
        self.dataset_name = ""
        self.order = ""
        if self.how == "By Position":
            cut = st.text_input("Example: 10,15", key=f"{orient}-partition-by-position")
            if cut != "":
                try:
                    self.cut = [int(c.strip()) for c in cut.split(",")]
                    self.ready = True
                except Exception:
                    st.error("Cannot parse your input into number, " "must be integer")
        else:
            self.dataset_name = st.selectbox(
                "Which dataset",
                key=f"{orient}-partition-select-dataset",
                options=[""] + datastorage.get_names(),
            )
            options = []
            if self.dataset_name != "":
                datasets = self.datastorage.get_datasets(self.dataset_name)
                options = np.unique(datasets)
            self.order = st.multiselect(
                "Order",
                options=options,
                default=options,
                key=f"{orient}-partition-order",
            )
            if len(self.order) != len(options):
                st.error("The order does not contain all the items", icon="🚨")
            else:
                self.ready = True
        if self.ready:
            self.datastorage.set_chunk(orient, self.get_chunks())

    def get_chunks(self) -> int:
        """Return the number of chunk the heatmap"""
        if self.how == "By Position":
            return len(self.cut) + 1
        else:
            if self.dataset_name != "":
                return len(self.order)
        return 1

    def apply(self, h: ClusterBoard):
        if not self.ready:
            return
        caller = h.hsplit if self.orient == "h" else h.vsplit
        if self.how == "By Position":
            caller(cut=self.cut, spacing=self.space / 100)
        else:
            if self.dataset_name != "":
                labels = self.datastorage.get_datasets(self.dataset_name)
                caller(labels=labels, order=self.order, spacing=self.space / 100)
