import streamlit as st

st.set_page_config(
    page_title="Upset Plot"
)

st.header("Upload Files")

st.info("If you have many sets, it will be more convenient to upload it in a file.")

st.file_uploader("Choose a table file")

st.header("Input text")
sets_count = st.number_input("Number of sets", min_value=3, max_value=50)
for i in range(sets_count):
    st.text_input(f"Sets {i + 1}")


