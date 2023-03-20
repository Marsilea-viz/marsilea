"""
Visualizing Single-cell RNA-seq Data
====================================

"""

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize

import heatgraphy as hg
from sklearn.preprocessing import normalize

mpl.rcParams['font.size'] = 8

pbmc3k = hg.load_data("pbmc3k")
exp = pbmc3k['exp']
pct_cells = pbmc3k['pct_cells']
count = pbmc3k['count']

matrix = normalize(exp.to_numpy(), axis=0)

cell_cat = ['Lymphoid', 'Myeloid', 'Lymphoid', 'Lymphoid',
            'Lymphoid', 'Myeloid', 'Myeloid', 'Myeloid']

# Make plots
cells_proportion = hg.plotter.SizedMesh(
    pct_cells, size_norm=Normalize(vmin=0, vmax=100),
    color="none", edgecolor="#6E75A4",
    size_legend_kws=dict(title="% of cells", show_at=[.3, .5, .8, 1])
)
mark_high = hg.plotter.MarkerMesh(matrix > 0.7, color="#DB4D6D", label="High")
cell_count = hg.plotter.Numbers(count['Value'], color="#fac858", label="Cell Count")
cell_exp = hg.plotter.Violin(exp, label="Expression", linewidth=0, color="#ee6666")
cell_types = hg.plotter.Labels(exp.index, align="center")
gene_names = hg.plotter.Labels(exp.columns)

# Group plots together
h = hg.Heatmap(matrix, cmap="Greens", label="Normalized\nExpression",
               width=3, height=3.5)
h.add_layer(cells_proportion)
h.add_layer(mark_high)
h.add_right(cell_count, pad=.1, size=.7)
h.add_top(cell_exp, pad=.1, size=.75)
h.add_left(cell_types)
h.add_bottom(gene_names)

h.hsplit(labels=cell_cat, order=['Lymphoid', 'Myeloid'])
h.add_left(hg.plotter.Chunk(['Lymphoid', 'Myeloid'], ["#33A6B8", "#B481BB"]),
           pad=.05)
h.add_dendrogram("left", colors=["#33A6B8", "#B481BB"])
h.add_dendrogram("bottom")
h.add_legends(pad=.1)
h.render()
