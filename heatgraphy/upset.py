from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from .base import _Base


@dataclass
class UpSetAttr:
    name: str
    data: np.ndarray


class UpsetData:

    names: np.ndarray  # columns
    items: np.ndarray  # row
    data: np.ndarray  # one-hot encode data
    attrs: UpSetAttr = None

    def __init__(self, names, items, data, attrs=None):
        self.names = names
        self.items = items
        self.data = data
        self.attrs = attrs

        self._set_table = pd.DataFrame(columns=names, index=items,
                                       data=data)

    @staticmethod
    def from_sets(sets: Dict) -> UpsetData:
        names = []
        items = set()
        new_sets = []
        for name, s in sets.items():
            names.append(name)
            s = set(s)
            new_sets.append(s)
            items.update(s)
        items = np.array(list(items))
        data = []
        for name, s in zip(names, new_sets):
            d = [i in s for i in items]
            data.append(d)
        data = np.array(data, dtype=int).T
        return UpsetData(names, items, data)

    def from_dataframe(self, data):
        pass

    def isin(self, item):
        """Return the sets name the item is in"""
        pass

    def overlap_items(self, sets_name):
        """Return the items that appears in sets"""
        pass

    def overlap_count(self, count, up=None, low=None):
        """Return the item that has overlap at exactly number of sets"""
        pass

    def get_sets_count(self, ascending=True):
        return (self._set_table.groupby(self.names)
                .size().sort_values(ascending=ascending))


class Upset(_Base):

    def __init__(self, data: UpsetData, orient="v",
                 set_order=None,
                 sort_by_intersection="ascend",
                 sort_by_size=None,
                 sort_by_degree=None,

                 ):
        super().__init__()

    def _render_main(self, matrix):
        pass
