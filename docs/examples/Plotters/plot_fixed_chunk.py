"""
FixedChunk
==========


"""

# %%
import numpy as np
import marsilea as ma
from marsilea.plotter import FixedChunk

matrix = np.random.randn(20, 20)

h = ma.Heatmap(matrix)
chunk = ["C1", "C2-1", "C2-2", "C4"]
labels = np.random.choice(chunk, size=20)
h.hsplit(labels=labels, order=chunk)
h.add_right(FixedChunk(chunk, bordercolor="gray"), pad=0.1)
h.add_right(
    FixedChunk(
        ["C1", "C2", "C3"],
        fill_colors="red",
        ratio=[1, 2, 1],
    ),
    pad=0.1,
)
h.render()
