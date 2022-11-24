A quick start guide to use Heatgraphy
=====================================

Heatgraphy is designed in object-oriented style, you can add blocks
and customize them freely.

Let's create a heatmap first. Here we use iris dataset.

.. plot::
    :context: close-figs

    >>> # load the dataset
    >>> from sklearn.datasets import load_iris
    >>> iris = load_iris()

    >>> import heatgraphy as hg
    >>> h = hg.Heatmap(iris.data)
    >>> h.render()


Now we create a minimum heatmap, but we want to add other
components like labels and other features of the iris dataset.

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


To perform cluster on the dataset, simply call
:meth:`add_dendrogram() <heatgraphy.base.MatrixBase.add_dendrogram>`, and it
will add the dendrogram for you. Here we add the dendrogram on the right side.
It's also possible to label your heatmap with colors, you don't need to care
about the order, we will take care for you.

But what if I want the colors to be together but not split them? You can
split the heatmap by labeling them. Use the :meth:`split_row() <heatgraphy.base.MatrixBase.split_row>`
or :meth:`split_col() <heatgraphy.base.MatrixBase.split_col>` to split your dataset.

.. code-block:: python
    :emphasize-lines: 3

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.split_row(labels=iris.target)
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.split_row(labels=iris.target)
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.render()

After that, we can add labels and title to the heatmap.

.. code-block:: python
    :emphasize-lines: 6,7

    >>> from heatgraphy.plotter import Labels
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.split_row(labels=iris.target)
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.add_bottom(Labels(iris.feature_names), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

    >>> from heatgraphy.plotter import Labels
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.split_row(labels=iris.target)
    >>> h.add_left(Colors(iris.target), size=.2, pad=.1)
    >>> h.add_bottom(Labels(iris.feature_names, rotation=90), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.render()

If we are happy with the results, we can finally add legends to the heatmap.

.. code-block:: python
    :emphasize-lines: 8

    >>> names = [iris.target_names[i] for i in iris.target]
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.split_row(labels=iris.target)
    >>> h.add_left(Colors(names, label="Names"), size=.2, pad=.1)
    >>> h.add_bottom(Labels(iris.feature_names, rotation=90), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.add_legends()
    >>> h.render()

.. plot::
    :context: close-figs
    :include-source: False

    >>> names = [iris.target_names[i] for i in iris.target]
    >>> h = hg.Heatmap(iris.data)
    >>> h.add_dendrogram("right")
    >>> h.split_row(labels=iris.target)
    >>> h.add_left(Colors(names, label="Names"), size=.2, pad=.1)
    >>> h.add_bottom(Labels(iris.feature_names, rotation=90), pad=.1)
    >>> h.add_title("Iris Dataset")
    >>> h.add_legends()
    >>> h.render()