"""
Single-cell RNA-seq heatmap in Python (PBMC 3k)
===============================================

Marker gene expression across PBMC cell types: a heatmap layered with
:class:`~marsilea.plotter.SizedMesh` dots, violins and cell counts.

"""

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import marsilea as ma
import marsilea.plotter as mp

from sklearn.preprocessing import normalize

# sphinx_gallery_start_ignore
import mpl_fontkit as fk

fk.install("Lato", verbose=False)
mpl.rcParams["font.size"] = 12
# sphinx_gallery_end_ignore

pbmc3k = ma.load_data("pbmc3k")
exp = pbmc3k["exp"]
pct_cells = pbmc3k["pct_cells"]
count = pbmc3k["count"]

matrix = normalize(exp.to_numpy(), axis=0)

cell_cat = [
    "Lymphoid",
    "Myeloid",
    "Lymphoid",
    "Lymphoid",
    "Lymphoid",
    "Myeloid",
    "Myeloid",
    "Myeloid",
]
cell_names = [
    "CD4 T",
    "CD14\nMonocytes",
    "B",
    "CD8 T",
    "NK",
    "FCGR3A\nMonocytes",
    "Dendritic",
    "Megakaryocytes",
]

# Make plots
cells_proportion = mp.SizedMesh(
    pct_cells,
    size_norm=Normalize(vmin=0, vmax=100),
    color="none",
    edgecolor="#6E75A4",
    linewidth=2,
    sizes=(1, 600),
    size_legend_kws=dict(title="% of cells", show_at=[0.3, 0.5, 0.8, 1]),
)
mark_high = mp.MarkerMesh(matrix > 0.7, color="#DB4D6D", label="High")
cell_count = mp.Numbers(count["Value"], color="#fac858", label="Cell Count")
cell_exp = mp.Violin(
    exp, label="Expression", linewidth=0, color="#ee6666", density_norm="count"
)
cell_types = mp.Labels(cell_names, align="center")
gene_names = mp.Labels(exp.columns)

# Group plots together
h = ma.Heatmap(
    matrix, cmap="Greens", label="Normalized\nExpression", width=4.5, height=5.5
)
h.add_layer(cells_proportion)
h.add_layer(mark_high)
h.add_right(cell_count, pad=0.1, size=0.7)
h.add_top(cell_exp, pad=0.1, size=0.75, name="exp")
h.add_left(cell_types)
h.add_bottom(gene_names)

h.group_rows(cell_cat, order=["Lymphoid", "Myeloid"])
h.add_left(mp.Chunk(["Lymphoid", "Myeloid"], ["#33A6B8", "#B481BB"]), pad=0.05)
h.add_dendrogram("left", colors=["#33A6B8", "#B481BB"])
h.add_dendrogram("bottom")
h.add_legends("right", align_stacks="center", align_legends="top", pad=0.2)
h.set_margin(0.2)
h.render()
exported_figure = plt.gcf().number

# h.get_ax("exp").set_yscale("symlog")

# %%
# The same figure from an AnnData
# -------------------------------
# If your data already lives in an :class:`~anndata.AnnData`, there is no need to
# pull the arrays out by hand. Bind the object to the board once, then name the
# pieces you want with :mod:`anndata.acc` references. See
# :doc:`/tutorial/anndata` for the full walkthrough.
#
# The frames above become an AnnData whose observations are cell types and whose
# variables are genes:

import anndata as ad
import pandas as pd
from anndata.acc import A

adata = ad.AnnData(
    X=matrix,
    obs=pd.DataFrame(
        {
            "lineage": pd.Categorical(cell_cat, categories=["Lymphoid", "Myeloid"]),
            "count": count["Value"].to_numpy(),
        },
        index=cell_names,
    ),
    var=pd.DataFrame(index=exp.columns),
)
adata.layers["pct_cells"] = pct_cells.to_numpy()
adata.layers["expression"] = exp.to_numpy()
adata.layers["high"] = matrix > 0.7

# %%
# Every data argument can now be a reference. ``A.obs[...]`` spans observations,
# so it belongs on the row sides, and ``A.var[...]`` belongs on the column sides.
# Add one to the wrong side and the board says so, rather than failing later
# during rendering.
#
# ``group_rows`` needs no ``order=`` here either. ``lineage`` is categorical, so
# its category order is used.

h = ma.Heatmap(
    adata,
    A.X[:, :],
    cmap="Greens",
    label="Normalized\nExpression",
    width=4.5,
    height=5.5,
)
h.add_layer(
    mp.SizedMesh(
        A.layers["pct_cells"][:, :],
        size_norm=Normalize(vmin=0, vmax=100),
        color="none",
        edgecolor="#6E75A4",
        linewidth=2,
        sizes=(1, 600),
        size_legend_kws=dict(title="% of cells", show_at=[0.3, 0.5, 0.8, 1]),
    )
)
h.add_layer(mp.MarkerMesh(A.layers["high"][:, :], color="#DB4D6D", label="High"))
h.add_right(
    mp.Numbers(A.obs["count"], color="#fac858", label="Cell Count"), pad=0.1, size=0.7
)
h.add_top(
    mp.Violin(
        A.layers["expression"][:, :],
        label="Expression",
        linewidth=0,
        color="#ee6666",
        density_norm="count",
    ),
    pad=0.1,
    size=0.75,
    name="exp",
)
h.add_left(mp.Labels(A.obs.index, align="center"))
h.add_bottom(mp.Labels(A.var.index))

h.group_rows(A.obs["lineage"])
h.add_left(mp.Chunk(["Lymphoid", "Myeloid"], ["#33A6B8", "#B481BB"]), pad=0.05)
h.add_dendrogram("left", colors=["#33A6B8", "#B481BB"])
h.add_dendrogram("bottom")
h.add_legends("right", align_stacks="center", align_legends="top", pad=0.2)
h.set_margin(0.2)
h.render()

# sphinx_gallery_start_ignore
# The exported asset below belongs to the first figure; re-select it so adding
# this section did not silently change which figure PBMC3K.svg holds.
plt.figure(exported_figure)
# sphinx_gallery_end_ignore

# sphinx_gallery_start_ignore
if "__file__" in globals():
    from pathlib import Path
    import matplotlib.pyplot as plt

    save_path = Path(__file__).parent / "imgs"
    mpl.rcParams["svg.fonttype"] = "none"
    # mpl.rcParams["font.family"] = "Arial"
    plt.savefig(save_path / "PBMC3K.svg", bbox_inches="tight")
# sphinx_gallery_end_ignore
