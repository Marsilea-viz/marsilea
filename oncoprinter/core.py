import warnings
from collections import Counter
from dataclasses import dataclass, field
from itertools import count
from typing import List

import numpy as np
import pandas as pd

from heatgraphy import ClusterCanvas, Heatmap
from heatgraphy.layers import Rect, FrameRect
from heatgraphy.plotter import LayersMesh, Labels, StackBar

from .preset import SHAPE_BANK, Alteration, MATCH_POOL


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


def guess_alteration(event: str):
    for alt, rule in MATCH_POOL.items():
        if rule.is_match(event):
            return alt
    return Alteration.OTHER


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
                 custom_pieces=None,
                 ):
        self.data = data.copy()
        self.data.columns = ['patient', 'track', 'event']

        if patients_order is None:
            patients_order = self.data['patient'].unique()
        self.patients = patients_order
        self._patients_ix = dict(zip(patients_order, count(0, 1)))

        if tracks_order is None:
            tracks_order = self.data['track'].unique()
        self.tracks = tracks_order
        self._tracks_ix = dict(zip(tracks_order, count(0, 1)))

        if custom_pieces is None:
            custom_pieces = {}
        custom_events = list(custom_pieces.keys())
        self.custom_pieces = custom_pieces

        self.events = self.data['event'].unique()
        self.events_alt = dict()

        unknown_alterations = []
        for e in self.events:
            alt = guess_alteration(e)
            if alt == Alteration.OTHER:
                alt = e
                if e not in custom_events:
                    unknown_alterations.append(e)
            self.events_alt[e] = alt
        if len(unknown_alterations) > 0:
            warnings.warn(f"Found unknown alterations: {unknown_alterations}, "
                          f"please specify a piece for this alteration.")

        self._shape = (len(self.tracks), len(self.patients))

    @property
    def shape(self):
        return self._shape

    def get_layers_pieces(self):
        layers = {
            Alteration.BACKGROUND: np.ones(self._shape)
        }
        for e in self.events:
            layers[self.events_alt[e]] = np.zeros(self._shape, dtype=bool)

        for _, row in self.data.iterrows():
            patient, track, event = row
            row_ix = self._tracks_ix[track]
            col_ix = self._patients_ix[patient]
            layers[self.events_alt[event]][row_ix, col_ix] = True

        new_pieces = []
        new_layers = []
        for alt in layers.keys():
            new_layers.append(layers[alt])
            if not isinstance(alt, Alteration):
                piece = self.custom_pieces.get(alt)
                if piece is None:
                    # The default style for OTHER
                    piece = FrameRect(color="pink", label=alt)
                new_pieces.append(piece)
            else:
                new_pieces.append(SHAPE_BANK[alt])

        return new_layers, new_pieces

    def get_track_mutation_rate(self):
        gb = self.data.groupby('track', sort=False)
        ts = {}
        for track, df in gb:
            ts[track] = len(df['patient'].unique())
        counts = np.array([ts[t] for t in self.tracks])
        return counts / len(self.patients)

    def get_track_mutation_types(self):
        gb = self.data.groupby('track', sort=False)
        cs = {}
        for track, df in gb:
            cs[track] = Counter(df['event'])
        types = [cs[t] for t in self.tracks]
        return pd.DataFrame(types).fillna(0.).T

    def get_patient_mutation_types(self):
        gb = self.data.groupby('patient', sort=False)
        cs = {}
        for track, df in gb:
            cs[track] = Counter(df['event'])
        types = [cs[p] for p in self.patients]
        return pd.DataFrame(types).fillna(0.).T

    def get_pieces_colors(self):
        pass


class OncoPrint:

    def __init__(self, genomic_data=None,
                 patients_order=None,
                 tracks_order=None,
                 background_color="#BEBEBE",
                 # TODO: How to change background color
                 shrink=(.8, .8),
                 width=None,
                 height=None,
                 aspect=2.5,
                 legend_kws=None,
                 ):
        data = GenomicData(genomic_data,
                           patients_order=patients_order,
                           tracks_order=tracks_order, )

        Y, X = data.shape
        main_aspect = Y * aspect / X
        self.canvas = ClusterCanvas(
            cluster_data=np.zeros(data.shape),
            width=width, height=height,
            aspect=main_aspect)
        layers, pieces = data.get_layers_pieces()
        track_names = data.tracks

        legend_options = dict(handleheight=2, handlelength=2/aspect)
        legend_kws = {} if legend_kws is None else legend_kws
        legend_options.update(legend_kws)

        mesh = LayersMesh(layers=layers, pieces=pieces,
                          shrink=shrink, legend_kws=legend_options)
        self.canvas.add_layer(mesh)
        self.canvas.add_left(Labels(track_names, text_pad=.1))
        # Add other statistics
        track_mut_rate = data.get_track_mutation_rate()
        # Convert to percentage string
        rates = [f"{i}%" for i in (np.array(track_mut_rate) * 100).astype(int)]
        self.canvas.add_right(Labels(rates, text_pad=.1))

        track_counter = data.get_track_mutation_types()
        self.canvas.add_right(StackBar(track_counter.to_numpy()))

        patients_counter = data.get_patient_mutation_types()
        self.canvas.add_top(StackBar(patients_counter.to_numpy()))

    def append_expression(self, data, name=None):
        h = Heatmap(data)
        if name is not None:
            h.add_title(top=name, align="left")
        self.canvas /= h

    def append_clinical(self):
        pass

    def render(self):
        self.canvas.add_legends()
        self.canvas.render()
