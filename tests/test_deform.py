from copy import deepcopy
from itertools import product

import pytest
import numpy as np
from marsilea import Deformation

matrix = np.random.randn(7, 5)

col1d = np.array([1, 2, 3, 4, 5])
col2d = np.array([[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]])

row1d = np.array([1, 2, 3, 4, 5, 6, 7])
row2d = np.array([[1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7]])

row_cluster = [True, False]
col_cluster = [True, False]
split_row = [True, False]
split_col = [True, False]


@pytest.mark.parametrize(
    "row_cluster,col_cluster,split_row,split_col,tdata",
    product(row_cluster, col_cluster, split_row, split_col, [col1d, col2d]),
)
def test_deform_trans_col(row_cluster, col_cluster, split_row, split_col, tdata):
    deform = Deformation(matrix)
    deform.set_cluster(col=col_cluster, row=row_cluster)
    if split_col:
        deform.set_split_col([2])
    if split_row:
        deform.set_split_row([2])
    results = deform.transform_col(tdata)

    total = 0
    if isinstance(results, np.ndarray):
        total = results.size
    else:
        for i in results:
            total += i.size

    assert total == tdata.size


@pytest.mark.parametrize(
    "row_cluster,col_cluster,split_row,split_col,tdata",
    product(row_cluster, col_cluster, split_row, split_col, [row1d, row2d]),
)
def test_deform_trans_row(row_cluster, col_cluster, split_row, split_col, tdata):
    deform = Deformation(matrix)
    deform.set_cluster(col=col_cluster, row=row_cluster)
    if split_col:
        deform.set_split_col([2])
    if split_row:
        deform.set_split_row([2])
    results = deform.transform_row(tdata)

    total = 0
    if isinstance(results, np.ndarray):
        total = results.size
    else:
        for i in results:
            total += i.size

    assert total == tdata.size


@pytest.mark.parametrize(
    "row_cluster,col_cluster,split_row,split_col",
    product(row_cluster, col_cluster, split_row, split_col),
)
def test_deform_trans_both(row_cluster, col_cluster, split_row, split_col):
    deform = Deformation(matrix)
    deform.set_cluster(col=col_cluster, row=row_cluster)
    if split_col:
        deform.set_split_col([2])
    if split_row:
        deform.set_split_row([2])
    results = deform.transform(matrix)

    total = 0
    if isinstance(results, np.ndarray):
        total = results.size
    elif isinstance(results[0], np.ndarray):
        for i in results:
            total += i.size
    else:
        for row in results:
            for i in row:
                total += i.size

    assert total == matrix.size


# --- Characterization: the exact permutation, not just the element count ---
#
# The tests above only assert that no data is lost. They pass just as happily
# when rows come out in the wrong order, which is the one thing this module
# exists to get right. Everything below pins the actual permutation.

N, M = 8, 6
GEOM = np.random.default_rng(42).standard_normal((N, M))
GROUP_ROW = list("aabbbccc")
GROUP_COL = list("xxyyyy")

# Captured from the implementation before the dendrogram refactor. Keys are
# "<mode>-<row_cluster><col_cluster><split_row><split_col>" as 0/1 flags.
GOLDEN = {
    "cut-1111": ([[0, 1, 2], [5, 3, 6, 4, 7]], [[0, 1], [4, 5, 2, 3]]),
    "cut-1110": ([[0, 1, 2], [5, 3, 6, 4, 7]], [3, 1, 2, 0, 4, 5]),
    "cut-1101": ([0, 2, 5, 1, 3, 6, 4, 7], [[0, 1], [4, 5, 2, 3]]),
    "cut-1100": ([0, 2, 5, 1, 3, 6, 4, 7], [3, 1, 2, 0, 4, 5]),
    "cut-1011": ([[0, 1, 2], [5, 3, 6, 4, 7]], [[0, 1], [2, 3, 4, 5]]),
    "cut-1010": ([[0, 1, 2], [5, 3, 6, 4, 7]], [0, 1, 2, 3, 4, 5]),
    "cut-1001": ([0, 2, 5, 1, 3, 6, 4, 7], [[0, 1], [2, 3, 4, 5]]),
    "cut-1000": ([0, 2, 5, 1, 3, 6, 4, 7], [0, 1, 2, 3, 4, 5]),
    "cut-0111": ([[0, 1, 2], [3, 4, 5, 6, 7]], [[0, 1], [4, 5, 2, 3]]),
    "cut-0110": ([[0, 1, 2], [3, 4, 5, 6, 7]], [3, 1, 2, 0, 4, 5]),
    "cut-0101": ([0, 1, 2, 3, 4, 5, 6, 7], [[0, 1], [4, 5, 2, 3]]),
    "cut-0100": ([0, 1, 2, 3, 4, 5, 6, 7], [3, 1, 2, 0, 4, 5]),
    "cut-0011": ([[0, 1, 2], [3, 4, 5, 6, 7]], [[0, 1], [2, 3, 4, 5]]),
    "cut-0010": ([[0, 1, 2], [3, 4, 5, 6, 7]], [0, 1, 2, 3, 4, 5]),
    "cut-0001": ([0, 1, 2, 3, 4, 5, 6, 7], [[0, 1], [2, 3, 4, 5]]),
    "cut-0000": ([0, 1, 2, 3, 4, 5, 6, 7], [0, 1, 2, 3, 4, 5]),
    "group-1111": ([[0, 1], [4, 2, 3], [5, 6, 7]], [[0, 1], [4, 5, 2, 3]]),
    "group-1110": ([[0, 1], [4, 2, 3], [5, 6, 7]], [3, 1, 2, 0, 4, 5]),
    "group-1101": ([0, 2, 5, 1, 3, 6, 4, 7], [[0, 1], [4, 5, 2, 3]]),
    "group-1100": ([0, 2, 5, 1, 3, 6, 4, 7], [3, 1, 2, 0, 4, 5]),
    "group-1011": ([[0, 1], [4, 2, 3], [5, 6, 7]], [[0, 1], [2, 3, 4, 5]]),
    "group-1010": ([[0, 1], [4, 2, 3], [5, 6, 7]], [0, 1, 2, 3, 4, 5]),
    "group-1001": ([0, 2, 5, 1, 3, 6, 4, 7], [[0, 1], [2, 3, 4, 5]]),
    "group-1000": ([0, 2, 5, 1, 3, 6, 4, 7], [0, 1, 2, 3, 4, 5]),
    "group-0111": ([[0, 1], [2, 3, 4], [5, 6, 7]], [[0, 1], [4, 5, 2, 3]]),
    "group-0110": ([[0, 1], [2, 3, 4], [5, 6, 7]], [3, 1, 2, 0, 4, 5]),
    "group-0101": ([0, 1, 2, 3, 4, 5, 6, 7], [[0, 1], [4, 5, 2, 3]]),
    "group-0100": ([0, 1, 2, 3, 4, 5, 6, 7], [3, 1, 2, 0, 4, 5]),
    "group-0011": ([[0, 1], [2, 3, 4], [5, 6, 7]], [[0, 1], [2, 3, 4, 5]]),
    "group-0010": ([[0, 1], [2, 3, 4], [5, 6, 7]], [0, 1, 2, 3, 4, 5]),
    "group-0001": ([0, 1, 2, 3, 4, 5, 6, 7], [[0, 1], [2, 3, 4, 5]]),
    "group-0000": ([0, 1, 2, 3, 4, 5, 6, 7], [0, 1, 2, 3, 4, 5]),
}

CASES = [
    (mode, rc, cc, sr, sc)
    for mode in ("cut", "group")
    for rc, cc, sr, sc in product([True, False], repeat=4)
]


def _group_split(deform, labels, axis):
    """Reproduce what ClusterBoard.group_rows/group_cols does to a Deformation."""
    uni, idx = np.unique(labels, return_inverse=True)
    reindex = np.argsort(idx, kind="stable")
    breakpoints = np.cumsum(np.bincount(idx))[:-1]
    if axis == "row":
        deform.set_data_row_reindex(reindex)
        deform.set_split_row(breakpoints, order=uni)
    else:
        deform.set_data_col_reindex(reindex)
        deform.set_split_col(breakpoints, order=uni)


def build(mode, row_cluster, col_cluster, split_row, split_col):
    deform = Deformation(GEOM)
    deform.set_cluster(col=col_cluster, row=row_cluster)
    if mode == "cut":
        if split_row:
            deform.set_split_row([3])
        if split_col:
            deform.set_split_col([2])
    else:
        if split_row:
            _group_split(deform, GROUP_ROW, "row")
        if split_col:
            _group_split(deform, GROUP_COL, "col")
    return deform


def as_lists(result):
    if isinstance(result, np.ndarray):
        return result.tolist()
    return [np.asarray(chunk).tolist() for chunk in result]


def flatten(result):
    """Chunked or not, give back one flat order."""
    if isinstance(result, np.ndarray):
        return result.tolist()
    return [i for chunk in result for i in np.asarray(chunk).tolist()]


def case_id(case):
    mode, rc, cc, sr, sc = case
    return f"{mode}-{int(rc)}{int(cc)}{int(sr)}{int(sc)}"


@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_permutation_matches_golden(case):
    """The exact row/col order must not drift."""
    deform = build(*case)
    expect_row, expect_col = GOLDEN[case_id(case)]
    assert as_lists(deform.transform_row(np.arange(N))) == expect_row
    assert as_lists(deform.transform_col(np.arange(M))) == expect_col


@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_main_and_side_agree(case):
    """A side plot's order must equal the main canvas's order.

    This is the whole point of the module: the heatmap body and every flank
    plot are deformed by separate calls and have to land on the same rows.
    """
    deform = build(*case)
    marker = np.arange(N * M).reshape(N, M)
    body = deform.transform(marker)
    row_chunks = deform.transform_row(np.arange(N))
    col_chunks = deform.transform_col(np.arange(M))

    n_col_chunks = 1 if isinstance(col_chunks, np.ndarray) else len(col_chunks)
    blocks = [np.asarray(b) for b in ([body] if isinstance(body, np.ndarray) else body)]
    # transform flattens a 2D split row-major, so the first block of each grid
    # row carries the row order and the first grid row carries the column order
    body_rows = [i for b in blocks[::n_col_chunks] for i in (b[:, 0] // M).tolist()]
    body_cols = [j for b in blocks[:n_col_chunks] for j in (b[0, :] % M).tolist()]

    assert body_rows == flatten(row_chunks)
    assert body_cols == flatten(col_chunks)


@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_ratios_match_chunk_sizes(case):
    """Axis split ratios must match the chunk sizes the data is cut into."""
    deform = build(*case)
    for ratios, chunks, total in [
        (deform.row_ratios, deform.transform_row(np.arange(N)), N),
        (deform.col_ratios, deform.transform_col(np.arange(M)), M),
    ]:
        if ratios is None:
            assert isinstance(chunks, np.ndarray)
            continue
        assert list(ratios) == [len(c) for c in chunks]
        assert sum(ratios) == total


@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_transform_is_idempotent_and_leaves_input_alone(case):
    deform = build(*case)
    marker = np.arange(N * M).reshape(N, M)
    untouched = marker.copy()

    first = as_lists(deform.transform(marker))
    assert np.array_equal(marker, untouched), "transform mutated its input"
    assert as_lists(deform.transform(marker)) == first


def test_cluster_runs_once():
    """Clustering is the expensive part; it must stay memoized."""
    deform = build("cut", True, True, True, True)
    calls = {"row": 0, "col": 0}
    real_row, real_col = deform.cluster_row, deform.cluster_col

    def counting_row():
        calls["row"] += 1
        return real_row()

    def counting_col():
        calls["col"] += 1
        return real_col()

    deform.cluster_row, deform.cluster_col = counting_row, counting_col

    for _ in range(3):
        deform.transform(GEOM)
        deform.transform_row(np.arange(N))
        deform.transform_col(np.arange(M))
        _, _ = deform.row_ratios, deform.col_ratios

    assert calls == {"row": 1, "col": 1}


def test_instances_do_not_share_state():
    """State must be per-instance, not class-level."""
    first, second = Deformation(GEOM), Deformation(GEOM)
    first.set_cluster(row=True, method="ward")
    first.set_split_row([3])

    assert second.row_cluster_kws == {}
    assert not second.is_row_split
    assert not second.is_row_cluster
    assert second.row_breakpoints is None


def test_deepcopy_is_independent():
    """ClusterBoard deep-copies its Deformation; the copy must detach cleanly."""
    original = build("cut", True, True, False, False)
    clone = deepcopy(original)
    clone.set_split_row([3])

    assert not original.is_row_split
    assert isinstance(original.transform_row(np.arange(N)), np.ndarray)
    assert len(clone.transform_row(np.arange(N))) == 2
