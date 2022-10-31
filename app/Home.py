import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Heatmap"
)

st.header("Beautiful heatmap creator")

tb_file = st.file_uploader("Choose a table file",
                           accept_multiple_files=False,
                           type=["txt", "csv", "xlsx", "xls"]
                           )

if tb_file is not None:
    data = pd.read_table(tb_file)

    st.dataframe(data)

    fig = plt.figure()
    plt.pcolormesh(data)
    st.pyplot(fig)
