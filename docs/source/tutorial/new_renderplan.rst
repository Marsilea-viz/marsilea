Create New RenderPlan
=====================

The built-in plotting options in Marsilea
may not be perfect for your presentation.
This section will show you how to create your own visualization.
It's expected that you are familiar with Python's class inheritance.


Every plot renders on the canvas in Marsilea is derived from
:class:`RenderPlan <marsilea.plotter.base.RenderPlan>`.
To create a new visualization, we also need to inherit from
:class:`RenderPlan <marsilea.plotter.base.RenderPlan>`.

Simple Lollipop plot
--------------------

Let's create a Lollipop plot as example:

.. plot::
    :context: close-figs

        >>> import marsilea as ma
        >>> from marsilea.base import RenderPlan

        >>> class Lollipop(RenderPlan):
        ...     pass


The current :code:`Lollipop` does nothing,
it does not know how to draw a lollipop.

.. plot::
    :context: close-figs

        >>> data = np.random.rand(20, 20)
        >>> h = ma.Heatmap(data)
        >>> h.add_top(Lollipop())
        >>> h.render()


We need to implement the :meth:`render_ax() <marsilea.plotter.base.RenderPlan.render_ax>` method,
which takes one argument: the :class:`spec <marsilea.plotter.base.RenderSpec>`. The :code:`spec` contains
necessary information to draw the plot. It handles data and axes for you.

.. plot::
    :context: close-figs

        >>> class Lollipop(RenderPlan):
        ...
        ...     def __init__(self, data):
        ...         self.set_data(data)
        ...
        ...     def render_ax(self, spec):
        ...         ax = spec.ax
        ...         data = spec.data
        ...         lim = len(data)
        ...         locs = np.arange(lim) + 0.5
        ...         ax.stem(locs, data, basefmt="none")
        ...         ax.set_axis_off()
        ...         ax.set_xlim(0, lim)
        ...

        >>> lp_data = np.arange(20) + 1
        >>> h = ma.Heatmap(data)
        >>> h.add_top(Lollipop(lp_data))
        >>> h.render()


Drawing logics for different sides
----------------------------------

If you try add our lollipop to the left, it will not rotate accordingly.

.. plot::
    :context: close-figs

    >>> h = ma.Heatmap(data)
    >>> h.add_left(Lollipop(lp_data))
    >>> h.render()

We need to implement the drawing logic for different sides. Here we use
a pre-config :code:`RenderPlan` that are designed for stats plot: :class:`StatsBase`.

.. plot::
    :context: close-figs

    >>> from marsilea.plotter.base import StatsBase
    >>> class Lollipop(StatsBase):
    ...
    ...    def __init__(self, data):
    ...        self.set_data(data)
    ...
    ...    def render_ax(self, spec):
    ...        ax = spec.ax
    ...        data = spec.data
    ...        lim = len(data)
    ...        locs = np.arange(lim) + .5
    ...        orientation = "vertical" if self.is_body else "horizontal"
    ...        ax.stem(locs, data, basefmt="none", orientation=orientation)
    ...        ax.set_axis_off()
    ...        if self.is_body:
    ...            ax.set_xlim(0, lim)
    ...        if self.side == "left":
    ...           ax.invert_xaxis()
    ...        if self.is_flank:
    ...             ax.set_ylim(lim, 0)
    ...

We use the `is_body` attribute to query the side where our Lollipop is drawn.

Below is list of attributes that you can use to know
which side that the :class:`RenderPlan <marsilea.plotter.base.RenderPlan>` is drawn.

- :attr:`.side <marsilea.plotter.base.RenderPlan.side>`: Get the current side of the RenderPlan
- :attr:`.is_body <marsilea.plotter.base.RenderPlan.is_body>`: Top, Bottom or Main
- :attr:`.is_flank <marsilea.plotter.base.RenderPlan.is_flank>`: Left or Right

We make the orientation changed when the :code:`Lollipop` is rendered on different
side of heatmap.

Now we try add it to the left again.

.. plot::
    :context: close-figs

    >>> h = ma.Heatmap(data)
    >>> h.add_left(Lollipop(lp_data))
    >>> h.hsplit(cut=[5, 10])
    >>> h.render()


Make a legend
-------------

If your :class:`RenderPlan <marsilea.plotter.base.RenderPlan>` need to have legends,
you need to implement the
:meth:`get_legends() <marsilea.plotter.base.RenderPlan.get_legends>`.

We also develop `legendkit <https://legendkit.readthedocs.io/en/latest/>`_ to help
you create legend easily, it is used to handle legends in Marsilea.

.. plot::
    :context: close-figs

    >>> from legendkit import CatLegend
    >>>
    >>> class Lollipop(Lollipop):
    ...
    ...    def get_legends(self):
    ...        return CatLegend(colors=["b"], labels=["Lollipop"], handle="circle")

Now we can add the legends and let Marsilea automatically handle all the legends for you.

.. plot::
    :context: close-figs

    >>> h = ma.Heatmap(data)
    >>> h.add_left(Lollipop(lp_data))
    >>> h.add_legends()
    >>> h.render()

