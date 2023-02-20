from pathlib import Path

import matplotlib.pyplot as plt
import mpl_fontkit as fk
import numpy as np
import pandas as pd

import heatgraphy as hg
from heatgraphy.plotter import SizedMesh
from heatgraphy.upset import UpsetData, Upset
from oncoprinter import OncoPrint

SAVE_PATH = Path(__file__).parent.parent.parent / 'img' / 'publication'
SAVE_PATH.mkdir(exist_ok=True)
fk.install('Lato')

if __name__ == "__main__":
    onco_data = hg.load_data('oncoprint')
    cna = onco_data['cna']
    mrna_exp = onco_data['mrna_exp']
    methyl_exp = onco_data['methyl_exp']
    clinical = onco_data['clinical']

    h = hg.Heatmap(mrna_exp, cmap="gist_heat_r", height=.9, width=5,
                   cbar_kws=dict(orientation="horizontal",
                                 title="mRNA Expression"))
    h.add_title(top="mRNA expression Z-SCORE", align="left", pad=.1,
                fontsize=10)
    h.add_pad("top", size=.1)
    h.add_left(hg.plotter.Labels(mrna_exp.index), pad=.1)

    m = hg.Heatmap(methyl_exp.astype(float), height=.6, width=5,
                   cmap="summer_r",
                   cbar_kws=dict(orientation="horizontal",
                                 title="Methylation"))
    m.add_title(top="Methylation", align="left", pad=.1, fontsize=10)
    m.add_pad("top", size=.1)
    m.add_left(hg.plotter.Labels(methyl_exp.index), pad=.1)

    op = OncoPrint(cna, name="main", legend_kws=dict(title="Alteration"))

    clinical = clinical[op.patients_order]
    tumor_type = clinical.loc['Cancer Type Detailed']
    tumor_colors = hg.plotter.Colors(tumor_type, label="Tumor Type",
                                     label_loc="left")

    mut_count = clinical.loc['Mutation Count']
    mut_number = hg.plotter.Numbers(mut_count, show_value=False,
                                    color="orange")

    op.canvas.add_bottom(tumor_colors, size=.2, pad=.1)
    op.canvas.add_bottom(mut_number, size=.2, name="mutation_count", pad=.1,
                         legend=False)

    op.canvas /= h
    op.canvas /= m

    op.canvas.add_legends(box_padding=2, stack_size=4)
    op.canvas.render()
    mut_ax = op.canvas.get_ax("main", "mutation_count")
    mut_ax.set_axis_off()
    mut_ax.text(0, .5, "Mutation Count", rotation=0, ha="right",
                va="center", transform=mut_ax.transAxes)
    plt.savefig(SAVE_PATH / "oncoprint.png", dpi=300)
