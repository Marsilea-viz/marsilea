import streamlit as st

from .cmap_selector import ColormapSelector
from .data_input import FileUpload
from .font import FontFamily
from .transformation import Transformation

INPUT_FORMAT = "Input format: \n" \
               "- Tab-seperated file (.tsv/.txt)\n" \
               "- Comma-seperated file (.csv)\n" \
               "- Excel file (.xlsx/.xls)"


def data_ready_action(data, data_key, raw_data_key, transform_key,
                      transform_tab, viewer_tab):
    st.session_state[data_key] = data
    st.session_state[raw_data_key] = data
    if not st.session_state["data_ready"]:
        st.session_state["main_data"] = data
        st.session_state["data_ready"] = True

    with viewer_tab:
        data_anchor = st.empty()

    with transform_tab:
        reset = st.button("Reset", key=data_key + raw_data_key)
        if reset:
            st.session_state[data_key] = \
                st.session_state[raw_data_key]
        Transformation(
            transform_key,
            key=data_key + raw_data_key + "trans")

    if st.session_state[transform_key] is not None:
        action = st.session_state[transform_key]
        st.session_state[data_key] = \
            action.apply(st.session_state[raw_data_key])

    data_anchor.dataframe(st.session_state[data_key])


class HeatmapData:
    allow_text = True
    cmap = "coolwarm"
    annot = False
    linewidth = 0
    fontsize = 6

    def __init__(self):
        data_input, data_transformation, data_viewer, style = st.tabs(
            ["Input Data", "Transform", "View", "Styles"])

        with data_input:
            st.markdown(INPUT_FORMAT)
            user_input = FileUpload(key="main-data")
        data = user_input.parse()

        if data is not None:

            if data.size > 200:
                self.allow_text = False

            data_ready_action(data, "heatmap_data", "heatmap_raw_data",
                              "heatmap_transform",
                              data_transformation, data_viewer)

        with style:
            self.styles()

    def styles(self):
        annot = st.checkbox("Add Text", disabled=not self.allow_text)

        c1, c2 = st.columns(2)

        with c1:
            fontsize = st.number_input("Font size", min_value=1,
                                       step=1, value=6)
        with c2:
            grid_linewidth = st.number_input("Grid line", min_value=0.)

        cmap_selector = ColormapSelector(default="coolwarm")

        self.cmap = cmap_selector.get_cmap()
        self.annot = annot
        self.linewidth = grid_linewidth
        self.fontsize = fontsize

    def get_styles(self):
        return dict(cmap=self.cmap, annot=self.annot,
                    linewidth=self.linewidth,
                    annot_kws=dict(fontsize=self.fontsize),
                    )


marker_options = {
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

MARKERS = list(marker_options.keys())
CIRCLE_INDEX = MARKERS.index("Circle")
CROSS_INDEX = MARKERS.index("Cross (stroke)")


class SizedHeatmapData:
    cmap = "Greens"
    color = "#BF6766"
    edgecolor = "#91989F"
    marker = "o"
    linewidth = 0.

    def __init__(self):
        data_input, size_transformation, size_viewer, \
            color_transformation, color_viewer, style = st.tabs([
            "Input Data",
            "Transform (Size)",
            "View (Size)",
            "Transform(Color)",
            "View (Color)",
            "Styles"])
        with data_input:
            st.markdown(INPUT_FORMAT)
            st.markdown("**Size Data**")
            size_input = FileUpload(key="size-data")
            st.markdown("**Color Data** (optional)")
            color_input = FileUpload(key="color-data")

        size_data = size_input.parse()
        color_data = color_input.parse()

        if size_data is not None:
            data_ready_action(size_data, "size_data", "size_raw_data",
                              "size_transform",
                              size_transformation, size_viewer)
        if color_data is not None:
            data_ready_action(size_data, "color_data", "color_raw_data",
                              "color_transform",
                              color_transformation, color_viewer)

        with style:
            self.styles()

    def styles(self):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.session_state["color_data"] is not None:
                cmap_selector = ColormapSelector(default="Greens")
                self.cmap = cmap_selector.get_cmap()
            else:
                self.color = st.color_picker(label="Fill Color",
                                             value="#BF6766")

        with c2:
            self.edgecolor = st.color_picker(label="Stroke Color",
                                             value="#C1C1C1")
        with c3:
            self.linewidth = st.number_input(label="Stroke size",
                                             min_value=0., value=.5)

        with c4:
            marker = st.selectbox(label="Shape", options=MARKERS,
                                  index=CIRCLE_INDEX)

        self.marker = marker_options[marker]

    def get_styles(self):
        return dict(
            cmap=self.cmap, color=self.color,
            edgecolor=self.edgecolor,
            marker=self.marker,
            linewidth=self.linewidth,
        )


class MarkerData:
    color = "#CB4042"
    marker = "s"
    marker_size = 30

    def __init__(self):
        data_input, data_transformation, data_viewer, style = st.tabs(
            ["Input Data", "Transform", "View", "Styles"])

        with data_input:
            st.markdown(INPUT_FORMAT)
            st.markdown("The data must only contains 1 and 0 "
                        "to indicate whether to mark a cell.")
            user_input = FileUpload(key="marker-data")
        data = user_input.parse()

        if data is not None:
            st.session_state["mark_data"] = data
            st.session_state["data_ready"] = True

        with style:
            self.styles()

    def styles(self):
        c1, c2, c3 = st.columns(3)

        with c1:
            self.color = st.color_picker("Color", value="#CB4042")

        with c2:
            marker = st.selectbox(label="Mark Shape",
                                  options=MARKERS,
                                  index=CROSS_INDEX)
            self.marker = marker_options[marker]

        with c3:
            self.marker_size = st.number_input(label="size",
                                               min_value=0, value=30)

    def get_styles(self):
        return dict(
            color=self.color, marker=self.marker,
            size=self.marker_size,
        )


@st.experimental_memo
def get_font_list():
    return FontFamily().font_list


class GlobalConfig:
    cluster_name = {
        "heatmap_data": "Heatmap",
        "size_data": "Sized Data",
        "color_data": "Color Data",
        "mark_data": "Mark Data"
    }

    def __init__(self):
        self.add_legends = st.checkbox("Add Legends", value=True)
        self.cluster_data_name = st.selectbox(
            "Use which data for cluster",
            options=self.get_cluster_data_options(),
            format_func=self._format_cluster_name)

        st.markdown("Font Options")
        c1, c2 = st.columns(2)
        with c1:
            self.fontsize = st.number_input(
                "Font size", min_value=1, step=1, value=10)
        with c2:
            font_list = get_font_list()
            DEFAULT_FONT = font_list.index("Source Sans Pro")
            self.fontfamily = st.selectbox("Font Family", options=font_list,
                                           index=DEFAULT_FONT)

        st.markdown("Main Canvas Size")
        c3, c4 = st.columns(2)
        with c3:
            self.width = st.number_input("Width", min_value=1, step=1,
                                         max_value=10, value=5)
        with c4:
            self.height = st.number_input("Height", min_value=1, step=1,
                                          max_value=10, value=4)

    def _format_cluster_name(self, v):
        return self.cluster_name[v]

    def get_cluster_data_options(self):
        options = []
        if st.session_state["heatmap_data"] is not None:
            options.append("heatmap_data")
        if st.session_state["size_data"] is not None:
            options.append("size_data")
        if st.session_state["color_data"] is not None:
            options.append("color_data")
        if st.session_state["mark_data"] is not None:
            options.append("mark_data")
        return options

    def get_conf(self):
        return dict(
            cluster_data_name=self.cluster_data_name,
            fontsize=self.fontsize,
            fontfamily=self.fontfamily,
            add_legends=self.add_legends,
            width=self.width,
            height=self.height
        )
