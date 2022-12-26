from itertools import product
import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import heatgraphy as hg
from heatgraphy.plotter import Numbers, Bar
from heatgraphy.plotter.mesh import ColorMesh, Colors, LayersMesh, \
    TextMesh, SizedMesh, MarkerMesh

COLUMN = 21
ROW = 20

main_data = np.random.randint(0, 101, (ROW, COLUMN))


def test_colormesh():
    h = hg.Heatmap(main_data)
    h.render()
    plt.close()


def test_colors():
    h = hg.CatHeatmap(main_data)
    h.render()
    plt.close()


def test_sizedmesh():
    h = hg.SizedHeatmap(main_data, main_data)
    h.render()
    plt.close()


def test_markermesh():
    data = main_data > 0
    h = hg.WhiteBoard()
    h.add_layer(MarkerMesh(data))
    h.render()
    plt.close()


def test_layersmesh_one_layer():
    one_layer = np.random.choice([1, 2, 3], (3, 5))
    pieces = {
        1: hg.layers.Rect(),
        2: hg.layers.FracRect(),
        3: hg.layers.FrameRect()
    }
    h = hg.layers.Layers(data=one_layer, pieces=pieces)
    h.render()


def test_layersmesh_multiple_layer():
    d1 = np.random.rand(3, 5) > 0
    d2 = np.random.rand(3, 5) > 0
    d3 = np.random.rand(3, 5) > 0

    pieces = [
        hg.layers.Rect(),
        hg.layers.FracRect(),
        hg.layers.FrameRect(),
    ]
    h = hg.layers.Layers(layers=[d1, d2, d3], pieces=pieces)
    h.render()

