Stack Multiple Cross-layouts
============================

:class:`StackBoard <marsilea.base.StackBoard>` offers an alternative way to
place multiple cross-layouts. Unlike :class:`CompositeBoard <marsilea.base.CompositeBoard>`,
it can also stack itself.

.. warning::
    The :class:`StackBoard <marsilea.base.StackBoard>` is still considered experimental.
    There might be some issues with the rendering.

Let's create three different heatmaps for demonstration:

.. plot::
    :context: close-figs

    >>> import marsilea as ma
    >>> import marsilea.plotter as mp
    >>> import numpy as np
    >>> data1 = np.random.rand(10, 15)
    >>> data2 = np.random.rand(20, 10)
    >>> data3 = np.random.rand(15, 20)
    >>> h1 = ma.Heatmap(data1, cmap="Reds", height=1, width=1.5)
    >>> h1.add_top(mp.Colors(data1.sum(axis=0)), size=0.2, pad=0.1)
    >>> h2 = ma.Heatmap(data2, cmap="Greens", height=2, width=1)
    >>> h2.add_right(mp.Colors(data2.sum(axis=1)), size=0.3, pad=0.1)
    >>> h2.add_left(mp.Colors(data2.sum(axis=1)), size=0.3, pad=0.1)
    >>> h3 = ma.Heatmap(data3, cmap="Blues", height=1.5, width=2)
    >>> h3.add_bottom(mp.Colors(data3.sum(axis=0)), size=0.1, pad=0.1)

We can stack them in different ways, notice that the alignment is relative to the main canvas:

:code:`direction="horizontal"` and :code:`align="top"`:

.. plot::
    :context: close-figs

    >>> sb = ma.StackBoard([h1, h2, h3], direction="horizontal", align="top")
    >>> sb.render()


:code:`direction="horizontal"` and :code:`align="center"`:

.. plot::
    :context: close-figs

    >>> sb = ma.StackBoard([h1, h2, h3], direction="horizontal", align="center")
    >>> sb.render()


:code:`direction="horizontal"` and :code:`align="bottom"`:

.. plot::
    :context: close-figs

    >>> sb = ma.StackBoard([h1, h2, h3], direction="horizontal", align="bottom")
    >>> sb.render()


:code:`direction="vertical"` and :code:`align="left"`:

.. plot::
    :context: close-figs

    >>> sb = ma.StackBoard([h1, h2, h3], direction="vertical", align="left")
    >>> sb.render()


:code:`direction="vertical"` and :code:`align="center"`:

.. plot::
    :context: close-figs

    >>> sb = ma.StackBoard([h1, h2, h3], direction="vertical", align="center")
    >>> sb.render()


:code:`direction="vertical"` and :code:`align="right"`:

.. plot::
    :context: close-figs

    >>> sb = ma.StackBoard([h1, h2, h3], direction="vertical", align="right")
    >>> sb.render()


Grid of heatmaps?
-----------------

You can also stack multiple heatmaps in a grid layout. For example, let's stack

.. plot::
    :context: close-figs

    >>> data = np.random.rand(10, 10)
    >>> h1 = ma.Heatmap(data, cmap="Reds", height=1, width=1)
    >>> h2 = ma.Heatmap(data, cmap="Greens", height=1, width=1)
    >>> h3 = ma.Heatmap(data, cmap="Blues", height=1, width=1)
    >>> h4 = ma.Heatmap(data, cmap="Purples", height=1, width=1)
    >>> sb1 = ma.StackBoard([h1, h2], direction="horizontal", align="center")
    >>> sb2 = ma.StackBoard([h3, h4], direction="horizontal", align="center")
    >>> final_sb = ma.StackBoard([sb1, sb2], direction="vertical", align="center")
    >>> final_sb.render()