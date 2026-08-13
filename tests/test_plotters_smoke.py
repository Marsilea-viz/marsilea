"""Smoke tests: each plotter renders without error."""

import numpy as np
import pandas as pd
import pytest
import marsilea as ma
import marsilea.plotter as mp


@pytest.fixture
def rng():
    return np.random.default_rng(0)


@pytest.fixture
def data_2d(rng):
    return rng.standard_normal((8, 6))


@pytest.fixture
def data_1d(rng):
    return rng.standard_normal(6)


@pytest.fixture
def data_1d_row(rng):
    return rng.standard_normal(8)


@pytest.fixture
def text_1d():
    return [f"L{i}" for i in range(6)]


@pytest.fixture
def text_1d_row():
    return [f"R{i}" for i in range(8)]


# --- Numbers ---


def test_numbers(data_2d, data_1d):
    h = ma.Heatmap(data_2d)
    h.add_top(mp.Numbers(data_1d))
    h.render()


# --- StackBar ---


def test_stackbar(data_2d, rng):
    stack_data = pd.DataFrame(rng.random((3, 6)), index=["cat_a", "cat_b", "cat_c"])
    h = ma.Heatmap(data_2d)
    h.add_top(mp.StackBar(stack_data))
    h.render()


def test_stackbar_legend_default_palette(data_2d, rng):
    # The default palette is 16 colors regardless of item count; the legend must
    # trim it to the labels or legendkit rejects the length mismatch.
    stack_data = pd.DataFrame(rng.random((3, 6)), index=["cat_a", "cat_b", "cat_c"])
    h = ma.Heatmap(data_2d)
    h.add_top(mp.StackBar(stack_data))
    h.add_legends()
    h.render()


# --- CenterBar ---


def test_centerbar(data_2d, rng):
    center_data = rng.random((6, 2))  # (n_items, 2) shape
    h = ma.Heatmap(data_2d)
    h.add_top(mp.CenterBar(center_data, names=["A", "B"]))
    h.render()


# --- Labels ---


def test_labels(data_2d, text_1d):
    h = ma.Heatmap(data_2d)
    h.add_top(mp.Labels(text_1d))
    h.render()


def test_labels_left(data_2d, text_1d_row):
    h = ma.Heatmap(data_2d)
    h.add_left(mp.Labels(text_1d_row))
    h.render()


# --- Title ---


def test_title_plotter(data_2d):
    h = ma.Heatmap(data_2d)
    h.add_top(mp.Title("Top Title"))
    h.add_left(mp.Title("Left Title"))
    h.render()


# --- Chunk ---


def test_chunk(data_2d):
    h = ma.Heatmap(data_2d)
    labels = ["A"] * 3 + ["B"] * 3  # 6 cols
    h.group_cols(labels, order=["A", "B"])
    h.add_top(mp.Chunk(["A", "B"]))
    h.render()


# --- TextMesh ---


def test_textmesh(rng):
    text_data = rng.choice(list("ABCD"), (8, 6))
    wb = ma.WhiteBoard()
    wb.add_layer(mp.TextMesh(text_data))
    wb.render()


# --- AnnoLabels ---


def test_anno_labels_mark(data_2d, text_1d_row):
    # The `mark` path is numpy-API sensitive: it broke silently on a numpy bump
    # and only the docs build caught it.
    h = ma.Heatmap(data_2d)
    h.add_right(mp.AnnoLabels(text_1d_row, mark=[text_1d_row[0], text_1d_row[-1]]))
    h.render()


# --- MarkerMesh ---


def test_markermesh(rng):
    bool_data = rng.random((8, 6)) > 0.5
    wb = ma.WhiteBoard()
    wb.add_layer(mp.MarkerMesh(bool_data))
    wb.render()


# --- Area ---


def test_area(data_2d, data_1d):
    h = ma.Heatmap(data_2d)
    h.add_top(mp.Area(np.abs(data_1d)))
    h.render()


# --- Arc ---


def test_arc(data_2d):
    anchors = np.arange(6)
    links = [(0, 3), (1, 5), (2, 4)]
    h = ma.Heatmap(data_2d)
    h.add_top(mp.Arc(anchors, links))
    h.render()


# --- Range ---


def test_range(data_2d, rng):
    df = pd.DataFrame({"low": rng.random(8), "high": rng.random(8) + 1})
    h = ma.Heatmap(data_2d)
    h.add_left(mp.Range(df))
    h.render()


# --- Seaborn wrappers ---


@pytest.mark.parametrize(
    "PlotClass", [mp.Bar, mp.Box, mp.Boxen, mp.Violin, mp.Point, mp.Strip, mp.Swarm]
)
def test_seaborn_wrappers(rng, PlotClass):
    data = rng.standard_normal((8, 6))
    side_data = rng.standard_normal((3, 6))  # 3 replicates per column
    cb = ma.ClusterBoard(data)
    cb.add_layer(mp.ColorMesh(data))
    cb.add_top(PlotClass(side_data))
    cb.render()


@pytest.mark.parametrize(
    "PlotClass", [mp.Bar, mp.Box, mp.Boxen, mp.Violin, mp.Point, mp.Strip, mp.Swarm]
)
@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
@pytest.mark.parametrize("native_scale", [False, True])
def test_seaborn_cat_axis_stays_aligned(rng, PlotClass, side, native_scale):
    """The categorical axis must span one unit per category, even after an autoscale.

    Seaborn leaves autoscaling on for the categorical axis, so anything that
    triggers a rescale (an overlay, ``ax.margins``, a shared axis) used to move
    the plot out of alignment with the rest of the canvas. Under
    ``native_scale`` seaborn skips its adjustment entirely, so the span and the
    direction both have to come from us.
    """
    is_horizontal = side in ("left", "right")
    n_cat = 8 if is_horizontal else 6
    h = ma.Heatmap(rng.standard_normal((8, 6)))
    h.add_plot(
        side,
        PlotClass(rng.standard_normal((20, n_cat)), native_scale=native_scale),
        name="p",
    )
    h.render()

    ax = h.get_ax("p")
    ax.scatter([0], [0])  # an overlay requests an autoscale on the next draw
    h.figure.canvas.draw()

    lo, hi = ax.get_ylim() if is_horizontal else ax.get_xlim()
    assert abs(hi - lo) == pytest.approx(n_cat)
    # a horizontal plot runs top-to-bottom, like the rows of the main canvas
    assert (lo > hi) == is_horizontal
