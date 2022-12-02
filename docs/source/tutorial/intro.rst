10 Minutes to Heatgraphy
=========================

Heatgraphy can help you create grid layout visualization.
It's designed in object-oriented style that makes adding blocks
and customization easily.

A minimum heatmap
-----------------

Let's try create a heatmap! Here we use the iris dataset.

.. plot::
    :context: close-figs

    >>> # load the dataset
    >>> from sklearn.datasets import load_iris
    >>> iris = load_iris()

    >>> import heatgraphy as hg
    >>> h = hg.Heatmap(iris.data)
    >>> h.render()


Now a minimum heatmap is created, remember to call :meth:`render() <heatgraphy.base.Base.render>` to actually render your
plot. Otherwise, no plot will be generated.

Add side plots
--------------

Usually, we want to add components like labels, dendrogram and other plots when making a heatmap.

.. code-block:: python
    :emphasize-lines: 3,4

    >>> from heatgraphy.plotter import Colors
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.render()


.. plot::
    :context: close-figs
    :include-source: False

    >>> from heatgraphy.plotter import Colors
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.render()


To add a dendrogram on the dataset, simply call
:meth:`add_dendrogram() <heatgraphy.base.MatrixBase.add_dendrogram>`, and it
will add the dendrogram for you. Here we add the dendrogram on the right side.
You can also add it to the top or bottom to perform column-wise cluster.

Split heatmap
-------------

We also use colors to label the names of iris. What if I want the same color to be together? You can
split the heatmap by labeling them. Use the :meth:`split_row() <heatgraphy.base.MatrixBase.split_row>`
or :meth:`split_col() <heatgraphy.base.MatrixBase.split_col>` to split the heatmap.

.. code-block:: python
    :emphasize-lines: 4

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.split_row(labels=iris.target)
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.split_row(labels=iris.target)
    >>> h.render()

.. note::

    The order of adding plots or split the heatmap is arbitrary,
    just make sure you remember to call :meth:`render()` at the very end.


Add title and labels
--------------------

You can also add labels and title to the heatmap.

.. code-block:: python
    :emphasize-lines: 6,7

    >>> from heatgraphy.plotter import Labels
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.split_row(labels=iris.target)
    >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

    >>> from heatgraphy.plotter import Labels
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.split_row(labels=iris.target)
    >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.render()


Add legends
-----------

If we are happy with the results, you may add legends to the heatmap.

.. code-block:: python
    :emphasize-lines: 8

    >>> names = [iris.target_names[i] for i in iris.target]
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(names, label="Names"), size=.2, pad=.1)
    >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
    >>> h.split_row(labels=iris.target)
    >>> h.add_title("Iris Dataset")
    >>> h.add_legends()
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

    >>> names = [iris.target_names[i] for i in iris.target]
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(names, label="Names"), size=.2, pad=.1)
    >>> h.split_row(labels=iris.target)
    >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.add_legends()
    >>> h.render()

Add layers
----------

It's also possible to add an extra layer of heatmap to label a specific plot.

Here we can try to label the data that are larger than 4.

.. code-block:: python
    :emphasize-lines: 8

    >>> ix = np.random.choice(np.arange(len(iris.data)), 10, replace=False)
    >>> h = hg.Heatmap(iris.data[ix])
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(np.array(names)[ix], label="Names"), size=.2, pad=.1)
    >>> h.split_row(labels=iris.target[ix])
    >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.add_layer(hg.plotter.MarkerMesh(iris.data[ix] > 4, label="Larger than 4"))
    >>> h.add_legends()
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

    >>> ix = np.random.choice(np.arange(len(iris.data)), 10, replace=False)
    >>> h = hg.Heatmap(iris.data[ix])
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(np.array(names)[ix], label="Names"), size=.2, pad=.1)
    >>> h.split_row(labels=iris.target[ix])
    >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.add_layer(hg.plotter.MarkerMesh(iris.data[ix] > 4, label="Larger than 4"))
    >>> h.add_legends()
    >>> h.render()