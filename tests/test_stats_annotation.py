"""Significance annotation on the seaborn plotters.

The pair-resolution tests are pure logic and run everywhere; the rendering
tests need the optional ``statannotations`` extra.
"""

import warnings

import numpy as np
import pandas as pd
import pytest
from matplotlib.lines import Line2D
from matplotlib.patches import PathPatch

import marsilea as ma
import marsilea.plotter as mp
from marsilea.plotter._stats_annot import (
    Endpoint,
    StatsConfig,
    plan_pairs,
    resolve_pairs,
)

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


# --- planning across chunks ---


def test_plan_splits_within_chunk_from_cross_chunk():
    config = StatsConfig(
        pairs=[
            (("a", "WT"), ("b", "KO")),  # both in chunk 0
            (("a", "WT"), ("d", "KO")),  # chunk 0 -> chunk 1
            (("a", "WT"), ("zz", "KO")),  # nowhere
        ]
    )
    per_chunk, cross, unknown = plan_pairs(config, [["a", "b"], ["c", "d"]], HUE)

    assert [plan.pairs for plan in per_chunk] == [[((0, "WT"), (1, "KO"))], []]
    assert len(cross) == 1
    assert (cross[0].left.chunk, cross[0].left.position) == (0, 0)
    assert (cross[0].right.chunk, cross[0].right.position) == (1, 1)
    assert unknown == [(("a", "WT"), ("zz", "KO"))]


def test_plan_gives_each_chunk_only_its_own_pvalues():
    config = StatsConfig(
        pairs=[("a", "b"), ("a", "d"), ("c", "d")], pvalues=[0.1, 0.2, 0.3]
    )
    per_chunk, cross, _ = plan_pairs(config, [["a", "b"], ["c", "d"]], None)

    assert [plan.pvalues for plan in per_chunk] == [[0.1], [0.3]]
    assert [pair.pvalue for pair in cross] == [0.2]


def test_plan_expands_a_reference_over_every_chunk():
    """`ref` in one chunk still has something to say about the others."""
    config = StatsConfig(pairs="all", ref="a")
    per_chunk, cross, _ = plan_pairs(config, [["a", "b"], ["c", "d"]], None)

    assert [plan.pairs for plan in per_chunk] == [[(0, 1)], []]
    assert [(p.right.chunk, p.right.position) for p in cross] == [(1, 0), (1, 1)]


def test_plan_leaves_a_single_chunk_alone():
    config = StatsConfig(pairs=[("a", "b")])
    per_chunk, cross, unknown = plan_pairs(config, [["a", "b"]], None)
    assert [plan.pairs for plan in per_chunk] == [[(0, 1)]]
    assert cross == [] and unknown == []


def test_endpoint_dodges_like_seaborn():
    assert Endpoint(0, 3, "WT").coord(HUE) == pytest.approx(2.8)
    assert Endpoint(0, 3, "KO").coord(HUE) == pytest.approx(3.2)
    assert Endpoint(0, 3).coord(None) == pytest.approx(3.0)


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


# --- brackets that span the chunk axes ---


def _split_board(pairs, orient="v", side="top", n_cat=12, cuts=(4, 8), **kws):
    rng = np.random.default_rng(0)
    cols = [f"c{i}" for i in range(n_cat)]
    data = {
        k: pd.DataFrame(rng.normal(shift, 1, (30, n_cat)), columns=cols)
        for k, shift in [("WT", 0), ("KO", 2)]
    }
    plot = mp.Box(data, orient=orient)
    plot.annotate_stats(pairs=pairs, text_format="star", **kws)
    h = ma.Heatmap(rng.standard_normal((n_cat, n_cat)), width=3, height=3)
    (h.cut_rows if side in ("left", "right") else h.cut_cols)(list(cuts))
    h.add_plot(side, plot, size=2, name="p")
    h.render()
    h.figure.canvas.draw()
    return h, plot, data


def _figure_brackets(h):
    return [a for a in h.figure.artists if isinstance(a, Line2D)]


def test_pairs_spanning_two_chunks_are_drawn_across_axes():
    """statannotations cannot reach across Axes, so marsilea draws these itself."""
    h, plot, _ = _split_board(
        [
            (("c0", "WT"), ("c0", "KO")),  # inside chunk 0
            (("c0", "WT"), ("c9", "KO")),  # chunk 0 -> chunk 2
            (("c0", "WT"), ("c5", "KO")),  # chunk 0 -> chunk 1
        ]
    )
    axes = _side_axes(h, plot)

    # the within-chunk pair still goes through statannotations, per Axes
    assert [len(ax.texts) for ax in axes] == [1, 0, 0]
    # the two spanning pairs are figure-level artists instead
    assert len(_figure_brackets(h)) == 2
    assert [t.get_text() for t in h.figure.texts] == ["****", "****"]


def test_cross_brackets_end_over_the_categories_they_name():
    """Each end sits on its own chunk's Axes, at that category's dodged position."""
    h, plot, _ = _split_board([(("c1", "WT"), ("c9", "KO"))])
    axes = _side_axes(h, plot)
    (bracket,) = _figure_brackets(h)
    to_figure = h.figure.transFigure.inverted()

    def figure_x(ax, position):
        return to_figure.transform(ax.transData.transform((position, 0)))[0]

    # c1 is at position 1 of chunk 0, WT dodges left; c9 at position 1 of
    # chunk 2, KO dodges right
    left, right = bracket.get_xdata()[1], bracket.get_xdata()[2]
    assert left == pytest.approx(figure_x(axes[0], 1 - 0.2), abs=1e-6)
    assert right == pytest.approx(figure_x(axes[2], 1 + 0.2), abs=1e-6)


def test_cross_brackets_clear_the_within_group_ones():
    """A spanning bracket passes over other chunks, so it has to sit above them."""
    h, plot, _ = _split_board(
        [(("c0", "WT"), ("c0", "KO")), (("c0", "WT"), ("c9", "KO"))]
    )
    axes = _side_axes(h, plot)
    to_figure = h.figure.transFigure.inverted()

    within = max(
        to_figure.transform(t.get_window_extent().get_points())[:, 1].max()
        for ax in axes
        for t in ax.texts
    )
    (bracket,) = _figure_brackets(h)
    assert min(bracket.get_ydata()) > within
    # and all three chunks were grown to make the room, together
    assert len({ax.get_ylim() for ax in axes}) == 1


@pytest.mark.parametrize("side,orient", [("top", "v"), ("left", "h"), ("right", "h")])
def test_cross_brackets_in_every_orientation(side, orient):
    h, plot, data = _split_board(
        [(("c0", "WT"), ("c9", "KO"))], orient=orient, side=side
    )
    (bracket,) = _figure_brackets(h)
    (label,) = h.figure.texts
    axes = _side_axes(h, plot)
    value_axis = 0 if orient == "h" else 1

    # the bracket clears the data on the value axis, whichever way it runs
    reach = max(d.values.max() for d in data.values())
    to_figure = h.figure.transFigure.inverted()
    outer = to_figure.transform(
        axes[0].transData.transform((reach, 0) if orient == "h" else (0, reach))
    )[value_axis]
    ends = bracket.get_xdata() if orient == "h" else bracket.get_ydata()
    inverted = axes[0].xaxis_inverted() if orient == "h" else False
    assert (min(ends) < outer) if inverted else (min(ends) > outer)
    assert label.get_rotation() == (270 if orient == "h" else 0)


def test_reference_reaches_across_groups():
    """`ref` names one category; the groups it is not in still get compared."""
    h, plot, _ = _split_board("all", n_cat=6, cuts=(3,), ref="c0")
    axes = _side_axes(h, plot)
    # within chunk 0: c0 vs c1, c0 vs c2, once per hue level
    assert len(axes[0].texts) == 4
    # across to chunk 1: c0 vs c3/c4/c5, once per hue level
    assert len(_figure_brackets(h)) == 6


def test_supplied_pvalues_are_split_between_chunks_and_brackets():
    """Each value must reach the pair it belongs to, wherever that pair landed."""
    h, plot, _ = _split_board(
        [
            (("c0", "WT"), ("c0", "KO")),  # chunk 0
            (("c0", "WT"), ("c9", "KO")),  # spans chunks
            (("c5", "WT"), ("c5", "KO")),  # chunk 1
        ],
        pvalues=[0.5, 1e-6, 1e-6],
    )
    axes = _side_axes(h, plot)
    assert axes[0].texts[0].get_text() == "ns"
    assert axes[1].texts[0].get_text() == "****"
    assert [t.get_text() for t in h.figure.texts] == ["****"]


def test_pairs_naming_an_unknown_category_warn():
    with pytest.warns(UserWarning, match="not in the data"):
        h, plot, _ = _split_board([(("c0", "WT"), ("nope", "KO"))])
    assert _figure_brackets(h) == []


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
