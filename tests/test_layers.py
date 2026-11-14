"""Tests for LayersMesh and Piece classes."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from marsilea.layers import (
    Rect,
    FracRect,
    FrameRect,
    RightTri,
    Marker,
    Layers,
    LayersMesh,
)
import marsilea as ma


# --- Individual Pieces ---


def test_rect_draw():
    p = Rect(color="red")
    artist = p.draw(0, 0, 1, 1, None)
    assert isinstance(artist, Artist)


def test_fracrect_draw():
    p = FracRect(color="blue", frac=(0.8, 0.6))
    artist = p.draw(0, 0, 1, 1, None)
    assert isinstance(artist, Artist)


def test_framerect_draw():
    p = FrameRect(color="green")
    artist = p.draw(0, 0, 1, 1, None)
    assert isinstance(artist, Artist)


def test_righttri_draw():
    p = RightTri(color="purple", right_angle="lower left")
    artist = p.draw(0, 0, 1, 1, None)
    assert isinstance(artist, Artist)


def test_marker_draw():
    fig, ax = plt.subplots()
    p = Marker("o", color="red")
    artist = p.draw(0, 0, 1, 1, ax)
    assert artist is not None


# --- Layers (single layer mode) ---


def test_layers_single():
    data = np.array([[1, 2], [3, 1]])
    pieces = {1: Rect("C0"), 2: FracRect("C1"), 3: FrameRect("C2")}
    h = Layers(data=data, pieces=pieces)
    h.render()


# --- Layers (multi-layer mode) ---


def test_layers_multi():
    rng = np.random.default_rng(0)
    d1 = rng.random((3, 4)) > 0.5
    d2 = rng.random((3, 4)) > 0.5
    pieces = [Rect("C0"), FracRect("C1")]
    h = Layers(layers=[d1, d2], pieces=pieces)
    h.render()


# --- set_legends ---


def test_layersmesh_set_legends():
    # LayersMesh holds `_legend_kws` but used to inherit the RenderPlan stub
    pieces = {1: Rect("C0"), 2: FracRect("C1"), 3: FrameRect("C2")}
    mesh = LayersMesh(data=np.array([[1, 2], [3, 1]]), pieces=pieces)
    mesh.set_legends(title="Pieces", frameon=True)
    # new options merge into the constructor defaults, they do not replace them
    assert mesh._legend_kws == dict(
        frameon=True, handlelength=1, handleheight=1, title="Pieces"
    )


# --- Layers in ClusterBoard with split ---


def test_layers_in_clusterboard_split():
    data = np.random.default_rng(7).integers(1, 4, (6, 5))
    pieces = {1: Rect("C0"), 2: FracRect("C1"), 3: FrameRect("C2")}
    mesh = ma.layers.Layers(data=data, pieces=pieces)
    mesh.cut_rows([3])
    mesh.render()


def _right_angle_corner(tri):
    # The right-angle vertex is the one shared by the two legs, i.e. the one
    # whose x matches one neighbour and whose y matches the other.
    pts = tri.get_xy()[:3]
    for i, (x, y) in enumerate(pts):
        others = np.delete(pts, i, axis=0)
        if np.isclose(others[:, 0], x).any() and np.isclose(others[:, 1], y).any():
            return x, y
    raise AssertionError("not a right triangle")


def test_righttri_corner_follows_inverted_axis():
    # LayersMesh inverts the y-axis, so "lower" must be the larger y there,
    # matching what the legend (drawn on a normal axis) shows.
    _, ax = plt.subplots()
    ax.set_ylim(0, 1)
    p = RightTri(right_angle="lower left")
    assert _right_angle_corner(p.draw(0, 0, 1, 1, ax)) == (0, 0)
    ax.invert_yaxis()
    assert _right_angle_corner(p.draw(0, 0, 1, 1, ax)) == (0, 1)
    p = RightTri(right_angle="upper right")
    assert _right_angle_corner(p.draw(0, 0, 1, 1, ax)) == (1, 0)
    plt.close("all")


def test_righttri_in_layers_matches_legend():
    p = RightTri(color="red", right_angle="lower left")
    h = Layers(layers=[np.ones((1, 1), dtype=bool)], pieces=[p])
    h.render()
    ax = h.get_main_ax()
    (tri,) = [a for a in ax.get_children() if a.__class__.__name__ == "Polygon"]
    # y-axis is inverted, so the lower-left corner of the cell is (0, 1)
    assert ax.yaxis_inverted()
    assert _right_angle_corner(tri) == (0, 1)
    plt.close("all")
