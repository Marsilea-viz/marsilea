from dataclasses import dataclass
from typing import Any

import numpy as np


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
    split_col = False
    split_row = False
    _split_index_col: np.ndarray = None
    _split_index_row: np.ndarray = None
    wspace: float = 0.05
    hspace: float = 0.05

    def __init__(self, data):
        self.data = data
        self._nrow, self._ncol = data.shape

    def set_split_index(self, col=None, row=None):
        if col is not None:
            col = np.sort(np.asarray(col))
            self._split_index_col = col
            self.split_col = True

        if row is not None:
            row = np.sort(np.asarray(row))
            self._split_index_row = row
            self.split_row = True

    def set_order(self, col=None, row=None):
        """This is used to record the order of generated dendrogram
        when no split happen
        """

        pass

    def set_chunk_order(self, col=None, row=None,
                        col_meta=None, row_meta=None):
        pass

    def get_render_data(self):
        pass

    # @property
    # def split_index_x(self):
    #     return self._split_index_x

    # @split_index_x.setter
    # def split_index_x(self, v):
    #     v = np.sort(np.asarray(v))
    #     # if v[-1] >= self.data.shape[1]:
    #     #     raise IndexError("Cannot split more than the size of data")
    #     # else:
    #     self._split_index_x = v
    #     self.split_x = True
    #
    # @property
    # def split_index_y(self):
    #     return self._split_index_y
    #
    # @split_index_y.setter
    # def split_index_y(self, v):
    #     v = np.sort(np.asarray(v))
    #     # if v[-1] >= self._X:
    #     #     raise IndexError("Cannot split more than the size of data")
    #     # else:
    #     self._split_index_y = v
    #     self.split_y = True

    def split_data(self, data=None):
        if data is None:
            data = self.data
        split_data = []
        if self.split_col & self.split_row:
            # split x and y
            start_x = 0
            start_y = 0
            for iy in [*self.split_index_y, self._Y]:
                for ix in [*self.split_index_x, self._X]:
                    # print((start_y, iy), (start_x, ix))
                    split_data.append(
                        data[start_y:iy, start_x:ix]
                    )
                    start_x = ix
                start_x = 0
                start_y = iy
        else:
            if self.split_col:
                # split x
                start_x = 0
                for ix in [*self.split_index_x, self._X]:
                    split_data.append(
                        data[:, start_x:ix]
                    )
                    start_x = ix
            if self.split_row:
                # split y
                start_y = 0
                for iy in [*self.split_index_y, self._Y]:
                    split_data.append(
                        data[start_y:iy]
                    )
                    start_y = iy
        return split_data

    def split_other_x(self, data: np.ndarray):
        if self.split_col:
            split_data = []
            start_x = 0
            for ix in self.split_index_x:
                if data.ndim == 2:
                    chunk = data[:, start_x:ix]
                elif data.ndim == 1:
                    chunk = data[start_x:ix]
                else:
                    raise ValueError("Cannot split data more than 2d")
                split_data.append(chunk)
                start_x += ix
        else:
            return data

    def split_other_y(self, data: np.ndarray):
        if self.split_row:
            split_data = []
            start_y = 0
            for iy in self.split_index_y:
                if data.ndim == 2:
                    chunk = data[start_y:iy, :]
                elif data.ndim == 1:
                    chunk = data[start_y:iy]
                else:
                    raise ValueError("Cannot split data more than 2d")
                split_data.append(chunk)
                start_y += iy
        else:
            return data

    @property
    def split_ratio_x(self):
        if self.split_index_x is not None:
            # Reverse the ratio to match reversed data
            return self.split_index_x / self._X
        else:
            return None

    @property
    def split_ratio_y(self):
        if self.split_index_y is not None:
            return self.split_index_y / self._Y
        else:
            return None
