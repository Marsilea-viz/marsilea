"""Significance annotation for the seaborn plotters, backed by statannotations.

Marsilea melts its wide input into a long frame with *positional* categories
(``var`` is the column's index within its chunk) before handing it to seaborn.
This module keeps that convention: the user names categories with the labels of
their input, and everything here translates those labels into positions before
statannotations ever sees them. Feeding real labels to seaborn instead would
change how it scales the categorical axis and break alignment with the canvas.
"""

import warnings
from dataclasses import dataclass, field, replace
from itertools import combinations
from typing import Any, Dict, List

import numpy as np
from matplotlib.lines import Line2D

#: The plots statannotations' seaborn engine implements. ``boxenplot`` and
#: ``pointplot`` are not among them.
SUPPORTED_PLOTS = ("barplot", "boxplot", "stripplot", "swarmplot", "violinplot")

_INSTALL_HINT = (
    "Statistical annotation requires `statannotations`: pip install marsilea[stats]"
)

# Seaborn kwargs that move the drawn elements. statannotations rebuilds the
# category positions itself with width=0.8, gap=0, dodge=True hardcoded, so
# these would silently desync the brackets from the artists.
POSITION_KWS = ("width", "gap", "dodge", "native_scale")

_ALL_PAIRS_LIMIT = 8

# Seaborn's own defaults, which is where it puts the boxes statannotations
# brackets. Only used to find the two ends of a cross-group bracket.
_CAT_WIDTH = 0.8

# Cross-group bracket geometry, as a fraction of the value span / figure.
_CROSS_PAD = 0.10
_CROSS_STEP = 0.26
_CROSS_STEM = 0.010
_CROSS_TEXT_PAD = 0.004


def load_annotator():
    """Import statannotations, or explain how to get it."""
    try:
        from statannotations.Annotator import Annotator
    except ImportError as e:
        raise ImportError(_INSTALL_HINT) from e
    return Annotator


def load_stats_api():
    """statannotations' testing and formatting, without its Annotator.

    A cross-group bracket spans two Axes, which ``Annotator`` cannot do -- it
    binds to one. Marsilea draws those itself, but borrows the test catalogue,
    the corrections and the p-value formatting from here so the two kinds of
    bracket cannot drift apart.
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
        CONFIGURABLE_PARAMETERS,
        ComparisonsCorrection,
    )


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
    x: str
    y: str
    hue: Any
    hue_order: Any
    orient: str
    names: Any


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
                stacklevel=4,
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
        Pairs in statannotations form, with positions instead of labels.
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


@dataclass
class Endpoint:
    """One side of a cross-group bracket, once its category has been found."""

    chunk: int
    position: int
    hue: Any = None

    def coord(self, hue_order):
        """Categorical coordinate, including seaborn's dodge for the hue level."""
        if not hue_order or self.hue is None:
            return float(self.position)
        levels = len(hue_order)
        offset = (hue_order.index(self.hue) - (levels - 1) / 2) * _CAT_WIDTH / levels
        return self.position + offset


@dataclass
class CrossPair:
    """A pair whose two sides were drawn on different chunk axes."""

    left: Endpoint
    right: Endpoint
    original: Any
    pvalue: Any = None

    @property
    def reach(self):
        """How far the bracket travels, so short ones can be stacked first."""
        return abs(self.right.chunk - self.left.chunk), abs(
            self.right.position - self.left.position
        )


@dataclass
class ChunkPlan:
    """What one chunk's Axes is asked to annotate on its own."""

    pairs: List
    pvalues: Any = None


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
        What each chunk's Axes annotates by itself, via statannotations.
    cross : list of CrossPair
        Pairs whose sides landed on different chunk axes; marsilea draws these.
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
            cross.append(CrossPair(left, right, pair, pvalue))

    return per_chunk, cross, unknown


def cross_annotations(cross, chunks, config):
    """Test every cross-group pair and format it exactly like the rest."""
    StatTest, StatResult, PValueFormat, formattable, Correction = load_stats_api()

    options = dict(config.configure_kws)
    alpha = options.get("alpha", 0.05)
    correction = options.get("comparisons_correction")

    def observations(end):
        frame = chunks[end.chunk].pdata
        keep = frame["var"] == end.position
        if end.hue is not None:
            keep &= frame["hue"] == end.hue
        return frame.loc[keep, "value"].to_numpy()

    if config.pvalues is None:
        test = StatTest.from_library(config.test)
        results = [
            test(observations(pair.left), observations(pair.right), alpha=alpha)
            for pair in cross
        ]
    else:
        results = [
            StatResult(None, None, None, None, pval=pair.pvalue, alpha=alpha)
            for pair in cross
        ]

    if correction is not None:
        if isinstance(correction, str):
            correction = Correction(correction, alpha=alpha)
        correction.apply(results)

    formatter = PValueFormat()
    formatter.config(**{k: v for k, v in options.items() if k in formattable})
    return [formatter.format_data(result) for result in results]


def _to_figure(fig, ax, orient, category, value):
    point = (value, category) if orient == "h" else (category, value)
    return fig.transFigure.inverted().transform(ax.transData.transform(point))


def _outward(fig, ax, orient):
    """Unit vector in figure coordinates pointing toward larger values."""
    limits = ax.get_xlim() if orient == "h" else ax.get_ylim()
    low = np.asarray(_to_figure(fig, ax, orient, 0, min(limits)))
    high = np.asarray(_to_figure(fig, ax, orient, 0, max(limits)))
    step = high - low
    return step / np.hypot(*step)


def _value_limits(ax, orient):
    return ax.get_xlim() if orient == "h" else ax.get_ylim()


def _set_value_limits(ax, orient, near, far):
    """Push the outer limit out, keeping whichever direction the axis runs."""
    current = _value_limits(ax, orient)
    limits = (far, near) if current[0] > current[1] else (near, far)
    ax.set_xlim(*limits) if orient == "h" else ax.set_ylim(*limits)


def draw_cross_brackets(fig, axes, cross, texts, orient, hue_order, color="0.2"):
    """Draw brackets that span chunk axes, in figure coordinates.

    Every chunk shares one value scale by the time this runs, so a value maps
    to the same figure position in all of them and only the categorical ends
    need each chunk's own transform.
    """
    order = sorted(range(len(cross)), key=lambda i: cross[i].reach)
    near, far = min(_value_limits(axes[0], orient)), max(_value_limits(axes[0], orient))
    span = far - near

    # Make room first: the transforms below have to see the final limits.
    for ax in axes:
        _set_value_limits(
            ax, orient, near, far + span * (_CROSS_PAD + _CROSS_STEP * len(cross))
        )

    direction = _outward(fig, axes[0], orient)
    stem = direction * _CROSS_STEM
    vertical_value = abs(direction[1]) > abs(direction[0])

    for level, index in enumerate(order):
        pair, text = cross[index], texts[index]
        value = far + span * (_CROSS_PAD + _CROSS_STEP * level)
        a = _to_figure(
            fig, axes[pair.left.chunk], orient, pair.left.coord(hue_order), value
        )
        b = _to_figure(
            fig, axes[pair.right.chunk], orient, pair.right.coord(hue_order), value
        )
        fig.add_artist(
            Line2D(
                [a[0] - stem[0], a[0], b[0], b[0] - stem[0]],
                [a[1] - stem[1], a[1], b[1], b[1] - stem[1]],
                transform=fig.transFigure,
                color=color,
                linewidth=1.2,
                solid_capstyle="butt",
            )
        )
        middle = (np.asarray(a) + np.asarray(b)) / 2 + direction * _CROSS_TEXT_PAD
        # `va` drives which side of the anchor the label grows on in display
        # space, for the rotated horizontal case too -- see _mirror_labels.
        grows_up = direction[1] > 0 if vertical_value else direction[0] > 0
        fig.text(
            middle[0],
            middle[1],
            text,
            transform=fig.transFigure,
            ha="center",
            va="bottom" if grows_up else "top",
            rotation=0 if vertical_value else 270,
            color=color,
        )


def _value_axis_inverted(ax, orient):
    return ax.xaxis_inverted() if orient == "h" else ax.yaxis_inverted()


def _flip_value_axis(ax, orient):
    if orient == "h":
        ax.set_xlim(*ax.get_xlim()[::-1])
    else:
        ax.set_ylim(*ax.get_ylim()[::-1])


def _mirror_labels(texts):
    """Move each label to the other side of its bracket.

    statannotations anchors the label on the bracket and lets it grow away
    from the data, using ``va="bottom"`` plus an offset in points -- both in
    display space, so both point the wrong way once the value axis is
    inverted and the label lands back on top of the plot. The brackets
    themselves are in data coordinates and need no such fix.
    """
    for text in texts:
        text.set_va("top" if text.get_va() == "bottom" else "bottom")
        dx, dy = text.get_position()
        text.set_position((-dx, -dy))


def annotate(chunk: DrawnChunk, plan: ChunkPlan, plot: str, config: StatsConfig):
    """Run the tests and draw the brackets on one chunk's axes."""
    Annotator = load_annotator()
    pairs = plan.pairs

    # statannotations stacks brackets toward the high end of the value axis. A
    # left-side plot has that axis inverted, which would put them inside the
    # plot; annotate upright, then flip back. The brackets it draws live in data
    # coordinates, so they follow the flip onto the outer side.
    flipped = _value_axis_inverted(chunk.ax, chunk.orient)
    if flipped:
        _flip_value_axis(chunk.ax, chunk.orient)
    drawn_before = len(chunk.ax.texts)

    plot_kws = {} if chunk.hue is None else {"dodge": True}
    annotator = Annotator(
        chunk.ax,
        pairs,
        plot=plot,
        data=chunk.pdata,
        x=chunk.x,
        y=chunk.y,
        hue=chunk.hue,
        order=list(range(len(chunk.names))),
        hue_order=chunk.hue_order,
        orient=chunk.orient,
        verbose=False,
        **plot_kws,
    )

    options = dict(verbose=0)
    options.update(config.configure_kws)
    if plan.pvalues is None:
        annotator.configure(test=config.test, **options)
        annotator.apply_and_annotate()
    else:
        # Only this chunk's share of the supplied values, one per drawn pair.
        annotator.configure(test=None, **options)
        annotator.set_pvalues(plan.pvalues)
        annotator.annotate()

    if flipped:
        _flip_value_axis(chunk.ax, chunk.orient)
        _mirror_labels(chunk.ax.texts[drawn_before:])
