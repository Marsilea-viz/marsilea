"""
Annotate stacked bar
====================

"""

import numpy as np
import pandas as pd
import heatgraphy as hg

data = np.random.randint(1, 100, (5, 10))
data = pd.DataFrame(data=data, index=list("abcde"))

bar = hg.plotter.StackBar(data, legend_kws=dict(title="Stacked Bar"))
wb = hg.WhiteBoard(width=3, height=3)
wb.add_layer(bar)

top_colors = hg.plotter.Colors([1, 1, 2, 2, 4], cmap="Set2", label="Category")
wb.add_top(top_colors, size=.2)

bottom_mesh = hg.plotter.ColorMesh(data.sum(), cmap="Reds",
                                   cbar_kws=dict(orientation="horizontal"))
wb.add_bottom(bottom_mesh, size=.2, pad=.3)
wb.add_legends()
wb.render()
