.. meta::
   :description: Plot single-cell data in Marsilea directly from an AnnData or MuData object,
       using anndata accessor references for the matrix, cell annotations and gene annotations.

AnnData and MuData
==================

Marsilea can read straight from an :class:`~anndata.AnnData`. You bind the object
to a board once, then name the pieces to plot with :mod:`anndata.acc`
references instead of pulling arrays out by hand:

.. code-block:: bash

    $ pip install "marsilea[anndata]"

References need anndata 0.13 or newer, which requires Python 3.12.

Binding a source
----------------

Pass the object as the first argument, or as ``source=``. The two forms are
equivalent:

.. code-block:: python

    import marsilea as ma
    import marsilea.plotter as mp
    from anndata.acc import A

    h = ma.Heatmap(adata, A.X[:, :])
    h = ma.Heatmap(A.X[:, :], source=adata)

Every board accepts ``source=``, including boards that take no data of their own,
such as :class:`WhiteBoard <marsilea.WhiteBoard>`.

The examples below build a small AnnData from the bundled ``pbmc3k`` dataset, so
each figure can be reproduced as written:

.. plot::
    :context: close-figs

        >>> import anndata as ad
        >>> import pandas as pd
        >>> import marsilea as ma
        >>> import marsilea.plotter as mp
        >>> from anndata.acc import A
        >>>
        >>> pbmc3k = ma.load_data("pbmc3k")
        >>> exp, pct = pbmc3k["exp"], pbmc3k["pct_cells"]
        >>> lineage = ["Lymphoid", "Myeloid", "Lymphoid", "Lymphoid",
        ...            "Lymphoid", "Myeloid", "Myeloid", "Myeloid"]
        >>> adata = ad.AnnData(
        ...     X=exp.to_numpy(),
        ...     obs=pd.DataFrame(
        ...         {"lineage": pd.Categorical(lineage,
        ...                                    categories=["Lymphoid", "Myeloid"])},
        ...         index=exp.index),
        ...     var=pd.DataFrame(index=exp.columns),
        ... )
        >>> adata.layers["pct"] = pct.to_numpy()
        >>> h = ma.Heatmap(adata, A.X[:, :], width=4, height=3.5)
        >>> h.render()

Here observations are cell types and variables are genes.

References carry their axis
---------------------------

A reference knows which axes it spans, which is what lets a board place it.
``A.obs[...]`` spans observations, so it belongs on the left or right;
``A.var[...]`` spans variables, so it belongs on the top or bottom:

.. plot::
    :context: close-figs

        >>> h = ma.Heatmap(adata, A.X[:, :], width=4, height=3.5)
        >>> h.add_left(mp.Colors(A.obs["lineage"]), size=0.2)
        >>> h.add_left(mp.Labels(A.obs.index))
        >>> h.add_bottom(mp.Labels(A.var.index))
        >>> h.render()

Add one to the wrong side and the board raises ``MisalignedRef`` at that call,
naming both the reference and the fix. Without the axis information this would
surface much later, as a length mismatch during rendering.

``A.obs`` on its own is an accessor rather than a reference, since it carries no
index yet. Marsilea rejects it with a suggested spelling, ``A.obs["column"]``.

Genes as rows
-------------

An AnnData is observations by variables, but a single-cell heatmap usually wants
genes down the rows. ``obs_axis="col"`` swaps which board axis each AnnData axis
maps to. Your references still describe the real object, so nothing has to be
transposed in your head:

.. plot::
    :context: close-figs

        >>> h = ma.Heatmap(adata, A.X[:, :], obs_axis="col", width=4, height=3.5)
        >>> h.add_top(mp.Colors(A.obs["lineage"]), size=0.2)
        >>> h.add_left(mp.Labels(A.var.index))
        >>> h.render()

Selecting genes
---------------

Indexing with a list produces one reference per gene, and Marsilea stacks them
into a matrix. There is no need to subset the object first:

.. plot::
    :context: close-figs

        >>> genes = list(exp.columns[:6])
        >>> h = ma.Heatmap(adata, A.X[:, genes], width=3, height=3.5)
        >>> h.add_bottom(mp.Labels(genes))
        >>> h.render()

Grouping follows the categories
-------------------------------

When a column is categorical, its category order becomes the group order, so
``order=`` is usually unnecessary. This is what keeps cluster labels in the order
``0, 1, 2, 10`` instead of sorting them as text:

.. plot::
    :context: close-figs

        >>> h = ma.Heatmap(adata, A.X[:, :], width=4, height=3.5)
        >>> h.group_rows(A.obs["lineage"])
        >>> h.add_left(mp.Chunk(["Lymphoid", "Myeloid"], ["#33A6B8", "#B481BB"]))
        >>> h.render()

An explicit ``order=`` still takes precedence. Entries with no assigned category
form their own group, labelled ``NA``.

Layers and other arrays
-----------------------

Anything a reference can name works the same way, including layers and the
matrices behind a :class:`SizedHeatmap <marsilea.SizedHeatmap>`:

.. plot::
    :context: close-figs

        >>> h = ma.SizedHeatmap(adata, A.layers["pct"][:, :], A.X[:, :],
        ...                     width=4, height=3.5)
        >>> h.add_left(mp.Labels(A.obs.index))
        >>> h.render()

Sparse matrices
---------------

``adata.X`` is usually sparse, and Marsilea converts it for you, once per board.
Very large conversions raise a ``PerformanceWarning``; subsetting the object
first, with ``adata[:, genes]``, avoids it.

MuData
------

Everything above applies unchanged to a :class:`~mudata.MuData`, because
:mod:`mudata.acc` reuses the same reference objects. Import ``A`` from
``mudata.acc`` and reach into a modality with ``A.mod``:

.. code-block:: python

    from mudata.acc import A

    h = ma.Heatmap(mdata, A.mod["rna"].X[:, :])
    h.add_left(mp.Colors(A.obs["celltype"]))
    h.add_right(mp.ColorMesh(A.mod["adt"].X[:, :]))
    h.group_rows(A.obs["celltype"])

Modalities share the ``obs`` axis, so plots drawn from different modalities line
up on the rows without any reindexing on your part.


Working without references
--------------------------

None of this is required. Plain arrays behave exactly as they always have, and
sparse input is converted on that path too:

.. code-block:: python

    ma.Heatmap(adata[:, genes].X).render()
