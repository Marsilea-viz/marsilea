"""Significance annotation on the seaborn plotters.

The pair-resolution tests are pure logic and run everywhere; the rendering
tests need the optional ``statannotations`` extra.
"""

import warnings

import numpy as np
import pandas as pd
import pytest
from matplotlib.patches import PathPatch

import marsilea as ma
import marsilea.plotter as mp
from marsilea.plotter._stats_annot import StatsConfig, resolve_pairs

HUE = ["WT", "KO"]


@pytest.fixture
def rng():
    return np.random.default_rng(0)


@pytest.fixture
def wide(rng):
    """Wide data with labelled columns, matching a 12-column canvas."""
    cols = [f"c{i}" for i in range(12)]
    return {
        "WT": pd.DataFrame(rng.normal(0, 1, (30, 12)), columns=cols),
        "KO": pd.DataFrame(rng.normal(2, 1, (30, 12)), columns=cols),
    }


# --- pair resolution ---


def test_resolve_hue_pairs():
    pairs, dropped = resolve_pairs(StatsConfig(pairs="hue"), ["a", "b"], HUE)
    assert pairs == [((0, "WT"), (0, "KO")), ((1, "WT"), (1, "KO"))]
    assert dropped == []


def test_resolve_hue_pairs_needs_hue():
    with pytest.raises(ValueError, match="needs hue data"):
        resolve_pairs(StatsConfig(pairs="hue"), ["a", "b"], None)


def test_resolve_hue_ref_reduces_to_reference():
    config = StatsConfig(pairs="hue", ref="WT")
    pairs, _ = resolve_pairs(config, ["a"], ["WT", "KO", "DKO"])
    assert pairs == [((0, "WT"), (0, "KO")), ((0, "WT"), (0, "DKO"))]


def test_resolve_hue_ref_must_be_a_hue_level():
    with pytest.raises(ValueError, match="not one of the hue levels"):
        resolve_pairs(StatsConfig(pairs="hue", ref="nope"), ["a"], HUE)


def test_resolve_all_pairs_without_hue():
    pairs, _ = resolve_pairs(StatsConfig(pairs="all"), ["a", "b", "c"], None)
    assert pairs == [(0, 1), (0, 2), (1, 2)]


def test_resolve_all_pairs_repeats_per_hue_level():
    pairs, _ = resolve_pairs(StatsConfig(pairs="all"), ["a", "b"], HUE)
    assert pairs == [((0, "WT"), (1, "WT")), ((0, "KO"), (1, "KO"))]


def test_resolve_all_pairs_with_ref_column():
    config = StatsConfig(pairs="all", ref="b")
    pairs, _ = resolve_pairs(config, ["a", "b", "c"], None)
    assert pairs == [(1, 0), (1, 2)]


def test_resolve_all_pairs_ref_outside_chunk_yields_nothing():
    """The reference column lives in another chunk, so this chunk draws nothing."""
    pairs, _ = resolve_pairs(StatsConfig(pairs="all", ref="z"), ["a", "b"], None)
    assert pairs == []


def test_resolve_all_pairs_warns_when_dense():
    names = [f"c{i}" for i in range(9)]
    with pytest.warns(UserWarning, match="rarely readable"):
        resolve_pairs(StatsConfig(pairs="all"), names, None)


def test_resolve_explicit_pairs_translates_labels_to_positions():
    config = StatsConfig(pairs=[(("b", "WT"), ("b", "KO")), (("a", "WT"), ("c", "KO"))])
    pairs, dropped = resolve_pairs(config, ["a", "b", "c"], HUE)
    assert pairs == [((1, "WT"), (1, "KO")), ((0, "WT"), (2, "KO"))]
    assert dropped == []


def test_resolve_explicit_pairs_without_hue_translates_labels_to_positions():
    config = StatsConfig(pairs=[("a", "c")])
    pairs, dropped = resolve_pairs(config, ["a", "b", "c"], None)
    assert pairs == [(0, 2)]
    assert dropped == []


def test_hue_data_needs_hue_levels_in_the_pairs():
    config = StatsConfig(pairs=[("a", "b")])
    with pytest.raises(ValueError, match=r"must be \(category, hue_level\)"):
        resolve_pairs(config, ["a", "b"], HUE)


def test_plain_data_rejects_hue_levels_in_the_pairs():
    config = StatsConfig(pairs=[(("a", "WT"), ("b", "WT"))])
    with pytest.raises(ValueError, match="each side of a pair is a category label"):
        resolve_pairs(config, ["a", "b"], None)


def test_resolve_explicit_pairs_drops_labels_outside_the_chunk():
    config = StatsConfig(pairs=[("a", "b"), ("a", "z")])
    pairs, dropped = resolve_pairs(config, ["a", "b"], None)
    assert pairs == [(0, 1)]
    assert dropped == [("a", "z")]


def test_resolve_pairs_accepts_integer_labels():
    """A plain array input names its categories by position."""
    config = StatsConfig(pairs=[(0, 2)])
    pairs, dropped = resolve_pairs(config, np.arange(4), None)
    assert pairs == [(0, 2)]
    assert dropped == []


def test_resolve_pairs_rejects_unknown_shorthand():
    with pytest.raises(ValueError, match="Unknown pairs"):
        resolve_pairs(StatsConfig(pairs="everything"), ["a"], None)


# --- configuration errors, no statannotations needed for the plot check ---


@pytest.mark.parametrize("PlotClass", [mp.Boxen, mp.Point])
def test_unsupported_plots_raise(rng, PlotClass):
    plot = PlotClass(rng.standard_normal((10, 6)))
    with pytest.raises(ValueError, match="statannotations cannot annotate"):
        plot.annotate_stats(pairs="all")


# --- rendering ---

pytest.importorskip("statannotations")


def _side_axes(board, plot):
    axes = board.layout.get_ax(plot.name)
    return axes if isinstance(axes, list) else [axes]


@pytest.mark.parametrize("PlotClass", [mp.Bar, mp.Box, mp.Violin, mp.Strip, mp.Swarm])
def test_annotate_every_supported_plot(rng, wide, PlotClass):
    plot = PlotClass(wide)
    plot.annotate_stats(pairs="hue", text_format="star")
    h = ma.Heatmap(rng.standard_normal((8, 12)))
    h.add_top(plot, size=2)
    h.render()
    assert len(_side_axes(h, plot)[0].texts) == 12


def _annotated_board(side, orient, pairs, n_cat=6):
    """A ``n_cat``-column canvas with an annotated Box on one side."""
    rng = np.random.default_rng(0)
    cols = [f"c{i}" for i in range(n_cat)]
    data = {
        k: pd.DataFrame(rng.normal(shift, 1, (30, n_cat)), columns=cols)
        for k, shift in [("WT", 0), ("KO", 2)]
    }
    plot = mp.Box(data, orient=orient)
    plot.annotate_stats(pairs=pairs, text_format="star")
    h = ma.Heatmap(rng.standard_normal((n_cat, n_cat)), width=2, height=2)
    h.add_plot(side, plot, size=2, name="p")
    h.render()
    h.figure.canvas.draw()
    return h, data


@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_labels_land_beyond_the_data_on_every_side(side, orient):
    """Whichever way the value axis runs, the label sits past the data.

    Only a horizontal plot on the left has that axis inverted, but assert it
    everywhere so a change to the orientation handling cannot quietly put
    labels back on top of the plot.
    """
    h, data = _annotated_board(side, orient, pairs="hue")
    ax = h.get_ax("p")
    value_axis = 0 if orient == "h" else 1
    to_data = ax.transData.inverted()

    assert len(ax.texts) == 6
    for text in ax.texts:
        category = int(round(text.xy[1 - value_axis]))
        span = to_data.transform(text.get_window_extent().get_points())[:, value_axis]
        reach = max(d.iloc[:, category].max() for d in data.values())
        assert min(span) > reach
        lo, hi = sorted(ax.get_xlim() if orient == "h" else ax.get_ylim())
        assert lo <= min(span) and max(span) <= hi


@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_brackets_land_on_the_category_they_name(side, orient):
    """The categorical axis is inverted for horizontal plots; positions must hold."""
    h, _ = _annotated_board(side, orient, pairs=[(("c4", "WT"), ("c4", "KO"))])
    ax = h.get_ax("p")

    (text,) = ax.texts
    category_axis = 1 if orient == "h" else 0
    assert text.xy[category_axis] == pytest.approx(4, abs=0.5)

    # seaborn dodges c4's two boxes around position 4; the bracket spans them
    boxes = [
        p.get_path().vertices[:, category_axis]
        for p in ax.patches
        if isinstance(p, PathPatch)
    ]
    around_c4 = [v for v in boxes if abs((v.min() + v.max()) / 2 - 4) < 0.5]
    assert len(around_c4) == 2


def test_annotation_keeps_split_chunks_aligned(rng, wide):
    """Brackets grow the value axis, so the chunks must be re-unified."""
    plot = mp.Violin(wide)
    plot.annotate_stats(pairs="hue", text_format="star")
    h = ma.Heatmap(rng.standard_normal((8, 12)))
    h.cut_cols([4, 8])
    h.add_top(plot, size=2)
    h.render()

    axes = _side_axes(h, plot)
    assert len(axes) == 3
    assert all(len(ax.texts) == 4 for ax in axes)
    lims = {ax.get_ylim() for ax in axes}
    assert len(lims) == 1
    # every bracket has to fit inside the shared limit
    ((_, top),) = {(round(lo, 6), round(hi, 6)) for lo, hi in lims}
    assert all(t.xy[1] <= top for ax in axes for t in ax.texts)


def _horizontal_board(rng, side):
    cols = [f"c{i}" for i in range(8)]
    data = {
        k: pd.DataFrame(rng.normal(shift, 1, (30, 8)), columns=cols)
        for k, shift in [("WT", 0), ("KO", 2)]
    }
    plot = mp.Box(data, orient="h")
    plot.annotate_stats(pairs="hue", text_format="star")
    h = ma.Heatmap(rng.standard_normal((8, 12)))
    h.add_plot(side, plot, size=2, name="p")
    h.render()
    return h, data


def test_annotation_follows_the_inverted_axis_of_a_left_plot(rng):
    """A left plot has its value axis inverted; brackets belong outside the data."""
    h, data = _horizontal_board(rng, "left")

    ax = h.get_ax("p")
    assert ax.xaxis_inverted()
    # each bracket is anchored at (value, category); it belongs past the
    # outer end of its own category, not inside the boxes
    for text in ax.texts:
        category = int(round(text.xy[1]))
        assert text.xy[0] > max(d.iloc[:, category].max() for d in data.values())


def _label_spans(h):
    """Where each label actually sits on the value axis, in data coordinates."""
    ax = h.get_ax("p")
    h.figure.canvas.draw()
    to_data = ax.transData.inverted()
    return {
        int(round(t.xy[1])): sorted(
            to_data.transform(t.get_window_extent().get_points())[:, 0]
        )
        for t in ax.texts
    }


def test_labels_sit_outside_the_bracket_on_an_inverted_axis(rng):
    """The label grows away from the data on both sides.

    statannotations places the label with ``va`` and an offset in points, both
    in display space, so on a left plot they point back into the plot. Mirrored,
    a left plot must lay its labels out exactly like a right plot.
    """
    left, data = _horizontal_board(np.random.default_rng(0), "left")
    right, _ = _horizontal_board(np.random.default_rng(0), "right")

    left_spans, right_spans = _label_spans(left), _label_spans(right)
    assert left_spans.keys() == right_spans.keys()
    for category, (lo, hi) in left_spans.items():
        assert (lo, hi) == pytest.approx(right_spans[category])
        # and neither one overlaps the data it annotates
        assert lo > max(d.iloc[:, category].max() for d in data.values())


def test_pairs_spanning_two_chunks_are_skipped(rng, wide):
    plot = mp.Bar(wide)
    plot.annotate_stats(
        pairs=[(("c0", "WT"), ("c0", "KO")), (("c0", "WT"), ("c9", "KO"))],
        text_format="star",
    )
    h = ma.Heatmap(rng.standard_normal((8, 12)))
    h.cut_cols([4, 8])
    h.add_top(plot, size=2)
    with pytest.warns(UserWarning, match="span more than one group"):
        h.render()

    axes = _side_axes(h, plot)
    assert [len(ax.texts) for ax in axes] == [1, 0, 0]


def test_pairs_are_matched_after_clustering_reorders_columns(rng):
    """Labels ride the same deformation as the data, so they stay attached."""
    cols = [f"c{i}" for i in range(6)]
    data = {
        k: pd.DataFrame(rng.normal(shift, 1, (30, 6)), columns=cols)
        for k, shift in [("WT", 0), ("KO", 2)]
    }
    plot = mp.Box(data)
    plot.annotate_stats(pairs=[(("c3", "WT"), ("c3", "KO"))], text_format="star")
    h = ma.Heatmap(rng.standard_normal((8, 6)))
    h.add_dendrogram("bottom")
    h.add_top(plot, size=2)
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        h.render()

    ax = _side_axes(h, plot)[0]
    assert len(ax.texts) == 1
    # the bracket sits over c3 wherever clustering moved it
    order = list(h.get_deform().col_reorder_index)
    assert ax.lines[-1].get_xdata()[0] == pytest.approx(order.index(3) - 0.2)


def test_supplied_pvalues_skip_testing(rng, wide):
    plot = mp.Box(wide)
    plot.annotate_stats(
        pairs=[(("c0", "WT"), ("c0", "KO"))], pvalues=[0.5], text_format="star"
    )
    h = ma.Heatmap(rng.standard_normal((8, 12)))
    h.add_top(plot, size=2)
    h.render()
    assert _side_axes(h, plot)[0].texts[0].get_text() == "ns"


def test_duplicated_column_labels_are_rejected(rng):
    data = pd.DataFrame(rng.standard_normal((10, 3)), columns=["a", "a", "b"])
    with pytest.raises(ValueError, match="duplicated"):
        mp.Box(data).annotate_stats(pairs="all")


def test_ref_with_explicit_pairs_is_rejected(rng):
    plot = mp.Box(rng.standard_normal((10, 6)))
    with pytest.raises(ValueError, match="ref only applies"):
        plot.annotate_stats(pairs=[(0, 1)], ref=0)


def test_position_kwargs_warn(rng, wide):
    plot = mp.Box(wide, width=0.5)
    with pytest.warns(UserWarning, match="may not line up"):
        plot.annotate_stats(pairs="hue")
