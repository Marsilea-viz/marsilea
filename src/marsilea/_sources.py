"""Bind a data container to a board and resolve references against it.

A *source* is a data container; a *reference* names a piece of one without being
bound to it. ``A.obs["leiden"]``, ``A.X[:, :]`` and ``A.var.index`` are
references: they carry a ``dims`` set saying which axes they span, which is
exactly what a cross-layout needs. ``dims`` decides whether a plot belongs on the
rows or the columns, so putting one on the wrong side can be rejected with a real
message instead of an alignment failure at render time.

The protocol
------------

marsilea does not define an interface here -- scverse already standardized one,
and a container qualifies by satisfying four operations:

===============================  =========================================
operation                        how
===============================  =========================================
is this a source?                a registered type (see :data:`SOURCE_TYPES`)
is this a reference?             ``isinstance(obj, anndata.acc.AdRef)``
materialize                      ``source[ref]``
which axes does it span?         ``ref.dims``
===============================  =========================================

Only the first differs between containers, which is why this registers *types*
rather than adapters. :class:`~anndata.AnnData` and :class:`~mudata.MuData` both
qualify today: `mudata.acc` reuses anndata's ``AdRef`` and its accessors subclass
anndata's, so everything below already works on both.

Adding another container that speaks the protocol is one call::

    from marsilea._sources import register_source

    register_source("somepkg", "SomeContainer")

A container that does *not* speak it needs a real adapter, which is deliberately
not built for zero present callers.

Nothing here imports its containers: detection probes :data:`sys.modules`, which
is what keeps ``import marsilea`` free of anndata.
"""

from __future__ import annotations

import sys
import warnings
from functools import wraps

import numpy as np
import pandas as pd

from ._normalize import check_length, to_array
from .exceptions import MisalignedRef
from .utils import find_stack_level

#: Which board axis each container axis maps to. Keyed by *container* axis name.
AXIS_MAP_DEFAULT = {"obs": "row", "var": "col"}
AXIS_MAP_FLIPPED = {"obs": "col", "var": "row"}

#: Containers that speak the accessor protocol, as ``(module, qualname)``. Held
#: as names rather than types so that importing marsilea imports neither.
SOURCE_TYPES = [("anndata", "AnnData"), ("mudata", "MuData")]


def register_source(module, qualname):
    """Register a container type that speaks the accessor protocol.

    Parameters
    ----------
    module : str
        Import path of the module defining the container, e.g. ``"mudata"``.
    qualname : str
        Name of the container class within it, e.g. ``"MuData"``.

    Notes
    -----
    The container must satisfy all four operations in the module docstring --
    in particular ``container[ref]`` must materialize a reference. Registering a
    type that does not will fail at resolve time, not here.

    """
    entry = (module, qualname)
    if entry not in SOURCE_TYPES:
        SOURCE_TYPES.append(entry)


def axis_map(obs_axis="row"):
    """Build the container-axis -> board-axis map for ``obs_axis``."""
    if obs_axis not in ("row", "col"):
        msg = f"obs_axis must be 'row' or 'col', got {obs_axis!r}"
        raise ValueError(msg)
    return AXIS_MAP_DEFAULT if obs_axis == "row" else AXIS_MAP_FLIPPED


def _acc():
    """The `anndata.acc` module, or None.

    Probing rather than importing keeps `import marsilea` free of anndata. It is
    also exact: a reference cannot exist unless the module defining it has
    already been imported.
    """
    return sys.modules.get("anndata.acc")


def is_ref(obj):
    """Is `obj` a single data reference?"""
    acc = _acc()
    return acc is not None and isinstance(obj, acc.AdRef)


def has_ref(obj):
    """Is `obj` a reference, or a list/tuple/dict holding one?

    ``A.X[:, ["CD3E", "MS4A1"]]`` returns a *list* of references, and seaborn
    plotters accept a mapping of arrays, so containers have to be looked into.
    """
    if _acc() is None:  # no refs can exist; skip walking large containers
        return False
    if is_ref(obj):
        return True
    if isinstance(obj, (list, tuple)):
        return any(is_ref(o) for o in obj)
    if isinstance(obj, dict):
        return any(is_ref(o) for o in obj.values())
    return False


def is_source(obj):
    """Is `obj` a container a reference can be resolved against?"""
    for module, qualname in SOURCE_TYPES:
        mod = sys.modules.get(module)
        if mod is None:
            continue
        cls = getattr(mod, qualname, None)
        if cls is not None and isinstance(obj, cls):
            return True
    return False


def materialize(source, ref):
    """Pull the array a reference names out of a container."""
    return source[ref]


def axes_of(ref):
    """Which container axes a reference spans."""
    return ref.dims


def check_not_accessor(obj):
    """Reject a half-built accessor with the spelling the caller probably meant.

    ``A.obs`` and ``A.obsm["X_pca"]`` are accessors, not references -- they carry
    no index yet. Without this they reach a plotter raw and die somewhere far
    less legible.
    """
    acc = _acc()
    if acc is None or isinstance(obj, acc.AdRef):
        return
    if isinstance(obj, (acc.RefAcc, acc.MapAcc)):
        hint = {
            acc.MetaAcc: "A.obs['column']",
            acc.LayerAcc: "A.X[:, :]",
            acc.MultiAcc: "A.obsm['X_pca'][:, 0]",
            acc.GraphAcc: "A.obsp['connectivities'][:, :]",
        }.get(type(obj), "A.obs['column']")
        msg = (
            f"`{obj}` is an accessor, not a reference -- it needs an index. "
            f"Did you mean something like `{hint}`?"
        )
        raise TypeError(msg)


def _orient(arr, axis, amap):
    """Put a 2D array the right way round for where it is being drawn.

    The protocol fixes a materialized 2D reference as ``(obs, var)`` -- that is a
    property of the accessor protocol, not an assumption about one container, so
    the axis names are literal here on purpose.

    Only 2D arrays are ever transposed: on the main canvas axis 0 must be the
    board's row axis, and on a side the *last* axis has to index that side -- the
    contract ``Deformation._apply`` states ("Deform data whose last axis indexes
    this one") and the wide-format convention the seaborn plotters document.
    """
    if arr.ndim != 2:
        return arr
    if axis == "main":
        keep = amap["obs"] == "row"  # axis 0 must be the row axis
    else:
        keep = amap["obs"] != axis  # the last axis (var) must index this side
    return arr if keep else arr.T


def check_dims(ref, axis, amap, side=None):
    """Reject a 1D reference added to an axis it does not span."""
    dims = axes_of(ref)
    if len(dims) != 1 or axis == "main":
        return
    (ref_axis,) = dims
    board_axis = amap.get(ref_axis)
    if board_axis is not None and board_axis != axis:
        raise MisalignedRef(ref, ref_axis, side or axis, board_axis, amap["obs"])


def resolve(value, source, axis="main", amap=None, shape=None, side=None):
    """Materialize any references in `value` against `source`.

    Anything that is not a reference is returned untouched, so this is a no-op
    for every call that does not use one.

    Parameters
    ----------
    value : any
        A reference, a list/tuple/dict possibly holding references, or any other
        value (returned as-is).
    source : source container or None
        The container bound to the board.
    axis : {"row", "col", "main"}
        Where the resolved data is going.
    amap : dict, optional
        Container-axis -> board-axis map. Defaults to obs on rows.
    shape : tuple, optional
        ``(nrow, ncol)`` of the board, when it has one, for the length check.
    side : str, optional
        The side the plot was added to, used only to make errors name what the
        caller actually typed.

    """
    if not has_ref(value):
        return value
    if source is None:
        msg = (
            f"`{value}` is a data reference, but this board has no data source. "
            f"Build the board with the source, e.g. `ma.Heatmap(adata, {value})`."
        )
        raise ValueError(msg)
    if amap is None:
        amap = AXIS_MAP_DEFAULT

    def recurse(v):
        return resolve(v, source, axis, amap, shape, side)

    if isinstance(value, dict):
        return {k: recurse(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)) and not is_ref(value):
        # A list of 1D refs is a gene panel: A.X[:, ["CD3E", "MS4A1"]] stacks
        # into one (n_obs, n_genes) matrix. A list of anything else stays a
        # list, which is how `Layers(layers=[...])` means several arrays.
        parts = [recurse(v) for v in value]
        if all(is_ref(v) for v in value) and all(p.ndim == 1 for p in parts):
            # The elements are 1D, so _orient was a no-op on each of them; the
            # stack is what has to be oriented, exactly once, like any other 2D.
            spanned = set().union(*(axes_of(v) for v in value))
            if len(spanned) != 1:
                msg = f"Cannot stack references spanning different axes: {value}"
                raise ValueError(msg)
            stacked = np.column_stack(parts)
            # column_stack puts the shared axis first; _orient's premise is
            # (obs, var), so transpose when the shared axis is the second one.
            if spanned != {"obs"}:
                stacked = stacked.T
            stacked = _orient(stacked, axis, amap)
            check_length(value[0], stacked, shape, axis)
            return stacked
        return parts

    check_dims(value, axis, amap, side)
    arr, order = to_array(materialize(source, value))
    arr = _orient(arr, axis, amap)
    check_length(value, arr, shape, axis)
    if order is not None and arr.ndim == 1:
        # Hand back a categorical so plotters that colour by category (Colors)
        # can keep the declared order. Every other consumer treats it as an
        # array-like and is unaffected.
        return pd.Categorical(arr, categories=order)
    return arr


def resolve_group(value, source, axis, amap=None, shape=None):
    """Resolve a grouping vector, and take its order from the categories.

    Returns ``(labels, order)``. `order` is `None` unless the column is
    categorical, in which case it is the category order -- which is what makes
    ``group_rows(A.obs["leiden"])`` order clusters ``0, 1, 2, 10`` rather than
    lexicographically.

    Plain pandas input goes through here too: ``group_rows(adata.obs["leiden"])``
    has always been mis-ordered the same way.
    """
    if has_ref(value):
        if source is None:
            msg = f"`{value}` is a data reference, but this board has no data source."
            raise ValueError(msg)
        check_dims(value, axis, amap or AXIS_MAP_DEFAULT, side=f"group_{axis}s")
        ref, value = value, materialize(source, value)
        labels, order = to_array(value)
        check_length(ref, labels, shape, axis)
        return labels, order
    return to_array(value)


def accepts_source(init):
    """Let a board take a data source and references in its data arguments.

    The source is popped out of ``args`` before delegating, so every remaining
    positional lands on the parameter it always did::

        ma.Heatmap(adata, A.X[:, :])  # -> data=
        ma.SizedHeatmap(adata, A.layers["p"][:, :], A.X[:, :])  # -> size=, color=
        ma.Heatmap(A.X[:, :], source=adata)  # keyword form

    Binding is idempotent: board ``__init__``\\ s call each other through
    ``super()``, and only the call that actually carries a source may set it.
    """

    @wraps(init)
    def wrapper(self, *args, source=None, obs_axis="row", **kwargs):
        if args and is_source(args[0]):
            source, args = args[0], args[1:]
        for value in (*args, *kwargs.values()):
            check_not_accessor(value)
        # Validate unconditionally: boards absorb obs_axis whether or not they
        # have a source, so a typo would otherwise pass silently.
        amap_for_source = axis_map(obs_axis)
        if source is None and obs_axis != "row":
            warnings.warn(
                "obs_axis has no effect without a data source; pass one, e.g. "
                '`ma.Heatmap(adata, A.X[:, :], obs_axis="col")`.',
                UserWarning,
                stacklevel=find_stack_level(),
            )
        if source is not None:
            self._source = source
            self._axis_map = amap_for_source
        if self._source is not None:
            amap = self._axis_map
            args = tuple(resolve(a, self._source, "main", amap) for a in args)
            kwargs = {
                k: resolve(v, self._source, "main", amap) for k, v in kwargs.items()
            }
        return init(self, *args, **kwargs)

    return wrapper
