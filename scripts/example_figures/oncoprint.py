"""
Breast cancer mutation with Oncoprinter
=======================================

The Dataset is collected from cBioportal:
Breast Invasive Carcinoma (TCGA, PanCancer Atlas)

"""
# sphinx_gallery_thumbnail_number = -1
import matplotlib.pyplot as plt

import marsilea as ma
import marsilea.plotter as mp
from oncoprinter import OncoPrint

# sphinx_gallery_start_ignore
import mpl_fontkit as fk

fk.install("Lato", verbose=False)
# sphinx_gallery_end_ignore

# %%
# Load data


onco_data = ma.load_data("oncoprint")
cna = onco_data["cna"]
mrna_exp = onco_data["mrna_exp"]
methyl_exp = onco_data["methyl_exp"]
clinical = onco_data["clinical"]

# %%
# Make mRNA expression
# --------------------

mrna_exp = mrna_exp.loc[["TP53", "PTEN"]]
h = ma.Heatmap(
    mrna_exp,
    cmap="gist_heat_r",
    height=0.3,
    width=5,
    cbar_kws=dict(
        orientation="horizontal", height=1, width=10, title="mRNA Expression"
    ),
)
h.add_title(top="mRNA expression Z-SCORE", align="left", fontsize=10)
h.add_left(mp.Labels(mrna_exp.index), pad=0.1)
h.render()

# %%
# Make Methylation expression
# ---------------------------


m = ma.Heatmap(
    methyl_exp.astype(float),
    height=0.3,
    width=5,
    cmap="summer_r",
    cbar_kws=dict(orientation="horizontal", height=1, width=10, title="Methylation"),
)
m.add_title(top="Methylation", align="left", fontsize=10)
m.add_left(mp.Labels(["PTEN", "CDH13"]), pad=0.1)
m.render()

# %%
# Create Oncoprint
# ----------------
selected_genes = ["TP53", "PIK3CA", "GATA3", "TTN", "CDH1", "PTEN"]
cna = cna[~cna["track"].isin(["KMT2C", "TTN", "FLG"])]
# cna['sample'] = cna['sample'].str.slice(5, 12)

op = OncoPrint(
    cna,
    height=3,
    name="main",
    add_samples_names=False,
    legend_kws=dict(fontsize=8),
    add_tracks_counts_size=0.4,
    add_mut_counts_size=0.4,
    add_tracks_counts_pad=0.05,
)
op.render()

# %%
# Make clinical information
# -------------------------


clinical = clinical[op.samples_order]
short_term = {
    "Breast Invasive Ductal Carcinoma": "IDC",
    "Breast Invasive Lobular Carcinoma": "ILC",
    "Breast Invasive Carcinoma (NOS)": "BIC (NOS)",
}
tumor_type = clinical.loc["Cancer Type Detailed"].map(short_term)
tumor_palette = ["#DD5746", "#4793AF", "#FFC470"]
tumor_colors = mp.Colors(
    tumor_type,
    palette=tumor_palette,
    legend_kws=dict(fontsize=8),
    label="Tumor Type",
    label_loc="right",
)

mut_count = clinical.loc["Mutation Count"]
mut_number = mp.Numbers(
    mut_count, show_value=False, color="orange", label="Mutations", label_loc="right"
)

# %%
# Add clinical to the oncoprint

op.add_top(tumor_colors, size=0.15, pad=0.1)
op.add_top(mut_number, name="mut", size=0.15, pad=0.1, legend=False)
op.render()

# %%
# Append expression to the oncoprint

op /= h
op /= m

# %%
# Render

op.set_margin(0.2)
op.add_legends(box_padding=2, stack_size=4)
op.render()

op.get_ax("main", "mut").set_axis_off()

# sphinx_gallery_start_ignore
if "__file__" in globals():
    from pathlib import Path
    import matplotlib.pyplot as plt

    plt.rcParams["svg.fonttype"] = "none"
    save_path = Path(__file__).parent / "figures"
    plt.savefig(save_path / "oncoprint.svg", bbox_inches="tight")
else:
    plt.show()
# sphinx_gallery_end_ignore
