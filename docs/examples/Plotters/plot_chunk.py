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
labels = np.repeat(chunk, [6, 5, 5, 4])
h.group_rows(labels, order=chunk)
h.add_right(Chunk(chunk, bordercolor="gray"), pad=0.1)
h.add_dendrogram("left")
h.render()
