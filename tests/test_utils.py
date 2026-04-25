import pytest
from marsilea.utils import (
    pairwise,
    batched,
    relative_luminance,
    get_canvas_size_by_data,
)


# --- pairwise ---


def test_pairwise_empty():
    assert list(pairwise([])) == []


def test_pairwise_single():
    assert list(pairwise([1])) == []


def test_pairwise_multiple():
    assert list(pairwise([1, 2, 3])) == [(1, 2), (2, 3)]


# --- batched ---


def test_batched_exact():
    result = list(batched("ABCDEF", 3))
    assert result == [["A", "B", "C"], ["D", "E", "F"]]


def test_batched_remainder():
    result = list(batched("ABCDEFG", 3))
    assert result == [["A", "B", "C"], ["D", "E", "F"], ["G"]]


def test_batched_n1():
    result = list(batched("AB", 1))
    assert result == [["A"], ["B"]]


def test_batched_invalid():
    with pytest.raises(ValueError):
        list(batched("AB", 0))


# --- relative_luminance ---


def test_luminance_black():
    assert relative_luminance("black") == pytest.approx(0.0, abs=1e-6)


def test_luminance_white():
    assert relative_luminance("white") == pytest.approx(1.0, abs=1e-6)


# --- get_canvas_size_by_data ---


def test_canvas_default():
    w, h = get_canvas_size_by_data((10, 20))
    assert w == pytest.approx(6.0)
    assert h == pytest.approx(3.0)


def test_canvas_width_only():
    w, h = get_canvas_size_by_data((10, 20), width=4.0)
    assert w == pytest.approx(4.0)
    assert h > 0


def test_canvas_height_only():
    w, h = get_canvas_size_by_data((10, 20), height=3.0)
    assert h == pytest.approx(3.0)
    assert w > 0


def test_canvas_max_side_clamp():
    w, h = get_canvas_size_by_data((100, 200))
    assert max(w, h) <= 15.0
