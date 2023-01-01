from collections import Counter
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass(init=False)
class Track:
    name: str
    kind: str
    events: np.ndarray = field(repr=False)
    
    def __init__(self, name, kind, events):
        self.name = name
        self.kind = kind
        self.events = np.asarray(events)
    
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


@dataclass(init=False)
class NumTrack:
    name: str
    kind: str
    data: np.ndarray = field(repr=False)

    def __init__(self, name, kind, data):
        self.name = name
        self.kind = kind
        self.data = np.asarray(data)
    
    def get_data(self):
        return self.data


class NumTrackList:

    def __init__(self, tracks):
        self.tracks = tracks

    def add_track(self, track):
        self.tracks.append(track)

    @property
    def names(self):
        return [t.name for t in self.tracks]
    
    def get_matrix(self):
        return np.array([t.data.tolist() for t in self.tracks])


