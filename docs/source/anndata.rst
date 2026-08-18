Plotting from an AnnData or MuData
==================================

Marsilea boards can bind an :class:`~anndata.AnnData` or a
:class:`~mudata.MuData` and then take *references* — ``A.obs["leiden"]``,
``A.X[:, :]``, ``A.var.index`` — anywhere data is accepted. Install with:

.. code-block:: bash

    $ pip install "marsilea[anndata]"

This needs anndata 0.13 or newer (Python 3.12+), where ``anndata.acc`` was added.

Binding a source
----------------

Pass the object as the first argument, or as ``source=``:

.. code-block:: python

    import marsilea as ma
    import marsilea.plotter as mp
    from anndata.acc import A

    h = ma.Heatmap(adata, A.X[:, :])          # positional
    h = ma.Heatmap(A.X[:, :], source=adata)   # equivalent

Every board takes ``source=``, including ones with no data argument of their own
(``ma.WhiteBoard(adata)``).

References know their axis
--------------------------

Each reference carries the axes it spans, so marsilea can tell where a plot
belongs. ``A.obs[...]`` spans observations and goes on the row sides;
``A.var[...]`` spans variables and goes on the column sides:

.. code-block:: python

    h = ma.Heatmap(adata, A.X[:, :])
    h.add_left(mp.Colors(A.obs["cell_type"]))
    h.add_left(mp.Labels(A.obs.index))
    h.add_top(mp.Numbers(A.var["n_cells"]))
    h.render()

Put one on the wrong side and you get :class:`~marsilea.exceptions.MisalignedRef`
at the ``add_*`` call, naming the reference and the fix, rather than an alignment
failure later at render.

Note ``A.obs`` is an *accessor*, not a reference — it needs an index. Use
``A.obs["column"]``.

Genes as rows: ``obs_axis``
---------------------------

AnnData is observations × variables, but single-cell heatmaps usually want genes
on the rows. ``obs_axis="col"`` flips which board axis each AnnData axis maps to.
Your references still mean the real object — no mental transposition:

.. code-block:: python

    h = ma.Heatmap(adata, A.X[:, :], obs_axis="col")
    h.add_top(mp.Colors(A.obs["cell_type"]))   # obs -> columns
    h.add_left(mp.Labels(A.var.index))         # var -> rows
    h.group_cols(A.obs["leiden"])

Gene panels
-----------

Indexing with a list gives one reference per gene, stacked into a matrix — no need
to subset the object first:

.. code-block:: python

    h = ma.Heatmap(adata, A.X[:, ["CD3E", "MS4A1", "LYZ"]])

Grouping follows the categories
-------------------------------

When the column is categorical, its category order becomes the group order, so
``order=`` is usually unnecessary. This is what makes leiden clusters group
``0, 1, 2, 10`` rather than sorting as strings:

.. code-block:: python

    h.group_rows(A.obs["leiden"])                       # uses .cat.categories
    h.group_rows(A.obs["leiden"], order=["2", "1"])     # explicit still wins

An explicit ``order=`` always takes precedence. Unassigned (NaN) entries become
their own group, labelled ``NA``.

Sparse matrices
---------------

``adata.X`` is usually sparse. Marsilea densifies it for you, once per board, and
warns when the dense result would be very large — subset first
(``adata[:, genes]``) if you hit that.

MuData
------

Everything above works unchanged on a :class:`~mudata.MuData`, because
:mod:`mudata.acc` reuses the same reference objects. Import ``A`` from
``mudata.acc`` instead, and reach into a modality with ``A.mod``:

.. code-block:: python

    from mudata.acc import A

    h = ma.Heatmap(mdata, A.mod["rna"].X[:, :])
    h.add_left(mp.Colors(A.obs["celltype"]))     # shared obs
    h.add_right(mp.ColorMesh(A.mod["adt"].X[:, :]))
    h.group_rows(A.obs["celltype"])

Modalities share the ``obs`` axis, so plots drawn from different modalities line
up on the rows without any manual reindexing.

Other containers
----------------

Marsilea accepts any container that speaks the same accessor protocol: its
references are ``anndata.acc.AdRef``, ``container[ref]`` materializes one, and
``ref.dims`` reports the axes it spans. AnnData and MuData both qualify.

Register another with one call:

.. code-block:: python

    from marsilea._sources import register_source

    register_source("somepkg", "SomeContainer")

The type is named rather than imported, so registering it does not import the
package — detection only fires once the container has been imported anyway.
A container that does *not* speak the protocol needs more than this; open an
issue describing it.

Without references
------------------

None of this is required. Plain arrays still work exactly as before, and sparse
input is handled on that path too:

.. code-block:: python

    ma.Heatmap(adata[:, genes].X).render()
