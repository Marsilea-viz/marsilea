"""Tests for CompositeBoard, StackBoard, ZeroWidth, ZeroHeight."""

import marsilea as ma
import marsilea.plotter as mp


def _make_heatmap(rng, rows=5, cols=4):
    return ma.Heatmap(rng.standard_normal((rows, cols)))


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
    """Nesting StackBoards (grid of heatmaps)."""
    h1 = _make_heatmap(rng)
    h2 = _make_heatmap(rng)
    h3 = _make_heatmap(rng)
    h4 = _make_heatmap(rng)
    sb1 = ma.StackBoard([h1, h2], direction="horizontal")
    sb2 = ma.StackBoard([h3, h4], direction="horizontal")
    grid = ma.StackBoard([sb1, sb2], direction="vertical")
    grid.render()


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
