"""
Annotate stacked bar
====================

"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import heatgraphy as hg

np.random.seed(0)
data = np.random.randint(1, 100, (5, 10))
data = pd.DataFrame(data=data, index=list("abcde"))

bar = hg.plotter.StackBar(data / data.sum(), width=.9,
                          legend_kws=dict(title="Stacked Bar"))
wb = hg.WhiteBoard(width=3, height=3)
wb.add_layer(bar)

top_colors = hg.plotter.Colors([1, 1, 2, 2, 4], cmap="Set2", label="Category")
wb.add_top(top_colors, size=.2)

top_mesh = hg.plotter.ColorMesh(data.sum(), cmap="cool", label="Total",
                                cbar_kws=dict(orientation="horizontal"))
wb.add_top(top_mesh, size=.2, pad=.1)
wb.add_legends()
wb.add_pad("left", size=.3)
wb.add_pad("bottom", size=.3)
wb.render()
plt.savefig("Stacked bar.png", bbox_inches="tight", dpi=150)
plt.show()
