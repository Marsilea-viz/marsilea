Create custom visualization for heatgraphy
==========================================

Unleash the power of your heatmaps by adding custom visualizations.
Whether you want to make your data more dynamic or add context, this document will show you how.
By the end, you'll be able to create eye-catching heatmaps with personalized visualizations.
From adding simple annotations to combining multiple visualizations, the possibilities are endless.

For instance, let's add a Lollipop plot to our heatmap.

Import modules
--------------

.. plot::
    :context: close-figs

    >>> import heatgraphy as hg
    >>> import numpy as np
    >>> from heatgraphy.base import RenderPlan

| Here, we import the necessary modules for our visualization.
| The :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>` class from heatgraphy.base will serve as the base class for our custom visualization class

Define class
------------

Next, let's look at the definition of the Lollipop class:

.. code-block:: python

    >>> class Lollipop(RenderPlan):
    >>>     def __init__(self, data):
    >>>         self.data = data

This section defines the class :class:`Lollipop` that inherits from RenderPlan, and sets up an :meth:`__init__()` method that initializes the data parameter.



.. code-block:: python
    :emphasize-lines: 5, 6

    >>> class Lollipop(RenderPlan):
    >>>     def __init__(self, data):
    >>>         self.data = data
    >>>
    >>>     def get_legends(self):
    >>>         return CatLegend(label=['Lollipop'], handle="circle")

To arrange the layout of legends, :meth:`get_legends()` method is defined, which returns a CatLegend object with a label of :code:`Lollipop` and a handle of :code:`circle`.


.. code-block:: python
    :emphasize-lines: 8, 9, 10, 11, 12, 13, 14, 15, 16

    >>> class Lollipop(RenderPlan):
    >>>     def __init__(self, data):
    >>>         self.data = data
    >>>
    >>>     def get_legends(self):
    >>>         return CatLegend(label=['Lollipop'], handle="circle")
    >>>
    >>>     def render_ax(self, ax, data):
    >>>     orient = "horizontal" if self.is_flank else "vertical"
    >>>     lim = len(data)
    >>>     if self.is_flank:
    >>>         ax.set_ylim(0, lim)
    >>>         ax.set_xlim(0, None)
    >>>     else:
    >>>         ax.set_xlim(0, lim)
    >>>         ax.set_ylim(0, None)

This section defines the :meth:`render_ax()` method, which takes in two parameters, ax and data.
The method starts by determining the orientation of the plot (horizontal or vertical) based on the value of :code:`self.is_flank`,
and then sets the :code:`x` or :code:`y` limits of the plot based on the length of the data.



.. code-block:: python
    :emphasize-lines: 17, 18, 19, 20

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
    >>>         ax.set_ylim(0, lim)
    >>>         ax.set_xlim(0, None)
    >>>         else:
    >>>             ax.set_xlim(0, lim)
    >>>             ax.set_ylim(0, None)
    >>>         if self.side == "left":
    >>>             ax.invert_xaxis()
    >>>         for spine in ax.spines.values():
    >>>             spine.set_visible(False)

Then we inverts the x-axis if the side of plot is "left", and sets all of the plot spines to be invisible.



.. plot::
    :context: close-figs

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

This section sets the y-ticks and x-ticks to be empty,
and plots the data as stems with an orientation determined by the value of orient and with no formatting for the base.
The stems are spaced at intervals of 0.5 starting from 0.



Add custom visualization to heatmap
-----------------------------------

.. plot::
    :context: close-figs

    >>> d1 = np.random.rand(10, 12)
    >>> value = np.random.uniform(size=10)
    >>> bar1 = Lollipop(value)
    >>> h1 = hg.Heatmap(d1)
    >>> h1.add_right(bar1, name = 'bar')
    >>> h1.render()

In conclusion, customizing your heatmap visualizations has never been easier.
With the ability to create a custom class that extends the :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>` base class,
you can bring your data to life with any visualization style you desire.


The key to unlocking this power lies in writing the :meth:`render_ax()` method, where you can specify how your data should be plotted and represented.
Whether you want to add a Lollipop plot like in our example or create something completely new, the possibilities are endless.









