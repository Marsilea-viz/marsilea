"""Tests for CompositeBoard, StackBoard, ZeroWidth, ZeroHeight."""

import pytest

import marsilea as ma
import marsilea.plotter as mp


def _make_heatmap(rng, rows=5, cols=4):
    return ma.Heatmap(rng.standard_normal((rows, cols)))


def _bounds(figure):
    return [ax.get_position().bounds for ax in figure.axes]


def _assert_inside_figure(figure):
    """Every axes must sit within the figure, nothing clipped off the edge"""
    for ax in figure.axes:
        x0, y0, w, h = ax.get_position().bounds
        assert x0 >= -1e-9 and y0 >= -1e-9, f"{ax} starts outside the figure"
        assert x0 + w <= 1 + 1e-9 and y0 + h <= 1 + 1e-9, (
            f"{ax} ends outside the figure"
        )


def _assert_no_overlap(figure):
    """No two axes may cover the same area"""
    boxes = _bounds(figure)
    for i, (xi, yi, wi, hi) in enumerate(boxes):
        for j, (xj, yj, wj, hj) in enumerate(boxes[i + 1 :], start=i + 1):
            apart = (
                xi + wi <= xj + 1e-6
                or xj + wj <= xi + 1e-6
                or yi + hi <= yj + 1e-6
                or yj + hj <= yi + 1e-6
            )
            assert apart, f"axes {i} and {j} overlap"


# --- CompositeBoard ---


def test_composite_horizontal(rng):
    h1 = _make_heatmap(rng)
    h2 = _make_heatmap(rng)
    comp = h1 + h2
    comp.render()


def test_composite_vertical(rng):
    h1 = _make_heatmap(rng)
    h2 = _make_heatmap(rng)
    comp = h1 / h2
    comp.render()


def test_composite_after_render(rng):
    """Composing already-rendered boards must not deep-copy live figure/axes.

    The Violin gives the axes a categorical unit, whose matplotlib
    ``UnitData`` holds an ``itertools.count`` -- not copyable on Python
    3.14+, where it raised ``cannot pickle 'itertools.count' object``.
    """
    h1 = _make_heatmap(rng)
    h1.add_top(mp.Violin(rng.standard_normal((6, 4))))
    h2 = _make_heatmap(rng)
    h1.render()
    h2.render()
    comp = h1 / h2
    comp.render()
    # the copy got its own figure, the sources kept theirs
    assert comp.figure is not h1.figure
    assert h1.figure is not None


def test_composite_mixed(rng):
    h1 = _make_heatmap(rng)
    h2 = _make_heatmap(rng)
    h3 = _make_heatmap(rng)
    comp = (h1 + h2) / h3
    comp.render()


# --- StackBoard ---


def test_stack_horizontal(rng):
    boards = [_make_heatmap(rng) for _ in range(3)]
    sb = ma.StackBoard(boards, direction="horizontal")
    sb.render()


def test_stack_vertical(rng):
    boards = [_make_heatmap(rng) for _ in range(3)]
    sb = ma.StackBoard(boards, direction="vertical")
    sb.render()


def test_stack_nested(rng):
    """Nesting StackBoards must give a real grid, not four overlapping axes."""
    data = rng.standard_normal((5, 4))
    cmaps = ["Reds", "Greens", "Blues", "Purples"]
    h1, h2, h3, h4 = [ma.Heatmap(data, cmap=c, width=1, height=1) for c in cmaps]
    sb1 = ma.StackBoard([h1, h2], direction="horizontal")
    sb2 = ma.StackBoard([h3, h4], direction="horizontal")
    grid = ma.StackBoard([sb1, sb2], direction="vertical")
    grid.render()

    bounds = _bounds(grid.figure)
    assert len(bounds) == 4
    # two columns and two rows, no axes sharing a corner with another
    assert len({round(b[0], 6) for b in bounds}) == 2
    assert len({round(b[1], 6) for b in bounds}) == 2
    assert len({(round(b[0], 6), round(b[1], 6)) for b in bounds}) == 4
    _assert_inside_figure(grid.figure)

    # every heatmap draws its own mesh, with its own colormap
    drawn = []
    for ax in grid.figure.axes:
        meshes = [c for c in ax.collections if hasattr(c, "cmap")]
        assert len(meshes) == 1
        drawn.append(meshes[0].cmap.name)
    assert sorted(drawn) == sorted(cmaps)


def test_stack_nested_thrice(rng):
    """A stack of stacks of stacks still places every board once."""
    inner = [
        ma.StackBoard([_make_heatmap(rng), _make_heatmap(rng)], direction="horizontal")
        for _ in range(2)
    ]
    grid = ma.StackBoard(inner, direction="vertical")
    outer = ma.StackBoard([grid, _make_heatmap(rng)], direction="horizontal")
    outer.render()

    assert len(outer.figure.axes) == 5
    assert len({(round(b[0], 6), round(b[1], 6)) for b in _bounds(outer.figure)}) == 5
    _assert_inside_figure(outer.figure)


def test_stack_leaves_input_boards_alone(rng):
    """Boards are copied on construction, so the originals stay renderable."""
    h1 = _make_heatmap(rng)
    h2 = _make_heatmap(rng)
    ma.StackBoard([h1, h2], direction="horizontal").render()

    assert h1.figure is None
    h1.render()  # the original is untouched and still usable on its own


def test_stack_after_render(rng):
    """Stacking already-rendered boards must not copy live figure/axes.

    The StackBoard side of ``test_composite_after_render``: the Violin
    gives the axes a categorical unit whose matplotlib ``UnitData`` holds
    an ``itertools.count``, which cannot be copied on Python 3.14+.
    """
    h1 = _make_heatmap(rng)
    h1.add_top(mp.Violin(rng.standard_normal((6, 4))))
    h2 = _make_heatmap(rng)
    h1.render()
    h2.render()

    sb = ma.StackBoard([h1, h2], direction="horizontal")
    nested = ma.StackBoard([sb, _make_heatmap(rng)], direction="vertical")
    nested.render()

    assert nested.figure is not h1.figure
    assert h1.figure is not None


def test_stack_save_before_render(rng, tmp_path):
    sb = ma.StackBoard([_make_heatmap(rng)], direction="horizontal")
    out = tmp_path / "stack.png"
    sb.save(out)
    assert out.stat().st_size > 0


def test_stack_empty_boards():
    with pytest.raises(ValueError, match="empty list"):
        ma.StackBoard([])


def test_stack_keeps_per_board_legends(rng):
    """keep_legends=True: each board draws its own legend, with room for it."""
    h1 = _make_heatmap(rng)
    h1.add_legends()
    h2 = _make_heatmap(rng)
    h2.add_legends()

    sb = ma.StackBoard([h1, h2], direction="horizontal", keep_legends=True)
    sb.render()

    # two heatmaps plus a legend axes each, none clipped or overlapping
    assert len(sb.figure.axes) == 4
    assert sum(len(ax.artists) > 0 for ax in sb.figure.axes) == 2
    _assert_inside_figure(sb.figure)
    _assert_no_overlap(sb.figure)


@pytest.mark.parametrize("side", ["right", "left", "top", "bottom"])
def test_stack_legend_inside_figure(rng, side):
    """The figure has to grow for the legend instead of pushing it off-canvas."""
    sb = ma.StackBoard([_make_heatmap(rng), _make_heatmap(rng)], direction="horizontal")
    sb.add_legends(side=side)
    sb.render()

    legend_ax = sb.layout.get_legend_ax()
    assert legend_ax is not None
    _assert_inside_figure(sb.figure)


@pytest.mark.parametrize(
    "direction,align,add_side,n",
    [("vertical", "center", "left", 5), ("horizontal", "center", "top", 4)],
)
def test_stack_center_align_asymmetric(rng, direction, align, add_side, n):
    """Centering on the main canvas must still leave room for side plots."""
    h1 = ma.Heatmap(rng.standard_normal((5, 4)), width=1, height=1)
    getattr(h1, f"add_{add_side}")(mp.Colors(rng.standard_normal(n)), size=1.5, pad=0.1)
    h2 = ma.Heatmap(rng.standard_normal((5, 4)), width=1, height=1)

    sb = ma.StackBoard([h1, h2], direction=direction, align=align)
    sb.render()
    _assert_inside_figure(sb.figure)


# --- ZeroWidth ---


def test_zero_width_compose(rng):
    h = _make_heatmap(rng)
    zw = ma.ZeroWidth(height=3)
    zw.add_right(mp.Numbers(rng.standard_normal(5)))
    comp = zw + h
    comp.render()


# --- ZeroHeight ---


def test_zero_height_compose(rng):
    h = _make_heatmap(rng)
    zh = ma.ZeroHeight(width=3)
    zh.add_bottom(mp.Numbers(rng.standard_normal(4)))
    comp = h / zh
    comp.render()
