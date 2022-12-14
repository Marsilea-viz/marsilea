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

And we can still customize each heatmap without any influence from concatenation.

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


