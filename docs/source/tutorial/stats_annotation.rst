Significance Annotation
=======================

The seaborn plotters can run a statistical test on pairs of categories and draw
the result on the plot, using
`statannotations <https://github.com/trevismd/statannotations>`_. It is an
optional dependency::

    pip install marsilea[stats]

It works with :class:`Bar <marsilea.plotter.Bar>`,
:class:`Box <marsilea.plotter.Box>`, :class:`Violin <marsilea.plotter.Violin>`,
:class:`Strip <marsilea.plotter.Strip>` and
:class:`Swarm <marsilea.plotter.Swarm>`;
:class:`Boxen <marsilea.plotter.Boxen>` and
:class:`Point <marsilea.plotter.Point>` are not supported by statannotations.


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

Everything after *pairs* is handed to statannotations, so
:code:`test`, :code:`text_format`, :code:`loc` and
:code:`comparisons_correction` behave as documented in
:meth:`Annotator.configure() <statannotations.Annotator.Annotator.configure>`.
Correcting for multiple testing needs :code:`statsmodels`, and matters here:
:code:`pairs="hue"` runs one test per category.

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

A group is drawn on its own axes, though, so a pair whose two members end up in
different groups cannot be bracketed. Those pairs are skipped and a warning
tells you which ones.

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
