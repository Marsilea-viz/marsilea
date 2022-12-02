import io

import streamlit as st


def save_fig(fig, dpi, format):
    img = io.BytesIO()
    fig.savefig(img, dpi=dpi, format=format, bbox_inches="tight")
    return img


def plot_saver(fig, anchor):
    with anchor:
        with st.form("Export Options"):
            dpi = st.number_input("DPI", min_value=90, value=90, max_value=600,
                                  step=10)
            format = st.selectbox("Format",
                                  options=["png", "svg", "pdf", "jpeg"],
                                  format_func=lambda x: x.upper())
            save = st.form_submit_button("Confirm")
        if save:
            img_bytes = save_fig(fig, dpi, format)
            st.download_button(
                label=f"Download Image",
                data=img_bytes,
                file_name=f"Heatmap.{format}"
            )
