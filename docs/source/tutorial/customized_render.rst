How to customize your visualization?
====================================

Retrieve main axes
------------------

To retrieve the main axes, you can call :meth:`get_main_ax() <marsilea.WhiteBoard.get_main_ax>` to get
the main axes. Remember to retrieve the axes **after**
you render the plot. If not render, the axes will not be created.

Here we show an example of adding border for your heatmap.

.. code-block:: python
    :emphasize-lines: 7

    >>> import marsilea as hg
    >>> from matplotlib.patches import Rectangle
    >>> data = np.random.rand(10, 10)
    >>> h = hg.Heatmap(data)
    >>> h.render()
    >>> # Get the ax after render()
    >>> hax = h.get_main_ax()
    >>> border = Rectangle((0, 0), 1, 1, fill=False, ec=".1", lw=5, transform=hax.transAxes)
    >>> hax.add_artist(border)


.. plot::
    :context: close-figs
    :include-source: False

        >>> import marsilea as hg
        >>> from matplotlib.patches import Rectangle
        >>> data = np.random.rand(10, 10)
        >>> h = hg.Heatmap(data)
        >>> h.render()
        >>> # Get the ax after render()
        >>> hax = h.get_main_ax()
        >>> border = Rectangle((0, 0), 1, 1, fill=False, ec=".1", lw=5, transform=hax.transAxes)
        >>> hax.add_artist(border)

    If the heatmap is split, there will be multiple axes. The return order starts from upper left to lower right.

        >>> import marsilea as hg
        >>> from matplotlib.patches import Rectangle
        >>> data = np.random.rand(10, 10)
        >>> h = hg.Heatmap(data)
        >>> h.render()
        >>> # Get the ax after render()
        >>> hax = h.get_main_ax()
        >>> border = Rectangle((0, 0), 1, 1, fill=False, ec=".1", lw=5, transform=hax.transAxes)
        >>> hax.add_artist(border)

    If the heatmap is split, there will be multiple axes. The return order starts from upper left to lower right.

    >>> import marsilea as hg
    >>> from matplotlib.patches import Rectangle
    >>> data = np.random.rand(10, 10)
    >>> h = hg.Heatmap(data)
    >>> h.render()
    >>> # Get the ax after render()
    >>> hax = h.get_main_ax()
    >>> border = Rectangle((0, 0), 1, 1, fill=False, ec=".1", lw=5, transform=hax.transAxes)
    >>> hax.add_artist(border)

If the heatmap is split, there will be multiple axes. The return order starts from upper left to lower right.

.. plot::
    :context: close-figs

    >>> h = hg.Heatmap(data, cmap="binary")
    >>> h.hsplit(cut=[5])
    >>> h.vsplit(cut=[5])
    >>> h.render()
    >>> # Get the ax after render()
    >>> hax = h.get_main_ax()
    >>> print(hax)
        [<AxesSubplot: > <AxesSubplot: > <AxesSubplot: > <AxesSubplot: >]
    >>> colors = ["#9a60b4", "#73c0de", "#3ba272", "#fc8452"]
    >>> # purple, blue, green, orange
    >>> for ax, c in zip(hax, colors):
    ...     border = Rectangle((0, 0), 1, 1, fill=False, ec=c, lw=5, transform=ax.transAxes)
    ...     ax.add_artist(border)


Retrieve side axes
------------------

To get a side axes is similar to retrieve main axes. You can get it by calling :meth:`get_ax() <marsilea.WhiteBoard.get_ax>`
with the name of the target axes. Therefore, you need to explicitly assign a name to your target plot to get the axes
that it renders on.


.. code-block:: python
    :emphasize-lines: 5, 8

    >>> h = hg.Heatmap(data)
    >>> h.split_row(cut=[5])
    >>> bar = hg.plotter.Numbers(np.arange(10))
    >>> h.add_right(bar, name="My Bar")
    >>> h.render()
    >>> # Get the ax after render()
    >>> bar_axes = h.get_ax("My Bar")
    >>> colors = ["#9a60b4", "#73c0de"]
    >>> # purple, blue
    >>> for ax, c in zip(bar_axes, colors):
    ...     bg = Rectangle((0, 0), 1, 1, fc=c, zorder=-1, transform=ax.transAxes)
    ...     ax.add_artist(bg)


.. plot::
    :context: close-figs
    :include-source: False

    >>> h = hg.Heatmap(data)
    >>> h.hsplit(cut=[5])
    >>> bar = hg.plotter.Numbers(np.arange(10))
    >>> h.add_right(bar, name="My Bar")
    >>> h.render()
    >>> # Get the ax after render()
    >>> bar_axes = h.get_ax("My Bar")
    >>> colors = ["#9a60b4", "#73c0de"]
    >>> # purple, blue
    >>> for ax, c in zip(bar_axes, colors):
    ...     bg = Rectangle((0, 0), 1, 1, fc=c, zorder=-1, transform=ax.transAxes)
    ...     ax.add_artist(bg)