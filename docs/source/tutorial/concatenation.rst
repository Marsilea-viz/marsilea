Concatenation
=============

In some cases, we may want to concatenate multiple heatmaps.
Heatgraphy also provide flexible concatenation function.

|
Concatenate horizontally
------------------------
For example, if we want to horizontally concatenate two heatmaps, we can simply use **+**.

.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
    >>> import numpy as np
    >>> h1_data = np.random.rand(10,12)
    >>> h2_data = np.random.rand(5,10)
    >>> h1 = hg.Heatmap(h1_data)
    >>> h2 = hg.Heatmap(h2_data)
    >>> (h1 + 1 + h2).render()

As you can see, the two heatmaps are combined horizontally. The number in the middle indicates the space between two heatmaps.

|
Concatenate vertically
----------------------

If we want to vertically concatenate two heatmap, we can use **/**, which is quite vivid.

.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
    >>> import numpy as np
    >>> h1_data = np.random.rand(10,12)
    >>> h2_data = np.random.rand(5,10)
    >>> h1 = hg.Heatmap(h1_data)
    >>> h2 = hg.Heatmap(h2_data)
    >>> (h1 / 1 / h2).render()

|
Customize each heatmap
----------------------

And we can still customize each heatmap without any influence from concatenation. Here we add dendrogram and
marker to each heatmap respectively.

.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
    >>> import numpy as np
    >>> h1_data = np.random.rand(10,12)
    >>> h2_data = np.random.rand(5,10)
    >>> h1 = hg.Heatmap(h1_data)
    >>> h2 = hg.Heatmap(h2_data)
    >>> h1.add_dendrogram("left")
    >>> h2.add_dendrogram("right")
    >>> h1.add_layer(hg.plotter.MarkerMesh(h1_data > 0.8, label="Larger than 0.8"))
    >>> h2.add_layer(hg.plotter.MarkerMesh(h2_data > 0.5, label="Larger than 0.5"))
    >>> (h1 + 1 + h2).render()

|

It is important to note that if we want to add legends to a concatenation of multiple heatmaps, we should add after they
are concatenated. Additionally, to adjust the layout of legends, each thing we add require a name to be put into a list.
Then the list will be used in :meth:`add_legend() <heatgraphy.base.LegendMaker.add_legends>` to determine the order of legends.

.. plot::
    :context: close-figs

    >>> h1_data = np.random.rand(10,12)
    >>> h2_data = np.random.rand(5,10)
    >>> h1 = hg.Heatmap(h1_data,name="h1")
    >>> h2 = hg.Heatmap(h2_data,name="h2")
    >>> h1.add_dendrogram("left")
    >>> h2.add_dendrogram("right")
    >>> h1.add_layer(hg.plotter.MarkerMesh(h1_data > 0.8, color='darkgreen',label="Larger than 0.8", marker = 'o'), name='marker1')
    >>> h2.add_layer(hg.plotter.MarkerMesh(h2_data > 0.5, label="Larger than 0.5"),name = 'marker2')
    >>> hc = h1 + 1 + h2
    >>> hc.add_legends(side= "left",order=["h1","marker1","h2","marker2"],pad=1,stack_by='row',stack_size=2,align_legends='center')
    >>> hc.render()


The resulting composite heatmap, hc, has legends added to the left side using the :meth:`add_legend() <heatgraphy.base.LegendMaker.add_legends>` method.
The legends are stacked by row and have a padding of 1, and they are aligned to the center. The order of the legends is
specified as "h1", "marker1", "h2", "marker2".
