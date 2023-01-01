from collections import Counter
from dataclasses import dataclass, field
from itertools import count
from typing import List

import numpy as np
import pandas as pd

from heatgraphy.base import Base




@dataclass(init=False)
class Track:
    name: str
    events: list = field(default_factory=list)

    def __init__(self, name):
        self.name = name

    def add_event(self, event):
        self.events.append(event)

    def get_event(self, event):
        return self.events == event

    def get_ratios(self):
        return pd.isnull(self.events) / len(self.events)

    def get_counter(self):
        return Counter(pd.Series(self.events).dropna())


class TrackList:

    def __init__(self, tracks):
        tracks_mapper = dict()
        for t in tracks:
            tracks_mapper.setdefault(t.name, [])
            tracks_mapper[t.name].append(t)

        self.names = list(tracks_mapper.keys())
        self.tracks = tracks
        self.tracks_mapper = tracks_mapper

    def get_event(self, event):
        data = []
        for name in self.names:
            arr = [t.get_event(event).tolist() for t in self.tracks_mapper[name]]
            data.append(np.any(arr, axis=0))
        return np.array(data)

    def get_counter(self) -> pd.DataFrame:
        return pd.DataFrame([t.get_counter() for t in self.tracks])


class GenomicData:
    """Handle class for genomics data

    Parameters
    ----------
    data : pd.DataFrame
        Each column is:
            1) Patient name
            2) Track/Gene name
            3) Alteration event
    """

    def __init__(self,
                 data,
                 patients_order=None,
                 tracks_order=None,
                 ):
        self.data = data

        if patients_order is None:
            patients_order = data.iloc[0].unique()
        self.patients = patients_order
        self._patients_ix = dict(zip(patients_order, count(0, 1)))

        if tracks_order is None:
            tracks_order = data.iloc[1].unique()
        self.tracks = tracks_order
        self._tracks_ix = dict(zip(tracks_order, count(0, 1)))

        self.events = data.iloc[2].unique()
        self._shape = (len(self.tracks), len(self.patients))

    def new_layers(self):
        return dict(zip(self.events,
                        [np.zeros(self._shape, dtype=bool) for _ in range(len(self.events))]))

    def get_layers(self):
        layers = self.new_layers()
        for _, row in self.data.iterrows():
            patient, track, alt = row
            row_ix = self._tracks_ix[track]
            col_ix = self._patients_ix[patient]
            layers[alt][row_ix, col_ix] = True
        return layers


class OncoPrint(Base):

    def __init__(self, genomic_data=None,
                 ):

        super().__init__()

    def append_expression(self):
        pass

    def append_clinical(self):
        pass


