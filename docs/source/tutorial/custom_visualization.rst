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

.. plot::
    :context: close-figs

    >>> class Lollipop(RenderPlan):
    >>>     def __init__(self, data):
    >>>         self.data = data
    >>>     def get_legends(self):
    >>>         return CatLegend(label=['Lollipop'], handle="circle")
    >>>     def render_ax(self, ax, data):
    >>>         orient = "horizontal" if self.is_flank else "vertical"
    >>>         lim = len(data)
    >>>         if self.is_flank:
    >>>             ax.set_ylim(0, lim)
    >>>         else:
    >>>             ax.set_xlim(0, lim)
    >>>         if self.side == "left":
    >>>             ax.invert_xaxis()
    >>>          # Plot on every .5 start from 0
    >>>         locs = np.arange(0, lim) + 0.5
    >>>         ax.stem(locs, data, orientation=orient)

| This code showcases how to create a custom visualization class called :class:`Lollipop`.
| To start, the Lollipop class inherits from the :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>` base class and takes in the data to be plotted.
| The :meth:`get_legends()` method returns a categorical legend that clearly labels the Lollipop plot with a circle handle.
| In the :meth:`render_ax()` method, the Lollipop plot is created with the help of the :class:`matplotlib.axes.Axes.stem` function and plotted on the given axis.
| The orientation of the plot is determined by the position of the plot within the heatmap, whether it's on the flank or not.
| Additionally, the limits of the axis are set based on the length of the data and the side of the heatmap.

Add custom visualization to heatmap
-----------------------------------

.. plot::
    :context: close-figs

    >>> d1 = np.random.rand(10,12)
    >>> value = np.random.uniform(size=10)
    >>> bar1 = Lollipop(value)
    >>> h1 = hg.Heatmap(d1)
    >>> h1.add_right(bar1,size= 5,name = 'bar')
    >>> h1.render()

| In conclusion, customizing your heatmap visualizations has never been easier.
| With the ability to create a custom class that extends the :class:`RenderPlan <heatgraphy.plotter.base.RenderPlan>` base class, you can bring your data to life with any visualization style you desire.
| The key to unlocking this power lies in writing the :meth:`render_ax()` method, where you can specify how your data should be plotted and represented.
| Whether you want to add a Lollipop plot like in our example or create something completely new, the possibilities are endless.









