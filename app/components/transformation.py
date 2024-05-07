from dataclasses import dataclass, field
from typing import Callable

import streamlit as st
from sklearn.preprocessing import robust_scale, normalize, StandardScaler


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


def select_axis(key=None):
    direction = st.selectbox(
        "Apply along",
        options=["Row", "Column", "Both"],
        key=f"{key} apply along",
    )
    row = direction != "Column"
    col = direction != "Row"
    return row, col


def robust(key=None):
    key = f"Robust transform {key}"
    with st.form(key):
        low = st.number_input("Low (%)", 0, 100, value=2, step=1)
        high = st.number_input("High (%)", 0, 100, value=98, step=1)
        row, col = select_axis(key=key)
        apply = st.form_submit_button("Apply")
    if apply:
        return TransformAction(
            name="robust",
            func=robust_scale,
            kwargs=dict(quantile_range=(low, high)),
            row=row,
            col=col,
        )


def standard_scaler(data):
    scaler = StandardScaler()
    scaler.fit(data)
    return scaler.transform(data)


def standard_scale(key=None):
    key = f"{key} standard_scale"
    row, col = select_axis(key=key)
    apply = st.button("Apply", key=key)
    if apply:
        return TransformAction(
            name="standard_scale", func=standard_scaler, row=row, col=col
        )


def norm(key=None):
    key = f"{key} norm"
    row, col = select_axis(key=key)
    apply = st.button("Apply", key=key)
    if apply:
        return TransformAction(name="norm", func=normalize, row=row, col=col)


class Transformation:
    dispatcher = {
        "Robust": robust,
        "Standard Scale": standard_scale,
        "Normalize": norm,
    }

    def __init__(self, session_key, key=None):
        method = st.selectbox(
            "Select transformation",
            key=key,
            options=["Robust", "Standard Scale", "Normalize"],
        )

        action = self.dispatcher[method].__call__(key=key)
        if action is not None:
            st.session_state[session_key] = action
