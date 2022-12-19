from dataclasses import dataclass
import numpy as np


@dataclass(init=False)
class TrackBase:
    name: str
    ttype: str


@dataclass(init=False)
class Track:
    name: str
    style: str
    events: np.ndarray
    
    def __init__(self, name, style, events):
        self.name = name
        self.style = style
        self.events = np.asarray(events)
    
    def get_event(self, event):
        return self.events == event


@dataclass(init=False)
class NumericTrack:
    name: str
    style: str
    data: np.ndarray

    def __init__(self, name, style, data):
        self.name = name
        self.style = style
        self.data = np.asarray(data)
    
    def get_data(self):
        return self.data


class NumTrackList:

    def __init__(self, tracks):

        self.names = [t.name for t in tracks]
        self.matrix = np.array(
            [t.data.tolist() for t in tracks])
    
    def get_matrix(self):
        return self.matrix



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

