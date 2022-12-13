from dataclasses import dataclass, field
from typing import Callable

import streamlit as st
from sklearn.preprocessing import (robust_scale, normalize,
                                   minmax_scale, StandardScaler)


@dataclass
class TransformAction:
    name: str
    row: bool
    col: bool
    func: Callable
    kwargs: dict = field(default_factory=dict)

    def apply(self, data):
        if self.row:
            data = self.func(data, **self.kwargs)
        if self.col:
            data = self.func(data.T, **self.kwargs)
            data = data.T
        return data


def select_axis():
    direction = st.selectbox("Apply along",
                             options=["Row", "Column", "Both"])
    row = direction != "Column"
    col = direction != "Row"
    return row, col


def robust():
    with st.form("Robust transform"):
        low = st.number_input("Low (%)", 0, 100, value=2, step=1)
        high = st.number_input("High (%)", 0, 100, value=98, step=1)
        row, col = select_axis()
        apply = st.form_submit_button("Apply")
    if apply:
        st.session_state['transform'] = TransformAction(
            name="robust", func=robust_scale,
            kwargs=dict(quantile_range=(low, high)), row=row, col=col)


def standard_scaler(data):
    scaler = StandardScaler()
    scaler.fit(data)
    return scaler.transform(data)


def standard_scale():
    row, col = select_axis()
    apply = st.button("Apply")
    if apply:
        st.session_state['transform'] = TransformAction(
            name="standard_scale", func=standard_scaler, row=row, col=col)


def norm():
    row, col = select_axis()
    apply = st.button("Apply")
    if apply:
        st.session_state['transform'] = TransformAction(
            name="norm", func=normalize, row=row, col=col)


def transformation():

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
