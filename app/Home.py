import streamlit as st
from matplotlib.image import imread

from components.initialize import inject_css

st.set_page_config(
    page_title="Heatgraphy",
    layout="centered",
    page_icon=imread("app/img/favicon.png"),
    initial_sidebar_state="collapsed",
    menu_items={
        'Report a bug': 'https://github.com/heatgraphy/heatgraphy/issues/new/choose',
        'About': 'A web interface for Heatgraphy'
    }
)

inject_css()

banner, title = st.columns([1, 1.1], gap="medium")
with banner:
    st.video("https://www.youtube.com/watch?v=x7X9w_GIm1s")

with title:
    st.title("Heatgraphy")
    st.subheader("Create :blue[x-layout] visualization")
    st.text("")
    st.markdown(
        "*By [Mr.Milk](https://github.com/Mr-Milk) and [Squirtle692](https://github.com/Squirtle692)*")

st.markdown("---")

st.subheader("About")
st.markdown("")

st.markdown("---")

st.subheader("Online Toolbox")
st.text("")
t1, t2, t3 = st.columns(3)


def tools(name, img, size=150):
    st.markdown(
        f'<div style="display: flex; justify-content: center; align-items: center; flex-direction: column;">'
        f'<p style="font-weight: 600;">{name}</p>'
        f'<img style="width: {size}px;" src="{img}">'
        f'</div>',
        unsafe_allow_html=True)


with t1:
    tools("Simple Heatmap",
          "https://heatgraphy.readthedocs.io/en/latest/_images/customized_render-1.png")

with t2:
    tools("Upset Plot",
          "https://heatgraphy.readthedocs.io/en/latest/_images/sphx_glr_plot_upset_thumb.png",
          size=220)

with t3:
    tools("x-layout",
          "https://heatgraphy.readthedocs.io/en/latest/_images/sphx_glr_plot_pbmc3k_thumb.png",
          size=200)

st.markdown("---")


st.subheader("Python Package")
s1, s2, s3 = st.columns([1, 4, 5])
with s1:
    st.image(
        "https://cdn3.iconfinder.com/data/icons/logos-and-brands-adobe/512/267_Python-512.png",
        width=50)

with s2:
    st.markdown("Known how to program in Python? Try our Python package "
                "that can easily integrate into your data pipeline!")
with s3:

    st.code("pip install heatgraphy", language="bash")

st.markdown("---")

st.markdown("Copyright © 2023 [Heatgraphy](https://github.com/Heatgraphy)")
