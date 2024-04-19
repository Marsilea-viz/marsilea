"""
Upset Plot
===========

IMDB Top 1000 Movies

"""
from matplotlib import pyplot as plt

import marsilea as ma
from marsilea.upset import UpsetData

# sphinx_gallery_start_ignore
import mpl_fontkit as fk
fk.install("Lato", verbose=False)
plt.rcParams['font.size'] = 12
# sphinx_gallery_end_ignore

imdb = ma.load_data("imdb")

items_attrs = (imdb[['Title', 'Year', 'Runtime (Minutes)', 'Rating',
                     'Votes', 'Revenue (Millions)', 'Metascore']]
               .set_index('Title'))

upset_data = UpsetData.from_memberships(imdb.Genre.str.split(','),
                                        items_names=imdb['Title'],
                                        items_attrs=items_attrs)

us = ma.upset.Upset(upset_data, orient="v", min_cardinality=15)
us.highlight_subsets(min_cardinality=48, facecolor="#D0104C",
                     label="Larger than 48")
us.highlight_subsets(min_cardinality=32, edgecolor="green", edgewidth=1.5,
                     label="Larger than 32")
us.add_items_attr("left", "Revenue (Millions)", "strip", pad=.2, size=.5,
                  plot_kws=dict(color="#24936E", size=1.2, label="Revenue\n(Millions)"))
us.add_items_attr("right", "Rating", "box",
                  pad=.2,
                  plot_kws=dict(color="orange", linewidth=1, fliersize=1))

us.add_legends(box_padding=0)
us.set_margin(.3)
us.render()

# sphinx_gallery_start_ignore
if '__file__' in globals():
    from pathlib import Path
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    save_path = Path(__file__).parent / "imgs"
    mpl.rcParams['svg.fonttype'] = 'none'
    plt.savefig(save_path / "upset.svg", bbox_inches="tight", transparent=False)
# sphinx_gallery_end_ignore
