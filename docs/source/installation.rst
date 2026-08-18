:html_theme.sidebar_primary.remove:
:html_theme.sidebar.remove:


Installation
============

Marsilea is available on PyPI. You can install it with the following command:

.. code-block:: bash

    $ pip install marsilea


Optional features
-----------------

Some features need extra packages. Install them with the matching extra:

.. list-table::
    :header-rows: 1
    :widths: 20 80

    * - Extra
      - What it enables
    * - ``marsilea[anndata]``
      - Pass an :class:`~anndata.AnnData` to a board and name your data with
        :mod:`anndata.acc` references, e.g.
        ``ma.Heatmap(adata, A.X[:, :])`` and
        ``h.add_left(mp.Colors(A.obs["cell_type"]))``. Needs Python 3.12+.
    * - ``marsilea[stats]``
      - Significance annotation on the seaborn plotters
        (:meth:`~marsilea.plotter.Violin.annotate_stats`).
    * - ``marsilea[fast]``
      - Faster hierarchical clustering on large matrices via ``fastcluster``.

To install more than one at a time:

.. code-block:: bash

    $ pip install "marsilea[anndata,stats]"


