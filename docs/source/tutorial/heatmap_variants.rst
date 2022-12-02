Create different types of heatmap
=================================


Sized Heatmap
-------------

Besides colors, Sized heatmap enables you to encode another layer of information into the size of elements.

.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
    >>> size, color = np.random.randn(11, 12), np.random.randn(11, 12)
    >>> sh = hg.SizedHeatmap(size=size, color=color)
    >>> sh.render()

You may also add an extra layer to the sized heatmap.

.. plot::
    :context: close-figs

    >>> from heatgraphy.plotter import ColorMesh
    >>> sh = hg.SizedHeatmap(size=size, color=color)
    >>> data = np.random.randn(11, 12)
    >>> sh.add_layer(ColorMesh(data, cmap="BrBG"), zorder=-1)
    >>> sh.render()

A real world example is `Hinton diagram <https://matplotlib.org/stable/gallery/specialty_plots/hinton_demo.html>`_.
If your color is categorical, we can easily assign colors to each category.


.. plot::
    :context: close-figs

    >>> matrix = np.random.randint(-10, 10, (10, 10))
    >>> size = np.random.randint(-10, 10, (10, 10))
    >>> color = matrix > 0
    >>> sh = hg.SizedHeatmap(size=size, color=color, marker="s",
    ...                      palette={True: "#E87A90", False: "#BEC23F"})
    >>> sh.add_legends()
    >>> sh.render()

Other heatmap variants have no different than the :class:`Heatmap`, you can easily add other plots to it.

Since we have multiple layers here, you can explicitly ask the cluster to perform on size data.

.. plot::
    :context: close-figs

    >>> from heatgraphy.plotter import Violin
    >>> sh = hg.SizedHeatmap(size=size, color=color, marker="s", cluster_data=size,
    ...                      palette={True: "#E87A90", False: "#BEC23F"})
    >>> sh.split_row(cut=[5])
    >>> sh.add_dendrogram("left")
    >>> sh.add_top(Violin(np.random.randint(10, 100, (10, 10)), color="pink", inner="stick"), pad=.1)
    >>> sh.add_legends()
    >>> sh.render()

Categorical Heatmap
-------------------

Another useful type of heatmap variants is categorical heatmap that used to
visualize categorical data.

.. plot::
    :context: close-figs

    >>> cats = np.random.choice([0, 1, 2, 3], (11, 12))
    >>> ch = hg.CatHeatmap(cats)
    >>> ch.add_legends()
    >>> ch.render()

Layers Heatmap
--------------

A more powerful version of categorical heatmap that allows you to defined your own elements.

Heatgraphy provides you with predefined elements,

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
    >>> la.split_row(cut=[2], spacing=0.05)
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
    ...     def draw(self, x, y, w, h):
    ...         return Circle((x + 0.5, y + 0.5), radius=min(w, h)/2, lw=1, facecolor=self.color)
    >>> preview(MyCircle())