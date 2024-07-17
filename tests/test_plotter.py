# The plotter tests should test if a plotter can be rendered
# with following combinations:
# 1. Positions: top, bottom, left, right, main
# 2. Data: 2d matrix, 1d array
# 3. Data type: list, ndarray, pandas dataframe, pandas series, xarray
# 4. Dendrogram: None, row, column, both
from functools import cached_property

import numpy as np
import pandas as pd
import pytest

import marsilea as ma
import marsilea.plotter as mp


class DataInput:

    def __init__(self, row, column):
        self.row = row
        self.column = column

        self.data_skeleton = {
            "1d_row": np.random.randn(row),
            "1d_col": np.random.randn(column),
            "2d": np.random.randn(row, column),
            "2d_1col": np.random.randn(1, column),
            "2d_1row": np.random.randn(row, 1),
            "1d_text_row": np.random.choice(list("abc"), row),
            "1d_text_col": np.random.choice(list("abc"), column),
            "2d_text": np.random.choice(list("abc"), (row, column)),
        }

    def get_data(self, key, data_type):
        data = self.data_skeleton[key]
        if data_type == "list":
            return data.tolist()
        elif data_type == "ndarray":
            return data
        elif data_type == "dataframe":
            if key in {"1d_col", "1d_text_col"}:
                return pd.DataFrame(data).T
            return pd.DataFrame(data)
        elif data_type == "series":
            if key.startswith("2d"):
                return pd.DataFrame(data)
            return pd.Series(data)
        else:
            raise ValueError(f"Unknown data type: {data_type}")


data_input = DataInput(10, 20)


class TestClusterBoardInput:
    @pytest.mark.parametrize("data_name", ["2d", "2d_1col", "2d_1row"])
    @pytest.mark.parametrize("data_type", ["ndarray", "list", "dataframe", "series"])
    def test_2d(self, data_name, data_type):
        cb = ma.ClusterBoard(data_input.get_data(data_name, data_type))
        cb.render()

    @pytest.mark.xfail(raises=ValueError, strict=True)
    @pytest.mark.parametrize("data_name", ["1d_row", "1d_col"])
    @pytest.mark.parametrize("data_type", ["ndarray", "list", "series"])
    def test_1d(self, data_name, data_type):
        cb = ma.ClusterBoard(data_input.get_data(data_name, data_type))
        cb.render()


class TestColorMesh:
    @pytest.mark.parametrize("data_name", ["2d", "2d_1col", "2d_1row"])
    @pytest.mark.parametrize("data_type", ["ndarray", "list", "dataframe", "series"])
    def test_main(self, data_name, data_type):
        data = data_input.get_data(data_name, data_type)
        cb = ma.ClusterBoard(data)
        cb.add_layer(mp.ColorMesh(data))
        cb.add_dendrogram("left")
        cb.add_dendrogram("top")
        if not data_name.endswith("col"):
            cb.group_rows(data_input.get_data("1d_text_row", "list"))
        if not data_name.endswith("row"):
            cb.group_cols(data_input.get_data("1d_text_col", "list"))
        cb.render()

    @pytest.mark.parametrize("data_name", ["2d", "2d_1row", "1d_row"])
    @pytest.mark.parametrize("data_type", ["ndarray", "dataframe", "series"])
    def test_add_flank(self, data_name, data_type):
        data = data_input.get_data(data_name, data_type)
        cb = ma.ClusterBoard(data_input.get_data("2d", "ndarray"))
        cb.add_plot("left", mp.ColorMesh(data.T))
        cb.add_plot("right", mp.ColorMesh(data.T))
        cb.render()

    @pytest.mark.parametrize("data_name", ["2d", "2d_1col", "1d_col"])
    @pytest.mark.parametrize("data_type", ["ndarray", "dataframe", "series"])
    def test_add_body(self, data_name, data_type):
        data = data_input.get_data(data_name, data_type)
        cb = ma.ClusterBoard(data_input.get_data("2d", "ndarray"))
        cb.add_plot("top", mp.ColorMesh(data))
        cb.add_plot("bottom", mp.ColorMesh(data))
        cb.render()


class TestColors:
    @pytest.mark.parametrize("data_name", ["2d", "2d_1col", "2d_1row", "2d_text"])
    @pytest.mark.parametrize("data_type", ["ndarray", "list", "dataframe", "series"])
    def test_main(self, data_name, data_type):
        data = data_input.get_data(data_name, data_type)
        if data_name.endswith("text"):
            cluster_data = data_input.get_data("2d", "ndarray")
        else:
            cluster_data = data
        cb = ma.ClusterBoard(cluster_data)
        cb.add_layer(mp.Colors(data))
        cb.add_dendrogram("left")
        cb.add_dendrogram("top")
        if not data_name.endswith("col"):
            cb.group_rows(data_input.get_data("1d_text_row", "list"))
        if not data_name.endswith("row"):
            cb.group_cols(data_input.get_data("1d_text_col", "list"))
        cb.render()

    @pytest.mark.parametrize("data_name", ["2d", "2d_1row", "1d_row", "2d_text", "1d_text_row"])
    @pytest.mark.parametrize("data_type", ["ndarray", "dataframe", "series"])
    def test_add_flank(self, data_name, data_type):
        data = data_input.get_data(data_name, data_type)
        cb = ma.ClusterBoard(data_input.get_data("2d", "ndarray"))
        cb.add_plot("left", mp.Colors(data.T))
        cb.add_plot("right", mp.Colors(data.T))
        cb.render()

    @pytest.mark.parametrize("data_name", ["2d", "2d_1col", "1d_col", "2d_text", "1d_text_col"])
    @pytest.mark.parametrize("data_type", ["ndarray", "dataframe", "series"])
    def test_add_body(self, data_name, data_type):
        data = data_input.get_data(data_name, data_type)
        cb = ma.ClusterBoard(data_input.get_data("2d", "ndarray"))
        cb.add_plot("top", mp.Colors(data))
        cb.add_plot("bottom", mp.Colors(data))
        cb.render()
