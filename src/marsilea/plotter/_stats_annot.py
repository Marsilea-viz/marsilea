"""Significance annotation for the seaborn plotters.

Marsilea melts its wide input into a long frame with *positional* categories
(``var`` is the column's index within its chunk) before handing it to seaborn.
This module keeps that convention: the user names categories with the labels of
their input, and everything here translates those labels into positions. Feeding
real labels to seaborn instead would change how it scales the categorical axis
and break alignment with the canvas.

Marsilea draws every bracket itself, in figure coordinates, so that a bracket
between two groups of a split canvas -- which has to span two Axes -- looks
exactly like one inside a single group. The statistics come from
statannotations: its test catalogue, its multiple-comparison corrections and
its p-value formatting, none of which touch seaborn. Its ``Annotator`` is not
used, which is also what keeps this off seaborn's private API.
"""

import warnings
from dataclasses import dataclass, field, replace
from itertools import combinations
from typing import Any, Dict, List

import matplotlib as mpl
import numpy as np
from matplotlib.collections import Collection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text

from ..utils import find_stack_level

#: Every seaborn plotter marsilea wraps can be annotated.
SUPPORTED_PLOTS = (
    "barplot",
    "boxplot",
    "boxenplot",
    "pointplot",
    "stripplot",
    "swarmplot",
    "violinplot",
)

#: The plots seaborn does not dodge by default when given a hue.
_UNDODGED = ("stripplot", "swarmplot", "pointplot")

_INSTALL_HINT = (
    "Statistical annotation requires `statannotations`: pip install marsilea[stats]"
)

_ALL_PAIRS_LIMIT = 8
_CAT_WIDTH = 0.8

#: Bracket geometry, in points.
_STEM_POINTS = 4.0

#: Clear space kept between two labels on the same row.
_LABEL_GAP_POINTS = 4.0

#: Share of the panel kept clear above the top bracket, and the least the data
#: is allowed to shrink to when there are many rows of brackets.
_PANEL_MARGIN = 0.02
_MIN_DATA_SHARE = 0.25

#: Options marsilea consumes itself, on top of what PValueFormat accepts.
_STYLE_KWS = ("color", "line_width", "text_offset")
_STATS_KWS = ("alpha", "comparisons_correction")


def load_stats_api():
    """statannotations' statistics, without its Annotator.

    Every name here is pure statistics or formatting -- none of it imports
    seaborn, so none of it can break when seaborn moves its internals.
    """
    try:
        from statannotations.PValueFormat import CONFIGURABLE_PARAMETERS, PValueFormat
        from statannotations.stats.ComparisonsCorrection import ComparisonsCorrection
        from statannotations.stats.StatResult import StatResult
        from statannotations.stats.StatTest import StatTest
    except ImportError as e:
        raise ImportError(_INSTALL_HINT) from e
    return (
        StatTest,
        StatResult,
        PValueFormat,
        tuple(CONFIGURABLE_PARAMETERS),
        ComparisonsCorrection,
    )


def accepted_options():
    """Every keyword :meth:`annotate_stats` will take, for error messages."""
    _, _, _, formattable, _ = load_stats_api()
    return tuple(sorted(set(_STYLE_KWS + _STATS_KWS + formattable)))


@dataclass
class StatsConfig:
    """What the user asked for in :meth:`annotate_stats`."""

    pairs: Any
    ref: Any = None
    test: Any = "Mann-Whitney"
    pvalues: Any = None
    configure_kws: Dict = field(default_factory=dict)


@dataclass
class DrawnChunk:
    """One rendered axes and the long-form frame that produced it."""

    ax: Any
    pdata: Any
    hue: Any
    names: Any


@dataclass
class CategoryLayout:
    """Where seaborn put each (category, hue level).

    Built from the same options seaborn was called with, so the brackets cannot
    drift from the boxes the way a parallel position model does.
    """

    hue_order: Any = None
    width: float = _CAT_WIDTH
    dodge: bool = True

    @classmethod
    def from_kws(cls, plot, hue_order, kws):
        dodge = kws.get("dodge", plot not in _UNDODGED)
        if dodge == "auto":
            dodge = True
        return cls(
            hue_order=hue_order,
            width=kws.get("width", _CAT_WIDTH),
            dodge=bool(dodge),
        )

    @property
    def dodged(self):
        return bool(self.hue_order) and self.dodge

    def coord(self, position, hue=None):
        """Categorical coordinate of one drawn group."""
        if not self.dodged or hue is None:
            return float(position)
        levels = len(self.hue_order)
        offset = (self.hue_order.index(hue) - (levels - 1) / 2) * self.width / levels
        return position + offset

    def coords(self, n_categories):
        """Every drawn categorical coordinate, in order."""
        levels = self.hue_order if self.dodged else [None]
        return sorted(
            self.coord(position, hue)
            for position in range(n_categories)
            for hue in levels
        )


@dataclass
class Endpoint:
    """One side of a bracket, once its category has been found."""

    chunk: int
    position: int
    hue: Any = None

    def key(self, layout):
        """Sort key placing every drawn group on one line across the chunks."""
        return (self.chunk, layout.coord(self.position, self.hue))


@dataclass
class Bracket:
    """One comparison to draw, wherever its two sides ended up."""

    left: Endpoint
    right: Endpoint
    original: Any
    pvalue: Any = None

    @property
    def crosses(self):
        return self.left.chunk != self.right.chunk


@dataclass
class ChunkPlan:
    """What one chunk's Axes is asked to annotate on its own."""

    pairs: List
    pvalues: Any = None


# --- turning the user's pairs into positions -------------------------------


def _to_position(item, lookup, has_hue):
    """Translate one side of a pair into positional form.

    With hue data a side is ``(category, hue_level)``, otherwise a bare
    category label. Returns ``None`` when the category is not in this chunk.
    """
    if has_hue:
        if not (isinstance(item, tuple) and len(item) == 2):
            raise ValueError(
                "With hue data, each side of a pair must be "
                f"(category, hue_level); got {item!r}"
            )
        label, hue = item
        pos = lookup.get(label)
        return None if pos is None else (pos, hue)

    if isinstance(item, tuple):
        raise ValueError(
            f"Without hue data, each side of a pair is a category label; got {item!r}"
        )
    pos = lookup.get(item)
    return None if pos is None else pos


def _hue_pairs(names, hue_order, ref):
    """Compare hue levels inside every column."""
    if not hue_order:
        raise ValueError(
            "pairs='hue' needs hue data, pass a dict of arrays as the input data"
        )
    if ref is None:
        combos = list(combinations(hue_order, 2))
    else:
        if ref not in hue_order:
            raise ValueError(f"ref={ref!r} is not one of the hue levels {hue_order}")
        combos = [(ref, h) for h in hue_order if h != ref]
    return [((pos, a), (pos, b)) for pos in range(len(names)) for a, b in combos]


def _all_pairs(names, hue_order, ref):
    """Compare columns with each other, once per hue level."""
    lookup = {name: pos for pos, name in enumerate(names)}
    if ref is None:
        combos = list(combinations(range(len(names)), 2))
        if len(names) > _ALL_PAIRS_LIMIT:
            warnings.warn(
                f"pairs='all' on {len(names)} categories draws {len(combos)} "
                "brackets, which is rarely readable. Consider listing the pairs "
                "you care about.",
                stacklevel=find_stack_level(),
            )
    else:
        ref_pos = lookup.get(ref)
        if ref_pos is None:
            # The reference column lives in another chunk; nothing to compare here.
            return []
        combos = [(ref_pos, p) for p in range(len(names)) if p != ref_pos]

    if not hue_order:
        return [(a, b) for a, b in combos]
    return [((a, h), (b, h)) for a, b in combos for h in hue_order]


def resolve_pairs(config, names, hue_order):
    """Turn the user's ``pairs`` into positional pairs for this chunk.

    Parameters
    ----------
    config : StatsConfig
    names : array
        Labels of this chunk's categories, in drawing order.
    hue_order : list or None

    Returns
    -------
    pairs : list
        Pairs with positions instead of labels.
    dropped : list
        The explicit pairs that name a category outside this chunk.
    """
    names = np.asarray(names)

    if isinstance(config.pairs, str):
        if config.pairs == "hue":
            return _hue_pairs(names, hue_order, config.ref), []
        if config.pairs == "all":
            return _all_pairs(names, hue_order, config.ref), []
        raise ValueError(
            f"Unknown pairs={config.pairs!r}, use 'hue', 'all' or a list of pairs"
        )

    lookup = {name: pos for pos, name in enumerate(names)}
    has_hue = bool(hue_order)
    pairs, dropped = [], []
    for pair in config.pairs:
        left, right = (_to_position(item, lookup, has_hue) for item in pair)
        if (left is None) or (right is None):
            dropped.append(pair)
        else:
            pairs.append((left, right))
    return pairs, dropped


def _catalogue(chunk_names):
    """Map every category label to the chunk and position it ended up at."""
    return {
        name: (chunk, position)
        for chunk, names in enumerate(chunk_names)
        for position, name in enumerate(np.asarray(names))
    }


def _endpoint(item, catalogue, has_hue):
    label, hue = item if has_hue else (item, None)
    found = catalogue.get(label)
    return None if found is None else Endpoint(found[0], found[1], hue)


def _ref_pairs_over_all_chunks(config, catalogue, hue_order):
    """Expand ``pairs="all", ref=...`` against every category, not one chunk's.

    Without this the reference silently says nothing about the groups it does
    not live in, which is exactly the comparison a reference is asked for.
    """
    if config.ref not in catalogue:
        raise ValueError(f"ref={config.ref!r} is not one of the categories")
    others = [name for name in catalogue if name != config.ref]
    if not hue_order:
        return [(config.ref, other) for other in others]
    return [((config.ref, hue), (other, hue)) for other in others for hue in hue_order]


def plan_pairs(config, chunk_names, hue_order):
    """Split the requested pairs into per-chunk work and cross-chunk work.

    Returns
    -------
    per_chunk : list of ChunkPlan
        Pairs whose two sides share one chunk's Axes.
    cross : list of Bracket
        Pairs whose sides landed on different chunk axes.
    unknown : list
        Pairs naming a category that is nowhere in the data.
    """
    catalogue = _catalogue(chunk_names)
    if config.pairs == "all" and config.ref is not None and len(chunk_names) > 1:
        config = replace(
            config,
            pairs=_ref_pairs_over_all_chunks(config, catalogue, hue_order),
            ref=None,
        )

    requested = None if isinstance(config.pairs, str) else list(config.pairs)
    per_chunk, dropped_per_chunk = [], []
    for names in chunk_names:
        pairs, dropped = resolve_pairs(config, names, hue_order)
        dropped = set(dropped)
        pvalues = None
        if config.pvalues is not None and requested is not None:
            # Only this chunk's share, in the order the user listed the pairs.
            pvalues = [
                p for p, pair in zip(config.pvalues, requested) if pair not in dropped
            ]
        per_chunk.append(ChunkPlan(pairs, pvalues))
        dropped_per_chunk.append(dropped)

    cross, unknown = [], []
    if requested is not None and dropped_per_chunk:
        never = set.intersection(*dropped_per_chunk)
        has_hue = bool(hue_order)
        for index, pair in enumerate(requested):
            if pair not in never:
                continue
            left, right = (_endpoint(item, catalogue, has_hue) for item in pair)
            if left is None or right is None:
                unknown.append(pair)
                continue
            pvalue = None if config.pvalues is None else config.pvalues[index]
            cross.append(Bracket(left, right, pair, pvalue))

    return per_chunk, cross, unknown


def flatten(per_chunk, cross, hue_order):
    """One list of brackets, whether or not they stay inside a chunk."""
    brackets = list(cross)
    has_hue = bool(hue_order)
    for chunk, plan in enumerate(per_chunk):
        pvalues = plan.pvalues or [None] * len(plan.pairs)
        for pair, pvalue in zip(plan.pairs, pvalues):
            ends = []
            for side in pair:
                position, hue = side if has_hue else (side, None)
                ends.append(Endpoint(chunk, position, hue))
            brackets.append(Bracket(ends[0], ends[1], pair, pvalue))
    return brackets


# --- statistics ------------------------------------------------------------


def annotation_texts(brackets, chunks, config):
    """Test every bracket and format the labels, all as one family.

    Correcting across every drawn comparison at once is the point of doing this
    in one pass: a per-Axes correction would under-correct a split canvas.
    """
    StatTest, StatResult, PValueFormat, formattable, Correction = load_stats_api()

    options = dict(config.configure_kws)
    alpha = options.get("alpha", 0.05)
    correction = options.get("comparisons_correction")

    def observations(end):
        frame = chunks[end.chunk].pdata
        keep = frame["var"] == end.position
        if end.hue is not None:
            keep &= frame["hue"] == end.hue
        # Wide input pads its short columns with NaN. Seaborn already draws a
        # padded slot as absent; a test given one returns pval=nan, which
        # formats as an empty label on a bracket that is drawn regardless.
        return frame.loc[keep, "value"].dropna().to_numpy()

    if config.pvalues is None:
        test = StatTest.from_library(config.test)
        results = [
            test(observations(b.left), observations(b.right), alpha=alpha)
            for b in brackets
        ]
    else:
        results = [
            StatResult(None, None, None, None, pval=b.pvalue, alpha=alpha)
            for b in brackets
        ]

    if correction is not None:
        if isinstance(correction, str):
            correction = Correction(correction, alpha=alpha)
        correction.apply(results)

    formatter = PValueFormat()
    formatter.config(**{k: v for k, v in options.items() if k in formattable})
    texts = [formatter.format_data(result) for result in results]

    # An unlabelled bracket is the one failure a reader cannot see on the
    # figure: too few observations to test formats the same as a p-value the
    # caller passed as nan, and both look like a finished plot.
    if blank := [b.original for b, t in zip(brackets, texts) if not t.strip()]:
        warnings.warn(
            f"{len(blank)} pair(s) produced no p-value and are drawn without a "
            f"label: {sorted(blank, key=str)}",
            stacklevel=find_stack_level(),
        )
    return texts


# --- measuring what was actually drawn -------------------------------------


def _artist_points(artist, orient):
    """(categorical, value) pairs an artist occupies, or None to skip it."""
    if isinstance(artist, Collection):
        offsets = artist.get_offsets()
        parts = [np.asarray(offsets, dtype=float)] if len(offsets) else []
        parts += [path.vertices for path in artist.get_paths() if len(path.vertices)]
        if not parts:
            return None
        points = np.vstack(parts)
    elif isinstance(artist, Patch):
        path = artist.get_path()
        if path is None or not len(path.vertices):
            return None
        points = artist.get_patch_transform().transform(path.vertices)
    elif isinstance(artist, Line2D):
        x = np.asarray(artist.get_xdata(), dtype=float)
        y = np.asarray(artist.get_ydata(), dtype=float)
        if not len(x) or len(x) != len(y):
            return None
        points = np.column_stack([x, y])
    else:
        return None

    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        return None
    categorical, value = (
        (points[:, 1], points[:, 0]) if orient == "h" else (points[:, 0], points[:, 1])
    )
    return categorical, value


def measure_extents(ax, orient, coords):
    """Highest drawn value at each categorical coordinate.

    A bracket has to clear what was drawn, not what is in the data: whisker
    caps, error bars, outlier points and violin bodies all reach past it.
    """
    coords = np.asarray(coords, dtype=float)
    extents = {float(c): -np.inf for c in coords}
    if not len(coords):
        return extents
    # Half the gap between neighbouring groups, so a point is only claimed by
    # the group it was drawn for.
    reach = np.min(np.diff(coords)) / 2 if len(coords) > 1 else 0.5

    for artist in list(ax.collections) + list(ax.patches) + list(ax.lines):
        found = _artist_points(artist, orient)
        if found is None:
            continue
        categorical, value = found
        # Bin every point rather than place the whole artist by its mean: a
        # strip or swarm plot puts *all* categories in one collection per hue
        # level, so by its mean it belongs to no group at all.
        nearest = np.argmin(np.abs(coords[None, :] - categorical[:, None]), axis=1)
        claimed = np.abs(coords[nearest] - categorical) <= reach
        for index in np.unique(nearest[claimed]):
            group = claimed & (nearest == index)
            key = float(coords[index])
            extents[key] = max(extents[key], float(value[group].max()))

    finite = [v for v in extents.values() if np.isfinite(v)]
    fallback = max(finite) if finite else 0.0
    return {k: (v if np.isfinite(v) else fallback) for k, v in extents.items()}


# --- placing and drawing ---------------------------------------------------


def assign_levels(spans):
    """Give every bracket the lowest tier where nothing is in its way.

    *spans* are the intervals the brackets occupy along the categorical
    direction, in figure coordinates and already widened to hold their labels.
    Working in figure space rather than in categories is what lets a label
    wider than its own bracket push its neighbours up instead of printing on
    top of them, and it measures the gap between chunks correctly too.

    Tiers are integers: the value they map to is decided later, once the room
    a label needs is known.
    """
    order = sorted(
        range(len(spans)), key=lambda i: (spans[i][1] - spans[i][0], spans[i][0])
    )
    tiers = [0] * len(spans)
    placed = []
    for index in order:
        low, high = spans[index]
        tier = 0
        while any(
            t == tier and low < other_high and other_low < high
            for other_low, other_high, t in placed
        ):
            tier += 1
        tiers[index] = tier
        placed.append((low, high, tier))
    return tiers


def _renderer(fig):
    """A renderer to measure text with, or None if the backend cannot give one."""
    for source in (fig, getattr(fig, "canvas", None)):
        for name in ("_get_renderer", "get_renderer"):
            get = getattr(source, name, None)
            if get is None:
                continue
            try:
                return get()
            except Exception:
                continue
    return None


def _label_half_widths(fig, texts, style):
    """Half the width of each label, as a fraction of the figure.

    A label is laid along the categorical direction in both orientations -- a
    horizontal plot rotates it a quarter turn -- so its long dimension is what
    has to clear the neighbours either way.
    """
    size = style.fontsize
    if not isinstance(size, (int, float)):
        size = mpl.rcParams["font.size"]
    figure_width = fig.get_window_extent().width
    renderer = _renderer(fig)
    if renderer is None:
        # No renderer to measure with; 0.6 em per character is close enough to
        # keep labels off each other.
        return [len(t) * size * 0.6 * fig.dpi / 72 / figure_width / 2 for t in texts]

    widths = []
    for text in texts:
        probe = Text(0, 0, text, fontsize=size, figure=fig)
        widths.append(probe.get_window_extent(renderer).width / figure_width / 2)
    return widths


def _panel_extent(fig, axes, axis):
    """How far the plot reaches along the categorical direction, in the figure."""
    boxes = [
        ax.get_window_extent().transformed(fig.transFigure.inverted()) for ax in axes
    ]
    if axis == 0:
        return min(b.x0 for b in boxes), max(b.x1 for b in boxes)
    return min(b.y0 for b in boxes), max(b.y1 for b in boxes)


def bracket_spans(fig, axes, brackets, texts, layout, orient, style):
    """The figure-space interval each bracket needs, and where its label sits.

    The interval holds the label, not just the bracket, so a label wider than
    its own bracket pushes its neighbours onto another row instead of printing
    over them. A label is also nudged back inside the plot when centring it
    would hang it over the axis.
    """
    half_widths = _label_half_widths(fig, texts, style)
    axis = 1 if orient == "h" else 0
    gap = _LABEL_GAP_POINTS / (72 * fig.get_size_inches()[axis])
    panel_low, panel_high = _panel_extent(fig, axes, axis)

    spans, centres = [], []
    for bracket, half in zip(brackets, half_widths):
        ends = [
            _to_figure(
                fig,
                axes[end.chunk],
                orient,
                layout.coord(end.position, end.hue),
                0,
            )[axis]
            for end in (bracket.left, bracket.right)
        ]
        low, high = min(ends), max(ends)
        centre = (low + high) / 2
        if panel_high - panel_low > 2 * half:
            centre = min(max(centre, panel_low + half), panel_high - half)
        centres.append(centre)
        # `gap` keeps neighbours from abutting, which reads as one long string.
        spans.append((min(low, centre - half - gap), max(high, centre + half + gap)))
    return spans, centres


@dataclass
class BracketStyle:
    """How every bracket is drawn, whichever axes it spans."""

    color: str = "0.2"
    line_width: float = 1.5
    text_offset: float = 1.0  # points
    fontsize: Any = None

    @classmethod
    def from_kws(cls, kws):
        known = {k: kws[k] for k in _STYLE_KWS if k in kws}
        return cls(fontsize=kws.get("fontsize"), **known)

    def tier_points(self):
        """Height one row of brackets needs, label included."""
        size = self.fontsize
        if not isinstance(size, (int, float)):
            size = mpl.rcParams["font.size"]
        return _STEM_POINTS + self.text_offset + size * 1.35


def _to_figure(fig, ax, orient, categorical, value):
    point = (value, categorical) if orient == "h" else (categorical, value)
    return fig.transFigure.inverted().transform(ax.transData.transform(point))


def _panel_points(fig, ax, orient):
    """How many points the axes measures along the value direction."""
    box = ax.get_window_extent()
    pixels = box.width if orient == "h" else box.height
    return pixels * 72 / fig.dpi


def place_levels(fig, ax, orient, tiers, style, near, data_top):
    """Turn tiers into values, sizing the panel so every label fits.

    Solved rather than iterated: the label row is a fixed number of points, so
    its share of the panel is known, and the value range follows from what is
    left for the data.
    """
    rows = max(tiers) + 1 if len(tiers) else 0
    panel = _panel_points(fig, ax, orient)
    row = style.tier_points() / panel  # fraction of the panel per bracket row
    data_share = 1 - rows * row - _PANEL_MARGIN

    crowded = data_share < _MIN_DATA_SHARE
    if crowded:
        # Too many rows for the panel; keep the data legible and let the
        # brackets tighten rather than squash the plot to nothing.
        data_share = _MIN_DATA_SHARE
        row = (1 - data_share - _PANEL_MARGIN) / rows

    reach = max(data_top - near, np.finfo(float).eps)
    span = reach / data_share
    levels = [data_top + (tier + 0.5) * row * span for tier in tiers]
    return levels, near + span, crowded


def draw_brackets(fig, axes, brackets, levels, texts, centres, layout, orient, style):
    """Draw every bracket in figure coordinates, so they all match.

    A bracket between two groups has to span two Axes, which no single Axes'
    data coordinates can express; using figure coordinates for the ones inside
    a group too is what keeps the two looking the same.
    """
    limits = axes[0].get_xlim() if orient == "h" else axes[0].get_ylim()
    reference = np.asarray(_to_figure(fig, axes[0], orient, 0, min(limits)))
    towards = np.asarray(_to_figure(fig, axes[0], orient, 0, max(limits))) - reference
    outward = towards / np.hypot(*towards)
    vertical_value = abs(outward[1]) > abs(outward[0])

    inches = np.asarray(fig.get_size_inches())
    per_point = 1 / (72 * inches)  # figure fraction per point, (x, y)
    stem = outward * _STEM_POINTS * per_point
    pad = outward * style.text_offset * per_point

    # A rotated label is aligned by its rotated bounding box, so `ha` is what
    # pushes it clear of a horizontal bracket and `va` of a vertical one.
    if vertical_value:
        align = dict(ha="center", va="bottom" if outward[1] > 0 else "top")
    else:
        align = dict(ha="left" if outward[0] > 0 else "right", va="center")

    axis = 1 if orient == "h" else 0
    for bracket, level, text, centre in zip(brackets, levels, texts, centres):
        ends = [
            np.asarray(
                _to_figure(
                    fig,
                    axes[end.chunk],
                    orient,
                    layout.coord(end.position, end.hue),
                    level,
                )
            )
            for end in (bracket.left, bracket.right)
        ]
        a, b = ends
        fig.add_artist(
            Line2D(
                [a[0] - stem[0], a[0], b[0], b[0] - stem[0]],
                [a[1] - stem[1], a[1], b[1], b[1] - stem[1]],
                transform=fig.transFigure,
                color=style.color,
                linewidth=style.line_width,
                solid_capstyle="butt",
            )
        )
        middle = (a + b) / 2 + pad
        middle[axis] = centre
        fig.text(
            middle[0],
            middle[1],
            text,
            transform=fig.transFigure,
            rotation=0 if vertical_value else 270,
            color=style.color,
            fontsize=style.fontsize,
            **align,
        )


def _set_value_limits(ax, orient, near, far):
    """Push the outer limit out, keeping whichever direction the axis runs."""
    current = ax.get_xlim() if orient == "h" else ax.get_ylim()
    limits = (far, near) if current[0] > current[1] else (near, far)
    ax.set_xlim(*limits) if orient == "h" else ax.set_ylim(*limits)


def annotate(fig, axes, chunks, brackets, config, layout, orient, plot):
    """Test, place and draw every bracket for one plotter."""
    if not brackets:
        return

    texts = annotation_texts(brackets, chunks, config)
    style = BracketStyle.from_kws(config.configure_kws)

    n_categories = max(len(chunk.names) for chunk in chunks)
    coords = layout.coords(n_categories)
    extents = {}
    for index, chunk in enumerate(chunks):
        for coord, top in measure_extents(chunk.ax, orient, coords).items():
            extents[(index, coord)] = top

    limits = axes[0].get_xlim() if orient == "h" else axes[0].get_ylim()
    near = min(limits)
    spans, centres = bracket_spans(fig, axes, brackets, texts, layout, orient, style)
    tiers = assign_levels(spans)
    levels, far, crowded = place_levels(
        fig, axes[0], orient, tiers, style, near, max(extents.values())
    )
    if crowded:
        warnings.warn(
            f"{max(tiers) + 1} rows of brackets do not fit above the plot; "
            "the labels will be tight. Give the plot more room, or compare "
            "fewer pairs.",
            stacklevel=find_stack_level(),
        )

    # Make room before drawing: the transforms below need the final limits.
    for ax in axes:
        _set_value_limits(ax, orient, near, far)

    draw_brackets(fig, axes, brackets, levels, texts, centres, layout, orient, style)


def undodged_pairs(brackets, layout):
    """Pairs whose two sides were drawn on top of each other."""
    return [
        bracket.original
        for bracket in brackets
        if bracket.left.key(layout) == bracket.right.key(layout)
    ]
