from dataclasses import dataclass, field
from typing import Callable

import streamlit as st
from sklearn.preprocessing import (robust_scale, normalize,
                                   minmax_scale, StandardScaler)


@dataclass
class TransformAction:
    name: str
    func: Callable
    kwargs: dict = field(default_factory=dict)

    def apply(self, data):
        return self.func(data, **self.kwargs)


def robust():
    with st.form("Robust transform"):
        low = st.number_input("Low (%)", 0, 100, value=2, step=1)
        high = st.number_input("High (%)", 0, 100, value=98, step=1)
        apply = st.form_submit_button("Apply")
    if apply:
        st.session_state['transform'] = TransformAction(
            name="robust", func=robust_scale,
            kwargs=dict(quantile_range=(low, high)))


def standard_scaler(data):
    scaler = StandardScaler()
    scaler.fit(data)
    return scaler.transform(data)


def standard_scale():
    apply = st.button("Apply")
    if apply:
        st.session_state['transform'] = TransformAction(
            name="standard_scale", func=standard_scaler)


def norm():
    apply = st.button("Apply")
    if apply:
        st.session_state['transform'] = TransformAction(
            name="norm", func=normalize)


def transformation():
    with st.expander("Apply data transformation?"):

        reset = st.button("Reset")
        if reset:
            st.session_state["data"] = st.session_state["raw_data"]
            st.session_state["transform"] = None

        method = st.selectbox("Select transformation",
                              options=["Robust", "Standard Scale",
                                       "Normalize"])

        match method:
            case "Robust":
                robust()
            case "Standard Scale":
                standard_scale()
            case "Normalize":
                norm()
