"""Tests for resolving anndata.acc references against a board's data source."""

import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

import marsilea as ma
import marsilea.plotter as mp
from marsilea.exceptions import MisalignedRef

ad = pytest.importorskip("anndata", reason="requires the `anndata` extra")
A = pytest.importorskip("anndata.acc").A

N_OBS, N_VARS = 12, 5
# Deliberately not in lexicographic order: "10" sorts before "2".
LEIDEN = ["0", "1", "2", "10"]


@pytest.fixture
def adata(rng):
    obs = pd.DataFrame(
        {
            "leiden": pd.Categorical(
                [LEIDEN[i % 4] for i in range(N_OBS)], categories=LEIDEN
            ),
            "score": rng.random(N_OBS),
            "flag": rng.random(N_OBS) > 0.5,
        },
        index=[f"cell{i}" for i in range(N_OBS)],
    )
    var = pd.DataFrame(
        {"n_cells": rng.integers(1, 9, N_VARS)}, index=list("ABCDE")[:N_VARS]
    )
    obj = ad.AnnData(X=rng.random((N_OBS, N_VARS)), obs=obs, var=var)
    obj.layers["pct"] = rng.random((N_OBS, N_VARS))
    return obj


# --- Binding and basic resolution ---


def test_board_binds_source_positionally(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    assert h._source is adata
    assert h._cluster_data.shape == (N_OBS, N_VARS)


def test_board_binds_source_by_keyword(adata):
    h = ma.Heatmap(A.X[:, :], source=adata)
    assert h._source is adata
    assert h._cluster_data.shape == (N_OBS, N_VARS)


def test_gene_panel_stacks_into_a_matrix(adata):
    h = ma.Heatmap(adata, A.X[:, ["A", "C"]])
    assert h._cluster_data.shape == (N_OBS, 2)
    np.testing.assert_allclose(h._cluster_data[:, 0], adata[:, "A"].X.ravel())


def test_sized_heatmap_takes_two_refs(adata):
    h = ma.SizedHeatmap(adata, A.layers["pct"][:, :], A.X[:, :])
    h.render()


def test_ref_without_source_names_the_ref():
    with pytest.raises(ValueError, match=r"A\.obs\['leiden'\].*no data source"):
        ma.Heatmap(np.zeros((4, 4))).add_left(mp.Colors(A.obs["leiden"]))


# --- dims routing ---


@pytest.mark.parametrize("side", ["left", "right"])
def test_obs_ref_accepted_on_row_sides(adata, side):
    h = ma.Heatmap(adata, A.X[:, :])
    getattr(h, f"add_{side}")(mp.Colors(A.obs["leiden"]))
    h.render()


@pytest.mark.parametrize("side", ["top", "bottom"])
def test_obs_ref_rejected_on_col_sides(adata, side):
    h = ma.Heatmap(adata, A.X[:, :])
    with pytest.raises(MisalignedRef, match="spans the 'obs' axis"):
        getattr(h, f"add_{side}")(mp.Colors(A.obs["leiden"]))


@pytest.mark.parametrize("side", ["top", "bottom"])
def test_var_ref_accepted_on_col_sides(adata, side):
    h = ma.Heatmap(adata, A.X[:, :])
    getattr(h, f"add_{side}")(mp.Numbers(A.var["n_cells"]))
    h.render()


@pytest.mark.parametrize("side", ["left", "right"])
def test_var_ref_rejected_on_row_sides(adata, side):
    h = ma.Heatmap(adata, A.X[:, :])
    with pytest.raises(MisalignedRef, match="spans the 'var' axis"):
        getattr(h, f"add_{side}")(mp.Numbers(A.var["n_cells"]))


def test_obs_axis_col_flips_the_routing(adata):
    h = ma.Heatmap(adata, A.X[:, :], obs_axis="col")
    assert h._cluster_data.shape == (N_VARS, N_OBS)
    h.add_top(mp.Colors(A.obs["leiden"]))
    h.add_left(mp.Labels(A.var.index))
    h.render()

    with pytest.raises(MisalignedRef):
        ma.Heatmap(adata, A.X[:, :], obs_axis="col").add_left(
            mp.Colors(A.obs["leiden"])
        )


def test_index_refs_give_names(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.add_left(mp.Labels(A.obs.index))
    h.add_top(mp.Labels(A.var.index))
    h.render()
    assert list(h._row_plan[0].texts) == list(adata.obs_names)


def test_bad_obs_axis_is_rejected(adata):
    with pytest.raises(ValueError, match="obs_axis must be"):
        ma.Heatmap(adata, A.X[:, :], obs_axis="rows")


# --- Orientation of 2D refs ---


def test_2d_ref_orientation_follows_the_side(adata):
    top = ma.Heatmap(adata, A.X[:, :])
    top.add_top(mp.Violin(A.X[:, :]))
    left = ma.Heatmap(adata, A.X[:, :])
    left.add_left(mp.Violin(A.X[:, :]))

    on_top = top._col_plan[0].get_data()[0]
    on_left = left._row_plan[0].get_data()[0]
    # The last axis has to index the side the plot is on, so the two are
    # transposes of each other.
    assert on_top.shape == (N_OBS, N_VARS)
    assert on_left.shape == (N_VARS, N_OBS)
    np.testing.assert_allclose(on_top, on_left.T)


# --- Sparse ---


def test_sparse_x_matches_dense(adata, rng):
    dense = rng.random((N_OBS, N_VARS))
    sparse = ad.AnnData(X=sp.csr_matrix(dense), obs=adata.obs, var=adata.var)
    h = ma.Heatmap(sparse, A.X[:, :])
    np.testing.assert_allclose(h._cluster_data, dense)
    h.render()


def test_sparse_array_works_without_refs(rng):
    """`ma.Heatmap(adata.X)` must work on its own, no accessor involved."""
    dense = rng.random((6, 4))
    ma.Heatmap(sp.csr_matrix(dense)).render()


# --- Categorical order ---


def test_group_order_comes_from_categories(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.group_rows(A.obs["leiden"])
    assert list(h.get_deform().row_split_order) == LEIDEN


def test_group_order_from_plain_pandas(adata):
    """The non-ref path was mis-ordered the same way and gets the same fix."""
    h = ma.Heatmap(adata.X)
    h.group_rows(adata.obs["leiden"])
    assert list(h.get_deform().row_split_order) == LEIDEN


def test_explicit_order_still_wins(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.group_rows(A.obs["leiden"], order=["10", "2", "1", "0"])
    assert list(h.get_deform().row_split_order) == ["10", "2", "1", "0"]


def test_non_categorical_still_sorts(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.group_rows(np.array(["b", "a"] * (N_OBS // 2)))
    assert list(h.get_deform().row_split_order) == ["a", "b"]


def test_colors_legend_order_matches_chunks(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.add_left(mp.Colors(A.obs["leiden"]))
    h.group_rows(A.obs["leiden"])
    h.render()
    assert [str(c) for c in h._row_plan[0].palette] == LEIDEN


def test_unassigned_category_is_named_not_crashed(adata):
    adata.obs["part"] = pd.Categorical(
        ["a", None, "b"] * (N_OBS // 3), categories=["a", "b"]
    )
    h = ma.Heatmap(adata, A.X[:, :])
    h.add_left(mp.Colors(A.obs["part"]))
    h.group_rows(A.obs["part"])
    h.render()
    assert list(h.get_deform().row_split_order) == ["a", "b", "NA"]
    assert [str(c) for c in h._row_plan[0].palette] == ["a", "b", "NA"]


# --- Deferred construction ---


def test_recorded_calls_are_replayed(adata):
    plot = mp.ColorMesh(A.X[:, :], cmap="Blues")
    plot.set_legends(title="Expression")
    h = ma.Heatmap(adata, A.X[:, :])
    h.add_layer(plot)
    h.render()
    assert h._layer_plan[-1]._legend_kws["title"] == "Expression"


def test_deferred_is_no_more_chainable_than_the_plain_path(adata):
    """set_legends returns None on a real plotter; deferral must not differ."""
    assert mp.ColorMesh(np.zeros((2, 2))).set_legends(title="x") is None
    assert mp.ColorMesh(A.X[:, :]).set_legends(title="x") is None


def test_typo_on_a_deferred_plotter_raises_at_the_call_site():
    with pytest.raises(AttributeError, match="set_leggends"):
        mp.Colors(A.obs["leiden"]).set_leggends(title="x")


def test_plotters_survive_copy_and_pickle():
    """RenderPlan.__new__ must not break copying or pickling."""
    import copy as copy_mod
    import pickle

    plot = mp.Colors(np.array(["a", "b"]))
    assert isinstance(copy_mod.copy(plot), mp.Colors)
    assert isinstance(copy_mod.deepcopy(plot), mp.Colors)
    assert isinstance(pickle.loads(pickle.dumps(plot)), mp.Colors)


def test_plotters_without_refs_are_built_immediately():
    plot = mp.Colors(np.array(["a", "b"]))
    assert isinstance(plot, mp.Colors)


def test_ref_in_a_keyword_defers_too(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.add_layer(mp.ColorMesh(np.zeros((N_OBS, N_VARS)), mask=A.X[:, :]))
    h.render()


# --- 1D into mesh plotters ---


def test_1d_ref_into_sized_and_marker_mesh(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.add_left(mp.SizedMesh(A.obs["score"]))
    h.add_right(mp.MarkerMesh(A.obs["flag"]))
    h.render()


def test_single_gene_ref_is_an_obs_vector(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.add_left(mp.Numbers(A.X[:, "A"]))
    h.render()
    np.testing.assert_allclose(h._row_plan[0].get_data()[0], adata[:, "A"].X.ravel())


# --- Staleness and copying ---


def test_stale_source_is_caught_at_add_time(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h._source = adata[: N_OBS // 2]  # as if the caller subset it afterwards
    with pytest.raises(ValueError, match=r"A\.obs\['leiden'\].*resolved to 6"):
        h.add_left(mp.Colors(A.obs["leiden"]))


def test_stack_board_shares_the_source(adata):
    h1 = ma.Heatmap(adata, A.X[:, :])
    h2 = ma.Heatmap(adata, A.X[:, :])
    stack = ma.StackBoard([h1, h2])
    for board in stack._board_list:
        assert board._source is adata


# --- The optional dependency stays optional ---


def test_importing_marsilea_does_not_import_anndata():
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "-c", "import marsilea, sys; print('anndata' in sys.modules)"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "False"


# --- Regressions from code review ---


def test_gene_panel_is_oriented_like_any_other_2d(adata):
    """The stacked panel has to obey the same orientation rule as A.X[:, :]."""
    flipped = ma.Heatmap(adata, A.X[:, ["A", "C"]], obs_axis="col")
    assert flipped._cluster_data.shape == (2, N_OBS)

    h = ma.Heatmap(adata, A.X[:, :])
    h.add_left(mp.Violin(A.X[:, ["A", "C"]]))
    # On a row side the last axis must index rows.
    assert h._row_plan[0].get_data()[0].shape == (2, N_OBS)
    h.render()


def test_panel_of_mixed_axes_is_rejected(adata):
    with pytest.raises(ValueError, match="different axes"):
        ma.Heatmap(adata, [A.X[:, "A"], A.var["n_cells"]])


def test_category_literally_named_NA_is_not_a_missing_value():
    """Regression: this path is reachable with anndata never imported."""
    g = pd.Series(pd.Categorical(["a", "NA"] * 6, categories=["a", "NA"]))
    h = ma.Heatmap(np.zeros((12, 4)))
    h.group_rows(g)
    assert list(h.get_deform().row_split_order) == ["a", "NA"]


def test_real_nan_alongside_an_NA_category_gets_a_distinct_sentinel():
    g = pd.Series(pd.Categorical(["a", None, "NA"] * 4, categories=["a", "NA"]))
    h = ma.Heatmap(np.zeros((12, 4)))
    h.group_rows(g)
    assert list(h.get_deform().row_split_order) == ["a", "NA", "NA_"]


def test_numeric_categorical_keeps_its_dtype():
    g = pd.Series(pd.Categorical([1, 2, 3, 1] * 3, categories=[1, 2, 3]))
    h = ma.Heatmap(np.zeros((12, 4)))
    h.group_rows(g)
    order = list(h.get_deform().row_split_order)
    assert order == [1, 2, 3]
    assert all(isinstance(x, (int, np.integer)) for x in order)


def test_explicit_palette_follows_categorical_order(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h.add_left(mp.Colors(A.obs["leiden"], palette=["#111", "#222", "#333", "#444"]))
    h.group_rows(A.obs["leiden"])
    h.render()
    assert [str(c) for c in h._row_plan[0].palette] == LEIDEN


def test_error_suggests_the_other_obs_axis_not_the_current_one(adata):
    with pytest.raises(MisalignedRef, match=r'obs_axis="col"'):
        ma.Heatmap(adata, A.X[:, :]).add_left(mp.Numbers(A.var["n_cells"]))
    with pytest.raises(MisalignedRef, match=r'obs_axis="row"'):
        ma.Heatmap(adata, A.X[:, :], obs_axis="col").add_top(
            mp.Numbers(A.var["n_cells"])
        )


def test_obs_axis_is_validated_even_without_a_source():
    with pytest.raises(ValueError, match="obs_axis must be"):
        ma.Heatmap(np.zeros((3, 3)), obs_axis="banana")


def test_obs_axis_without_a_source_warns():
    with pytest.warns(UserWarning, match="no effect without a data source"):
        ma.Heatmap(np.zeros((3, 3)), obs_axis="col")


def test_stale_source_in_group_rows_names_the_ref(adata):
    h = ma.Heatmap(adata, A.X[:, :])
    h._source = adata[: N_OBS // 2]
    with pytest.raises(ValueError, match=r"A\.obs\['leiden'\].*resolved to 6"):
        h.group_rows(A.obs["leiden"])
