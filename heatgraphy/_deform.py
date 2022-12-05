from itertools import tee

import numpy as np

from .dendrogram import Dendrogram, GroupDendrogram
from .utils import pairwise


class Deformation:
    """A helper class to handle data

    #. Split the data based on index
    #. Reorder the data based on label order
    #. Reorder the data based on cluster order
    #. Compute the ratio to split axes that match with data

    """
    is_row_split = False
    is_col_split = False
    is_row_cluster = False
    is_col_cluster = False
    _row_clustered = False
    _col_clustered = False

    data_row_reindex = None
    data_col_reindex = None

    row_breakpoints = None
    col_breakpoints = None

    row_dendrogram = None
    col_dendrogram = None

    row_reorder_index = None
    col_reorder_index = None

    row_chunk_index = None
    col_chunk_index = None

    # just for storage
    wspace = 0
    hspace = 0

    row_cluster_kws = {}
    col_cluster_kws = {}

    data = None
    _nrow = None
    _ncol = None

    def __init__(self, data):
        self.set_data(data)

    def set_data(self, data):
        self.data = data
        self._nrow, self._ncol = data.shape
        self._col_clustered = False
        self._row_clustered = False

    def set_data_row_reindex(self, reindex):
        if len(reindex) != self._nrow:
            msg = f"Length of reindex ({len(reindex)}) should match " \
                  f"data row with {self._nrow} elements"
            raise ValueError(msg)
        self.data_row_reindex = reindex
        self._row_clustered = False

    def set_data_col_reindex(self, reindex):
        if len(reindex) != self._ncol:
            msg = f"Length of reindex ({len(reindex)}) should match " \
                  f"data col with {self._ncol} elements"
            raise ValueError(msg)
        self.data_col_reindex = reindex
        self._col_clustered = False

    def set_cluster(self, col=None, row=None):
        if col is not None:
            self.is_col_cluster = col
        if row is not None:
            self.is_row_cluster = row

    def get_data(self):
        data = self.data
        if self.data_row_reindex is not None:
            data = data[self.data_row_reindex]
        if self.data_col_reindex is not None:
            data = data[:, self.data_col_reindex]
        return data

    def set_split_row(self, breakpoints=None):
        if breakpoints is not None:
            self.is_row_split = True
            self.row_breakpoints = [0, *np.sort(np.asarray(breakpoints)),
                                    self._nrow]

    def set_split_col(self, breakpoints=None):
        if breakpoints is not None:
            self.is_col_split = True
            self.col_breakpoints = [0, *np.sort(np.asarray(breakpoints)),
                                    self._ncol]

    @property
    def row_ratios(self):
        self._run_cluster()
        if self.row_breakpoints is None:
            return None
        ratios = np.array([
            ix2 - ix1 for ix1, ix2 in pairwise(self.row_breakpoints)])

        if self.row_chunk_index is not None:
            return ratios[self.row_chunk_index]
        else:
            return ratios

    @property
    def col_ratios(self):
        self._run_cluster()
        if self.col_breakpoints is None:
            return None
        ratios = np.array([
            ix2 - ix1 for ix1, ix2 in pairwise(self.col_breakpoints)])

        if self.col_chunk_index is not None:
            return ratios[self.col_chunk_index]
        else:
            return ratios

    def set_row_chunk_order(self, order):
        self.row_chunk_index = order

    def set_col_chunk_order(self, order):
        self.col_chunk_index = order

    def split_by_row(self, data: np.ndarray):
        if not self.is_row_split:
            return data
        return [data[ix1:ix2] for ix1, ix2 in pairwise(self.row_breakpoints)]

    def split_by_col(self, data: np.ndarray):
        if not self.is_col_split:
            return data
        if data.ndim == 1:
            return [data[ix1:ix2] for ix1, ix2 in pairwise(
                self.col_breakpoints)]
        else:
            return [data[:, ix1:ix2] for ix1, ix2 in pairwise(
                self.col_breakpoints)]

    def split_cross(self, data: np.ndarray):
        if self.is_col_split & self.is_row_split:
            split_data = []
            for ix1, ix2 in pairwise(self.row_breakpoints):
                row = []
                for iy1, iy2 in pairwise(self.col_breakpoints):
                    row.append(
                        data[ix1:ix2, iy1:iy2]
                    )
                split_data.append(row)
            return split_data
        if self.is_row_split:
            return self.split_by_row(data)
        if self.is_col_split:
            return self.split_by_col(data)
        return data

    def cluster_row(self):
        row_data = self.split_by_row(self.get_data())
        if self.is_row_split:
            dens = [Dendrogram(
                chunk, **self.row_cluster_kws) for chunk in row_data]
            dg = GroupDendrogram(dens, **self.row_cluster_kws)
            self.row_chunk_index = dg.reorder_index
            self.row_reorder_index = [d.reorder_index for d in dens]
        else:
            dg = Dendrogram(row_data, **self.row_cluster_kws)
            self.row_reorder_index = dg.reorder_index
        self.row_dendrogram = dg

    def cluster_col(self):
        col_data = self.split_by_col(self.get_data())
        if self.is_col_split:
            dens = [Dendrogram(
                chunk.T, **self.col_cluster_kws) for chunk in col_data]
            dg = GroupDendrogram(dens, **self.col_cluster_kws)
            self.col_chunk_index = dg.reorder_index
            self.col_reorder_index = [d.reorder_index for d in dens]
        else:
            dg = Dendrogram(col_data.T, **self.col_cluster_kws)
            self.col_reorder_index = dg.reorder_index
        self.col_dendrogram = dg

    def set_row_cluster_params(self, **kws):
        self.row_cluster_kws = {**kws}
        self._row_clustered = False

    def set_col_cluster_params(self, **kws):
        self.col_cluster_kws = {**kws}
        self._col_clustered = False

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
                    for ix, order in zip(range(len(row)),
                                         self.col_reorder_index):
                        if row[ix].ndim == 2:
                            row[ix] = row[ix][:, order]
                        else:
                            row[ix] = row[ix][order]
                    final_data.append(
                        [row[ix] for ix in self.col_chunk_index]
                    )
                return final_data
            elif self.is_col_split:
                for ix, order in zip(range(len(data)),
                                     self.col_reorder_index):
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
            msg = f"The shape of input data {data.shape} does not align with" \
                  f" the shape of cluster data {(self._nrow, self._ncol)}"
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
        if data.ndim == 1:
            assert len(data) == self._nrow
        else:
            assert data.shape[1] == self._nrow

        if self.data_row_reindex is not None:
            data = data[self.data_row_reindex]

        data = data.T

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

    def get_row_dendrogram(self):
        # Update the cluster result
        self._run_cluster()
        return self.row_dendrogram

    def get_col_dendrogram(self):
        self._run_cluster()
        return self.col_dendrogram

    @property
    def is_split(self):
        return self.is_row_split | self.is_col_split
