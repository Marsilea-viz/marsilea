Significance Annotation
=======================

Every seaborn plotter can run a statistical test on pairs of categories and
draw the result on the plot: :class:`Bar <marsilea.plotter.Bar>`,
:class:`Box <marsilea.plotter.Box>`, :class:`Boxen <marsilea.plotter.Boxen>`,
:class:`Violin <marsilea.plotter.Violin>`,
:class:`Point <marsilea.plotter.Point>`,
:class:`Strip <marsilea.plotter.Strip>` and
:class:`Swarm <marsilea.plotter.Swarm>`.

The tests come from
`statannotations <https://github.com/trevismd/statannotations>`_, an optional
dependency::

    pip install marsilea[stats]

Marsilea draws the brackets itself, so a comparison between two groups of a
split canvas — which has to span two axes — comes out looking like any other.


Comparing conditions
--------------------

Pass a dict to a seaborn plotter to get one plot per condition, then call
:meth:`annotate_stats() <marsilea.plotter.Box.annotate_stats>` with
:code:`pairs="hue"` to compare the conditions inside every category.

.. plot::
    :context: close-figs

    >>> import marsilea as ma
    >>> import marsilea.plotter as mp
    >>> genes = [f"Gene {i}" for i in range(6)]
    >>> control = pd.DataFrame(np.random.normal(4, 1, (30, 6)), columns=genes)
    >>> treated = pd.DataFrame(
    ...     np.random.normal(4, 1, (30, 6)) + [0, 1, -1, 0, 1.5, 0], columns=genes
    ... )
    >>> box = mp.Box({"Control": control, "Treated": treated}, label="Expression")
    >>> box.annotate_stats(pairs="hue", test="Mann-Whitney", text_format="star")
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.add_top(box, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.add_legends()
    >>> h.render()

:code:`test`, :code:`text_format` and :code:`comparisons_correction` name the
same things statannotations does, and :code:`color`, :code:`line_width`,
:code:`text_offset` and :code:`fontsize` style the brackets. Correcting for
multiple testing needs :code:`statsmodels`, and matters here:
:code:`pairs="hue"` runs one test per category. The correction covers every
comparison drawn on the plot at once, groups included.

.. plot::
    :context: close-figs

    >>> box = mp.Box({"Control": control, "Treated": treated}, label="Expression")
    >>> box.annotate_stats(
    ...     pairs="hue",
    ...     test="t-test_ind",
    ...     text_format="simple",
    ...     comparisons_correction="Benjamini-Hochberg",
    ... )
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.add_top(box, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.render()


Naming the categories
---------------------

Categories are named with the **columns of the input data**. When the input is a
plain array, they are named by position instead (0, 1, 2, ...).

An explicit list of pairs annotates only the comparisons you care about. Each
side of a pair is a :code:`(category, condition)` tuple when the data has
conditions, or a bare category label when it does not.

.. plot::
    :context: close-figs

    >>> box = mp.Box({"Control": control, "Treated": treated}, label="Expression")
    >>> box.annotate_stats(
    ...     pairs=[
    ...         (("Gene 1", "Control"), ("Gene 1", "Treated")),
    ...         (("Gene 4", "Control"), ("Gene 4", "Treated")),
    ...         (("Gene 1", "Treated"), ("Gene 4", "Treated")),
    ...     ],
    ...     text_format="star",
    ... )
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.add_top(box, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.render()

Two shorthands save the typing when the comparisons are systematic.
:code:`pairs="all"` compares the categories with each other, and :code:`ref`
reduces either shorthand to comparisons against one reference — a condition for
:code:`pairs="hue"`, a category for :code:`pairs="all"`.

.. plot::
    :context: close-figs

    >>> dose = pd.DataFrame(np.random.normal(4, 1, (30, 4)), columns=list("0123"))
    >>> dose += [0, 0.5, 1.0, 1.8]
    >>> bar = mp.Bar(dose, color="#8FB9AA", label="Response")
    >>> bar.annotate_stats(pairs="all", ref="0", text_format="star")
    >>> h = ma.Heatmap(dose.values, label="Response", width=2, height=3)
    >>> h.add_top(bar, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels([f"{d} mg" for d in "0123"]))
    >>> h.render()


Grouping and clustering
-----------------------

The annotation is attached to the data, not to a position, so it follows the
categories wherever grouping and clustering move them.

.. plot::
    :context: close-figs

    >>> up = np.array([0, 1, -1, 0, 1.5, 0]) > 0
    >>> box = mp.Box({"Control": control, "Treated": treated}, label="Expression")
    >>> box.annotate_stats(pairs="hue", text_format="star")
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.group_cols(np.where(up, "Up", "Down"), order=["Up", "Down"])
    >>> h.add_top(box, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.add_legends()
    >>> h.render()


Comparing across groups
-----------------------

Each group is drawn on its own axes, so a bracket between two groups has to
span them. Ask for the pair and it is drawn: those brackets are placed in
figure coordinates, above every within-group bracket they pass over.

.. plot::
    :context: close-figs

    >>> box = mp.Box({"Control": control, "Treated": treated}, label="Expression")
    >>> box.annotate_stats(
    ...     pairs=[
    ...         (("Gene 1", "Control"), ("Gene 1", "Treated")),
    ...         (("Gene 1", "Treated"), ("Gene 2", "Treated")),
    ...         (("Gene 1", "Treated"), ("Gene 5", "Treated")),
    ...     ],
    ...     text_format="star",
    ... )
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.group_cols(np.where(up, "Up", "Down"), order=["Up", "Down"])
    >>> h.add_top(box, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.render()

:code:`ref` reaches across groups too, so a control category can be compared
with everything else no matter which group it ended up in. Remember it draws
one bracket per remaining category, per condition — with a single condition
that stays readable.

.. plot::
    :context: close-figs

    >>> box = mp.Box(treated, color="#8FB9AA", label="Expression")
    >>> box.annotate_stats(pairs="all", ref="Gene 0", text_format="star")
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.group_cols(np.where(up, "Up", "Down"), order=["Up", "Down"])
    >>> h.add_top(box, size=2.5, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.render()

.. note::

    Bare :code:`pairs="all"` stays inside each group — every pair across a
    9-category split would be 36 brackets. Name the pairs you want, or use
    :code:`ref`.


Overlaid hue levels
-------------------

:class:`Strip <marsilea.plotter.Strip>`,
:class:`Swarm <marsilea.plotter.Swarm>` and
:class:`Point <marsilea.plotter.Point>` draw their hue levels on top of each
other unless you pass :code:`dodge=True`. A bracket between two levels drawn at
the same place would have nothing to point at, so those comparisons are skipped
with a warning telling you what to pass.

.. plot::
    :context: close-figs

    >>> strip = mp.Strip(
    ...     {"Control": control, "Treated": treated},
    ...     dodge=True, size=3, label="Expression",
    ... )
    >>> strip.annotate_stats(pairs="hue", text_format="star")
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.add_top(strip, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.add_legends()
    >>> h.render()


Groups of unequal size
----------------------

Wide input has to be rectangular, and real groups rarely are. Pad the short
ones with :code:`NaN`; pandas does it for you and keeps the column labels that
name the pairs::

    pd.DataFrame({"A": pd.Series(a), "B": pd.Series(b)})

Padding is not data. It stays out of the plot and out of the test, so a group
of 8 is tested as 8 values.

If a group has nothing left to test, there is no p-value and no label. The
bracket is still drawn, and a warning names the pair, because an empty label
is easy to miss on a finished figure.

.. plot::
    :context: close-figs

    >>> sizes = [30, 12, 30, 8, 30, 30]
    >>> ragged = pd.DataFrame(
    ...     {g: pd.Series(np.random.normal(4, 1, n)) for g, n in zip(genes, sizes)}
    ... )
    >>> box = mp.Box({"Control": ragged, "Treated": treated}, label="Expression")
    >>> box.annotate_stats(pairs="hue", text_format="star")
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.add_top(box, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.add_legends()
    >>> h.render()


Orientation
-----------

A plot on the left or right is drawn horizontally, and the brackets follow — on
the left they are placed on the outer side, away from the main canvas.

.. plot::
    :context: close-figs

    >>> samples = [f"S{i}" for i in range(8)]
    >>> a = pd.DataFrame(np.random.normal(4, 1, (30, 8)), columns=samples)
    >>> b = pd.DataFrame(np.random.normal(5, 1, (30, 8)), columns=samples)
    >>> box = mp.Box({"Control": a, "Treated": b}, label="Expression")
    >>> box.annotate_stats(pairs="hue", text_format="star")
    >>> h = ma.Heatmap(b.values.T - a.values.T, label="Difference")
    >>> h.add_left(box, size=2, pad=0.1)
    >>> h.add_right(mp.Labels(samples))
    >>> h.render()


Annotating p-values you already have
------------------------------------

When the test comes from somewhere else — a differential expression pipeline, a
model — pass the p-values with :code:`pvalues` and no test is run. There must be
one value per pair, in the order the pairs were given.

.. plot::
    :context: close-figs

    >>> box = mp.Box({"Control": control, "Treated": treated}, label="Expression")
    >>> box.annotate_stats(
    ...     pairs=[
    ...         (("Gene 0", "Control"), ("Gene 0", "Treated")),
    ...         (("Gene 2", "Control"), ("Gene 2", "Treated")),
    ...     ],
    ...     pvalues=[0.3, 1e-5],
    ...     text_format="star",
    ... )
    >>> h = ma.Heatmap(treated.values - control.values, label="Difference")
    >>> h.add_top(box, size=2, pad=0.1)
    >>> h.add_bottom(mp.Labels(genes))
    >>> h.render()
