"""Tests for LayersMesh and Piece classes."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from marsilea.layers import Rect, FracRect, FrameRect, RightTri, Marker, Layers
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


# --- Layers in ClusterBoard with split ---


def test_layers_in_clusterboard_split():
    data = np.random.default_rng(7).integers(1, 4, (6, 5))
    pieces = {1: Rect("C0"), 2: FracRect("C1"), 3: FrameRect("C2")}
    mesh = ma.layers.Layers(data=data, pieces=pieces)
    mesh.cut_rows([3])
    mesh.render()
