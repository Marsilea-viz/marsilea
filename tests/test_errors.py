"""What the user sees when they get something wrong.

Marsilea builds lazily, so a mistake made at ``add_left`` used to surface at
``render`` with the real message swallowed and the offending line nowhere in
the traceback. These tests pin down the two halves of the fix: mismatches that
can be caught at the ``add_*`` call are caught there, and everything else keeps
its own error and gains a pointer back to where the plotter came from.
"""

import sys

import numpy as np
import pytest

import marsilea as ma
import marsilea.plotter as mp
from marsilea.utils import caller_location, _notebook_location


@pytest.fixture
def data():
    return np.random.RandomState(0).randn(10, 8)


# --- caught at the add_* call --------------------------------------------


@pytest.mark.parametrize(
    "side,expect",
    [
        ("left", "10 rows"),
        ("right", "10 rows"),
        ("top", "8 columns"),
        ("bottom", "8 columns"),
    ],
)
def test_wrong_length_is_rejected_where_it_is_added(data, side, expect):
    h = ma.Heatmap(data)
    with pytest.raises(ValueError, match=f"`Numbers` on '{side}'.*{expect}"):
        h.add_plot(side, mp.Numbers(np.arange(3)))


def test_layer_shape_is_rejected_where_it_is_added(data):
    h = ma.Heatmap(data)
    with pytest.raises(ValueError, match=r"`ColorMesh` has shape \(5, 5\)"):
        h.add_layer(mp.ColorMesh(np.random.rand(5, 5)))


def test_length_of_the_other_axis_suggests_the_other_side(data):
    h = ma.Heatmap(data)
    with pytest.raises(ValueError, match="try `add_top` or `add_bottom`"):
        h.add_left(mp.Numbers(np.arange(8)))

    h = ma.Heatmap(data)
    with pytest.raises(ValueError, match="try `add_left` or `add_right`"):
        h.add_top(mp.Numbers(np.arange(10)))


def test_a_length_that_fits_nothing_explains_the_convention(data):
    h = ma.Heatmap(data)
    with pytest.raises(ValueError, match="one value per row"):
        h.add_left(mp.Numbers(np.arange(3)))


def test_transposed_layer_is_named_as_such(data):
    h = ma.Heatmap(data)
    with pytest.raises(ValueError, match=r"looks transposed, try `data\.T`"):
        h.add_layer(mp.ColorMesh(np.random.rand(8, 10)))


def test_a_pinned_orient_does_not_suggest_moving_the_plot(data):
    # Violin(orient="h") reads its data along rows wherever it is put, so
    # "try the other side" would be wrong advice.
    h = ma.Heatmap(data)
    with pytest.raises(ValueError, match="orient='h' reads values along rows") as err:
        h.add_top(mp.Violin(np.random.rand(4, 8), orient="h"))
    assert "try `add_" not in str(err.value)


def test_a_rejected_plot_leaves_the_board_usable(data):
    h = ma.Heatmap(data)
    with pytest.raises(ValueError):
        h.add_left(mp.Numbers(np.arange(3)))
    # No orphan axes left in the layout by the failed add.
    h.add_left(mp.Numbers(np.arange(10)))
    h.render()


# --- and what must NOT be rejected ----------------------------------------


def test_correct_data_is_accepted_on_every_side(data):
    h = ma.Heatmap(data)
    h.add_left(mp.Numbers(np.arange(10)))
    h.add_top(mp.Numbers(np.arange(8)))
    h.add_layer(mp.MarkerMesh(data > 1, color="red"))
    h.render()


def test_seaborn_plotters_follow_their_orientation(data):
    h = ma.Heatmap(data)
    h.add_left(mp.Violin(np.random.rand(4, 10)))
    h.add_top(mp.Violin(np.random.rand(4, 8)))
    h.render()


def test_plotters_without_deformable_data_are_left_alone(data):
    h = ma.Heatmap(data)
    h.group_rows(["a"] * 5 + ["b"] * 5)
    h.add_right(mp.Chunk(["a", "b"]))  # counted per group, not per row
    h.add_title(top="a title")  # allow_split = False, never deformed
    h.render()


def test_a_board_without_a_grid_is_not_checked():
    wb = ma.WhiteBoard(width=3, height=3)
    wb.add_left(mp.Numbers(np.arange(4)))
    wb.add_top(mp.Numbers(np.arange(7)))
    wb.render()


# --- render-time failures keep their own error ----------------------------


def _chunk_board(data):
    h = ma.Heatmap(data)
    h.group_rows(["a"] * 5 + ["b"] * 5)
    h.add_right(mp.Chunk(["a", "b", "c"]))
    return h


def test_render_error_keeps_its_type_and_message(data):
    # Regression: this used to be re-wrapped into a bare Exception whose
    # message was the plotter's repr, discarding the real one.
    with pytest.raises(ValueError, match="has 3 labels but the rows are in 2 groups"):
        _chunk_board(data).render()


def test_render_error_names_the_plotter_and_its_call_site(data):
    h = _chunk_board(data)
    with pytest.raises(ValueError) as err:
        h.render()
    notes = "\n".join(err.value.__notes__)
    assert "while rendering Chunk on 'right'" in notes
    assert "added at" in notes
    assert __file__ in notes


def test_a_deformation_mismatch_reaches_the_caller_intact(data):
    # Reach past add_plot's check to prove the render path no longer swallows
    # the message Deformation raises.
    h = ma.Heatmap(data)
    plot = mp.Numbers(np.arange(10))
    h.add_left(plot)
    plot.set_data(np.arange(3))
    with pytest.raises(ValueError, match="3 elements on the row axis, expected 10"):
        h.render()


# --- the other messages ---------------------------------------------------


def test_text_data_points_at_the_categorical_heatmap():
    with pytest.raises(ValueError, match="needs numbers.*CatHeatmap"):
        ma.Heatmap(np.array([["a"] * 8] * 10))


def test_categorical_heatmap_still_takes_text():
    ma.CatHeatmap(np.array([["a", "b"], ["b", "a"]])).render()


def test_unknown_axes_name_lists_the_real_ones(data):
    h = ma.Heatmap(data)
    h.add_left(mp.Numbers(np.arange(10)), name="bars")
    h.render()
    with pytest.raises(KeyError, match="No axes named 'nope'.*Named axes.*bars"):
        h.get_ax("nope")


def test_asking_for_an_axes_before_render_says_so(data):
    h = ma.Heatmap(data)
    h.add_left(mp.Numbers(np.arange(10)), name="bars")
    with pytest.raises(KeyError, match="has no axes yet, call `render"):
        h.get_ax("bars")


def test_cut_outside_the_data_is_rejected(data):
    with pytest.raises(
        ValueError, match=r"Cannot cut rows at \[99\], there are only 10 rows"
    ):
        ma.Heatmap(data).cut_rows([99])
    with pytest.raises(
        ValueError, match=r"Cannot cut columns at \[99\], there are only 8 columns"
    ):
        ma.Heatmap(data).cut_cols([99])
    with pytest.raises(ValueError, match="Cuts go between 1 and 9"):
        ma.Heatmap(data).cut_rows([0])


def test_repeated_cut_is_rejected(data):
    with pytest.raises(ValueError, match=r"Cannot cut rows at \[4\] twice"):
        ma.Heatmap(data).cut_rows([4, 4])


def test_valid_cuts_and_groups_still_split(data):
    h = ma.Heatmap(data)
    h.cut_rows([4])
    h.render()

    h = ma.Heatmap(data)
    h.group_rows(["a"] * 5 + ["b"] * 5)
    h.render()


# --- where the call site points, per environment --------------------------


class _FakeCompiler:
    def __init__(self, mapping):
        self.mapping = mapping

    def format_code_name(self, name):
        number = self.mapping.get(name)
        return None if number is None else ("Cell", f"In[{number}]")


class _FakeIPython:
    """Just enough of the IPython module for `_notebook_location`."""

    def __init__(self, shell):
        self._shell = shell

    def get_ipython(self):
        return self._shell


class _FakeShell:
    def __init__(self, mapping):
        self.compile = _FakeCompiler(mapping)


def _fake_ipython(monkeypatch, shell):
    monkeypatch.setitem(sys.modules, "IPython", _FakeIPython(shell))


def test_a_notebook_cell_is_named_by_its_execution_count(monkeypatch):
    _fake_ipython(monkeypatch, _FakeShell({"/tmp/ipykernel_9/12345.py": 3}))
    assert _notebook_location("/tmp/ipykernel_9/12345.py", 12) == "Cell In[3]:12"


def test_a_real_file_keeps_its_path(monkeypatch):
    _fake_ipython(monkeypatch, _FakeShell({}))
    assert _notebook_location("/home/me/plot.py", 12) is None


def test_no_shell_running_falls_back_to_the_path(monkeypatch):
    _fake_ipython(monkeypatch, None)  # IPython imported, but not a shell
    assert _notebook_location("/tmp/ipykernel_9/12345.py", 12) is None


def test_an_unexpected_ipython_never_breaks_the_error(monkeypatch):
    class Exploding:
        @property
        def compile(self):
            raise RuntimeError("IPython changed shape")

    _fake_ipython(monkeypatch, Exploding())
    assert _notebook_location("/tmp/ipykernel_9/12345.py", 12) is None


def test_a_marimo_cell_is_named_by_its_cell_id(monkeypatch):
    _fake_ipython(monkeypatch, None)
    location = _notebook_location("/tmp/marimo_17/__marimo__cell_Hbol_.py", 3)
    assert location == "marimo cell Hbol:3"


def test_marimo_running_a_notebook_file_keeps_the_path(monkeypatch):
    # marimo notebooks are real .py files; when it runs one the frame already
    # points somewhere the reader can open.
    _fake_ipython(monkeypatch, None)
    assert _notebook_location("/home/me/analysis.py", 3) is None


def test_caller_location_reports_this_file_outside_a_notebook():
    location = caller_location()
    assert location.startswith(__file__)


def test_ipython_still_offers_the_api_the_cell_name_relies_on():
    # A contract test: if IPython drops or renames this, the call site quietly
    # degrades to a temp path, which is the whole thing worth avoiding.
    compilerop = pytest.importorskip("IPython.core.compilerop")
    assert hasattr(compilerop.CachingCompiler, "format_code_name")
