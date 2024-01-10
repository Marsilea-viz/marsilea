"""
Current available plotters in Marsilea
======================================

"""

# %%
# Import libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import marsilea as ma
import marsilea.plotter as mp

from marsilea.layers import Rect, RightTri, FrameRect, FracRect

# %%
# Mesh plotters
plt.ion()
rng = np.random.default_rng(0)
data = np.arange(5)
data2d = np.arange(5).reshape(1, 5)
pieces = {
    0: FrameRect(color="g", label="2"),
    1: Rect(color="g", label="2"),
    2: RightTri(color="g", label="3"),
    3: FracRect(color="b", label="3"),
    4: RightTri(color="b", label="3", right_angle="upper right"),
}

plotters = {
    "Color Mesh": mp.ColorMesh(data2d, cmap="Blues"),
    "Sized Mesh": mp.SizedMesh(data2d, sizes=(100, 500), cmap="Greens"),
    "Marker Mesh": mp.MarkerMesh(data2d >= 2, size=300, marker="*", color="red"),
    "Layers Mesh": ma.layers.LayersMesh(data2d, pieces=pieces),
}

canvas = ma.Heatmap(data2d, width=5, height=0, cmap="Oranges", label="Color Mesh")
for title, plotter in plotters.items():
    plotter.set_label(title, "right")
    canvas.add_bottom(plotter)

canvas.add_dendrogram("bottom", method="ward", colors="#FFDD95")
canvas.render()

for ax in canvas.figure.get_axes():
    ax.set_axis_off()

# %%
# Label plotters

labels = np.arange(100)
text, text_color = [], []
for t in labels:
    if t % 10 == 0:
        text.append(t)
        if t / 10 % 2 == 0:
            text_color.append("#B80000")
        else:
            text_color.append("#5F8670")
    else:
        text.append("")
        text_color.append(".1")
matrix = rng.standard_normal((1, 100))
canvas2 = ma.Heatmap(matrix, width=5, height=.1)
canvas2.add_top(mp.Labels(text, text_props={'color': text_color}, rotation=0, label="Labels"))
canvas2.add_bottom(mp.AnnoLabels(labels, mark=[3, 4, 5, 96, 97, 98], rotation=0))
canvas2.render()


# %%
# Statistics plotters

data1d = np.arange(1, 6)
data2d = rng.integers(1, 10, size=(10, 5))
bar_width = .6

plotters = {
    "Simple Bar": mp.Numbers(data1d, color="#756AB6", width=bar_width),
    "Bar": mp.Bar(data2d, color="#5F8670", width=bar_width),
    "Boxen": mp.Boxen(data2d, color="#FFB534", width=bar_width),
    "Violin": mp.Violin(rng.standard_normal((20, 5)), color="#65B741"),
    "Point": mp.Point(data2d, color="#4CB9E7"),
    "Strip": mp.Strip(data2d, color="#FF004D"),
    "Swarm": mp.Swarm(data2d, color="#647D87"),
    "Stacked Bar": mp.StackBar(rng.integers(1, 10, (5, 5)), items="abcde", width=bar_width),
    "Center Bar": mp.CenterBar(rng.integers(1, 10, (5, 2)), colors=["#EE7214", "#527853"], width=bar_width),
}

canvas3 = ma.Heatmap(rng.standard_normal((10, 5)), width=4, height=0)
for title, plotter in plotters.items():
    plotter.allow_labeling = True
    plotter.set_label(title, "right")
    canvas3.add_bottom(plotter, pad=.3, size=2, name=title)

canvas3.vsplit(cut=[2])
canvas3.add_bottom(mp.Chunk(["Lower", "Upper"], ["#FFDD95", "#FFB000"], padding=10))

canvas3.render()
for ax in canvas3.figure.get_axes():
    # close axes spines
    for dir in ["left", "right", "top", "bottom"]:
        ax.spines[dir].set_visible(False)
    ax.tick_params(left=False, labelleft=False)

# for title in plotters.keys():
#     ax = canvas3.get_ax(title)[0]
#     ax.text(-.1, .5, title, transform=ax.transAxes, fontsize=14, ha="right", va="center")


# %%
# Other plotters
matrix = pd.DataFrame(data=rng.integers(1, 10, (4, 5)), index=list("ACGT"))
colors = {"A": "r", "C": "b", "G": "g", "T": "black"}
seqlogo = mp.SeqLogo(matrix, color_encode=colors)
arc = mp.Arc([1, 2, 3, 4, 5], [(1, 5), (2, 3), (1, 2), (4, 5)], width=1, colors="#FF004D")

canvas4 = ma.Heatmap(rng.standard_normal((10, 5)), width=4, height=0)
canvas4.add_top(seqlogo, size=2)
canvas4.add_top(arc, size=1, pad=.2)
canvas4.render()
