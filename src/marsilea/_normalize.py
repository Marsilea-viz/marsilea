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
from .utils import find_stack_level

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
            stacklevel=find_stack_level(),
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


def _plural(n, unit):
    return f"{n} {unit}" if n == 1 else f"{n} {unit}s"


def check_plot_data(plot, side, axis, shape):
    """Reject plotter data that cannot align with the board it is added to.

    Boards render lazily, so a length mismatch used to surface inside
    :class:`~marsilea._deform.Deformation` with the caller's ``add_*`` line
    nowhere in the traceback. This asks the same question at the ``add_*``
    call instead.

    It asks exactly what `Deformation` asks at render: the same axis, the same
    ``shape[-1]`` rule, and the same set of plans that get a deformation at
    all. So it can only reject what the render would reject anyway.

    Parameters
    ----------
    plot : RenderPlan
        The plotter being added, already built (never a deferred one).
    side : str
        Where it is going, ``"main"`` for a layer.
    axis : {"row", "col", "main"}
        Which board axis its data indexes, from :meth:`RenderPlan.data_axis`.
    shape : tuple or None
        ``(nrow, ncol)`` of the board, or None when it has no fixed grid.

    """
    if shape is None:
        return
    if side != "main" and not plot.allow_split:
        # Never handed a deformation, so its data is drawn as given.
        return
    datasets = plot.get_data()
    if datasets is None:
        return

    name = type(plot).__name__
    for data in datasets:
        if data is None:
            continue
        try:
            arr = np.asarray(data)
        except Exception:  # ragged or exotic input; the render will speak up
            continue
        if arr.ndim == 0:
            continue
        if axis == "main":
            if arr.ndim == 2 and arr.shape != shape:
                msg = f"`{name}` has shape {arr.shape}, but the board is {shape}."
                if arr.shape == shape[::-1]:
                    msg += " That looks transposed, try `data.T`."
                raise ValueError(msg)
            continue

        expect, other = (shape[0], shape[1]) if axis == "row" else (shape[1], shape[0])
        got = arr.shape[-1]
        if got == expect:
            continue
        unit = "row" if axis == "row" else "column"
        msg = (
            f"`{name}` on {side!r} has {_plural(got, 'value')}, "
            f"but there are {_plural(expect, unit)}."
        )
        orient = getattr(plot, "orient", None)
        if orient is not None:
            # A pinned orient fixes the axis whatever side the plot is on, so
            # "try the other side" would be wrong advice here.
            msg += f" orient={orient!r} reads values along {unit}s on any side."
        elif got == other:
            # A length that fits the other axis is almost always a plot that
            # went on the wrong side.
            other_unit = "column" if axis == "row" else "row"
            sides = (
                "`add_top` or `add_bottom`"
                if axis == "row"
                else ("`add_left` or `add_right`")
            )
            msg += f" There are {_plural(other, other_unit)}, so try {sides} instead."
        else:
            msg += (
                " Left and right take one value per row, top and bottom one per column."
            )
        raise ValueError(msg)
