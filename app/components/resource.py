"""
Resources share by multiple pages
"""
from dataclasses import dataclass
from typing import Any

import mpl_fontkit as fk
import numpy as np
import pandas as pd
import streamlit as st

np.random.seed(0)


@st.cache_resource
def get_font_list():
    fonts = ["Source Sans Pro", "Roboto", "Open Sans", "Noto Sans", "Raleway",
             "Lato", "Montserrat", "Inter", "Oswald"]
    for f in fonts:
        fk.install(f, as_global=False)

    return fk.list_fonts()


@st.cache_data
def simple_heatmap_example_data():
    return pd.DataFrame(
        np.random.randn(5, 5) + 10,
        columns=["Apple", "Banana", "Orange", "Strawberry", "Coconut"],
        index=["Red", "Blue", "Yellow", "Green", "Black"])


@dataclass
class ExampleData:
    name: str
    data: Any


@st.cache_data
def xlayout_example_data():
    examples = []

    name = "Ex: Main Data"
    fake_data = np.random.randint(0, 100, (10, 10))
    examples.append(ExampleData(name, fake_data))

    name = "Ex: Main Mark Data"
    fake_data = np.random.randint(0, 2, (10, 10))
    examples.append(ExampleData(name, fake_data))

    name = "Ex: Unmatched Main Data"
    fake_data = np.random.randint(0, 100, (9, 9))
    examples.append(ExampleData(name, fake_data))

    name = "Ex: Side 1d"
    fake_data = np.random.randint(0, 100, 10)
    examples.append(ExampleData(name, fake_data))

    name = "Ex: Side 2d"
    fake_data = np.random.randint(0, 100, (5, 10))
    examples.append(ExampleData(name, fake_data))

    name = "Ex: H-Split"
    fake_data = np.random.choice(list("abc"), 10)
    examples.append(ExampleData(name, fake_data))

    name = "Ex: Unmatched Side Data"
    fake_data = np.random.randint(0, 100, 9)
    examples.append(ExampleData(name, fake_data))

    return examples
