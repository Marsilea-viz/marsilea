from dataclasses import dataclass
from typing import Any, Sequence, Iterable

import numpy as np

from ._plotter import Chart


def _segments(breakpoints, total):
    bp = np.array([*breakpoints, total])

    start = 0.0
    result = []
    for i in bp:
        end = i - start
        start += end
        result.append(end)

    return np.array(result)


@dataclass
class RenderPlan:
    name: str
    side: str
    data: Any
    size: float
    chart: Chart


# x: col, y: row
class SplitPlan:
    """A helper class that does:
    1. Split the data based on index
    2. Reorder data chunks and data within chunk
    3. Compute the ratio to split axes that match with data
    """
    data: np.ndarray
    split = False  # To known whether to do the split
    split_col = False
    split_row = False
    wspace: float = 0.05
    hspace: float = 0.05
    _split_index_col: np.ndarray = None
    _split_index_row: np.ndarray = None
    _split_col_data: np.ndarray = None
    _split_row_data: np.ndarray = None
    _split_data: np.ndarray = None
    _col_segments: np.ndarray = None
    _row_segments: np.ndarray = None
    _col_order: np.ndarray = None
    _row_order: np.ndarray = None
    _col_chunk_order: np.ndarray = None
    _row_chunk_order: np.ndarray = None

    def __repr__(self):
        return f"SplitPlan(row={self.split_row}, col={self.split_col})"

    def __init__(self, data):
        self.data = data
        self._nrow, self._ncol = data.shape

    def set_split_index(self, col=None, row=None):
        self.split = True
        if col is not None:
            col = np.sort(np.asarray(col))
            self._split_index_col = col
            self.split_col = True
            self._col_segments = _segments(col, self._ncol)

        if row is not None:
            row = np.sort(np.asarray(row))
            self._split_index_row = row
            self.split_row = True
            self._row_segments = _segments(row, self._nrow)

    def set_order(self, col=None, row=None,
                  col_chunk=None, row_chunk=None):
        """This is used to record the order of generated dendrogram
        when no split happen

        This function should only be called once in a render cycle

        """
        if col_chunk is not None:
            self._col_order = col
            self._col_chunk_order = col_chunk
            self._col_segments = self._col_segments[col_chunk]
        if row_chunk is not None:
            self._row_order = row
            self._row_chunk_order = row_chunk
            self._row_segments = self._row_segments[row_chunk]

    def _reorder_col(self, data):
        if self._col_chunk_order is not None:
            # When split both col and row
            if self.split_row:
                split_data = []
                for row_data_chunk in data:
                    row = []
                    for chunk, ix in zip(row_data_chunk, self._col_order):
                        row.append(chunk[:, ix])
                    split_data.append([row[i] for i in self._col_chunk_order])
                return split_data
            # When only split on col
            else:
                return self._reorder_1d_col(data, self._col_order,
                                            self._col_chunk_order)
        return data

    @staticmethod
    def _reorder_1d_col(data1d, order, chunk_order):
        for i, ix in zip(
                range(len(data1d)),
                order):
            data1d[i] = data1d[i][:, ix]
        return [data1d[i] for i in chunk_order]

    @staticmethod
    def _reorder_1d_row(data1d, order, chunk_order):
        for i, ix in zip(
                range(len(data1d)),
                order):
            data1d[i] = data1d[i][ix]
        return [data1d[i] for i in chunk_order]

    def _reorder_row(self, data):
        if self._row_chunk_order is not None:
            # When split both col and row
            if self.split_col:
                split_data = []
                for row_data_chunk, ix in zip(data, self._row_order):
                    row = []
                    for chunk in row_data_chunk:
                        row.append(chunk[ix])
                    split_data.append(row)
                return [split_data[i] for i in self._row_chunk_order]
            else:
                return self._reorder_1d_row(data, self._row_order,
                                            self._row_chunk_order)
        return data

    def get_split_col_data(self, reorder=True):
        if self.split_col:
            split_data = []
            start = 0
            for ix in [*self._split_index_col, self._ncol]:
                split_data.append(
                    self.data[:, start:ix]
                )
                start = ix
            if reorder:
                return self._reorder_col(split_data)
            else:
                return split_data
        return None

    def get_split_row_data(self, reorder=True):
        if self.split_row:
            split_data = []
            start = 0
            for ix in [*self._split_index_row, self._nrow]:
                split_data.append(
                    self.data[start:ix]
                )
                start += ix
            row_data = np.asarray(split_data)
            if reorder:
                return self._reorder_row(split_data)
            else:
                return split_data
        return None

    def get_split_data(self, reorder=True):
        """Return 1d data in list container"""
        if self.split_col & self.split_row:
            # split x and y
            split_data = []
            start_x = 0
            start_y = 0
            for iy in [*self._split_index_row, self._nrow]:
                row = []
                for ix in [*self._split_index_col, self._ncol]:
                    # print((start_y, iy), (start_x, ix))
                    row.append(
                        self.data[start_y:iy, start_x:ix]
                    )
                    start_x = ix
                split_data.append(row)
                start_x = 0
                start_y = iy
            if reorder:
                split_data = self._reorder_row(split_data)
                split_data = self._reorder_col(split_data)
            flatten_data = []
            for row in split_data:
                for i in row:
                    flatten_data.append(i)

            return flatten_data
        else:
            if self.split_col:
                return self.get_split_col_data(reorder=reorder)
            if self.split_row:
                return self.get_split_row_data(reorder=reorder)

    def split_by_col(self, data):
        if self.split_col:
            split_data = []
            start_x = 0
            for ix in self._split_index_col:
                if data.ndim == 2:
                    chunk = data[:, start_x:ix]
                elif data.ndim == 1:
                    chunk = data[start_x:ix]
                else:
                    raise ValueError("Cannot split data more than 2d")
                split_data.append(chunk)
                start_x += ix
            return self._reorder_col(split_data)
        else:
            return data

    def split_by_row(self, data):
        if self.split_row:
            split_data = []
            start_y = 0
            for iy in self._split_index_row:
                if data.ndim == 2:
                    chunk = data[start_y:iy, :]
                elif data.ndim == 1:
                    chunk = data[start_y:iy]
                else:
                    raise ValueError("Cannot split data more than 2d")
                split_data.append(chunk)
                start_y += iy
            return self._reorder_row(split_data)
        else:
            return data

    @property
    def col_segments(self):
        return self._col_segments

    @property
    def row_segments(self):
        return self._row_segments
