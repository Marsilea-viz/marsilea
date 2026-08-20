import warnings
from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from .dendrogram import Dendrogram, GroupDendrogram
from .utils import find_stack_level, pairwise

_ROW, _COL = 0, 1


@dataclass(frozen=True)
class _Plan:
    """One axis resolved into where every element ends up.

    ``index`` is a flat permutation of the axis and ``bounds`` marks the chunk
    boundaries within it, so deforming anything is a take followed by slices.
    """

    index: np.ndarray
    bounds: np.ndarray


@dataclass
class _AxisState:
    """Everything Deformation tracks about one axis."""

    n: int
    is_split: bool = False
    is_cluster: bool = False
    clustered: bool = False
    reindex: Any = None
    breakpoints: Any = None
    split_order: Any = None
    dendrogram: Any = None
    linkage: Any = None  # User supplied linkage
    meta_linkage: Any = None
    use_meta: bool = True
    reorder_index: Any = None
    chunk_index: Any = None
    cluster_kws: dict = field(default_factory=dict)
    plan: Any = None

    def invalidate(self):
        self.clustered = False
        self.plan = None


class _AxisAttr:
    """Forward ``Deformation.<row|col>_<name>`` to its per-axis state."""

    __slots__ = ("axis", "field")

    def __init__(self, axis, field):
        self.axis = axis
        self.field = field

    def __get__(self, obj, owner=None):
        if obj is None:
            return self
        return getattr(obj._axes[self.axis], self.field)

    def __set__(self, obj, value):
        setattr(obj._axes[self.axis], self.field, value)


def _forward_axis_attrs(cls):
    """Keep the public row_*/col_* names while the state lives per axis."""
    for template, attr in [
        ("is_{}_split", "is_split"),
        ("is_{}_cluster", "is_cluster"),
        ("_{}_clustered", "clustered"),
        ("data_{}_reindex", "reindex"),
        ("{}_breakpoints", "breakpoints"),
        ("{}_split_order", "split_order"),
        ("{}_dendrogram", "dendrogram"),
        ("{}_linkage", "linkage"),
        ("{}_meta_linkage", "meta_linkage"),
        ("_use_{}_meta", "use_meta"),
        ("{}_reorder_index", "reorder_index"),
        ("{}_chunk_index", "chunk_index"),
        ("{}_cluster_kws", "cluster_kws"),
    ]:
        setattr(cls, template.format("row"), _AxisAttr(_ROW, attr))
        setattr(cls, template.format("col"), _AxisAttr(_COL, attr))
    return cls


@_forward_axis_attrs
class Deformation:
    """A helper class to handle data

    #. Split the data based on index
    #. Reorder the data based on label order
    #. Reorder the data based on cluster order
    #. Compute the ratio to split axes that match with data

    """

    def __init__(self, data):
        self._axes = (_AxisState(0), _AxisState(0))
        # just for storage
        self.wspace = 0
        self.hspace = 0
        self.set_data(data)

    @property
    def _nrow(self):
        return self._axes[_ROW].n

    @property
    def _ncol(self):
        return self._axes[_COL].n

    def set_data(self, data):
        self.data = data
        self._axes[_ROW].n, self._axes[_COL].n = data.shape
        for state in self._axes:
            state.invalidate()

    def _set_reindex(self, axis, reindex):
        state = self._axes[axis]
        if len(reindex) != state.n:
            msg = (
                f"Length of reindex ({len(reindex)}) should match "
                f"data {'row' if axis == _ROW else 'col'} with "
                f"{state.n} elements"
            )
            raise ValueError(msg)
        state.reindex = reindex
        state.invalidate()

    def set_data_row_reindex(self, reindex):
        self._set_reindex(_ROW, reindex)

    def set_data_col_reindex(self, reindex):
        self._set_reindex(_COL, reindex)

    def set_cluster(
        self,
        col=None,
        row=None,
        use_meta=True,
        linkage=None,
        meta_linkage=None,
        **kwargs,
    ):
        for axis, cluster in ((_COL, col), (_ROW, row)):
            if cluster is None:
                continue
            state = self._axes[axis]
            state.is_cluster = cluster
            state.cluster_kws = kwargs
            state.use_meta = use_meta
            state.linkage = linkage
            state.meta_linkage = meta_linkage
            state.invalidate()

    def get_data(self):
        data = self.data
        if self.data_row_reindex is not None:
            data = data[self.data_row_reindex]
        if self.data_col_reindex is not None:
            data = data[:, self.data_col_reindex]
        return data

    def _set_split(self, axis, breakpoints=None, order=None):
        if breakpoints is None:
            return
        state = self._axes[axis]
        cuts = np.sort(np.asarray(breakpoints))
        self._check_cuts(axis, cuts, state.n)
        state.is_split = True
        state.breakpoints = [0, *cuts, state.n]
        if order is None:
            order = np.arange(len(breakpoints) + 1)
        state.split_order = order
        state.plan = None

    @staticmethod
    def _check_cuts(axis, cuts, n):
        """Reject cut positions that cannot split the axis.

        Out of range used to pass silently: the chunk it describes is empty, so
        the plot simply came out wrong with nothing said about it.
        """
        unit = "row" if axis == _ROW else "column"
        outside = [int(c) for c in cuts if c < 1 or c > n - 1]
        if outside:
            raise ValueError(
                f"Cannot cut {unit}s at {outside}, there are only {n} {unit}s. "
                f"Cuts go between 1 and {n - 1}."
            )
        values, counts = np.unique(cuts, return_counts=True)
        repeated = [int(v) for v in values[counts > 1]]
        if repeated:
            raise ValueError(
                f"Cannot cut {unit}s at {repeated} twice, "
                f"that would leave an empty group."
            )

    def set_split_row(self, breakpoints=None, order=None):
        self._set_split(_ROW, breakpoints, order)

    def set_split_col(self, breakpoints=None, order=None):
        self._set_split(_COL, breakpoints, order)

    def _ratios(self, axis):
        """Chunk sizes, in drawing order, for splitting the axes."""
        if self._axes[axis].breakpoints is None:
            self._run_cluster()
            return None
        return np.diff(self._get_plan(axis).bounds)

    @property
    def row_ratios(self):
        return self._ratios(_ROW)

    @property
    def col_ratios(self):
        return self._ratios(_COL)

    def _set_chunk_order(self, axis, order):
        state = self._axes[axis]
        state.chunk_index = order
        state.plan = None

    def set_row_chunk_order(self, order):
        self._set_chunk_order(_ROW, order)

    def set_col_chunk_order(self, order):
        self._set_chunk_order(_COL, order)

    def _split_chunks(self, axis, data):
        """Cut data at the breakpoints, still in the original order."""
        state = self._axes[axis]
        if not state.is_split:
            return data
        if axis == _ROW:
            return [data[ix1:ix2] for ix1, ix2 in pairwise(state.breakpoints)]
        # ... keeps this working for 1d column data too
        return [data[..., ix1:ix2] for ix1, ix2 in pairwise(state.breakpoints)]

    _linkage_check_msg = (
        "If you want to specific linkage when splitting, "
        "it must be a dict-like object, "
        "with keys as group names and values as linkage"
    )

    def _cluster(self, axis):
        """Cluster one axis, chunk by chunk when it is split.

        Columns are clustered as observations, so each chunk is transposed
        before it reaches the dendrogram.
        """
        state = self._axes[axis]
        data = self._split_chunks(axis, self.get_data())
        # rows are already observations; columns become observations transposed
        observations = (
            (lambda chunk: chunk) if axis == _ROW else (lambda chunk: chunk.T)
        )

        if state.is_split:
            if not (isinstance(state.linkage, Mapping) or (state.linkage is None)):
                raise TypeError(self._linkage_check_msg)
            dens = []
            for chunk, k in zip(data, state.split_order):
                linkage = None
                if state.linkage is not None:
                    linkage = state.linkage.get(k)
                    if linkage is None:
                        raise KeyError(f"Linkage for group {k} is not specified")
                dens.append(
                    Dendrogram(
                        observations(chunk),
                        linkage=linkage,
                        key=k,
                        **state.cluster_kws,
                    )
                )
            dg = GroupDendrogram(dens, linkage=state.meta_linkage, **state.cluster_kws)
            if state.use_meta:
                state.chunk_index = dg.reorder_index
            else:
                state.chunk_index = np.arange(len(dens))
            state.reorder_index = [d.reorder_index for d in dens]
        else:
            dg = Dendrogram(
                observations(data), linkage=state.linkage, **state.cluster_kws
            )
            state.reorder_index = dg.reorder_index
        state.dendrogram = dg

    def cluster_row(self):
        self._cluster(_ROW)

    def cluster_col(self):
        self._cluster(_COL)

    def _run_cluster(self):
        """Calculation of dendrogram is expensive,
        so only calculated once"""
        if self.is_row_cluster & (not self._row_clustered):
            self.cluster_row()
            self._row_clustered = True
        if self.is_col_cluster & (not self._col_clustered):
            self.cluster_col()
            self._col_clustered = True

    def _get_plan(self, axis) -> _Plan:
        """Resolve one axis into where every element ends up.

        Grouping, splitting, the leaf order within each chunk and the order of
        the chunks themselves all compose into a single permutation. This is
        the only place that decides layout.
        """
        state = self._axes[axis]
        if state.plan is not None:
            return state.plan
        self._run_cluster()

        index = (
            np.arange(state.n) if state.reindex is None else np.asarray(state.reindex)
        )
        if not state.is_split:
            if state.is_cluster:
                index = index[state.reorder_index]
            state.plan = _Plan(index, np.array([0, state.n]))
            return state.plan

        chunks = [index[ix1:ix2] for ix1, ix2 in pairwise(state.breakpoints)]
        if state.is_cluster:
            chunks = [c[np.asarray(o)] for c, o in zip(chunks, state.reorder_index)]
        if state.chunk_index is not None:
            chunks = [chunks[ix] for ix in state.chunk_index]
        state.plan = _Plan(
            np.concatenate(chunks),
            np.concatenate([[0], np.cumsum([len(c) for c in chunks])]),
        )
        return state.plan

    def _apply(self, axis, data):
        """Deform data whose last axis indexes this one."""
        state = self._axes[axis]
        if data.shape[-1] != state.n:
            msg = (
                f"Data has {data.shape[-1]} elements on the "
                f"{'row' if axis == _ROW else 'column'} axis, "
                f"expected {state.n}"
            )
            raise ValueError(msg)
        plan = self._get_plan(axis)
        deformed = np.take(data, plan.index, axis=-1)
        if not state.is_split:
            return deformed
        return [deformed[..., ix1:ix2] for ix1, ix2 in pairwise(plan.bounds)]

    def transform(self, data: np.ndarray):
        """data must be 2d array with the same shape as cluster data"""
        if not data.shape == (self._nrow, self._ncol):
            msg = (
                f"The shape of input data {data.shape} does not align with"
                f" the shape of cluster data {(self._nrow, self._ncol)}"
            )
            raise ValueError(msg)
        rows, cols = self._get_plan(_ROW), self._get_plan(_COL)
        deformed = data[np.ix_(rows.index, cols.index)]
        if not self.is_split:
            return deformed
        # a 2d split is handed back flattened, one row of blocks at a time
        return [
            deformed[ix1:ix2, iy1:iy2]
            for ix1, ix2 in pairwise(rows.bounds)
            for iy1, iy2 in pairwise(cols.bounds)
        ]

    def transform_row(self, data: np.ndarray):
        """Deform data whose last axis indexes rows."""
        return self._apply(_ROW, data)

    def transform_col(self, data: np.ndarray):
        """Deform data whose last axis indexes columns."""
        return self._apply(_COL, data)

    def _get_dendrogram(self, axis):
        # Update the cluster result
        self._run_cluster()
        return self._axes[axis].dendrogram

    def get_row_dendrogram(self):
        return self._get_dendrogram(_ROW)

    def get_col_dendrogram(self):
        return self._get_dendrogram(_COL)

    def _get_linkage(self, axis):
        state = self._axes[axis]
        if state.dendrogram is None:
            return None
        if state.is_split:
            # a single-element chunk has no linkage, its Z is None
            return {x.key: x.Z for x in state.dendrogram.orig_dens}
        return state.dendrogram.Z

    def get_row_linkage(self):
        return self._get_linkage(_ROW)

    def get_col_linkage(self):
        return self._get_linkage(_COL)

    @property
    def is_split(self):
        return self.is_row_split | self.is_col_split

    @property
    def is_cluster(self):
        return self.is_row_cluster | self.is_col_cluster

    # --- deprecated, remove in the next minor ---
    #
    # Internal steps that autodoc exposed. Nothing in marsilea calls them and
    # the reorder_* pair only accepts the intermediate structure that the old
    # transform() built, so they are kept working rather than kept tidy.

    def _deprecated(self, name, instead):
        warnings.warn(
            f"Deformation.{name} is an internal helper and will be removed, "
            f"use {instead} instead",
            DeprecationWarning,
            stacklevel=find_stack_level(),
        )

    def split_by_row(self, data: np.ndarray):
        self._deprecated("split_by_row", "transform_row")
        return self._split_chunks(_ROW, data)

    def split_by_col(self, data: np.ndarray):
        self._deprecated("split_by_col", "transform_col")
        return self._split_chunks(_COL, data)

    def split_cross(self, data: np.ndarray):
        self._deprecated("split_cross", "transform")
        if self.is_col_split & self.is_row_split:
            return [
                [data[ix1:ix2, iy1:iy2] for iy1, iy2 in pairwise(self.col_breakpoints)]
                for ix1, ix2 in pairwise(self.row_breakpoints)
            ]
        if self.is_row_split:
            return self._split_chunks(_ROW, data)
        if self.is_col_split:
            return self._split_chunks(_COL, data)
        return data

    def reorder_by_row(self, data, split="2d"):
        self._deprecated("reorder_by_row", "transform_row")
        self._run_cluster()
        if not self.is_row_cluster:
            return data

        if split == "2d":
            if self.is_row_split & self.is_col_split:
                for row, order in zip(data, self.row_reorder_index):
                    for ix in range(len(row)):
                        row[ix] = row[ix][order]
                return [data[ix] for ix in self.row_chunk_index]

        if self.is_row_split:
            for ix, order in zip(range(len(data)), self.row_reorder_index):
                data[ix] = data[ix][order]
            return [data[ix] for ix in self.row_chunk_index]
        else:
            if (split == "2d") & self.is_col_split:
                return [d[self.row_reorder_index] for d in data]
            return data[self.row_reorder_index]

    def reorder_by_col(self, data, split="2d"):
        self._deprecated("reorder_by_col", "transform_col")
        self._run_cluster()
        if not self.is_col_cluster:
            return data

        if split == "2d":
            if self.is_row_split & self.is_col_split:
                final_data = []
                for row in data:
                    for ix, order in zip(range(len(row)), self.col_reorder_index):
                        if row[ix].ndim == 2:
                            row[ix] = row[ix][:, order]
                        else:
                            row[ix] = row[ix][order]
                    final_data.append([row[ix] for ix in self.col_chunk_index])
                return final_data
            elif self.is_col_split:
                for ix, order in zip(range(len(data)), self.col_reorder_index):
                    data[ix] = data[ix][:, order]

                return [data[ix] for ix in self.col_chunk_index]
            elif self.is_split:
                return [d[:, self.col_reorder_index] for d in data]
            else:
                return data[:, self.col_reorder_index]
        # 1d list situation
        else:
            if self.is_col_split:
                for ix, order in zip(range(len(data)), self.col_reorder_index):
                    if data[ix].ndim == 2:
                        data[ix] = data[ix][:, order]
                    else:
                        data[ix] = data[ix][order]
                return [data[ix] for ix in self.col_chunk_index]
            else:
                if data.ndim == 2:
                    return data[:, self.col_reorder_index]
                else:
                    return data[self.col_reorder_index]
