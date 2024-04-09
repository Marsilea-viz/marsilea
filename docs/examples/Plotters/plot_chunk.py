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
chunk = ['C1', 'C2', 'C3', 'C4']
labels = np.random.choice(chunk, size=20)
h.hsplit(labels=labels, order=chunk)
h.add_right(Chunk(chunk, bordercolor="gray"), pad=.1)
h.add_dendrogram("left")
h.render()