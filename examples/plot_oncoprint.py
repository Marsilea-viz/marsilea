"""
Visualizing Breast cancer mutation using Oncoprinter
====================================================

The Dataset is collected from cBioportal:
Breast Invasive Carcinoma (TCGA, PanCancer Atlas)

"""
import matplotlib.pyplot as plt

import heatgraphy as hg
from oncoprinter import OncoPrint

# %%
# Load data


onco_data = hg.load_data('oncoprint')
cna = onco_data['cna']
mrna_exp = onco_data['mrna_exp']
methyl_exp = onco_data['methyl_exp']
clinical = onco_data['clinical']

# %%
# Make mRNA expression


h = hg.Heatmap(mrna_exp, cmap="gist_heat_r", height=.9, width=5,
               cbar_kws=dict(orientation="horizontal",
                             title="mRNA Expression"))
h.add_title(top="mRNA expression Z-SCORE", align="left", pad=.1, fontsize=10)
h.add_pad("top", size=.1)
h.add_left(hg.plotter.Labels(mrna_exp.index), pad=.1)

# %%
# Make Methylation expression


m = hg.Heatmap(methyl_exp.astype(float), height=.6, width=5, cmap="summer_r",
               cbar_kws=dict(orientation="horizontal",
                             title="Methylation"))
m.add_title(top="Methylation", align="left", pad=.1, fontsize=10)
m.add_pad("top", size=.1)
m.add_left(hg.plotter.Labels(methyl_exp.index), pad=.1)

# %%
# Create Oncoprint


op = OncoPrint(cna, name="main", legend_kws=dict(title="Alteration"))

# %%
# Make clinical information


clinical = clinical[op.patients_order]
tumor_type = clinical.loc['Cancer Type Detailed']
tumor_colors = hg.plotter.Colors(tumor_type, label="Tumor Type",
                                 label_loc="left")

mut_count = clinical.loc['Mutation Count']
mut_number = hg.plotter.Numbers(mut_count, show_value=False, color="orange")

# %%
# Add clinical to the oncoprint


op.canvas.add_bottom(tumor_colors, size=.2, pad=.1)
op.canvas.add_bottom(mut_number, size=.2, name="mutation_count", pad=.1,
                     legend=False)

# %%
# Add expression to the oncoprint

op.canvas /= h
op.canvas /= m

# %%
# Render


op.canvas.add_legends(box_padding=2, stack_size=4)
op.canvas.render()
mut_ax = op.canvas.get_ax("main", "mutation_count")
mut_ax.set_axis_off()
mut_ax.text(0, .5, "Mutation Count", rotation=0, ha="right",
            va="center", transform=mut_ax.transAxes)
plt.show()
