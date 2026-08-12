from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from .dendrogram import Dendrogram, GroupDendrogram
from .utils import pairwise

_ROW, _COL = 0, 1


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
    ratios_cache: Any = None


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
        ("_{}_ratios_cache", "ratios_cache"),
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
        self._col_clustered = False
        self._row_clustered = False

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
        state.clustered = False

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
            state.clustered = False
            state.ratios_cache = None
            state.use_meta = use_meta
            state.linkage = linkage
            state.meta_linkage = meta_linkage

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
        state.is_split = True
        state.breakpoints = [0, *np.sort(np.asarray(breakpoints)), state.n]
        if order is None:
            order = np.arange(len(breakpoints) + 1)
        state.split_order = order
        state.ratios_cache = None

    def set_split_row(self, breakpoints=None, order=None):
        self._set_split(_ROW, breakpoints, order)

    def set_split_col(self, breakpoints=None, order=None):
        self._set_split(_COL, breakpoints, order)

    def _ratios(self, axis):
        state = self._axes[axis]
        if state.ratios_cache is not None:
            return state.ratios_cache
        self._run_cluster()
        if state.breakpoints is None:
            return None
        ratios = np.array([ix2 - ix1 for ix1, ix2 in pairwise(state.breakpoints)])
        if state.chunk_index is not None:
            ratios = ratios[state.chunk_index]
        state.ratios_cache = ratios
        return ratios

    @property
    def row_ratios(self):
        return self._ratios(_ROW)

    @property
    def col_ratios(self):
        return self._ratios(_COL)

    def _set_chunk_order(self, axis, order):
        state = self._axes[axis]
        state.chunk_index = order
        state.ratios_cache = None

    def set_row_chunk_order(self, order):
        self._set_chunk_order(_ROW, order)

    def set_col_chunk_order(self, order):
        self._set_chunk_order(_COL, order)

    def split_by_row(self, data: np.ndarray):
        if not self.is_row_split:
            return data
        return [data[ix1:ix2] for ix1, ix2 in pairwise(self.row_breakpoints)]

    def split_by_col(self, data: np.ndarray):
        if not self.is_col_split:
            return data
        if data.ndim == 1:
            return [data[ix1:ix2] for ix1, ix2 in pairwise(self.col_breakpoints)]
        else:
            return [data[:, ix1:ix2] for ix1, ix2 in pairwise(self.col_breakpoints)]

    def split_cross(self, data: np.ndarray):
        if self.is_col_split & self.is_row_split:
            split_data = []
            for ix1, ix2 in pairwise(self.row_breakpoints):
                row = []
                for iy1, iy2 in pairwise(self.col_breakpoints):
                    row.append(data[ix1:ix2, iy1:iy2])
                split_data.append(row)
            return split_data
        if self.is_row_split:
            return self.split_by_row(data)
        if self.is_col_split:
            return self.split_by_col(data)
        return data

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
        splitter = self.split_by_row if axis == _ROW else self.split_by_col
        data = splitter(self.get_data())
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

    def reorder_by_row(self, data, split="2d"):
        self._run_cluster()
        # no cluster, return immediately
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
        self._run_cluster()
        # no cluster, return immediately
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

    def transform(self, data: np.ndarray):
        """data must be 2d array with the same shape as cluster data"""
        if not data.shape == (self._nrow, self._ncol):
            msg = (
                f"The shape of input data {data.shape} does not align with"
                f" the shape of cluster data {(self._nrow, self._ncol)}"
            )
            raise ValueError(msg)
        if self.data_row_reindex is not None:
            data = data[self.data_row_reindex]
        if self.data_col_reindex is not None:
            data = data[:, self.data_col_reindex]
        trans_data = self.split_cross(data)
        trans_data = self.reorder_by_row(trans_data, split="2d")
        trans_data = self.reorder_by_col(trans_data, split="2d")
        flatten_data = []
        if self.is_row_split & self.is_col_split:
            for chunk in trans_data:
                flatten_data += chunk
            return flatten_data
        return trans_data

    def transform_row(self, data: np.ndarray):
        data = data.T
        if data.ndim == 1:
            assert len(data) == self._nrow
        else:
            assert data.shape[0] == self._nrow

        if self.data_row_reindex is not None:
            data = data[self.data_row_reindex]

        trans_data = self.split_by_row(data)
        trans_data = self.reorder_by_row(trans_data, split="1d")
        if isinstance(trans_data, np.ndarray):
            return trans_data.T
        else:
            return [d.T for d in trans_data]

    def transform_col(self, data: np.ndarray):
        if data.ndim == 1:
            assert len(data) == self._ncol
        else:
            assert data.shape[1] == self._ncol

        if self.data_col_reindex is not None:
            if data.ndim == 2:
                data = data[:, self.data_col_reindex]
            else:
                data = data[self.data_col_reindex]

        trans_data = self.split_by_col(data)
        trans_data = self.reorder_by_col(trans_data, split="1d")
        return trans_data

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
