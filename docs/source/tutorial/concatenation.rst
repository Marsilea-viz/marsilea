Concatenate multiple heatmaps
=============================

You may want to visualize two or more heatmaps side by side. Although, this can be done simply
by merging images, heatgraphy provides a concatenation feature that can easily concatenate
multiple heatmaps together with ease.

Concatenate horizontally
------------------------

To horizontally concatenate heatmaps, we can simply use add operator **+**.

.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
    >>> h1_data = np.random.rand(10,12)
    >>> h2_data = np.random.rand(5,10)
    >>> h1 = hg.Heatmap(h1_data)
    >>> h2 = hg.Heatmap(h2_data)
    >>> (h1 + 1 + h2).render()

You can also add a number in between to add space between two heatmaps.

Concatenate vertically
----------------------

To vertically concatenate heatmaps, use divide operator **/**, which is quite vivid.

.. plot::
    :context: close-figs

    >>> h1_data = np.random.rand(10,12)
    >>> h2_data = np.random.rand(5,10)
    >>> h1 = hg.Heatmap(h1_data)
    >>> h2 = hg.Heatmap(h2_data)
    >>> (h1 / 1 / h2).render()


Customize each heatmap
----------------------

You can customize each heatmap separately. The concatenation process will have no influence
on the styles. But notice that the layout is subjected to the main heatmap that other
heatmaps concatenated to. Below shows the width of heatmap `h2` will subject to the width of `h1`.

.. plot::
    :context: close-figs

    >>> h1_data = np.random.rand(10, 12)
    >>> h2_data = np.random.rand(5, 10)
    >>> h1 = hg.Heatmap(h1_data, width=10)
    >>> h2 = hg.Heatmap(h2_data, width=5)
    >>> h1.add_dendrogram("left")
    >>> h2.add_dendrogram("right")
    >>> h1.add_layer(hg.plotter.MarkerMesh(h1_data > 0.8, label="Larger than 0.8"))
    >>> h2.add_layer(hg.plotter.MarkerMesh(h2_data > 0.5, label="Larger than 0.5"))
    >>> (h1 + 1 + h2).render()


Legends
-------

It is important to note the legends should be added after all concatenations.

.. plot::
    :context: close-figs

    >>> from heatgraphy.plotter import MarkerMesh
    >>> data1 = np.random.rand(10, 12)
    >>> data2 = np.random.rand(5, 10)
    >>> h1 = hg.Heatmap(data1, name="h1")
    >>> h2 = hg.Heatmap(data2, name="h2")
    >>> h1.add_dendrogram("left")
    >>> h2.add_dendrogram("right")
    >>> layer1 = MarkerMesh(h1_data > 0.8, color='darkgreen', label="Larger than 0.8", marker='o')
    >>> layer2 = MarkerMesh(h2_data > 0.5, label="Larger than 0.5")
    >>> h1.add_layer(layer1, name='marker1')
    >>> h2.add_layer(layer2, name='marker2')
    >>> hc = h1 + 1 + h2
    >>> hc.add_legends(side="left", order=["h1", "marker1", "h2", "marker2"],
    ...                 pad=1, stack_by='row', stack_size=2, align_legends='center')
    >>> hc.render()


The concatenation result has legends added to the left side
using the :meth:`add_legend() <heatgraphy.base.LegendMaker.add_legends>` method.

Here we also shows how to layout multiple legends.
The legends are stacked by row and have a padding of 1, and they are aligned to the center.
The order of the legends are specified by their name.
