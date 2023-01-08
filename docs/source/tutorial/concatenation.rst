Concatenate multiple heatmaps
=============================

You may want to visualize two or more heatmaps side by side. Although, this can be done simply
by merging images, heatgraphy provides a concatenation feature that can easily concatenate
multiple heatmaps together with ease.

Here we have one blue heatmap and a green heatmap.

.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
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


To horizontally concatenate heatmaps, use add operator **+**.

.. plot::
    :context: close-figs

    >>> (h1 + h2).render()

But this is not cool, the two heatmap stick together too closely. Don't worry,
we can add space between two heatmaps by adding a number.

.. plot::
    :context: close-figs

    >>> (h1 + .2 + h2).render()

To vertically concatenate heatmaps, use divide operator **/**

.. plot::
    :context: close-figs

    >>> (h1 / .2 / h2).render()

Notice that the width of :code:`h1` is 5 and the width of :code:`h2` is 3. The heatmap :code:`h2` concatenated
to the main heatmap :code:`h1` will be subject to the layout of main heatmap. So the width of :code:`h2`
becomes 5 which is the same as :code:`h1` after concatenation.

Legends
-------

It is important to remember that legends should be added after concatenations.
So that heatgraphy can layout legends from all your heatmaps.


.. plot::
    :context: close-figs

    >>> c = (h1 + .2 + h2)
    >>> c.add_legends()
    >>> c.render()


The concatenation process will have no influence on the styles.
But notice that the layout is subjected to the main heatmap that other
heatmaps concatenated to.

.. plot::
    :context: close-figs

    >>> from heatgraphy.plotter import MarkerMesh
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
using the :meth:`add_legend() <heatgraphy.base.LegendMaker.add_legends>` method.

Here we also shows how to layout multiple legends.
The legends are stacked by row and have a padding of 1, and they are aligned to the center.
The order of the legends are specified by their name.
