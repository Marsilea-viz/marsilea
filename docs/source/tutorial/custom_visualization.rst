Let's make new visualization for heatgraphy
============================================

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

Let's create a `RenderPlan` that can draw Lollipop plot:

.. code-block:: python

    from heatgraphy import RenderPlan

    class Lollipop(RenderPlan):
        pass


The current `Lollipop` does nothing,
it does not know how to draw a lollipop,
we need to implement the `render` method.


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


Congratulation! you just creat your `RenderPlan`.


But what if I want to add it to other side.

.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(data)
    >>> h.add_left(Lollipop(lol_data))
    >>> h.render()

Oh no, it's broken! Let's try fix it by adopt it to more situation

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
    ...        ax.stem(locs, self.data, basefmt="none")
    ...        ax.set_axis_off()
    ...        if self.side == "left":
    ...           ax.invert_xaxis()
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

If your `RenderPlan` need to have legends, you need to implement the
:meth:`get_legends <heatgraphy.plotter.base.RenderPlan.get_legends>`.

.. note::

    We also develop another package called :mod:`legendkit` to help
    you handle legend easily. Consider using it.


.. plot::
    :context: close-figs

    >>> from legendkit import CatLegend

    >>> class Lollipop(RenderPlan):
    ...
    ...    def __init__(self, data):
    ...        self.data = data
    ...
    ...    def render(self, ax):
    ...        lim = len(self.data)
    ...        locs = np.arange(lim) + 0.5
    ...        orientation = "vertical" if self.is_body else "horizontal"
    ...        ax.stem(locs, self.data, basefmt="none")
    ...        ax.set_axis_off()
    ...        if self.side == "left":
    ...            ax.invert_xaxis()
    ...
    ...    def get_legends(self):
    ...        return CatLegend(colors=["b"], labels=["Lollipop"], handle="circle")
    ...

    >>> h = hg.Heatmap(data)
    >>> h.add_left(Lollipop(lol_data))
    >>> h.add_legends()
    >>> h.render()

Create Splittable `RenderPlan`
------------------------------

Here we are going to dive into more advance topic,
if you try to split heatmap, it didn't work.

When the render plan gets render, the `ax` parameter is not
guarantee to be single `Axes`, there will be multiple `Axes` when
it gets split.

The simply way to refactor our `Lollipop` is to implement a special
method `render_ax`.

.. plot::
    :context: close-figs

    >>> class Lollipop(RenderPlan):
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
    ...
    ...        ax.set_xlim(0, locs[-1]+.5)
    ...        ax.set_ylim(0, 12)


.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(data)
    >>> h.vsplit(cut=[5])
    >>> h.add_top(Lollipop(np.arange(10) + 2))
    >>> h.render()

Here, the `render_ax` define the behavior on how to render on each `Axes` with each chunk of `data`.
Heatgraphy will automatically handle the split and data for you. If you want to handle the splitting
process, you can overwrite the `get_render_data` method.

Noticed that the lim of the axis also gets adjusted, it's not applicable to all situation but
you get the idea.








