Introduction: Basic Concepts
==============================

.. py:currentmodule:: marsilea

Marsilea is a powerful Python package that allows you to effortlessly
create visually appealing X-layout visualization. X-layout visualization is
designed specifically for multi-feature dataset.

This tutorial will guide you through the basic operation
for creating a x-layout visualization.


Prerequisites
-------------

This tutorial assumes that you have basic knowledge of Python,
and you know how to use NumPy and Matplotlib.

If you are not familiar with these packages, you can check out the following links:

- `NumPy <https://numpy.org/>`_
- `Matplotlib <https://matplotlib.org/>`_

It's recommended that you should be familiar with
the concept of :class:`Figure <matplotlib.figure.Figure>` and
:class:`Axes <matplotlib.axes.Axes>` in Matplotlib.

Create main visualization
-------------------------

.. plot::
    :context: close-figs

    >>> import marsilea as ma
    >>> import marsilea.plotter as mp

    The shorthand convention for Marsilea is :code:`ma` and for plotter is :code:`mp`.

    >>> data = np.random.randn(10, 6)
    >>> cb = ma.ClusterBoard(data, height=2, margin=.5)
    >>> cb.add_layer(mp.Violin(data, color="#FF6D60"))
    >>> cb.render()

Firstly, we create a :class:`ClusterBoard <marsilea.base.ClusterBoard>` to
draw the main visualization.
It's an empty canvas that allows you to append plots to it.
The canvas is initialized with height of 2 and margin of .5.
The margin can be used to reserve white space around the canvas to avoid
clipping of visualization when you save the plot.
In Marsilea, if not specified, the unit is **inches**.

Afterwards, we use :meth:`add_layer() <marsilea.base.WhiteBoard.add_layer>`
to add a :class:`Violin <marsilea.plotter.Violin>` plot to the canvas.

Finally, the :meth:`render() <marsilea.base.WhiteBoard.render>`
is called to draw our visualization.


Grouping
--------

.. plot::
    :context: close-figs

    >>> cb.vsplit(labels=["c1", "c1", "c2", "c2", "c3", "c3"],
    ...           order=["c1", "c2", "c3"], spacing=.08)
    >>> cb.render()

We use :meth:`vsplit() <marsilea.base.ClusterBoard.vsplit>` to split the canvas into three groups.
The :code:`labels` parameter specifies the gr oup for each column.
The :code:`order` parameter specifies the order of the groups that will present in the plot.
Let's add side plots to the groups to make it more visually distinct.
Here the spacing is the fraction of the width of the canvas.

Annotate with Additional components
-----------------------------------

.. plot::
    :context: close-figs

    >>> group_labels = mp.Chunk(["c1", "c2", "c3"],
    ...                         ["#FF6D60", "#F7D060", "#F3E99F"])
    >>> cb.add_top(group_labels, size=.2, pad=.1)
    >>> cb.render()

We use :meth:`add_top() <marsilea.base.WhiteBoard.add_top>` to
add a :class:`Chunk <marsilea.plotter.Chunk>` plot to the top of the canvas.
The :class:`Chunk <marsilea.plotter.Chunk>` plot is an annotation plot that use to annotate the groups.

You can use :code:`size` and :code:`pad` parameters to adjust the size
and the space between the plots. The unit is **inches**.

.. note::

    For plot like :class:`Chunk <marsilea.plotter.Chunk>` which draws text,
    the size of the plot will be automatically adjusted to fit the text,
    so you don't need to specify the size of the plot.


Hierarchical Clustering
-----------------------

.. plot::
    :context: close-figs

    >>> cb.add_dendrogram("bottom", colors="g")
    >>> cb.render()

We use :meth:`add_dendrogram() <marsilea.base.WhiteBoard.add_dendrogram>` to
add a dendrogram to the bottom of the canvas.
The dendrogram is a tree-like diagram that records the hierarchical clustering process.
In Marsilea, the clustering can be performed on different visualizations not limited to
heatmap.

Here, you may notice that the order of the order of groups and
the order within groups are automatically changed according
to the clustering result.


Add bottom plot and title
-------------------------

.. plot::
    :context: close-figs

    >>> cb.add_bottom(ma.plotter.Bar(data, color="#577D86"), size=2, pad=.1)
    >>> cb.add_title(top="My First Marsilea Example")
    >>> cb.render()


We can add more plots to the main visualization.
Here we add a :class:`Bar <marsilea.plotter.Bar>` plot to the bottom and
a title to the top using :meth:`add_title() <marsilea.base.WhiteBoard.add_title>`.


Save your visualization
-----------------------

You can save it to a file using :meth:`save() <marsilea.base.WhiteBoard.save>`.

.. code-block:: python

    >>> cb.save("my_first_marsilea_example.png")

Or you can save it like how you save all your matplotlib figure.
You can access figure object with :attr:`.figure <marsilea.base.WhiteBoard.figure>`.
It's recommended that you save it in the :code:`bbox_inches="tight"` mode to avoid
clipping. Alternatively, you can increase the margin of the canvas.

.. code-block:: python

    >>> cb.figure.savefig("my_first_marsilea_example.png", bbox_inches="tight")

Summary
-------

To summarize, here is a list of methods you can use to control your visualization.
Some of them will be introduced later.

Add to the main layer: :meth:`add_layer() <marsilea.base.WhiteBoard.add_layer>`

Add to the side:

- Left side: :meth:`add_left() <marsilea.base.WhiteBoard.add_left>`
- Right side: :meth:`add_right() <marsilea.base.WhiteBoard.add_right>`
- Top side: :meth:`add_top() <marsilea.base.WhiteBoard.add_top>`
- Bottom side: :meth:`add_bottom() <marsilea.base.WhiteBoard.add_bottom>`

Grouping:

- Group vertically: :meth:`hsplit() <marsilea.base.ClusterBoard.hsplit>`
- Group horizontally: :meth:`vsplit() <marsilea.base.ClusterBoard.vsplit>`

Add dendrogram: :meth:`add_dendrogram() <marsilea.base.ClusterBoard.add_dendrogram>`

Add title: :meth:`add_title() <marsilea.base.WhiteBoard.add_title>`

Add legend: :meth:`add_legends() <marsilea.base.LegendMaker.add_legends>`

Save the plot: :meth:`save() <marsilea.base.WhiteBoard.save>`
