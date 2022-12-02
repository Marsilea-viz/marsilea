import streamlit as st


def init_state(mapping):
    for key, value in mapping.items():
        if key not in st.session_state:
            st.session_state[key] = value
