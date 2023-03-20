"""
Upset Plot
===========

IMDB Top 1000 Movies

"""
from matplotlib import pyplot as plt

import heatgraphy as hg
from heatgraphy.upset import UpsetData, Upset

imdb = hg.load_data("imdb")

items_attrs = (imdb[['Title', 'Year', 'Runtime (Minutes)', 'Rating',
                     'Votes', 'Revenue (Millions)', 'Metascore']]
               .set_index('Title'))

upset_data = UpsetData.from_memberships(imdb.Genre.str.split(','),
                                        items_names=imdb['Title'],
                                        items_attrs=items_attrs)

us = Upset(upset_data, min_size=25,
           sets_order=["Action", "Adventure", "Sci-Fi", "Mystery", "Horror",
                       "Thriller", "Comedy", "Drama", "Romance", "Crime"])
us.highlight_subsets(min_size=48, facecolor="#D0104C", label="Larger than 48")
us.highlight_subsets(min_size=32, edgecolor="green", edgewidth=1.5,
                     label="Larger than 32")
us.add_items_attrs("bottom", "Revenue (Millions)", hg.plotter.Strip,
                   pad=.2, size=.5, plot_kws=dict(color="#24936E", size=1.2))
us.add_title(bottom="Revenue (Millions)", fontsize=10)

us.add_items_attrs("top", "Rating", hg.plotter.Box,
                   pad=.2,
                   plot_kws=dict(color="orange", linewidth=1, fliersize=1))
us.add_title(top="Rating", fontsize=10)

us.add_legends(box_padding=0)
us.render()
plt.show()
