import pytest
import numpy as np
import marsilea as ma
import marsilea.plotter as mp
from marsilea.exceptions import DuplicatePlotter, SplitTwice


@pytest.fixture
def data_2d():
    return np.random.RandomState(0).randn(10, 8)


@pytest.fixture
def data_1d_col():
    return np.random.RandomState(0).randn(8)


@pytest.fixture
def data_1d_row():
    return np.random.RandomState(0).randn(10)


# --- WhiteBoard add_plot to sides ---


@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
def test_whiteboard_add_plot_sides(data_2d, data_1d_col, data_1d_row, side):
    wb = ma.WhiteBoard(width=4, height=3)
    if side in ("top", "bottom"):
        wb.add_plot(side, mp.Numbers(data_1d_col))
    else:
        wb.add_plot(side, mp.Numbers(data_1d_row))
    wb.render()


# --- WhiteBoard add_layer ---


def test_whiteboard_add_layer(data_2d):
    wb = ma.WhiteBoard()
    wb.add_layer(mp.ColorMesh(data_2d))
    wb.render()


# --- add_title ---


def test_add_title(data_2d):
    h = ma.Heatmap(data_2d)
    h.add_title(top="Top", left="Left")
    h.render()


# --- ClusterBoard group rows/cols ---


def test_group_rows(data_2d):
    groups = ["A"] * 5 + ["B"] * 5
    cb = ma.ClusterBoard(data_2d)
    cb.add_layer(mp.ColorMesh(data_2d))
    cb.group_rows(groups)
    cb.render()


def test_group_cols(data_2d):
    groups = ["X"] * 4 + ["Y"] * 4
    cb = ma.ClusterBoard(data_2d)
    cb.add_layer(mp.ColorMesh(data_2d))
    cb.group_cols(groups)
    cb.render()


# --- ClusterBoard cut (split) ---


def test_cut_rows(data_2d):
    cb = ma.ClusterBoard(data_2d)
    cb.add_layer(mp.ColorMesh(data_2d))
    cb.cut_rows([3, 7])
    cb.render()


def test_cut_cols(data_2d):
    cb = ma.ClusterBoard(data_2d)
    cb.add_layer(mp.ColorMesh(data_2d))
    cb.cut_cols([4])
    cb.render()


# --- Dendrograms ---


@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
def test_dendrogram_sides(data_2d, side):
    cb = ma.ClusterBoard(data_2d)
    cb.add_layer(mp.ColorMesh(data_2d))
    cb.add_dendrogram(side)
    cb.render()


# --- Error: DuplicatePlotter ---


def test_duplicate_plotter_raises(data_2d, data_1d_col):
    wb = ma.WhiteBoard()
    p = mp.Numbers(data_1d_col)
    wb.add_top(p)
    with pytest.raises(DuplicatePlotter):
        wb.add_bottom(p)


# --- Error: SplitTwice ---


def test_split_twice_raises(data_2d):
    cb = ma.ClusterBoard(data_2d)
    cb.cut_rows([3])
    with pytest.raises(SplitTwice):
        cb.cut_rows([5])


# --- add_legends ---


def test_add_legends(data_2d):
    h = ma.Heatmap(data_2d)
    h.add_legends()
    h.render()


# --- Combined: split + dendrogram + side plot ---


def test_combined_split_dendrogram_sideplot(data_2d, data_1d_col):
    cb = ma.ClusterBoard(data_2d)
    cb.add_layer(mp.ColorMesh(data_2d))
    cb.cut_cols([4])
    cb.add_dendrogram("left")
    cb.add_top(mp.Numbers(data_1d_col))
    cb.render()
