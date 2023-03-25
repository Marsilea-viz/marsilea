Create different types of heatmap
=================================


Sized Heatmap
-------------

Add an extra dimension to your heatmaps with the Sized Heatmap feature!
Encode additional data layers into the size of heatmap elements for more informative visualizations.

.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
    >>> size, color = np.random.randn(11, 12), np.random.randn(11, 12)
    >>> sh = hg.SizedHeatmap(size=size, color=color)
    >>> sh.render()

Boost your Sized Heatmap by incorporating an extra layer.

.. plot::
    :context: close-figs

    >>> from heatgraphy.plotter import ColorMesh
    >>> sh = hg.SizedHeatmap(size=size, color=color)
    >>> data = np.random.randn(11, 12)
    >>> sh.add_layer(ColorMesh(data, cmap="BrBG"), zorder=-1)
    >>> sh.render()


A real world example is `Hinton diagram <https://matplotlib.org/stable/gallery/specialty_plots/hinton_demo.html>`_.
If your colors are categorical, you can easily assign colors to each category.


.. plot::
    :context: close-figs

    >>> matrix = np.random.randint(-10, 10, (10, 10))
    >>> size = np.random.randint(-10, 10, (10, 10))
    >>> color = matrix > 0
    >>> sh = hg.SizedHeatmap(size=size, color=color, marker="s",
    ...                      palette={True: "#E87A90", False: "#BEC23F"})
    >>> sh.add_legends()
    >>> sh.render()


Adding other plots to sized heatmap variants is as straightforward as it is with the basic :class:`Heatmap` class.
Since multiple layers are present, you can explicitly request clustering to be performed on size data.


.. plot::
    :context: close-figs

    >>> from heatgraphy.plotter import Violin
    >>> sh = hg.SizedHeatmap(size=size, color=color, marker="s", cluster_data=size,
    ...                      palette={True: "#E87A90", False: "#BEC23F"})
    >>> sh.hsplit(cut=[5])
    >>> sh.add_dendrogram("left")
    >>> sh.add_top(Violin(np.random.randint(10, 100, (10, 10)), color="pink", inner="stick"), pad=.1)
    >>> sh.add_legends()
    >>> sh.render()

Categorical Heatmap
-------------------

Visualize categorical data with the Categorical Heatmap, a versatile type of heatmap variant.

.. plot::
    :context: close-figs

    >>> cats = np.random.choice([0, 1, 2, 3], (11, 12))
    >>> ch = hg.CatHeatmap(cats)
    >>> ch.add_legends()
    >>> ch.render()

Layers Heatmap
--------------

Explore the Layers Heatmap, an even more powerful version of the categorical heatmap that enables you to define your own elements.
Heatgraphy provides predefined elements for your convenience.

.. plot::
    :context: close-figs

    >>> from heatgraphy.layers import Layers, Rect, FrameRect, FracRect
    >>> mapper = {0: Rect(color="red"), 1: Rect(color="purple"),
    ...           2: FrameRect(color="yellow"), 3: FracRect(color="blue"),
    ...           4: Rect(color="orange"), 5: FracRect(color="cyan")}
    >>> data = np.random.choice([0, 1, 2, 3, 4, 5], (10, 10))
    >>> l = Layers(data=data, pieces=mapper)
    >>> l.render()

Here we only render one layer of data, the layers heatmap allows you to render multiple layers of
custom elements.

.. plot::
    :context: close-figs

    >>> d0 = np.random.choice([0, 1], (5, 10))
    >>> d1 = np.random.choice([0, 1], (5, 10))
    >>> d2 = np.random.choice([0, 1], (5, 10))
    >>> d3 = np.random.choice([0, 1], (5, 10))
    >>> d4 = np.random.choice([0, 1], (5, 10))
    >>> layers = [d0, d1, d2, d3, d4]
    >>> pieces = [Rect(color="red", label="red rect"),
    ...           Rect(color="purple", label="purple rect"),
    ...           Rect(color="orange", label="orange rect"),
    ...           FrameRect(color="green", label="green rect"),
    ...           FracRect(color="blue", label="blue rect")]
    >>> la = hg.layers.Layers(layers=layers, pieces=pieces, cluster_data=d0)
    >>> la.hsplit(cut=[2], spacing=0.05)
    >>> la.add_dendrogram("left")
    >>> la.add_legends()
    >>> la.render()

You can easily define a custom element to render, here we shows how to render a circle.

.. plot::
    :context: close-figs

    >>> from heatgraphy.layers import Piece, preview
    >>> from matplotlib.patches import Circle
    >>> class MyCircle(Piece):
    ...     def __init__(self, color="C0", label=None):
    ...         self.color = color
    ...         self.label = label
    ...
    ...     def draw(self, x, y, w, h, ax):
    ...         return Circle((x + 0.5, y + 0.5), radius=min(w, h)/2, lw=1, facecolor=self.color)
    >>> preview(MyCircle())