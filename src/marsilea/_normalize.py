"""Normalize user data into the plain arrays the plotters expect.

Nothing here knows about any particular data container. These are the fixes that
have to happen to *any* input on its way into a board -- a `scipy.sparse` matrix
handed straight to :class:`~marsilea.Heatmap`, a categorical
:class:`pandas.Series` passed to ``group_rows`` -- whether or not a data
reference was ever involved. :mod:`marsilea._sources` builds on this.

This module sits at the bottom of the import graph, alongside
:mod:`~marsilea.exceptions`: ``base`` imports ``plotter``, so anything both need
has to live below both.
"""

from __future__ import annotations

import math
import warnings

import numpy as np

from .exceptions import PerformanceWarning

# Densifying above this many cells is worth warning about: a 30k x 20k matrix is
# ~4.8 GB dense, and add_dendrogram then runs a scipy linkage over it.
_DENSE_WARN_SIZE = 50_000_000

#: Label given to entries that are missing from a categorical.
_NA_CATEGORY = "NA"


def is_sparse(obj):
    """Is `obj` a sparse matrix or array?

    Duck-typed rather than ``scipy.sparse.issparse`` so that detection and
    conversion use one predicate -- they disagreed before, and a value could be
    routed down the sparse branch by one and passed through untouched by the
    other.
    """
    return hasattr(obj, "toarray")


def densify(arr):
    """Sparse -> dense, warning when the result is large. Anything else passes through."""
    if not is_sparse(arr):
        return arr
    size = math.prod(arr.shape)
    if size > _DENSE_WARN_SIZE:
        warnings.warn(
            f"Converting a sparse {arr.shape} array to dense uses about "
            f"{size * 8 / 1e9:.1f} GB. Subset the data before plotting it.",
            PerformanceWarning,
            stacklevel=4,
        )
    return arr.toarray()


def _is_na(v):
    return v is None or (isinstance(v, float) and v != v)


def to_array(value):
    """Materialized value -> ndarray, plus its category order if it has one.

    Returns ``(array, order | None)``. Categories carry the order set with
    ``.cat.reorder_categories``, and are the only thing that makes cluster labels
    sort ``0, 1, 2, 10`` instead of ``0, 1, 10, 2``.
    """
    # A resolved reference gives a pandas Categorical; a caller passing a column
    # straight in gives a Series, which keeps its categories under ``.cat``.
    categories = getattr(value, "categories", None)
    if categories is None:
        categories = getattr(getattr(value, "cat", None), "categories", None)
    if categories is None:
        return np.asarray(densify(value)), None

    order = list(categories)
    if not any(_is_na(v) for v in value):
        # No missing values: keep the categories' own dtype. Stringifying here
        # would quietly turn an integer or interval categorical into strings.
        return np.asarray(value), order

    # With missing values present everything has to share one dtype, or
    # np.unique and sorted() raise comparing str to float. Name the gap rather
    # than crash, with a sentinel that cannot collide with a real category.
    sentinel = _NA_CATEGORY
    existing = {str(c) for c in categories}
    while sentinel in existing:
        sentinel += "_"
    arr = np.asarray([sentinel if _is_na(v) else str(v) for v in value], dtype=object)
    return arr, [str(c) for c in categories] + [sentinel]


def check_length(name, arr, shape, axis):
    """Reject data whose length does not match the board it is being added to.

    Catches the mismatch where it happens instead of at render, where the error
    `Deformation` raises is swallowed twice before it reaches the caller.

    `name` is only interpolated into the message, so callers pass whatever names
    the data best -- a reference, a column name, a plotter.
    """
    if shape is None or axis == "main" or arr.ndim == 0:
        return
    expect = shape[0] if axis == "row" else shape[1]
    got = arr.shape[-1]  # once oriented, the last axis always indexes this side
    if got != expect:
        msg = (
            f"`{name}` resolved to {got} entries along the {axis} axis, but the "
            f"board has {expect}. Did the data source change after the board was "
            f"built?"
        )
        raise ValueError(msg)
