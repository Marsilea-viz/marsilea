Let's make new visualization for heatgraphy
============================================

..

Previously, this is how you add plots in Heatgraphy

.. code-block:: python

    import numpy as np
    import heatgraphy as hg

    h = hg.Heatmap(np.random.rand(10, 10))
    h.add_left(hg.plotter.Colors(list("1122233344")))
    h.render()

However, the preset included in Heatgraphy may not fit your need.
What if I want a Lollipop plot? It's not in Heatgraphy.

We will show you how to make a new visualization to express your data more dynamically.
You need to be familiar with Python's Class inheritance to understand how it works.

Understand :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>`
-------------------------------------------------------------------

Everything render on the canvas in Heatgraphy is a :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>`,
or inherited from it. To create a new visualization, we also need to inherit from this base class.

Let's create a :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>` that can draw Lollipop plot:

.. code-block:: python

    from heatgraphy import RenderPlan

    class Lollipop(RenderPlan):
        pass


The current `Lollipop` does nothing,
it does not know how to draw a lollipop,
we need to implement the `render` method.
The `render` method takes one argument, which is the `Axes`
where we do all the drawing.


.. code-block:: python

    class Lollipop(RenderPlan):

        def __init__(self, data):
            self.data = data

        def render(self, ax):
            lim = len(self.data)
            locs = np.arange(lim) + 0.5
            ax.stem(locs, self.data, basefmt="none")
            ax.set_axis_off()

Now lets create a heatmap and add it to the top

.. plot::
    :context: close-figs
    :include-source: false

    >>> from heatgraphy.base import RenderPlan

    >>> class Lollipop(RenderPlan):
    ...
    ...     def __init__(self, data):
    ...         self.data = data
    ...
    ...     def render(self, ax):
    ...         lim = len(self.data)
    ...         locs = np.arange(lim) + 0.5
    ...         ax.stem(locs, self.data, basefmt="none")
    ...         ax.set_axis_off()
    ...


.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
    >>> data = np.random.rand(10, 10)
    >>> lol_data = np.arange(10) + 2
    >>> h = hg.Heatmap(data)
    >>> h.add_top(Lollipop(lol_data))
    >>> h.render()


Congratulation! you just creat your :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>`.


But what if I want to add it to other side.

.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(data)
    >>> h.add_left(Lollipop(lol_data))
    >>> h.render()

Oh no, it's broken! Let's try to fix it.

.. code-block:: python

    class Lollipop(RenderPlan):

        def __init__(self, data):
            self.data = data

        def render(self, ax):
            lim = len(self.data)
            locs = np.arange(lim) + 0.5
            orientation = "vertical" if self.is_body else "horizontal"
            ax.stem(locs, self.data, basefmt="none")
            ax.set_axis_off()
            if self.side == "left":
                ax.invert_xaxis()
            if self.is_flank:
                ax.invert_yaxis()

Here we use the `is_body` attribute to query the side,
here is a list of attributes that you can use to know
which side that the :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>` is drawn.

- :attr:`.side <heatgraphy.plotter.base.RenderPlan.side>`: Directly known the side
- :attr:`.is_body <heatgraphy.plotter.base.RenderPlan.is_body>`: Top, Bottom or Main
- :attr:`.is_flank <heatgraphy.plotter.base.RenderPlan.is_flank>`: Left or Right

.. plot::
    :context: close-figs
    :include-source: false

    >>> class Lollipop(RenderPlan):
    ...
    ...    def __init__(self, data):
    ...        self.data = data
    ...
    ...    def render(self, ax):
    ...        lim = len(self.data)
    ...        locs = np.arange(lim) + 0.5
    ...        orientation = "vertical" if self.is_body else "horizontal"
    ...        ax.stem(locs, self.data, basefmt="none", orientation=orientation)
    ...        ax.set_axis_off()
    ...        if self.side == "left":
    ...           ax.invert_xaxis()
    ...        if self.is_flank:
    ...             ax.invert_yaxis()
    ...

We make the orientation changed when the `Lollipop` is rendered on different
side of heatmap.

Now we try add it to the left again.

.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(data)
    >>> h.add_left(Lollipop(lol_data))
    >>> h.render()


Make a legend
-------------

If your :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>` need to have legends,
you need to implement the
:meth:`get_legends <heatgraphy.plotter.base.RenderPlan.get_legends>`.

.. note::

.. code-block:: python
    :emphasize-lines: 21, 22, 23, 24, 25

    >>> class Lollipop(RenderPlan):
    >>>     def __init__(self, data):
    >>>         self.data = data
    >>>
    >>>     def get_legends(self):
    >>>         return CatLegend(label=['Lollipop'], handle="circle")
    >>>
    >>>     def render_ax(self, ax, data):
    >>>         orient = "horizontal" if self.is_flank else "vertical"
    >>>         lim = len(data)
    >>>         if self.is_flank:
    >>>             ax.set_ylim(0, lim)
    >>>             ax.set_xlim(0, None)
    >>>         else:
    >>>             ax.set_xlim(0, lim)
    >>>             ax.set_ylim(0, None)
    >>>         if self.side == "left":
    >>>             ax.invert_xaxis()
    >>>         for spine in ax.spines.values():
    >>>             spine.set_visible(False)
    >>>          # Plot on every .5 start from 0
    >>>         locs = np.arange(0, lim) + 0.5
    >>>         ax.set_yticks([])
    >>>         ax.set_xticks([])
    >>>         ax.stem(locs, data, orientation=orient, basefmt=" ")
=======
    We also develop another package called `legendkit <https://legendkit.readthedocs.io/en/latest/>`_ to help
    you handle legend easily. Consider using it.



.. plot::
    :context: close-figs
    :include-source: false

    >>> from legendkit import CatLegend
    >>>
    >>> class Lollipop(RenderPlan):
    ...
    ...    def __init__(self, data):
    ...        self.data = data
    ...
    ...    def render(self, ax):
    ...        lim = len(self.data)
    ...        locs = np.arange(lim) + 0.5
    ...        orientation = "vertical" if self.is_body else "horizontal"
    ...        ax.stem(locs, self.data, basefmt="none", orientation=orientation)
    ...        ax.set_axis_off()
    ...        if self.side == "left":
    ...            ax.invert_xaxis()
    ...        if self.is_flank:
    ...             ax.invert_yaxis()
    ...
    ...    def get_legends(self):
    ...        return CatLegend(colors=["b"], labels=["Lollipop"], handle="circle")
    ...

    >>> h = hg.Heatmap(data)
    >>> h.add_left(Lollipop(lol_data))
    >>> h.add_legends()
    >>> h.render()


The Heatgraphy will automatically handle all the legends for you.


Create Splittable `RenderPlan`
------------------------------

Here we are going to dive into more advance topic,
if you try to split heatmap with the Lollipop, it didn't work.

.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(data)
    >>> h.vsplit(cut=[5])
    >>> h.add_left(Lollipop(lol_data))
    >>> h.render()

When the render plan gets render, the `ax` parameter is not
guarantee to be single :class:`Axes <matplotlib.axes.Axes>`, there will be multiple
:class:`Axes <matplotlib.axes.Axes>` when it gets split.

The simply way to refactor our `Lollipop` is to implement a method
:meth:`render_ax <heatgraphy.plotter.base.RenderPlan.render_ax>`.
It takes two paramters, an axes to be drawn and the data that are already split.

.. plot::
    :context: close-figs

    >>> from heatgraphy.plotter.base import StatsBase
    >>>
    >>> class Lollipop(StatsBase):
    ...
    ...    def __init__(self, data):
    ...        self.data = data
    ...
    ...    def render_ax(self, ax, data):
    ...        lim = len(data)
    ...        locs = np.arange(lim) + 0.5
    ...        orientation = "vertical" if self.is_body else "horizontal"
    ...        ax.stem(locs, data, basefmt="none")
    ...        ax.set_axis_off()
    ...        if self.side == "left":
    ...            ax.invert_xaxis()
    ...        if self.is_flank:
    ...             ax.invert_yaxis()
    ...        ax.set_xlim(0, locs[-1]+.5)
    ...

    >>> h = hg.Heatmap(data)
    >>> h.vsplit(cut=[5])
    >>> h.add_top(Lollipop(np.arange(10) + 2))
    >>> h.render()

What's happening under the hood is clearly illustrated in the flowchart below.

Here, the :meth:`render_ax <heatgraphy.plotter.base.RenderPlan.render_ax>`
define the behavior on how to render on each `Axes` with each chunk of `data`.
Heatgraphy will automatically handle the split and data for you. If you want to handle the splitting
process, you can overwrite the :meth:`get_render_data <heatgraphy.plotter.base.RenderPlan.get_render_data>`
method.

.. image:: ../img/heatgraphy-renderplan-logic.drawio.svg

Great, hope you get the idea on how to implement your visualization.








