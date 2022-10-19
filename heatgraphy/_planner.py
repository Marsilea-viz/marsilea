from itertools import tee

import numpy as np

from .dendrogram import Dendrogram, GroupDendrogram


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class Deformation:
    """A helper class that does:
        1. Split the data based on index
        2. Reorder data chunks and data within chunk
        3. Compute the ratio to split axes that match with data
    """
    is_row_split = False
    is_col_split = False
    is_row_cluster = False
    is_col_cluster = False
    _row_clustered = False
    _col_clustered = False

    row_ratios = None
    col_ratios = None

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

    def __init__(self, data):
        self.data = data
        self._nrow, self._ncol = data.shape

    def set_split_row(self, breakpoints=None):
        if breakpoints is not None:
            self.is_row_split = True
            self.row_breakpoints = [0, *np.sort(np.asarray(breakpoints)),
                                    self._nrow]
            self.row_ratios = np.array(
                [ix2 - ix1 for ix1, ix2 in pairwise(self.row_breakpoints)]
            )

    def set_split_col(self, breakpoints=None):
        if breakpoints is not None:
            self.is_col_split = True
            self.col_breakpoints = [0, *np.sort(np.asarray(breakpoints)),
                                    self._ncol]
            self.col_ratios = np.array(
                [ix2 - ix1 for ix1, ix2 in pairwise(self.col_breakpoints)]
            )

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
        row_data = self.split_by_row(self.data)
        if self.is_row_split:
            dens = [Dendrogram(chunk) for chunk in row_data]
            dg = GroupDendrogram(dens)
            self.row_chunk_index = dg.reorder_index
            self.row_reorder_index = [d.reorder_index for d in dens]
        else:
            dg = Dendrogram(row_data)
            self.row_reorder_index = dg.reorder_index
        self.row_dendrogram = dg

    def cluster_col(self):
        col_data = self.split_by_col(self.data)
        if self.is_col_split:
            dens = [Dendrogram(chunk.T) for chunk in col_data]
            dg = GroupDendrogram(dens)
            self.col_chunk_index = dg.reorder_index
            self.col_reorder_index = [d.reorder_index for d in dens]
        else:
            dg = Dendrogram(col_data.T)
            self.col_reorder_index = dg.reorder_index
        self.col_dendrogram = dg

    def _run_cluster(self):
        """Calculation of dendrogram is expensive,
        so only calculated once"""
        if self.is_row_cluster & (not self._row_clustered):
            self.cluster_row()
            self._row_clustered = True
        if self.is_col_cluster & (not self._col_clustered):
            self.cluster_col()
            self._col_clustered = True

    def reorder_by_row(self, data, split="both"):
        self._run_cluster()
        if not self.is_row_cluster:
            return data
        # no split
        elif not self.is_split:
            return data[self.row_reorder_index]
        # 2d list situation
        elif self.is_row_split & self.is_col_split & (split == "both"):
            for row, order in zip(data, self.row_reorder_index):
                for ix in range(len(row)):
                    row[ix] = row[ix][order]
            return [data[ix] for ix in self.row_chunk_index]
        # 1d list situation
        else:
            for ix in range(len(data)):
                data[ix] = data[ix][self.row_reorder_index]
            if self.is_row_split:
                return [data[ix] for ix in self.row_chunk_index]
            else:
                return data

    def reorder_by_col(self, data, split="both"):
        self._run_cluster()
        if not self.is_col_cluster:
            return data
        # no split
        elif not self.is_split:
            if data.ndim == 2:
                return data[:, self.col_reorder_index]
            else:
                return data[self.col_reorder_index]
        # 2d list situation
        elif self.is_row_split & self.is_col_split & (split == "both"):
            final_data = []
            for row in data:
                for ix, order in zip(range(len(row)), self.col_reorder_index):
                    if row[ix].ndim == 2:
                        row[ix] = row[ix][:, order]
                    else:
                        row[ix] = row[ix][order]
                final_data.append(
                    [row[ix] for ix in self.col_chunk_index]
                )
            return final_data
        # 1d list situation
        else:
            for ix, order in zip(range(len(data)), self.col_reorder_index):
                if data[ix].ndim == 2:
                    data[ix] = data[ix][:, order]
                else:
                    data[ix] = data[ix][order]
            if self.is_col_split:
                return [data[ix] for ix in self.col_chunk_index]
            else:
                return data

    def transform(self, data: np.ndarray):
        """data must be 2d array with the same shape as cluster data"""
        if not data.shape == (self._nrow, self._ncol):
            msg = f"The shape of input data {data.shape} does not align with" \
                  f" the shape of cluster data {(self._nrow, self._ncol)}"
            raise ValueError(msg)
        trans_data = self.split_cross(data)
        trans_data = self.reorder_by_row(trans_data, split="both")
        trans_data = self.reorder_by_col(trans_data, split="both")

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

        trans_data = self.split_by_row(data)
        trans_data = self.reorder_by_row(trans_data, split="row")
        return trans_data

    def transform_col(self, data: np.ndarray):
        if data.ndim == 1:
            assert len(data) == self._ncol
        else:
            assert data.shape[1] == self._ncol

        trans_data = self.split_by_col(data)
        trans_data = self.reorder_by_col(trans_data, split="col")
        return trans_data

    def get_row_dendrogram(self):
        return self.row_dendrogram

    def get_col_dendrogram(self):
        return self.col_dendrogram

    @property
    def is_split(self):
        return self.is_row_split | self.is_col_split
