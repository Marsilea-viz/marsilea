import streamlit as st
from components.initialize import init_page, inject_css

init_page("Marsilea")
inject_css()

banner, title = st.columns([1, 1.5])
with banner:
    st.markdown(
        '<video controls width="250" autoplay="true" muted="true" '
        'loop="true" playsinline style="pointer-events: none;">'
        '<source src="https://raw.githubusercontent.com/Marsilea-viz/'
        'marsilea/main/app/img/V1.mp4" '
        'type="video/mp4" /></video>',
        unsafe_allow_html=True,
    )

with title:
    st.title("Marsilea")
    st.subheader("Create :blue[composable] visualization")
    st.text("")
    st.markdown(
        "*By [Mr.Milk](https://github.com/Mr-Milk) and "
        "[Squirtle692](https://github.com/Squirtle692)*"
    )

st.markdown("---")

st.subheader("About")
st.markdown(
    "Marsilea is a tool for you to create composable visualization. "
    "A single-plot visualization can be combined with other plots to capture"
    "the full picture of your data."
)

st.markdown("---")

st.subheader("Online Toolbox")
st.text("")
t1, t2, t3 = st.columns(3)


def tools(name, img, page, size=150):
    st.markdown(
        f'<div style="display: flex; justify-content: center; '
        f'align-items: center; flex-direction: column;">'
        f'<p style="font-weight: 600;">{name}</p>'
        f'<a target="_self" href="{page}">'
        f'<img style="width: {size}px;" src="{img}"></a>'
        f"</div>",
        unsafe_allow_html=True,
    )


with t1:
    tools(
        "Simple Heatmap",
        "https://marsilea.readthedocs.io/en/latest/" "_images/concatenation-1.png",
        page="/Simple_Heatmap",
        size=130,
    )

with t2:
    tools(
        "Complex Heatmap",
        "https://marsilea.readthedocs.io/en/latest/"
        "_images/sphx_glr_plot_pbmc3k_thumb.png",
        page="X-Layout_Heatmap",
        size=200,
    )

with t3:
    tools(
        "Upset Plot",
        "https://marsilea.readthedocs.io/en/latest/"
        "_images/sphx_glr_plot_upset_thumb.png",
        page="/Upsetplot",
        size=220,
    )

st.markdown("---")


st.subheader("Python Package")
s1, s2, s3 = st.columns([1, 4, 5])
with s1:
    st.image(
        "https://cdn3.iconfinder.com/data/icons/logos-and-brands-adobe/512/267_Python-512.png",
        width=50,
    )

with s2:
    st.markdown(
        "Familiar with Python? Try our Python package "
        "that can be easily integrated into your data pipeline!"
    )
with s3:
    st.code("pip install marsilea", language="bash")

st.markdown("---")

st.markdown("Copyright © 2024 [Marsilea](https://github.com/Marsilea-viz)")
