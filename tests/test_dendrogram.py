"""Tests for Dendrogram and GroupDendrogram."""

import numpy as np
import pytest
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage

from marsilea.dendrogram import Dendrogram, GroupDendrogram


@pytest.fixture
def data_5x3():
    return np.random.default_rng(42).standard_normal((5, 3))


# --- Construction ---


def test_dendrogram_basic(data_5x3):
    den = Dendrogram(data_5x3)
    assert len(den.reorder_index) == 5
    assert den.n_leaves == 5


def test_dendrogram_singleton():
    data = np.array([[1.0, 2.0, 3.0]])
    den = Dendrogram(data)
    assert den.is_singleton
    assert den.reorder_index.tolist() == [0]


def test_dendrogram_precomputed_linkage(data_5x3):
    Z = linkage(data_5x3, method="ward")
    den = Dendrogram(data_5x3, linkage=Z)
    assert len(den.reorder_index) == 5


def test_dendrogram_reorder_is_permutation(data_5x3):
    den = Dendrogram(data_5x3)
    assert sorted(den.reorder_index) == list(range(5))


def test_dendrogram_center(data_5x3):
    den = Dendrogram(data_5x3)
    assert den.center.shape == (3,)


# --- Draw ---


@pytest.mark.parametrize("orient", ["top", "bottom", "left", "right"])
def test_dendrogram_draw(data_5x3, orient):
    den = Dendrogram(data_5x3)
    fig, ax = plt.subplots()
    den._draw_dendrogram(ax, orient=orient)


# --- GroupDendrogram ---


def test_group_dendrogram():
    rng = np.random.default_rng(99)
    d1 = Dendrogram(rng.standard_normal((4, 3)))
    d2 = Dendrogram(rng.standard_normal((4, 3)))
    d3 = Dendrogram(rng.standard_normal((4, 3)))
    gd = GroupDendrogram([d1, d2, d3])
    assert gd.n == 3
    assert len(gd.dens) == 3
