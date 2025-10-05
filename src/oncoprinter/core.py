import warnings
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from itertools import count
from typing import Any

import numpy as np
import pandas as pd
from marsilea import ClusterBoard
from marsilea.layers import LayersMesh, FrameRect, Piece
from marsilea.plotter import Labels, StackBar, Numbers, ColorMesh
from marsilea.utils import get_canvas_size_by_data

from .preset import SHAPE_BANK, MATCH_POOL, Alteration


def guess_alteration(event: str):
    for alt, rule in MATCH_POOL.items():
        if rule.is_match(event):
            return alt
    return Alteration.OTHER


@dataclass(repr=False)
class LayerData:
    matrix: np.ndarray
    piece: Piece
    color: Any
    event: Any

    def __repr__(self):
        return f"{self.piece.label} ({self.color})"


class GenomicData:
    """Handle class for genomics data

    Parameters
    ----------
    data : pd.DataFrame
        Each column is:
            1) Sample ID
            2) Track name
            3) Alteration
    samples_order : list, optional
        The order of samples, by default None
    tracks_order : list, optional
        The order of tracks, by default None
    custom_pieces : dict, optional
        Custom pieces for each alteration, by default None

    """

    def __repr__(self):
        ntrack, nsample = self.shape
        return (
            f"{ntrack} Tracks, {nsample} Samples with "
            f"{len(self.events)} Alterations"
        )

    def __init__(
        self,
        data,
        samples_order=None,
        tracks_order=None,
        custom_pieces=None,
    ):
        self.data = data.copy()
        self.data.columns = ["sample", "track", "event"]

        if samples_order is None:
            samples_order = self.data["sample"].unique()

        self.samples = samples_order
        self._patients_ix = dict(zip(samples_order, count(0, 1)))

        if tracks_order is None:
            tracks_order = self.data["track"].unique()
        self.tracks = tracks_order
        self._tracks_ix = dict(zip(tracks_order, count(0, 1)))

        self._shape = (len(self.tracks), len(self.samples))

        if custom_pieces is None:
            custom_pieces = {}
        self.custom_pieces = custom_pieces

        self._process_alterations()

        layers = {}
        for e in self.events:
            layers[e] = np.zeros(self._shape, dtype=bool)

        for _, row in self.data.iterrows():
            patient, track, event = row
            row_ix = self._tracks_ix[track]
            col_ix = self._patients_ix[patient]
            layers[event][row_ix, col_ix] = True

        self.layers = layers

    def _process_alterations(self):
        events_alt = dict()
        custom_events = list(self.custom_pieces.keys())
        raw_events = self.data["event"].unique()

        unknown_alterations = []
        for e in raw_events:
            alt = guess_alteration(e)
            if alt == Alteration.OTHER:
                alt = e
                if e not in custom_events:
                    unknown_alterations.append(e)
            events_alt[e] = alt
        self.data["event"] = [events_alt[e] for e in self.data["event"]]
        self.events = self.data["event"].unique()
        if len(unknown_alterations) > 0:
            msg = (
                f"Found unknown alterations: {unknown_alterations}, "
                f"please specify a piece for this alteration."
            )
            warnings.warn(msg)

    @property
    def shape(self):
        return self._shape

    def get_layers_data(self, background_color="#BEBEBE"):
        # explicitly make copy
        bg_pieces = deepcopy(SHAPE_BANK[Alteration.BACKGROUND])
        bg_pieces.background_color = background_color

        # Add background layer
        layers_data = [
            LayerData(
                np.ones(self._shape), bg_pieces, background_color, Alteration.BACKGROUND
            )
        ]
        for alt in self.events:
            layer = self.layers[alt]
            if not isinstance(alt, Alteration):
                piece = self.custom_pieces.get(alt)
                if piece is None:
                    # The default style for OTHER
                    piece = FrameRect(color="pink", label=alt)
                else:
                    piece = deepcopy(piece)
            else:
                piece = deepcopy(SHAPE_BANK[alt])
            color = piece.color
            piece.background_color = background_color

            layers_data.append(LayerData(layer, piece, color, alt))

        return layers_data

    def get_track_mutation_rate(self):
        gb = self.data.groupby("track", sort=False, observed=True)
        ts = {}
        for track, df in gb:
            ts[track] = len(df["sample"].unique())
        counts = np.array([ts[t] for t in self.tracks])
        return counts / len(self.samples)

    def get_track_mutation_types(self):
        gb = self.data.groupby("track", sort=False, observed=True)
        cs = {}
        for track, df in gb:
            cs[track] = Counter(df["event"])
        return pd.DataFrame(cs).fillna(0.0).loc[:, self.tracks]

    def get_sample_mutation_types(self):
        gb = self.data.groupby("sample", sort=False, observed=True)
        cs = {}
        for track, df in gb:
            cs[track] = Counter(df["event"])
        return pd.DataFrame(cs).fillna(0.0)


class OncoPrint(ClusterBoard):
    """OncoPrint plot

    The oncoprint plot is a visualization for genomics data in cancer research.
    It's first introduced by the cBioPortal project.
    See https://www.cbioportal.org/oncoprinter for more details.

    To use this class, import from oncoprinter

        >>> from oncoprinter import OncoPrint

    Parameters
    ----------
    genomic_data : pd.DataFrame
        Genomics data, each column is:
            1) Sample ID
            2) Track name
            3) Alteration

    patients_order : list, optional
        The order of samples, by default None
    tracks_order : list, optional
        The order of tracks, by default None
    pieces : dict, optional
        Custom pieces for each alteration, by default None
        See :class:`Piece <marsilea.layers.Piece>` for details
    background_color : str, optional, default: "#BEBEBE"
        The background color
    shrink : tuple, optional, default: (0.8, 0.8)
        The shrink ratio for each layer
    width, height : float, optional
        The size in inches to define the size of main canvas
    aspect : float, optional, default: 2.5
        The aspect ratio of the main canvas
    legend_kws : dict, optional
        The options for legend, by default None
        See :class:`cat_legend <legendkit.cat_legend>` for details
    name : str, optional
        The name of this OncoPrint
    add_tracks_names : str, optional, default: "left"
        The position to add tracks names
        If None, will not add tracks names
    add_samples_names : str, optional, default: "bottom"
        The position to add samples names
        If None, will not add samples names
    add_mut_perc : str, optional, default: "right"
        The position to add mutation percentage
        If None, will not add mutation percentage
    add_tracks_counts : str, optional, default: "right"
        The position to add tracks mutation counts
        If None, will not add tracks mutation counts
    add_mut_counts : str, optional, default: "top"
        The position to add mutation counts
        If None, will not add mutation counts
    add_tracks_counts_size : float, optional, default: 0.2
        The size of tracks mutation counts
    add_tracks_counts_pad : float, optional, default: 0
        The padding of tracks mutation counts
    add_mut_counts_size : float, optional, default: 0.2
        The size of mutation counts
    add_mut_counts_pad : float, optional, default: 0.1
        The padding of mutation counts

    """

    def __init__(
        self,
        genomic_data=None,
        patients_order=None,
        tracks_order=None,
        pieces=None,
        background_color="#BEBEBE",
        shrink=(0.8, 0.8),
        width=None,
        height=None,
        aspect=2.5,
        legend_kws=None,
        name=None,
        add_tracks_names="left",
        add_samples_names="bottom",
        add_mut_perc="right",
        add_tracks_counts="right",
        add_mut_counts="top",
        add_tracks_counts_size=0.2,
        add_tracks_counts_pad=0,
        add_mut_counts_size=0.2,
        add_mut_counts_pad=0.1,
    ):
        data = GenomicData(
            genomic_data,
            samples_order=patients_order,
            tracks_order=tracks_order,
            custom_pieces=pieces,
        )
        self.genomic_data = data
        width, height = get_canvas_size_by_data(
            data.shape, width=width, height=height, scale=0.2, aspect=aspect
        )

        self.canvas = super().__init__(
            name=name, cluster_data=np.zeros(data.shape), width=width, height=height
        )

        legend_options = dict(title="Alterations", handleheight=aspect, handlelength=1)
        legend_kws = {} if legend_kws is None else legend_kws
        legend_options.update(legend_kws)

        layers, pieces, colors_mapper = [], [], {}
        for layer in data.get_layers_data(background_color):
            layers.append(layer.matrix)
            pieces.append(layer.piece)
            colors_mapper[layer.event] = layer.color
        mesh = LayersMesh(
            layers=layers, pieces=pieces, shrink=shrink, legend_kws=legend_options
        )
        self.add_layer(mesh)

        if add_tracks_names:
            self.add_plot(add_tracks_names, Labels(data.tracks))

        # Add other statistics
        track_mut_rate = data.get_track_mutation_rate()
        # Convert to percentage string
        if add_mut_perc:
            rates = [_format_percentage(t) for t in track_mut_rate]
            self.add_plot(add_mut_perc, Labels(rates))
        if add_samples_names:
            self.add_plot(add_samples_names, Labels(data.samples))

        if add_tracks_counts:
            track_counter = data.get_track_mutation_types()
            colors = [colors_mapper[e] for e in track_counter.index]
            track_bar = StackBar(track_counter, colors=colors, show_value=False)
            self.add_plot(
                add_tracks_counts,
                track_bar,
                legend=False,
                size=add_tracks_counts_size,
                pad=add_tracks_counts_pad,
            )

        if add_mut_counts:
            patients_counter = data.get_sample_mutation_types()
            colors = [colors_mapper[e] for e in patients_counter.index]
            patients_bar = StackBar(patients_counter, colors=colors, show_value=False)
            self.add_plot(
                add_mut_counts,
                patients_bar,
                legend=False,
                size=add_mut_counts_size,
                pad=add_mut_counts_pad,
            )
        self.add_legends()

    clinical_plots = {
        "bar": Numbers,
        "stack_bar": StackBar,
    }

    def add_clinical_data(self, data, plot="bar", size=None, pad=0.1, **kwargs):
        data = data.loc[self.samples_order]
        plotter = self.clinical_plots[plot]
        self.add_bottom(plotter(data, **kwargs), size=size, pad=pad)

    def add_heatmap_data(self, data, size=0.2, pad=0.1, **kwargs):
        data = data.loc[self.samples_order]
        options = {"cmap": "Blues", "label_loc": "left", **kwargs}
        self.add_bottom(ColorMesh(data, **options), size=size, pad=pad)

    @property
    def samples_order(self):
        return self.genomic_data.samples

    @property
    def tracks_order(self):
        return self.genomic_data.tracks


def _format_percentage(t):
    return f"{float(t) * 100:.2f}".rstrip("0").rstrip(".") + "%"
