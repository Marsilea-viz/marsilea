10 Minutes to Heatgraphy
=========================

Heatgraphy can help you create x-layout visualization.
It's designed in object-oriented style that makes adding blocks
and customization easily.

A minimum heatmap
-----------------

Let's try create a heatmap! Heatgraphy provides many high-level plotting function
to be used.

.. plot::
    :context: close-figs

        >>> # load the dataset
        >>> from sklearn.datasets import load_iris
        >>> iris = load_iris()

        >>> import marsilea as hg
        >>> h = hg.Heatmap(iris.data)
        >>> h.render()


    Now a minimum heatmap is created, remember to call

        >>> # load the dataset
        >>> from sklearn.datasets import load_iris
        >>> iris = load_iris()

        >>> import marsilea as hg
        >>> h = hg.Heatmap(iris.data)
        >>> h.render()


    Now a minimum heatmap is created, remember to call

    >>> # load the dataset
    >>> from sklearn.datasets import load_iris
    >>> iris = load_iris()

    >>> import marsilea as hg
    >>> h = hg.Heatmap(iris.data)
    >>> h.render()


Now a minimum heatmap is created, remember to call :meth:`render() <marsilea.WhiteBoard.render>` to actually render your
plot. Otherwise, no plot will be generated.

Add side plots
--------------

Usually, we want to add components like labels, dendrogram and other plots when making a heatmap.

.. code-block:: python
    :emphasize-lines: 3,4

    >>> from marsilea.plotter import Colors
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.render()


.. plot::
    :context: close-figs
    :include-source: False

        >>> from marsilea.plotter import Colors
        >>> h = hg.Heatmap(iris.data)
        >>> h.add_dendrogram("right")
        >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
        >>> h.render()


    To add a dendrogram on the dataset, simply call

        >>> from marsilea.plotter import Colors
        >>> h = hg.Heatmap(iris.data)
        >>> h.add_dendrogram("right")
        >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
        >>> h.render()


    To add a dendrogram on the dataset, simply call

    >>> from marsilea.plotter import Colors
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.render()


To add a dendrogram on the dataset, simply call
:meth:`add_dendrogram() <marsilea.ClusterBoard.add_dendrogram>`, and it
will add the dendrogram for you. Here we add the dendrogram on the right side.
You can also add it to the top or bottom to perform column-wise cluster.

Split heatmap
-------------

We also use colors to label the names of iris. What if I want the same color to be together? You can
split the heatmap by labeling them. Use the :meth:`hsplit() <marsilea.ClusterBoard.hsplit>`
or :meth:`vsplit() <marsilea.ClusterBoard.vsplit>` to split the heatmap.

.. code-block:: python
    :emphasize-lines: 4

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.hsplit(labels=iris.target)
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.hsplit(labels=iris.target)
    >>> h.render()

.. note::

    The order of adding plots or split the heatmap is arbitrary,
    just make sure you remember to call :meth:`render()` at the very end.


Add title and labels
--------------------

You can also add labels and title to the heatmap.

.. code-block:: python
    :emphasize-lines: 6,7

    >>> from marsilea.plotter import Labels
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.hsplit(labels=iris.target)
    >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

        >>> from marsilea.plotter import Labels
        >>> h = hg.Heatmap(iris.data)
        >>> h.add_dendrogram("right")
        >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
        >>> h.hsplit(labels=iris.target)
        >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
        >>> h.add_title("Iris Dataset")
        >>> h.render()

        >>> from marsilea.plotter import Labels
        >>> h = hg.Heatmap(iris.data)
        >>> h.add_dendrogram("right")
        >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
        >>> h.hsplit(labels=iris.target)
        >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
        >>> h.add_title("Iris Dataset")
        >>> h.render()

    >>> from marsilea.plotter import Labels
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.hsplit(labels=iris.target)
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
    >>> h.hsplit(labels=iris.target)
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
    >>> h.hsplit(labels=iris.target)
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
    >>> h.hsplit(labels=iris.target[ix])
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
    >>> h.hsplit(labels=iris.target[ix])
    >>> h.add_bottom(Labels(iris.feature_names, rotation=0, fontsize=6), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.add_layer(hg.plotter.MarkerMesh(iris.data[ix] > 4, label="Larger than 4"))
    >>> h.add_legends()
    >>> h.render()


Adjust plot size and spacing
-----------------------------

Adjust figure size
##################

To adjust the overall figure size. You can simply pass :obj:`scale` parameter to :meth:`render()`

.. plot::
    :context: close-figs

    >>> data = np.random.rand(10, 10)
    >>> h = hg.Heatmap(data)
    >>> h.render()


.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(data)
    >>> h.render(scale=0.1)

You can also adjust the canvas size by :obj:`width` and :obj:`height`.
The unit are proportional to the figure size. Suppose the figure width is 12 inches,
you have a main canvas with width of 5 and a side plot with width of 1. As a result,
your main canvas is 10 inches width and the side plot is 2 inches width.

.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(data, width=10, height=5)
    >>> h.render()

Adjust size of side plot
########################

You may already notice that you can change
the size of the side plots by :obj:`size` and add spacing by :obj:`pad`.


.. plot::
    :context: close-figs

        >>> from marsilea.plotter import Colors
        >>> h = hg.Heatmap(iris.data)
        >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
        >>> h.render()

        >>> from marsilea.plotter import Colors
        >>> h = hg.Heatmap(iris.data)
        >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
        >>> h.render()

    >>> from marsilea.plotter import Colors
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.render()


.. plot::
    :context: close-figs

        >>> from marsilea.plotter import Colors
        >>> h = hg.Heatmap(iris.data)
        >>> h.add_left(Colors(iris.target), size=.5, pad=.2)
        >>> h.render()

        >>> from marsilea.plotter import Colors
        >>> h = hg.Heatmap(iris.data)
        >>> h.add_left(Colors(iris.target), size=.5, pad=.2)
        >>> h.render()

    >>> from marsilea.plotter import Colors
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_left(Colors(iris.target), size=.5, pad=.2)
    >>> h.render()


Adjust spacing of split heatmap
###############################

You can also adjust the spacing when split heatmap, the unit is the ratio of the axes.

.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.hsplit(labels=iris.target)
    >>> h.render()


.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.hsplit(labels=iris.target, spacing=.01)
    >>> h.render()


You may change the spacing by supplying an array.


.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.hsplit(labels=iris.target, spacing=[.02, .04])
    >>> h.render()