"""Significance annotation for the seaborn plotters, backed by statannotations.

Marsilea melts its wide input into a long frame with *positional* categories
(``var`` is the column's index within its chunk) before handing it to seaborn.
This module keeps that convention: the user names categories with the labels of
their input, and everything here translates those labels into positions before
statannotations ever sees them. Feeding real labels to seaborn instead would
change how it scales the categorical axis and break alignment with the canvas.
"""

import warnings
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, List

import numpy as np

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


def load_annotator():
    """Import statannotations, or explain how to get it."""
    try:
        from statannotations.Annotator import Annotator
    except ImportError as e:
        raise ImportError(_INSTALL_HINT) from e
    return Annotator


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


def _value_axis_inverted(ax, orient):
    return ax.xaxis_inverted() if orient == "h" else ax.yaxis_inverted()


def _flip_value_axis(ax, orient):
    if orient == "h":
        ax.set_xlim(*ax.get_xlim()[::-1])
    else:
        ax.set_ylim(*ax.get_ylim()[::-1])


def annotate(chunk: DrawnChunk, pairs: List, plot: str, config: StatsConfig):
    """Run the tests and draw the brackets on one chunk's axes."""
    Annotator = load_annotator()

    # statannotations stacks brackets toward the high end of the value axis. A
    # left-side plot has that axis inverted, which would put them inside the
    # plot; annotate upright, then flip back. The brackets it draws live in data
    # coordinates, so they follow the flip onto the outer side.
    flipped = _value_axis_inverted(chunk.ax, chunk.orient)
    if flipped:
        _flip_value_axis(chunk.ax, chunk.orient)

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
    if config.pvalues is None:
        annotator.configure(test=config.test, **options)
        annotator.apply_and_annotate()
    else:
        annotator.configure(test=None, **options)
        annotator.set_pvalues(config.pvalues)
        annotator.annotate()

    if flipped:
        _flip_value_axis(chunk.ax, chunk.orient)
