# %%
from pathlib import Path

import matplotlib.pyplot as plt
import mpl_fontkit as fk
import numpy as np
import pandas as pd
import pyBigWig

fk.install("Lato")

import marsilea as ma
import marsilea.plotter as mp

# Please downlaod data from https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE137105
bws = [i for i in Path("data/GSE137105_RAW/").glob("*.bw")]

MYC_START = 127734550
MYC_END = 127744631

pdata = []
for bw in bws:
    names = bw.stem.split("_")
    bw = pyBigWig.open(str(bw))
    # Gene location of MYC
    c = bw.intervals("chr8", MYC_START, MYC_END)
    vs = np.array([i[2] for i in c])
    pdata.append({"cond": names[1], "enz": names[2], "track": vs})

pdata = pd.DataFrame(pdata)
pdata["enz"] = pdata["enz"].replace("INPUT", "Background")
pdata = pdata.sort_values(["enz", "cond"]).reset_index(drop=True)


# %%
def add_gene_structure(ax):
    import re
    from matplotlib.lines import Line2D

    myc_structure = pd.read_csv("data/MYC.GFF3", sep="\t", comment="#", header=None)
    myc_structure = myc_structure[myc_structure[2] == "exon"]

    def extract_id(text):
        return re.search(r"ID=exon-(.*?)-", text).group(1)

    myc_structure["id"] = myc_structure[8].apply(extract_id)

    # Skeleton
    # _, ax = plt.subplots(figsize=(5, 1))
    ranges = myc_structure[[3, 4]]
    rmin, rmax = np.min(ranges), np.max(ranges)
    ske = Line2D([rmin, rmax], [0, 0], linewidth=1, color="k")
    ax.add_artist(ske)

    colors = ["#AF8260", "#E4C59E"]
    ix = 0
    for _, df in myc_structure.groupby("id"):
        for _, row in df.iterrows():
            start, end = row[3], row[4]
            e = Line2D([start, end], [0, 0], linewidth=10, color=colors[ix])
            ax.add_artist(e)
        ix += 1

    ax.set_xlim(MYC_START, MYC_END)
    ax.set_ylim(-1, 1)
    ax.set_axis_off()


# %%
colors = {
    "H3K9me1": "#DD6E42",
    "H3K9me2": "#E8DAB2",
    "H3K9me3": "#4F6D7A",
    "Background": "#C0D6DF",
}

lims = {
    "H3K9me1": 20,
    "H3K9me2": 35,
    "H3K9me3": 35,
    "Background": 20,
}

TRACK_HEIGHT = 0.5
TRACK_PAD = 0.1
myc_track = ma.ZeroHeight(4.5, name="myc")

for _, row in pdata.iterrows():
    track = row["track"]
    name = f"{row['cond']}{row['enz']}"
    color = colors[row["enz"]]
    myc_track.add_bottom(
        mp.Area(track, color=color, add_outline=False, alpha=1),
        size=TRACK_HEIGHT,
        pad=TRACK_PAD,
        name=name,
    )

myc_track.add_canvas("bottom", name="gene", size=0.2, pad=0.1)
myc_track.add_title(bottom="MYC")

cond_canvas = ma.ZeroHeight(0.8)
for cond in pdata["cond"]:
    cond_canvas.add_bottom(
        mp.Title(cond, align="left"), size=TRACK_HEIGHT, pad=TRACK_PAD
    )

enz_canvas = ma.ZeroHeight(1, name="enz")
for enz in pdata["enz"].drop_duplicates():
    enz_canvas.add_bottom(
        mp.Title(f"‎ ‎ {enz}", align="left"),
        size=TRACK_HEIGHT * 2,
        pad=TRACK_PAD * 2,
        name=enz,
    )

comp = myc_track + 0.1 + cond_canvas + enz_canvas
comp.render()

# Add a line for enz
for enz in pdata["enz"].drop_duplicates():
    ax = comp.get_ax("enz", enz)
    ax.axvline(x=0, color="k", lw=4)

for _, row in pdata.iterrows():
    name = f"{row['cond']}{row['enz']}"
    lim = lims[row["enz"]]
    ax = comp.get_ax("myc", name)
    ax.set_ylim(0, lim)
    ax.set_yticks([lim])

# Add gene structure
ax = comp.get_ax("myc", "gene")
add_gene_structure(ax)

if "__file__" in globals():
    save_path = Path(__file__).parent / "figures"
    plt.rcParams["svg.fonttype"] = "none"
    plt.savefig(save_path / "tracks.svg", bbox_inches="tight", facecolor="none")
else:
    plt.show()
