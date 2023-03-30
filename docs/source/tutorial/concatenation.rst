Concatenate multiple x-layout
=============================

multiple heatmaps together with ease.
=======
Visualizing multiple heatmaps side by side can provide valuable insights.
While merging images is one way to do this,
Marsilea offers a seamless concatenation feature that effortlessly combines multiple heatmaps for you.

Suppose you have a blue heatmap and a green heatmap, as shown below:

.. plot::
    :context: close-figs

        >>> import marsilea as hg
        >>> data1 = np.random.rand(10,12)
        >>> h1 = hg.Heatmap(data1, cmap="Blues", width=5, name="h1")
        >>> h1.add_title(top="Blue", align="left")
        >>> h1.render()

        >>> import marsilea as hg
        >>> data1 = np.random.rand(10,12)
        >>> h1 = hg.Heatmap(data1, cmap="Blues", width=5, name="h1")
        >>> h1.add_title(top="Blue", align="left")
        >>> h1.render()

    >>> import marsilea as hg
    >>> data1 = np.random.rand(10,12)
    >>> h1 = hg.Heatmap(data1, cmap="Blues", width=5, name="h1")
    >>> h1.add_title(top="Blue", align="left")
    >>> h1.render()


.. plot::
    :context: close-figs

    >>> data2 = np.random.rand(5,10)
    >>> h2 = hg.Heatmap(data2, cmap="Greens", width=3, name="h2")
    >>> h2.add_title(top="Green", align="left")
    >>> h2.render()


To concatenate heatmaps horizontally, simply use the add operator **+**.:

.. plot::
    :context: close-figs

    >>> (h1 + h2).render()

But if the heatmaps appear too close together, don't fret!
You can add space between them by including a number:

.. plot::
    :context: close-figs

    >>> (h1 + .2 + h2).render()

For vertical concatenation, use the divide operator **/**:

.. plot::
    :context: close-figs

    >>> (h1 / .2 / h2).render()

Take note that when concatenating,
the width of the secondary heatmap(s) will be adjusted to match the main heatmap's layout.
For example, the width of :code:`h2` becomes 5 to match :code:`h1`


Legends
-------

It is important to remember that legends should be added after concatenations.
So that marsilea can layout legends from all your heatmaps.
=======
It's crucial to add legends after concatenation,
so Marsilea can effectively arrange legends from all your heatmaps.


.. plot::
    :context: close-figs

    >>> c = (h1 + .2 + h2)
    >>> c.add_legends()
    >>> c.render()


Concatenation won't affect the heatmap styles.
However, the layout will be determined by the main heatmap to which others are concatenated.

.. plot::
    :context: close-figs

        >>> from marsilea.plotter import MarkerMesh
        >>> h1.add_dendrogram("left")
        >>> h2.add_dendrogram("right")
        >>> layer1 = MarkerMesh(data1 > 0.8, color='red', marker='o', label="> 0.8")
        >>> layer2 = MarkerMesh(data2 > 0.5, color='orange', label="> 0.5")
        >>> h1.add_layer(layer1, name='marker1')
        >>> h2.add_layer(layer2, name='marker2')
        >>> c = h1 + .2 + h2
        >>> c.add_legends(side="right", order=["h1", "marker1", "h2", "marker2"],
        ...               stack_by='row', stack_size=2, align_legends='center')
        >>> c.render()


    The concatenation result has legends added to the left side
    using the

        >>> from marsilea.plotter import MarkerMesh
        >>> h1.add_dendrogram("left")
        >>> h2.add_dendrogram("right")
        >>> layer1 = MarkerMesh(data1 > 0.8, color='red', marker='o', label="> 0.8")
        >>> layer2 = MarkerMesh(data2 > 0.5, color='orange', label="> 0.5")
        >>> h1.add_layer(layer1, name='marker1')
        >>> h2.add_layer(layer2, name='marker2')
        >>> c = h1 + .2 + h2
        >>> c.add_legends(side="right", order=["h1", "marker1", "h2", "marker2"],
        ...               stack_by='row', stack_size=2, align_legends='center')
        >>> c.render()


    The concatenation result has legends added to the left side
    using the

    >>> from marsilea.plotter import MarkerMesh
    >>> h1.add_dendrogram("left")
    >>> h2.add_dendrogram("right")
    >>> layer1 = MarkerMesh(data1 > 0.8, color='red', marker='o', label="> 0.8")
    >>> layer2 = MarkerMesh(data2 > 0.5, color='orange', label="> 0.5")
    >>> h1.add_layer(layer1, name='marker1')
    >>> h2.add_layer(layer2, name='marker2')
    >>> c = h1 + .2 + h2
    >>> c.add_legends(side="right", order=["h1", "marker1", "h2", "marker2"],
    ...               stack_by='row', stack_size=2, align_legends='center')
    >>> c.render()

Here, the concatenated result has legends added to the left side using
the :meth:`add_legend() <heatgraphy.base.LegendMaker.add_legends>` method.


The example also demonstrates how to arrange multiple legends.
Legends are stacked by row with a padding of 1, centered, and ordered by their names.
