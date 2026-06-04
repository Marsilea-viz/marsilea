import numpy as np
import pandas as pd
import pytest
from marsilea.plotter import Bar, Numbers
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


def test_intersection_empty_returns_degree0():
    # Bug 1 (#84): item4 belongs to no set -> intersection([]) must return it
    data = pd.DataFrame(
        {"A": [True, False], "B": [False, False]},
        index=["item1", "item4"],
    )
    upset_data = UpsetData(data=data)
    assert upset_data.intersection([]) == ["item4"]


def test_intersection_special_char_columns():
    # Bug 2 (#84): column names with special chars broke query() backtick parsing
    col = "Set (NºA.1, integración)"
    data = pd.DataFrame(
        {
            col: [True, True, False],
            "Set B": [True, False, True],
        },
        index=["item1", "item2", "item3"],
    )
    upset_data = UpsetData(data=data)
    shared = upset_data.intersection([col, "Set B"])
    assert shared == ["item1"]


def test_add_items_attr_special_chars_and_empty():
    # End-to-end repro from #84: must not raise ValueError/KeyError
    data = pd.DataFrame(
        {
            "Set (NºA.1, integración)": [True, True, False, False],
            "Set B": [True, False, True, False],
            "Set C": [False, True, True, False],
        },
        index=["item1", "item2", "item3", "item4"],
    )
    items_attrs = pd.DataFrame(
        {"group": ["X", "X", "Y", "Y"]},
        index=["item1", "item2", "item3", "item4"],
    )
    upset_data = UpsetData(data=data, items_attrs=items_attrs)
    upset = Upset(data=upset_data)
    upset.add_items_attr(side="top", attr_name="group", plot="bar")


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


# --- add_items_attr / add_sets_attr ---


def _abc_with_degree0():
    # i4 belongs to no set (degree-0)
    data = pd.DataFrame(
        {
            "A": [1, 1, 0, 0],
            "B": [1, 0, 1, 0],
            "C": [0, 1, 1, 0],
        },
        index=["i1", "i2", "i3", "i4"],
    )
    items_attrs = pd.DataFrame(
        {"group": ["X", "X", "Y", "Y"]},
        index=["i1", "i2", "i3", "i4"],
    )
    return UpsetData(data=data, items_attrs=items_attrs)


def test_add_items_attr_stack_bar_degree0():
    # Bug #86: stack_bar branch was dead (string vs class) and crashed on degree-0
    upset = Upset(data=_abc_with_degree0())
    upset.add_items_attr("top", "group", "stack_bar")
    upset.render()


def test_add_items_attr_plotter_class():
    # plot may be a plotter class, not only a registry string
    upset = Upset(data=_abc_with_degree0())
    upset.add_items_attr("top", "group", Bar)
    upset.render()


def test_add_items_attr_plotter_instance():
    # plot may be a fully-built instance, aligned to subset_order by the caller
    upset = Upset(data=_abc_with_degree0())
    arr = np.arange(len(upset.subset_order))
    upset.add_items_attr("top", plot=Numbers(arr))
    upset.render()


def test_add_sets_attr_default_kws(three_sets):
    # add_sets_attr used to pass **plot_kws (None) -> TypeError; label never set
    sets_attrs = pd.DataFrame({"score": [1.0, 2.0, 3.0]}, index=["A", "B", "C"])
    data = UpsetData.from_sets(
        three_sets, sets_names=["A", "B", "C"], sets_attrs=sets_attrs
    )
    upset = Upset(data)
    upset.add_sets_attr("left", "score", "bar")
    upset.render()


def test_add_sets_attr_no_attrs_raises(upset_data):
    upset = Upset(upset_data)
    with pytest.raises(ValueError):
        upset.add_sets_attr("left", "missing", "bar")


def test_get_items_attr_exclusive_matches_cardinality():
    # Item-attr collectors must use EXCLUSIVE subsets so counts match the bars.
    data = pd.DataFrame(
        {
            "A": [1, 1, 1, 1, 0, 0],
            "B": [1, 1, 0, 0, 1, 0],
            "C": [1, 0, 0, 0, 0, 1],
        },
        index=["i1", "i2", "i3", "i4", "i5", "i6"],
    )
    items_attrs = pd.DataFrame(
        {"group": ["X", "X", "Y", "Y", "X", "Y"]},
        index=["i1", "i2", "i3", "i4", "i5", "i6"],
    )
    d = UpsetData(data=data, items_attrs=items_attrs)
    collectors = d.get_items_attr("group")
    cardinality = d.sets_table()["cardinality"]
    # "A only" exclusive == {i3, i4} (2); old inclusive path would have given 4
    assert [len(c) for c in collectors] == list(cardinality)
    assert sum(len(c) for c in collectors) == len(d.items)


def test_get_items_attr_single_set():
    # Single set -> scalar (not tuple) group keys / index entries
    data = pd.DataFrame({"A": [1, 0, 1]}, index=["i1", "i2", "i3"])
    items_attrs = pd.DataFrame({"g": ["X", "Y", "X"]}, index=["i1", "i2", "i3"])
    d = UpsetData(data=data, items_attrs=items_attrs)
    collectors = d.get_items_attr("g")
    assert sum(len(c) for c in collectors) == 3


# --- ordering accessors ---


def test_order_accessors(upset_data):
    u = Upset(upset_data)
    assert list(u.sets_order) == list(u.sets_size.index)
    assert list(u.subset_order) == list(u.sets_table.index)


def test_add_top_instance_extra_plot(three_sets):
    # Heatmap-style: hand-built plotter instance via inherited add_top
    data = UpsetData.from_sets(three_sets, sets_names=["A", "B", "C"])
    u = Upset(data)
    arr = np.arange(len(u.subset_order))
    u.add_top(Numbers(arr))
    u.render()


# --- no in-place mutation ---


def test_no_inplace_mutation(three_sets):
    data = UpsetData.from_sets(three_sets, sets_names=["A", "B", "C"])
    before_len = len(data.sets_table())
    before_cols = list(data.binary_table().columns)
    # min_degree=2 filters and sort_sets reorders -- on a copy, not the input
    Upset(data, min_degree=2, sort_sets="ascending")
    assert len(data.sets_table()) == before_len
    assert list(data.binary_table().columns) == before_cols
