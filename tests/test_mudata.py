"""MuData as a second container behind the same accessor protocol.

These tests exist to prove the source registry is really a seam and not an
abstraction with one implementation: nothing in `marsilea._sources` is
MuData-aware beyond one entry in `SOURCE_TYPES`, because `mudata.acc` reuses
anndata's `AdRef` and `MuData.__getitem__` already resolves it.
"""

import numpy as np
import pandas as pd
import pytest

import marsilea as ma
import marsilea.plotter as mp
from marsilea._sources import SOURCE_TYPES, is_source, register_source
from marsilea.exceptions import MisalignedRef

ad = pytest.importorskip("anndata", reason="requires the `anndata` extra")
md = pytest.importorskip("mudata", reason="requires mudata")
A = pytest.importorskip("mudata.acc").A

N_OBS, N_RNA, N_ADT = 9, 4, 3
CELLTYPES = ["a", "b", "c"]


@pytest.fixture
def mdata(rng):
    names = [f"cell{i}" for i in range(N_OBS)]
    rna = ad.AnnData(
        X=rng.random((N_OBS, N_RNA)),
        obs=pd.DataFrame(index=names),
        var=pd.DataFrame(index=[f"gene{i}" for i in range(N_RNA)]),
    )
    adt = ad.AnnData(
        X=rng.random((N_OBS, N_ADT)),
        obs=pd.DataFrame(index=names),
        var=pd.DataFrame(index=[f"prot{i}" for i in range(N_ADT)]),
    )
    obj = md.MuData({"rna": rna, "adt": adt})
    obj.obs["celltype"] = pd.Categorical(CELLTYPES * 3, categories=CELLTYPES)
    return obj


def test_mudata_is_recognised_as_a_source(mdata):
    assert is_source(mdata)


def test_board_binds_a_mudata(mdata):
    h = ma.Heatmap(mdata, A.mod["rna"].X[:, :])
    assert h._source is mdata
    assert h._cluster_data.shape == (N_OBS, N_RNA)


def test_obs_ref_resolves_against_a_mudata(mdata):
    h = ma.Heatmap(mdata, A.mod["rna"].X[:, :])
    h.add_left(mp.Colors(A.obs["celltype"]))
    h.add_left(mp.Labels(A.obs.index))
    h.render()
    assert list(h._row_plan[1].texts) == list(mdata.obs_names)


def test_dims_routing_behaves_exactly_as_for_anndata(mdata):
    h = ma.Heatmap(mdata, A.mod["rna"].X[:, :])
    with pytest.raises(MisalignedRef, match="spans the 'obs' axis"):
        h.add_top(mp.Colors(A.obs["celltype"]))


def test_obs_axis_flip_works_for_mudata(mdata):
    h = ma.Heatmap(mdata, A.mod["rna"].X[:, :], obs_axis="col")
    assert h._cluster_data.shape == (N_RNA, N_OBS)
    h.add_top(mp.Colors(A.obs["celltype"]))
    h.render()


def test_categorical_order_carries_over(mdata):
    h = ma.Heatmap(mdata, A.mod["rna"].X[:, :])
    h.group_rows(A.obs["celltype"])
    assert list(h.get_deform().row_split_order) == CELLTYPES


def test_two_modalities_on_one_board(mdata):
    """The case MuData exists for: modalities share obs, so they align."""
    h = ma.Heatmap(mdata, A.mod["rna"].X[:, :])
    h.add_left(mp.Colors(A.obs["celltype"]))
    h.add_right(mp.ColorMesh(A.mod["adt"].X[:, :]))
    h.render()
    # add_right indexes rows, so the last axis must be obs.
    assert h._row_plan[1].get_data()[0].shape == (N_ADT, N_OBS)


# --- The registry itself ---


def test_register_source_extends_detection():
    class Fake:
        pass

    assert not is_source(Fake())
    before = list(SOURCE_TYPES)
    try:
        register_source(Fake.__module__, "Fake")
        # Detection probes sys.modules, so the class must be reachable by name.
        import sys

        setattr(sys.modules[Fake.__module__], "Fake", Fake)
        assert is_source(Fake())
    finally:
        SOURCE_TYPES[:] = before
    assert not is_source(Fake())


def test_register_source_is_idempotent():
    before = len(SOURCE_TYPES)
    register_source("anndata", "AnnData")  # already present
    assert len(SOURCE_TYPES) == before


def test_unregistered_container_is_not_a_source():
    assert not is_source(np.zeros((3, 3)))
    assert not is_source(pd.DataFrame({"a": [1, 2]}))
