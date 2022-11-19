import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# This make the nested columns available
# import components.nested_columns

st.set_page_config(
    page_title="Heatmap",
    layout="centered",
    page_icon="🎨"
)

st.markdown(
        f"""
<style>
    .main .block-container{{
        min-width: 800px;
        max-width: 1200px;
    }}
</style>
""",
        unsafe_allow_html=True,
    )

st.markdown("Try other tools: - [Upsetplot](/upset) - [Corrgram](/upset)")

st.header("Beautiful heatmap creator")


mcol1, mcol2 = st.columns([1, 2])
with mcol2:
    chart = st.empty()

with mcol1:
    tb_file = st.file_uploader("Choose a table file",
                               accept_multiple_files=False,
                               type=["txt", "csv", "xlsx", "xls"]
                               )
    if tb_file is not None:
        data = pd.read_table(tb_file)

        with st.expander("View data"):
            st.dataframe(data)

        with st.expander("Apply data transformation?"):
            method = st.selectbox("Select transformation",
                                  options=["Robust", "Standard Scale"])
            if method == "Robust":
                with st.form("Data transformation"):
                    low = st.number_input("Low (%)", 0, 100, value=2, step=1)
                    high = st.number_input("High (%)", 0, 100, value=98,
                                           step=1)
                    st.form_submit_button("Run")


if tb_file is not None:

    add_plots = st.number_input("Add plots", min_value=0, max_value=50)
    for i in range(add_plots):
        with st.form(f"Add side plotter-{i}"):
            st.selectbox("Side", options=["right", "left", "bottom", "top"])
            st.selectbox("Plot type", options=["Bar", "Colors"])
            st.form_submit_button("Add")

    fig = plt.figure()
    plt.pcolormesh(data)
    chart.pyplot(fig)
