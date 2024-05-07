"""
Sequence Alignment Plot
=======================
"""
from collections import Counter
import numpy as np
import pandas as pd

import marsilea as ma
import matplotlib as mpl
import matplotlib.pyplot as plt

# sphinx_gallery_start_ignore
import mpl_fontkit as fk

fk.install("Roboto Mono", verbose=False)

mpl.rcParams["font.size"] = 10
# sphinx_gallery_end_ignore

# %%
# Load data
# ---------
seq = ma.load_data("seq_align")
seq = seq.iloc[:, 135:155]

species = [
    "PH4H_Homo_sapiens",
    "PH4H_Mus_musculus",
    # 'PH4H_Rattus_norvegicus',
    # 'PH4H_Bos_taurus',
    "PH4H_Chromobacterium_violaceum",
    "PH4H_Ralstonia_solanacearum",
    # 'PH4H_Caulobacter_crescentus',
    "PH4H_Pseudomonas_aeruginosa",
    "PH4H_Rhizobium_loti",
]
seq = seq.loc[species]

# %%
# Calculate the height of each amino acid.
# See https://en.wikipedia.org/wiki/Sequence_logo

collect = []
for _, col in seq.items():
    collect.append(Counter(col))

hm = pd.DataFrame(collect)
del hm["-"]
hm = hm.T.fillna(0.0)
hm.columns = seq.columns
hm /= hm.sum(axis=0)

n = hm.shape[1]
s = 20
En = (1 / np.log(2)) * ((s - 1) / (2 * n))

heights = []
for _, col in hm.items():
    H = -(np.log2(col) * col).sum()
    R = np.log2(20) - (H + En)
    heights.append(col * R)

logo = pd.DataFrame(heights).T

# %%
# Prepare color palette and data
# ------------------------------

color_encode = {
    "A": "#f76ab4",
    "C": "#ff7f00",
    "D": "#e41a1c",
    "E": "#e41a1c",
    "F": "#84380b",
    "G": "#f76ab4",
    "H": "#3c58e5",
    "I": "#12ab0d",
    "K": "#3c58e5",
    "L": "#12ab0d",
    "M": "#12ab0d",
    "N": "#972aa8",
    "P": "#12ab0d",
    "Q": "#972aa8",
    "R": "#3c58e5",
    "S": "#ff7f00",
    "T": "#ff7f00",
    "V": "#12ab0d",
    "W": "#84380b",
    "Y": "#84380b",
    "-": "white",
}

max_aa = []
freq = []

for _, col in hm.items():
    ix = np.argmax(col)
    max_aa.append(hm.index[ix])
    freq.append(col[ix])

position = []
mock_ticks = []
for i in seq.columns:
    if int(i) % 10 == 0:
        position.append(i)
        mock_ticks.append("^")
    else:
        position.append("")
        mock_ticks.append("")

# %%
# Plot
# ----

height = 1.3
width = height * seq.shape[1] / seq.shape[0]

ch = ma.CatHeatmap(seq.to_numpy(), palette=color_encode, height=height, width=width)
seq_text = seq.to_numpy()
ch.add_layer(ma.plotter.TextMesh(seq_text, color="white"))
gap_text = seq_text.copy()
gap_text[np.where(gap_text != "-")] = " "
ch.add_layer(ma.plotter.TextMesh(gap_text, color="black"))
ch.add_top(ma.plotter.SeqLogo(logo, color_encode=color_encode), pad=0.05, size=0.5)
ch.add_right(ma.plotter.Labels(seq.index.str.slice(5)), pad=0.05)
ch.add_bottom(ma.plotter.Labels(mock_ticks, rotation=0))
ch.add_bottom(ma.plotter.Labels(position, rotation=0))
ch.add_bottom(
    ma.plotter.Numbers(freq, width=0.9, color="#FFB11B", show_value=False),
    name="freq_bar",
    size=0.4,
)
ch.add_bottom(ma.plotter.Labels(max_aa, rotation=0), pad=0.05)
ch.render()

ch.get_ax("freq_bar").set_axis_off()

# sphinx_gallery_start_ignore
if "__file__" in globals():
    from pathlib import Path

    save_path = Path(__file__).parent / "figures"
    mpl.rcParams["svg.fonttype"] = "none"
    plt.savefig(save_path / "msa.svg", bbox_inches="tight")
else:
    plt.show()
# sphinx_gallery_end_ignore
