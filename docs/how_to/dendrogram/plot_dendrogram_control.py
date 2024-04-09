"""
Meta dendrogram
================

This example shows how to add only meta dendrogram to a heatmap.

"""

# %%
import numpy as np
import marsilea as ma

data = np.random.randint(0, 10, (100, 3))

# %%
h = ma.Heatmap(data, width=3, height=3)
h.cut_rows([30, 50, 75])
h.add_dendrogram("left", add_base=False, meta_color="#7EA1FF")
h.render()
