UpSet Plot: The Ultimate Venn Diagram Alternative for Multiple Sets
===================================================================

UpSet Plot offers a powerful alternative to Venn diagrams when dealing with multiple sets,
making it easier to analyze and visualize complex data relationships.



Data Input Made Easy
--------------------

Understanding the data format for UpSet plots is a breeze. Marsilea handles these formats effortlessly:

A list of sets and their respective items.
A list of items and the sets they belong to.
A binary table with columns representing sets,
rows representing items, and values of 0 or 1 to indicate an item's presence in a set.



The versatile :class:`UpsetData <heatgraphy.upset.UpsetData>` utility class from
Marsilea simplifies working with set data,
offering useful methods for querying information about various sets.

To demonstrate, we'll use the Top 1000 movies from the IMDB database.



.. plot::
    :context: close-figs

        >>> from marsilea import load_data
        >>> from marsilea.upset import UpsetData
        >>> imdb = load_data('imdb')
        >>> imdb = imdb.drop_duplicates('Title')
        >>> upset_data = UpsetData.from_memberships(imdb.Genre.str.split(','))

        >>> from marsilea import load_data
        >>> from marsilea.upset import UpsetData
        >>> imdb = load_data('imdb')
        >>> imdb = imdb.drop_duplicates('Title')
        >>> upset_data = UpsetData.from_memberships(imdb.Genre.str.split(','))

        >>> from marsilea import load_data
        >>> from marsilea.upset import UpsetData
        >>> imdb = load_data('imdb')
        >>> imdb = imdb.drop_duplicates('Title')
        >>> upset_data = UpsetData.from_memberships(imdb.Genre.str.split(','))

        >>> from marsilea import load_data
        >>> from marsilea.upset import UpsetData
        >>> imdb = load_data('imdb')
        >>> imdb = imdb.drop_duplicates('Title')
        >>> upset_data = UpsetData.from_memberships(imdb.Genre.str.split(','))

    >>> from marsilea import load_data
    >>> from marsilea.upset import UpsetData
    >>> imdb = load_data('imdb')
    >>> imdb = imdb.drop_duplicates('Title')
    >>> upset_data = UpsetData.from_memberships(imdb.Genre.str.split(','))

.. plot::
    :context: close-figs
    :include-source: False

    >>> from matplotlib import rcParams
    >>> rcParams['font.size'] = 8


Creating an UpSet Plot in a Snap
--------------------------------

The :class:`Upset <heatgraphy.upset.Upset>`  class in Marsilea makes it easy to create your first UpSet plot.
Like other visualizations in Marsilea, simply call the :meth:`render()` method to bring your plot to life.
>>>>>>> e86bad189545a898a222acaa5b40e03033dbed34

.. plot::
    :context: close-figs

        >>> from marsilea.upset import Upset
        >>> us = Upset(upset_data, min_size=15)
        >>> us.render()

    You can also change the position of different components

        >>> from marsilea.upset import Upset
        >>> us = Upset(upset_data, min_size=15)
        >>> us.render()

    You can also change the position of different components

    >>> from marsilea.upset import Upset
    >>> us = Upset(upset_data, min_size=15)
    >>> us.render()

Customize component positions for a tailored look:

.. plot::
    :context: close-figs

    >>> us = Upset(upset_data, min_size=15, add_labels="left", add_sets_size="right")
    >>> us.render()

For even more control:

.. plot::
    :context: close-figs

    >>> us = Upset(upset_data, min_size=15, add_labels=False, add_sets_size=False)
    >>> us.add_sets_label(side="left", pad=0, align="center")
    >>> us.add_sets_size(side="left", pad=0)
    >>> us.render()


Highlighting Sets with Ease
---------------------------

To emphasize specific sets, use the :meth:`highlight_subsets() <heatgraphy.upset.Upset.highlight_subsets>` method.


.. plot::
    :context: close-figs

    >>> us = Upset(upset_data, min_size=15)
    >>> us.highlight_subsets(facecolor='red', min_size=25, max_size=40, label="25~40")
    >>> us.highlight_subsets(edgecolor='green', min_size=20, max_size=30,label="20~30")
    >>> us.add_legends()
    >>> us.render()


Visualizing Set and Item Attributes
-----------------------------------

UpSet plots not only showcase intersections but also display the distribution of different attributes.

.. plot::
    :context: close-figs

        >>> from marsilea.plotter import Box, Strip
        >>> items_attrs = imdb[['Title', 'Rating', 'Revenue (Millions)']].set_index('Title')
        >>> imdb_data = UpsetData.from_memberships(imdb.Genre.str.split(','),
        >>>                                        items_names=imdb['Title'], items_attrs=items_attrs)
        >>> us = Upset(imdb_data, min_size=15)
        >>> us.add_items_attrs("top", "Rating", Box, pad=.2, plot_kws=dict(color="orange", linewidth=1, fliersize=1))
        >>> us.add_title(top="Rating")
        >>> us.add_items_attrs("bottom", "Revenue (Millions)", Strip, pad=.2, plot_kws=dict(size=1, color="#24936E"))
        >>> us.add_title(bottom="Revenue (Millions)")
        >>> us.render()

        >>> from marsilea.plotter import Box, Strip
        >>> items_attrs = imdb[['Title', 'Rating', 'Revenue (Millions)']].set_index('Title')
        >>> imdb_data = UpsetData.from_memberships(imdb.Genre.str.split(','),
        >>>                                        items_names=imdb['Title'], items_attrs=items_attrs)
        >>> us = Upset(imdb_data, min_size=15)
        >>> us.add_items_attrs("top", "Rating", Box, pad=.2, plot_kws=dict(color="orange", linewidth=1, fliersize=1))
        >>> us.add_title(top="Rating")
        >>> us.add_items_attrs("bottom", "Revenue (Millions)", Strip, pad=.2, plot_kws=dict(size=1, color="#24936E"))
        >>> us.add_title(bottom="Revenue (Millions)")
        >>> us.render()

    >>> from marsilea.plotter import Box, Strip
    >>> items_attrs = imdb[['Title', 'Rating', 'Revenue (Millions)']].set_index('Title')
    >>> imdb_data = UpsetData.from_memberships(imdb.Genre.str.split(','),
    >>>                                        items_names=imdb['Title'], items_attrs=items_attrs)
    >>> us = Upset(imdb_data, min_size=15)
    >>> us.add_items_attrs("top", "Rating", Box, pad=.2, plot_kws=dict(color="orange", linewidth=1, fliersize=1))
    >>> us.add_title(top="Rating")
    >>> us.add_items_attrs("bottom", "Revenue (Millions)", Strip, pad=.2, plot_kws=dict(size=1, color="#24936E"))
    >>> us.add_title(bottom="Revenue (Millions)")
    >>> us.render()

