"""
Balancing dendrogram heights
============================

When groups cluster at very different tightness, the default scaling can make
the dendrogram look lopsided. This example shows the two knobs that fix it.

"""

# %%
import numpy as np
import marsilea as ma

# Three groups with deliberately different spread: the first is tight, the
# second is diffuse, the third sits in between.
rng = np.random.default_rng(0)
data = np.vstack(
    [
        rng.standard_normal((10, 8)) * 0.05,
        rng.standard_normal((25, 8)) * 3.0,
        rng.standard_normal((15, 8)),
    ]
)
groups = ["tight"] * 10 + ["diffuse"] * 25 + ["middle"] * 15
order = ["tight", "diffuse", "middle"]


# %%
# The default, ``height_scale="minmax"``, stretches each group over the full
# height. Every group reaches the same apex whatever its rows actually do, so
# the tight group looks as deep as the diffuse one and the meta dendrogram
# sits on a flat plateau.

h = ma.Heatmap(data, width=3, height=3)
h.group_rows(groups, order=order)
h.add_dendrogram("left", method="ward")
h.render()

# %%
# ``height_scale="shared"`` measures every group against the tallest merge
# anywhere, so the drawn heights are in proportion to the real distances. The
# tight group now draws short, and the length of each root line says how far
# that group had left to travel before joining the others.

h = ma.Heatmap(data, width=3, height=3)
h.group_rows(groups, order=order)
h.add_dendrogram("left", method="ward", height_scale="shared")
h.render()

# %%
# Honest heights can be hard to read when one group is very tight. Merges also
# tend to bunch up near the leaves, badly so with ``method="ward"``, leaving
# the top of the plot empty. ``height_transform`` opens up the low end without
# ever reordering two merges.
#
# ``"sqrt"`` is the gentlest, ``"log"`` stronger, and ``"rank"`` spreads the
# merges out evenly. They buy legibility by giving up readable distances, so
# reach for them when the shape of the tree matters more than its scale.

h = ma.Heatmap(data, width=3, height=3)
h.group_rows(groups, order=order)
h.add_dendrogram("left", method="ward", height_scale="shared", height_transform="sqrt")
h.render()

# %%
# With any scale other than the default, ``meta_ratio`` is exact: the meta
# dendrogram is drawn at that fraction of the base dendrogram's height, and
# its leaves sit directly on the divider.

h = ma.Heatmap(data, width=3, height=3)
h.group_rows(groups, order=order)
h.add_dendrogram(
    "left", method="ward", height_scale="shared", meta_ratio=0.4, meta_color="#7EA1FF"
)
h.render()
