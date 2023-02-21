import streamlit as st

from components.initialize import init_page

init_page("Manual")

IMG_ROOT = "https://raw.githubusercontent.com/" \
           "Heatgraphy/heatgraphy/main/app/img"

st.header("Manual")

st.markdown("## What's x-layout?")

_, img, _ = st.columns((1, 2, 1))
with img:
    st.image(f"{IMG_ROOT}/x-layout.png", use_column_width=True,
             caption="Schematic of x-layout")

st.markdown(
    "Sometimes a single plot is not enough to represent the whole picture of"
    "a dataset. The idea of cross (x) layout is using plots to annotate plot, "
    "thus generate a more comprehensive representation of dataset. \n\n"
    "In the above picture, different features from the same dataset can be "
    "added as side plot to reveal unseen aspect of main feature. \n\n"
    "It's not necessary a heatmap, it can also used to create "
    "upset plot, density plot, oncoprint etc. "
    "But heatmap is indeed the most widely use case."
)

st.markdown("## How to export image?")

st.markdown("After you render the plot, "
            "an export panel will appear on the sidebar. "
            "Select your desire format and DPI to export.")

st.markdown("## I encounter an error!")

st.markdown("If an error pop up when you render the plot, "
            "try click render again. The current platform is low-resource, "
            "the render may fail from time to time. "
            "If re-render doesn't solve your problem, "
            "consider report the bug to us")

st.markdown("## How to report a bug?")

st.markdown("Click the botton on the Top Right ➡️ **Report a bug**")

st.markdown("## Can I host my own version of Heatgraphy?")

st.markdown("Sure! Check our "
            "[GitHub repository](https://github.com/heatgraphy/heatgraphy) "
            "for detail instruction.")
