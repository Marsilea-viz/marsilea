import pytest
from marsilea.upset import UpsetData, Upset


# --- Fixtures ---


@pytest.fixture
def three_sets():
    """Three overlapping sets for testing."""
    return [[1, 2, 3, 4], [3, 4, 5, 6], [1, 6, 10, 11]]


@pytest.fixture
def upset_data(three_sets):
    return UpsetData.from_sets(three_sets, sets_names=["A", "B", "C"])


# --- from_sets ---


def test_from_sets_list(three_sets):
    data = UpsetData.from_sets(three_sets)
    assert len(data.sets_names) == 3
    assert repr(data).startswith("UpsetData")


def test_from_sets_dict():
    data = UpsetData.from_sets({"X": [1, 2], "Y": [2, 3]})
    assert list(data.sets_names) == ["X", "Y"]


def test_from_sets_names(upset_data):
    assert list(upset_data.sets_names) == ["A", "B", "C"]


# --- from_memberships ---


def test_from_memberships_list():
    items = [["A", "B"], ["B", "C"], ["A"]]
    data = UpsetData.from_memberships(items)
    assert len(data.items) == 3


def test_from_memberships_dict():
    items = {"x": ["A", "B"], "y": ["B"]}
    data = UpsetData.from_memberships(items)
    assert set(data.items) == {"x", "y"}


# --- filter ---


def test_filter_min_degree(upset_data):
    upset_data.filter(min_degree=2)
    table = upset_data.sets_table()
    assert (table["degree"] >= 2).all()


def test_filter_max_cardinality(upset_data):
    original_len = len(upset_data.sets_table())
    upset_data.filter(max_cardinality=1)
    assert len(upset_data.sets_table()) <= original_len


# --- sort ---


def test_sort_subsets_by_cardinality(upset_data):
    result = upset_data.sort_subsets(by="cardinality")
    # Returns self for chaining
    assert result is upset_data
    # Cardinality values exist and are positive integers
    assert (upset_data.cardinality().values > 0).all()


def test_sort_subsets_by_degree(upset_data):
    upset_data.sort_subsets(by="degree")
    # Should not raise
    assert len(upset_data.sets_table()) > 0


def test_sort_sets_explicit_order(upset_data):
    upset_data.sort_sets(order=["C", "A", "B"])
    assert list(upset_data.sets_names) == ["C", "A", "B"]


# --- queries ---


def test_has_item(upset_data):
    # Item 3 is in sets A and B
    sets_for_3 = upset_data.has_item(3)
    assert "A" in sets_for_3
    assert "B" in sets_for_3


def test_intersection(upset_data):
    shared = upset_data.intersection(["A", "B"])
    assert 3 in shared and 4 in shared


def test_sets_size(upset_data):
    sizes = upset_data.sets_size()
    assert sizes["A"] == 4
    assert sizes["B"] == 4


# --- reset ---


def test_reset_restores(upset_data):
    original_len = len(upset_data.sets_table())
    upset_data.filter(min_degree=3)
    assert len(upset_data.sets_table()) < original_len
    upset_data.reset()
    assert len(upset_data.sets_table()) == original_len


# --- Upset render smoke ---


def test_upset_render(three_sets):
    data = UpsetData.from_sets(three_sets, sets_names=["A", "B", "C"])
    u = Upset(data)
    u.render()


def test_upset_render_vertical(three_sets):
    data = UpsetData.from_sets(three_sets, sets_names=["A", "B", "C"])
    u = Upset(data, orient="v")
    u.render()
