"""
Chunk
=====


"""

# %%
import numpy as np
import marsilea as ma
from marsilea.plotter import Chunk

matrix = np.random.randn(20, 20)
h = ma.Heatmap(matrix)
chunk = ["C1", "C2", "C3", "C4"]
# Fixed group sizes: drawing the labels leaves a 1-in-80 chance that one chunk
# never comes up, and `order` below then asks for a group that is not in the data.
labels = np.repeat(chunk, [6, 5, 5, 4])
h.group_rows(labels, order=chunk)
h.add_right(Chunk(chunk, bordercolor="gray"), pad=0.1)
h.add_dendrogram("left")
h.render()
