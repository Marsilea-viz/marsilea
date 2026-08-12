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


# --- Geometry ---
#
# GroupDendrogram.draw() was never exercised before. These pin the drawn
# coordinates so the height-scaling rewrite cannot move the default output.


@pytest.fixture
def group_den():
    rng = np.random.default_rng(0)
    dens = [
        Dendrogram(rng.standard_normal((n, 4)), method="average") for n in (5, 3, 6)
    ]
    return GroupDendrogram(dens, method="average")


def test_group_dendrogram_draw_golden(group_den):
    """Default output, captured before the refactor."""
    fig, ax = plt.subplots()
    group_den.draw(ax, spacing=0.05)

    assert group_den.den_ylim == pytest.approx(1.26)
    assert group_den.divider == pytest.approx(1.323)
    assert ax.get_ylim()[1] == pytest.approx(1.70667)
    assert ax.get_xlim()[1] == pytest.approx(31.111111111111)

    assert np.allclose(
        group_den._render_x_coords,
        [
            [10.430555555556, 10.430555555556, 22.736111111111, 22.736111111111],
            [2.5, 2.5, 16.583333333333, 16.583333333333],
        ],
    )
    assert np.allclose(
        group_den._render_y_coords,
        [[1.323, 1.3734, 1.3734, 1.323], [1.323, 1.6254, 1.6254, 1.3734]],
    )


def test_every_group_apex_is_pinned_to_the_same_height(group_den):
    """Documents the imbalance: per-group min-max erases real spread.

    Each base dendrogram is normalized against its own range, so a tight group
    and a diffuse one both top out at 1.2. Kept as the contrast case for the
    shared height scale.
    """
    fig, ax = plt.subplots()
    group_den.draw(ax)
    assert [d.render_root[1] for d in group_den.dens] == pytest.approx([1.2, 1.2, 1.2])


@pytest.mark.parametrize("orient", ["top", "bottom", "left", "right"])
def test_group_dendrogram_draw_orients(group_den, orient):
    fig, ax = plt.subplots()
    group_den.draw(ax, orient=orient)
    assert np.isfinite(ax.get_xlim()).all()
    assert np.isfinite(ax.get_ylim()).all()
    assert len(ax.collections) > 0


def test_meta_x_is_piecewise_linear_over_the_leaf_skeleton(group_den):
    """The meta leaves sit over the base roots; internal nodes interpolate.

    This is what keeps the dendrogram aligned with the split heatmap chunks.
    """
    fig, ax = plt.subplots()
    group_den.draw(ax, spacing=0.05)

    skeleton = 1.0 + 2.0 * np.arange(group_den.n_leaves)
    skeleton_x = [d.render_root[0] for d in group_den.dens]
    assert np.allclose(
        group_den._render_x_coords,
        np.interp(group_den.x_coords, skeleton, skeleton_x),
    )


def test_base_roots_stay_inside_their_own_slot(group_den):
    """Each base dendrogram must stay over its own heatmap chunk."""
    fig, ax = plt.subplots()
    group_den.draw(ax, spacing=0.05)
    for den in group_den.dens:
        lo, hi = den._render_xlim
        assert lo <= den.render_root[0] <= hi


# --- Degenerate inputs ---


def test_equal_merge_heights_do_not_produce_nan():
    """All merge heights equal makes the min-max interval zero."""
    data = np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [1.0, 1.0]])
    den = Dendrogram(data, method="average")
    assert not np.isnan(den.y_coords).any()
    assert np.isfinite(den.max_dependent_coord)


def test_identical_group_centroids_can_be_drawn():
    """Two groups with the same centroid merge at height zero."""
    rng = np.random.default_rng(7)
    chunk = rng.standard_normal((5, 4))
    dens = [
        Dendrogram(chunk),
        Dendrogram(chunk.copy()),
        Dendrogram(rng.standard_normal((5, 4))),
    ]
    fig, ax = plt.subplots()
    GroupDendrogram(dens).draw(ax)


@pytest.mark.xfail(reason="scipy's dendrogram() recurses per tree level", strict=True)
def test_large_dendrogram_does_not_blow_the_stack():
    """Single linkage chains, so tree depth grows with the leaf count."""
    data = np.random.default_rng(3).standard_normal((3000, 10))
    assert Dendrogram(data).n_leaves == 3000


def test_linkage_readable_with_a_singleton_group():
    import marsilea as ma

    board = ma.Heatmap(np.random.default_rng(5).standard_normal((6, 5)))
    board.group_rows(["a", "a", "a", "a", "a", "b"])
    board.add_dendrogram("left")
    board.render()

    linkages = board.get_row_linkage()
    assert set(linkages) == {"a", "b"}
    assert linkages["b"] is None
