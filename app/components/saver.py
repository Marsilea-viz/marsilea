import io

import streamlit as st


def save_fig(fig, dpi, format):
    img = io.BytesIO()
    fig.savefig(img, dpi=dpi, format=format, bbox_inches="tight")
    return img


class ChartSaver:
    dpi: float
    format: str

    def __init__(self):
        self.fig = st.session_state["figure"]
        with st.form("Export Options"):
            self.save_options()
            save = st.form_submit_button("Confirm")
        if save:
            st.download_button(
                label=f"Download Image",
                data=self.serialize(),
                file_name=f"Heatmap.{self.format}"
            )

    def serialize(self):
        img = io.BytesIO()
        self.fig.savefig(img, dpi=self.dpi, format=self.format,
                         bbox_inches="tight")
        return img

    def save_options(self):
        col1, col2, _ = st.columns([1, 1, 3])
        with col1:
            self.dpi = st.number_input("DPI", min_value=90, value=90,
                                       max_value=600,
                                       step=10)
        with col2:
            self.format = st.selectbox("Format",
                                       options=["png", "svg", "pdf", "jpeg"],
                                       format_func=lambda x: x.upper())
