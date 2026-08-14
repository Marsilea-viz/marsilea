"""Significance annotation on the seaborn plotters.

The pair-resolution tests are pure logic and run everywhere; the rendering
tests need the optional ``statannotations`` extra.
"""

import warnings

import numpy as np
import pandas as pd
import pytest
from matplotlib.lines import Line2D

import marsilea as ma
import marsilea.plotter as mp
from marsilea.plotter._stats_annot import (
    CategoryLayout,
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


def test_layout_places_groups_where_seaborn_does():
    dodged = CategoryLayout.from_kws("boxplot", HUE, {})
    assert dodged.coord(3, "WT") == pytest.approx(2.8)
    assert dodged.coord(3, "KO") == pytest.approx(3.2)
    # seaborn overlays strip/swarm/point hue levels unless told to dodge
    overlaid = CategoryLayout.from_kws("stripplot", HUE, {})
    assert overlaid.coord(3, "WT") == overlaid.coord(3, "KO") == 3.0
    assert CategoryLayout.from_kws("stripplot", HUE, {"dodge": True}).coord(
        3, "WT"
    ) == pytest.approx(2.8)
    # a narrower width narrows the dodge with it
    narrow = CategoryLayout.from_kws("boxplot", HUE, {"width": 0.4})
    assert narrow.coord(3, "WT") == pytest.approx(2.9)


# --- rendering ---

pytest.importorskip("statannotations")

ALL_PLOTS = [mp.Bar, mp.Box, mp.Boxen, mp.Violin, mp.Point, mp.Strip, mp.Swarm]
# seaborn overlays hue levels for these unless told otherwise
NEEDS_DODGE = {mp.Point, mp.Strip, mp.Swarm}


def _board(
    pairs,
    Plot=mp.Box,
    side="top",
    orient="v",
    n_cat=6,
    cuts=None,
    plot_kws=None,
    **stats_kws,
):
    """A canvas with one annotated plot, optionally split into groups."""
    rng = np.random.default_rng(0)
    cols = [f"c{i}" for i in range(n_cat)]
    data = {
        k: pd.DataFrame(rng.normal(shift, 1, (30, n_cat)), columns=cols)
        for k, shift in [("WT", 0), ("KO", 2)]
    }
    kws = dict(plot_kws or {})
    if Plot in NEEDS_DODGE:
        kws.setdefault("dodge", True)
    plot = Plot(data, orient=orient, **kws)
    plot.annotate_stats(pairs=pairs, text_format="star", **stats_kws)

    h = ma.Heatmap(rng.standard_normal((n_cat, n_cat)), width=3, height=3)
    if cuts:
        (h.cut_rows if side in ("left", "right") else h.cut_cols)(list(cuts))
    h.add_plot(side, plot, size=2, name="p")
    h.render()
    h.figure.canvas.draw()
    return h, plot, data


def _axes(board):
    axes = board.get_ax("p")
    return list(axes) if isinstance(axes, (list, np.ndarray)) else [axes]


def _brackets(board):
    return [a for a in board.figure.artists if isinstance(a, Line2D)]


def _labels(board):
    return list(board.figure.texts)


def _spans(board, artist, value_axis):
    """A figure artist's extent in the value direction, in data coordinates."""
    to_data = _axes(board)[0].transData.inverted()
    if isinstance(artist, Line2D):
        points = board.figure.transFigure.transform(
            list(zip(artist.get_xdata(), artist.get_ydata()))
        )
    else:
        points = artist.get_window_extent().get_points()
    return sorted(to_data.transform(points)[:, value_axis])


@pytest.mark.parametrize("PlotClass", ALL_PLOTS)
def test_every_seaborn_plotter_can_be_annotated(PlotClass):
    """Nothing is off-limits now that marsilea does the drawing itself."""
    board, _, _ = _board("hue", Plot=PlotClass)
    assert len(_brackets(board)) == 6
    assert len(_labels(board)) == 6
    # the plot's own axes stay free of annotation artists
    assert all(len(ax.texts) == 0 for ax in _axes(board))


@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_labels_land_beyond_the_data_on_every_side(side, orient):
    """Whichever way the value axis runs, the label sits past the data."""
    board, _, data = _board("hue", side=side, orient=orient)
    value_axis = 0 if orient == "h" else 1
    limits = sorted(
        _axes(board)[0].get_xlim() if orient == "h" else _axes(board)[0].get_ylim()
    )
    reach = max(d.values.max() for d in data.values())

    assert len(_labels(board)) == 6
    for label in _labels(board):
        low, high = _spans(board, label, value_axis)
        assert low > reach
        assert limits[0] <= low and high <= limits[1]


@pytest.mark.parametrize("side", ["top", "bottom", "left", "right"])
@pytest.mark.parametrize("orient", ["v", "h"])
def test_brackets_land_on_the_category_they_name(side, orient):
    """The categorical axis is inverted for horizontal plots; positions hold."""
    board, _, _ = _board([(("c4", "WT"), ("c4", "KO"))], side=side, orient=orient)
    (bracket,) = _brackets(board)
    ax = _axes(board)[0]

    category_axis = 1 if orient == "h" else 0
    to_data = ax.transData.inverted()
    points = board.figure.transFigure.transform(
        list(zip(bracket.get_xdata(), bracket.get_ydata()))
    )
    ends = to_data.transform(points)[1:3, category_axis]
    # seaborn dodges c4's two boxes to 3.8 and 4.2
    assert sorted(ends) == pytest.approx([3.8, 4.2], abs=1e-6)


def test_labels_are_placed_identically_whichever_way_the_axis_runs():
    """A left plot inverts its value axis; it must still lay labels out the same."""
    left, _, _ = _board("hue", side="left", orient="h")
    right, _, _ = _board("hue", side="right", orient="h")
    assert _axes(left)[0].xaxis_inverted()
    assert not _axes(right)[0].xaxis_inverted()

    assert [t.get_text() for t in _labels(left)] == [
        t.get_text() for t in _labels(right)
    ]
    for a, b in zip(_labels(left), _labels(right)):
        assert _spans(left, a, 0) == pytest.approx(_spans(right, b, 0))


def test_a_label_never_sits_on_a_bracket():
    """Each row reserves the space its label needs, so nothing collides."""
    board, _, _ = _board("hue", n_cat=4)
    figure = board.figure
    for label in _labels(board):
        box = label.get_window_extent()
        for bracket in _brackets(board):
            points = figure.transFigure.transform(
                list(zip(bracket.get_xdata(), bracket.get_ydata()))
            )
            xs, ys = points[:, 0], points[:, 1]
            if box.x1 < xs.min() or box.x0 > xs.max():
                continue
            assert box.y0 >= ys.max() or box.y1 <= ys.min()


def test_style_is_shared_by_every_bracket():
    """Within-group and cross-group brackets come out of the same call."""
    board, _, _ = _board(
        [(("c0", "WT"), ("c0", "KO")), (("c0", "WT"), ("c5", "KO"))],
        n_cat=6,
        cuts=(3,),
        color="#123456",
        line_width=2.5,
    )
    brackets = _brackets(board)
    assert len(brackets) == 2
    assert {b.get_linewidth() for b in brackets} == {2.5}
    assert {b.get_color() for b in brackets} == {"#123456"}
    assert {t.get_color() for t in _labels(board)} == {"#123456"}


def test_unknown_options_are_rejected():
    plot = mp.Box(np.random.default_rng(0).standard_normal((10, 4)))
    with pytest.raises(ValueError, match="Unknown option"):
        plot.annotate_stats(pairs="all", nonsense=1)


# --- brackets that span the chunk axes ---


def test_pairs_spanning_two_chunks_are_drawn_across_axes():
    """statannotations cannot reach across Axes; marsilea draws these itself."""
    board, _, _ = _board(
        [
            (("c0", "WT"), ("c0", "KO")),  # inside chunk 0
            (("c0", "WT"), ("c5", "KO")),  # chunk 0 -> chunk 1
        ],
        n_cat=6,
        cuts=(3,),
    )
    brackets = _brackets(board)
    assert len(brackets) == 2
    assert [t.get_text() for t in _labels(board)] == ["****", "****"]

    axes = _axes(board)
    to_figure = board.figure.transFigure.inverted()
    within, across = sorted(brackets, key=lambda b: np.ptp(b.get_xdata()))
    # the spanning one reaches past the first chunk's Axes
    edge = to_figure.transform(axes[0].transAxes.transform((1, 0)))[0]
    assert max(across.get_xdata()) > edge
    assert max(within.get_xdata()) < edge


def test_cross_brackets_end_over_the_categories_they_name():
    """Each end sits on its own chunk's Axes, at that category's dodged position."""
    board, _, _ = _board([(("c1", "WT"), ("c5", "KO"))], n_cat=6, cuts=(3,))
    axes = _axes(board)
    (bracket,) = _brackets(board)
    to_figure = board.figure.transFigure.inverted()

    def figure_x(ax, position):
        return to_figure.transform(ax.transData.transform((position, 0)))[0]

    left, right = bracket.get_xdata()[1], bracket.get_xdata()[2]
    assert left == pytest.approx(figure_x(axes[0], 1 - 0.2), abs=1e-6)
    assert right == pytest.approx(figure_x(axes[1], 2 + 0.2), abs=1e-6)


def test_cross_brackets_clear_the_within_group_ones():
    """A spanning bracket passes over other groups, so it sits above them."""
    board, _, _ = _board(
        [(("c0", "WT"), ("c0", "KO")), (("c0", "WT"), ("c5", "KO"))],
        n_cat=6,
        cuts=(3,),
    )
    within, across = sorted(_brackets(board), key=lambda b: np.ptp(b.get_xdata()))
    assert min(across.get_ydata()) > max(within.get_ydata())
    # all chunks were grown together to make the room
    assert len({ax.get_ylim() for ax in _axes(board)}) == 1


def test_reference_reaches_across_groups():
    """`ref` names one category; the groups it is not in still get compared."""
    board, _, _ = _board("all", n_cat=6, cuts=(3,), ref="c0")
    # c0 against each of the 5 others, once per hue level
    assert len(_brackets(board)) == 10


def test_supplied_pvalues_reach_the_pair_they_belong_to():
    board, _, _ = _board(
        [
            (("c0", "WT"), ("c0", "KO")),  # chunk 0
            (("c0", "WT"), ("c5", "KO")),  # spans chunks
            (("c4", "WT"), ("c4", "KO")),  # chunk 1
        ],
        n_cat=6,
        cuts=(3,),
        pvalues=[0.5, 1e-6, 0.5],
    )
    assert sorted(t.get_text() for t in _labels(board)) == ["****", "ns", "ns"]


def test_pvalues_reject_a_shorthand():
    plot = mp.Box(np.random.default_rng(0).standard_normal((10, 4)))
    with pytest.raises(ValueError, match="explicit list of pairs"):
        plot.annotate_stats(pairs="hue", pvalues=[0.1])


def test_pairs_naming_an_unknown_category_warn():
    with pytest.warns(UserWarning, match="not in the data"):
        board, _, _ = _board([(("c0", "WT"), ("nope", "KO"))], n_cat=6, cuts=(3,))
    assert len(_brackets(board)) == 0


# --- what seaborn actually drew ---


@pytest.mark.parametrize("PlotClass", [mp.Strip, mp.Swarm, mp.Point])
def test_overlaid_hue_levels_are_refused(PlotClass):
    """seaborn does not dodge these by default, so the two sides coincide."""
    with pytest.warns(UserWarning, match="drawn at the same place"):
        board, _, _ = _board("hue", Plot=PlotClass, plot_kws={"dodge": False})
    assert len(_brackets(board)) == 0


def test_a_narrower_width_moves_the_brackets_with_the_boxes():
    """Positions come from the options seaborn was called with."""
    board, _, _ = _board([(("c2", "WT"), ("c2", "KO"))], plot_kws={"width": 0.4})
    (bracket,) = _brackets(board)
    ax = _axes(board)[0]
    to_data = ax.transData.inverted()
    points = board.figure.transFigure.transform(
        list(zip(bracket.get_xdata(), bracket.get_ydata()))
    )
    ends = sorted(to_data.transform(points)[1:3, 0])
    assert ends == pytest.approx([2 - 0.1, 2 + 0.1], abs=1e-6)


def test_brackets_clear_the_drawn_artists_not_just_the_data():
    """Error bars reach past the mean, and the bracket has to clear them."""
    rng = np.random.default_rng(0)
    cols = [f"c{i}" for i in range(4)]
    data = {
        k: pd.DataFrame(rng.normal(shift, 1, (30, 4)), columns=cols)
        for k, shift in [("WT", 0), ("KO", 2)]
    }
    plot = mp.Bar(data)
    plot.annotate_stats(pairs="hue", text_format="star")
    h = ma.Heatmap(rng.standard_normal((4, 4)), width=3, height=3)
    h.add_top(plot, size=2, name="p")
    h.render()
    h.figure.canvas.draw()

    ax = h.get_ax("p")
    error_bar_top = max(
        np.nanmax(line.get_ydata()) for line in ax.lines if len(line.get_ydata())
    )
    lowest = min(min(b.get_ydata()) for b in _brackets(h))
    to_data = ax.transData.inverted()
    lowest_value = to_data.transform(h.figure.transFigure.transform((0, lowest)))[1]
    assert lowest_value > error_bar_top


# --- other configuration ---


def test_pairs_are_matched_after_clustering_reorders_columns():
    """Labels ride the same deformation as the data, so they stay attached."""
    rng = np.random.default_rng(0)
    cols = [f"c{i}" for i in range(6)]
    data = {
        k: pd.DataFrame(rng.normal(shift, 1, (30, 6)), columns=cols)
        for k, shift in [("WT", 0), ("KO", 2)]
    }
    plot = mp.Box(data)
    plot.annotate_stats(pairs=[(("c3", "WT"), ("c3", "KO"))], text_format="star")
    h = ma.Heatmap(rng.standard_normal((8, 6)))
    h.add_dendrogram("bottom")
    h.add_top(plot, size=2, name="p")
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        h.render()
    h.figure.canvas.draw()

    (bracket,) = _brackets(h)
    order = list(h.get_deform().col_reorder_index)
    ax = h.get_ax("p")
    to_data = ax.transData.inverted()
    points = h.figure.transFigure.transform(
        list(zip(bracket.get_xdata(), bracket.get_ydata()))
    )
    ends = sorted(to_data.transform(points)[1:3, 0])
    assert ends == pytest.approx([order.index(3) - 0.2, order.index(3) + 0.2], abs=1e-6)


def test_correction_covers_every_bracket_at_once():
    """One family of tests, not one per group; a split must not under-correct."""
    plain, _, _ = _board("hue", n_cat=6, cuts=(3,))
    corrected, _, _ = _board(
        "hue", n_cat=6, cuts=(3,), comparisons_correction="Benjamini-Hochberg"
    )
    assert len(_labels(plain)) == len(_labels(corrected)) == 6


def test_duplicated_column_labels_are_rejected():
    rng = np.random.default_rng(0)
    data = pd.DataFrame(rng.standard_normal((10, 3)), columns=["a", "a", "b"])
    with pytest.raises(ValueError, match="duplicated"):
        mp.Box(data).annotate_stats(pairs="all")


def test_ref_with_explicit_pairs_is_rejected():
    plot = mp.Box(np.random.default_rng(0).standard_normal((10, 6)))
    with pytest.raises(ValueError, match="ref only applies"):
        plot.annotate_stats(pairs=[(0, 1)], ref=0)
