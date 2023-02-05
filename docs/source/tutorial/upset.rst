UpSet plot
==========

UpSet plot can be considered as venn plot for many sets.


Data Input
----------

The data format of upset data is a bit complicated. Currently, Heatgraphy can handle following format.

- A list of sets and the items in each set.
- A list of items and the sets that the item belongs to.
- A binary table, columns are sets, rows are items. The value of 0 or 1 indicates if an item is in a set.

Heatgraphy provides a utility class :class:`UpsetData <heatgraphy.upset.UpsetData>` to handle sets data.
It contains helpful methods to query information about different sets.

Here we use the Top 1000 movies in IMDB database for illustration.

.. plot::
    :context: close-figs

    >>> from heatgraphy import load_data
    >>> from heatgraphy.upset import UpsetData
    >>> imdb = load_data('imdb')
    >>> imdb = imdb.drop_duplicates('Title')
    >>> upset_data = UpsetData.from_memberships(imdb.Genre.str.split(','))

.. plot::
    :context: close-figs
    :include-source: False

    >>> from matplotlib import rcParams
    >>> rcParams['font.size'] = 8


Create an UpSet plot
--------------------

The :class:`Upset <heatgraphy.upset.Upset>` is here to help you create your first upset plot.
Like other visualization in heatgraphy, remember to call :meth:`render()`
to actually render your plot.

.. plot::
    :context: close-figs

    >>> from heatgraphy.upset import Upset
    >>> us = Upset(upset_data, min_size=15)
    >>> us.render()

You can also change the position of different components

.. plot::
    :context: close-figs

    >>> us = Upset(upset_data, min_size=15, add_labels="left", add_sets_size="right")
    >>> us.render()

Alternatively, to have better control

.. plot::
    :context: close-figs

    >>> us = Upset(upset_data, min_size=15, add_labels=False, add_sets_size=False)
    >>> us.add_sets_label(side="left", pad=0, align="center", text_pad=.1)
    >>> us.add_sets_size(side="left", pad=0)
    >>> us.render()


Highlight Sets
--------------

To highlight specific sets, try :meth:`highlight_subsets() <heatgraphy.upset.Upset.highlight_subsets>`.

.. plot::
    :context: close-figs

    >>> us = Upset(upset_data, min_size=15)
    >>> us.highlight_subsets(facecolor='red', min_size=25, max_size=40, label="25~40")
    >>> us.highlight_subsets(edgecolor='green', min_size=20, max_size=30,label="20~30")
    >>> us.add_legends()
    >>> us.render()


Sets attributes and items attributes
------------------------------------

UpSet plot can not only visualize the intersections, but also the distribution of different attributes.

.. plot::
    :context: close-figs

    >>> from heatgraphy.plotter import Box, Strip
    >>> items_attrs = imdb[['Title', 'Rating', 'Revenue (Millions)']].set_index('Title')
    >>> imdb_data = UpsetData.from_memberships(imdb.Genre.str.split(','),
    >>>                                        items_names=imdb['Title'], items_attrs=items_attrs)
    >>> us = Upset(imdb_data, min_size=15)
    >>> us.add_items_attrs("top", "Rating", Box, pad=.2, plot_kws=dict(color="orange", linewidth=1, fliersize=1))
    >>> us.add_title(top="Rating")
    >>> us.add_items_attrs("bottom", "Revenue (Millions)", Strip, pad=.2, plot_kws=dict(size=1, color="#24936E"))
    >>> us.add_title(bottom="Revenue (Millions)")
    >>> us.render()

