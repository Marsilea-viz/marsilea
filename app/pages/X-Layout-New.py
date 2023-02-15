import streamlit as st
from components.data_input import FileUpload
from components.state import State

s = State(
    datasets_names=[],
    datasets={}
)

st.title("X-Layout Visualization Creator")

st.header("Prepare Datasets")

file = FileUpload(key="x-layout", header=False, index=False)
data_name = st.text_input("Name")
add = st.button("Add Dataset")
if add:
    if file is not None:
        process = True
        if data_name == "":
            st.error("Please give a name to your dataset")
            process = False
        if data_name in s['datasets_names']:
            st.error("The name is already taken by other datasets")
            process = False

        if process:
            data = file.parse()
            s['datasets_names'].append(data_name)
            s['datasets'][data_name] = data


def dataset_name(name):
    return f"<span style='" \
           f"background-color: #9F353A; " \
           f"color: white; " \
           f"padding: 4px; " \
           f"margin-right: 10px;" \
           f"border-radius: 4px;'>" \
           f"{name}</span>"


used_datasets = st.multiselect("Loaded Dataset",
                               options=s['datasets_names'],
                               default=s['datasets_names'],
                               help="Select datasets for plotting"
                               )

st.markdown("---")

st.header("Main Plot")
