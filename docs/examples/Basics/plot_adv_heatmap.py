"""
Complex annotated heatmap in Python
===================================

Group and cluster the rows of a heatmap, then label the groups beside it with
:class:`~marsilea.plotter.Chunk`.

"""

# %%
import numpy as np
import marsilea as ma

data = np.random.randint(0, 10, (10, 10))
# Fixed sizes rather than a draw: `order` below names all three groups, and
# drawing them left a 1-in-20 chance that one never came up.
groups = np.repeat(["A", "B", "C"], [4, 3, 3])

# %%

h = ma.Heatmap(data)
h.add_dendrogram("right")
h.group_rows(groups, order=["A", "B", "C"])
h.add_left(
    ma.plotter.Chunk(["A", "B", "C"], fill_colors=["#F05454", "#F0F0F0", "#54F0F0"])
)
h.add_legends("left")
h.add_title("Grouped heatmap")
h.render()
