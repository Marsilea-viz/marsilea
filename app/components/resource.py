"""
Resources share by multiple pages
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mpl_fontkit as fk
import numpy as np
import pandas as pd
import streamlit as st

np.random.seed(0)


@st.cache_resource
def get_font_list():
    fonts = ["Source Sans 3", "Roboto", "Open Sans", "Noto Sans", "Raleway",
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

    name = "Main Data (example)"
    fake_data = np.random.randint(0, 100, (10, 10))
    examples.append(ExampleData(name, fake_data))

    name = "Main Mark Data (example)"
    fake_data = np.random.randint(0, 2, (10, 10))
    examples.append(ExampleData(name, fake_data))

    # name = "Ex: Unmatched Main Data"
    # fake_data = np.random.randint(0, 100, (9, 9))
    # examples.append(ExampleData(name, fake_data))

    name = "Side 1d (example)"
    fake_data = np.random.randint(0, 100, 10)
    examples.append(ExampleData(name, fake_data))

    name = "Side 2d (example)"
    fake_data = np.random.randint(0, 100, (5, 10))
    examples.append(ExampleData(name, fake_data))

    name = "Partition (example)"
    fake_data = np.random.choice(["Chunk 1", "Chunk 2", "Chunk 3"], 10)
    examples.append(ExampleData(name, fake_data))

    name = "Labels (example)"
    fake_data = np.random.choice(
        ["Camel", "Walrus", "Horse", "Canary", "Hog",
         "Lamb", "Mole", "Crocodile", "Gazelle", "Cat"], 10)
    examples.append(ExampleData(name, fake_data))

    # name = "Ex: Unmatched Side Data"
    # fake_data = np.random.randint(0, 100, 9)
    # examples.append(ExampleData(name, fake_data))

    return examples


@st.cache_data
def upset_showcase_data():
    sets_df = pd.DataFrame({"Set 1": ["Item 1", "Item 2", ""],
                            "Set 2": ["Item 4", "Item 2", "Item 3"],
                            "Set 3": ["Item 9", "", ""]})
    items_df = pd.DataFrame({"Item 1": ["Set 1", "Set 2", ""],
                             "Item 2": ["Set 4", "Set 2", "Set 3"],
                             "Item 3": ["Set 9", "", ""]})

    binary_df = pd.DataFrame(data=np.random.randint(0, 2, (3, 3)),
                             index=["Item 1", "Item 2", "Item 3"],
                             columns=["Set 1", "Set 2", "Set 3"])

    return {
        'sets': sets_df,
        'memberships': items_df,
        'binary': binary_df
    }


@st.cache_data
def upset_example_data():
    return pd.read_csv(Path(__file__).parent / 'upset_example.csv', index_col=0)
