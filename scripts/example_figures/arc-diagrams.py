"""
Les Miserables Arc Diagram
===============================

This example shows how to create an arc diagram from a network.

"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import networkx as nx

import marsilea as ma
import marsilea.plotter as mp

# sphinx_gallery_start_ignore
import mpl_fontkit as fk

fk.install("Lato", verbose=False)
# sphinx_gallery_end_ignore

# %%
# Create Arc Diagram
# ------------------

data = pd.read_csv("data/PPI.csv")
G = nx.from_pandas_edgelist(data, "source", "target", create_using=nx.DiGraph)

protein_classification = {
    "MAP Kinases": [
        "MAP2K7",
        "RPS6KA3",
        "MAPK7",
        "RPS6KB1",
        "MAPKAPK5",
        "RPS6KB2",
        "JUN",
        "RPS6KA1",
        "MAPK10",
        "MAPK1",
        "MAPK14",
        "MAPK3",
        "MAP2K1",
        "MAPK12",
        "MAP2K4",
        "MAPK9",
        "MAPK8",
    ],
    "Kinases": [
        "CSNK2A1",
        "GSK3B",
        "CSNK1A1",
        "PRKACA",
        "SYK",
        "JAK2",
        "GSK3A",
        "PRKCA",
        "CDK1",
        "ITK",
        "ELK1",
        "LYN",
        "PRKCD",
        "CDK4",
        "PLK1",
        "PAK1",
        "CDK7",
        "LCK",
        "CDK5",
        "MAPK8",
        "GRK2",
        "AURKB",
        "PRKCQ",
        "CDC25C",
        "CHEK2",
        "CDK7",
        "TP53",
    ],
    "Transcription Factors": ["NFKBIA", "MEF2A", "ESR1", "CREB1", "NFATC4"],
    "Tyrosine Kinases": [
        "HCLS1",
        "FCGR2A",
        "BTK",
        "SYK",
        "HCK",
        "PTK2B",
        "LCK",
        "FYN",
        "ZAP70",
    ],
    "Adaptor Proteins": ["IRS1", "CBL", "SHC1", "GRB2"],
    "Ubiquitin Ligases": ["MDM2", "CBL"],
    "Cell Structure/Signaling": [
        "STK11",
        "FGFR1",
        "CSK",
        "ILK",
        "CTTN",
        "SNCA",
        "KRT8",
    ],
    "Other": ["HNRNPK"],
}


colormap = {
    "MAP Kinases": "#E2DFD0",
    "Kinases": "#CA8787",
    "Transcription Factors": "#E65C19",
    "Tyrosine Kinases": "#F8D082",
    "Adaptor Proteins": "#0A6847",
    "Ubiquitin Ligases": "#7ABA78",
    "Cell Structure/Signaling": "#03AED2",
    "Other": ".7",
}

# Reverse mapping to get labels for each protein
protein_labels = {}
for label, proteins in protein_classification.items():
    for protein in proteins:
        protein_labels[protein] = label

nodes = list(G.nodes)
nodes = pd.DataFrame(
    {"nodes": nodes, "type": [protein_labels[n] for n in nodes]}
).sort_values("type")["nodes"]

degs = nx.degree(G)
degree_arr = np.array([[degs[n] for n in nodes]])
color_arr = np.array([[protein_labels[n] for n in nodes]])

edges = list(G.edges)
edges_colors = [colormap[protein_labels[a]] for a, _ in edges]

sources = set([a for a, _ in edges])
is_sources = np.array([["*" if n in sources else "" for n in nodes]])

wb = ma.SizedHeatmap(
    degree_arr,
    color_arr,
    palette=colormap,
    sizes=(10, 300),
    frameon=False,
    width=10.5,
    height=0.3,
    size_legend_kws={"func": lambda x: [int(i) for i in x], "title": "Count"},
    color_legend_kws={"title": "Protein Type"},
)
wb.add_bottom(mp.Labels(nodes, align="bottom"))
wb.add_bottom(mp.Labels(is_sources, fontsize=16))
arc = mp.Arc(nodes, edges, colors=edges_colors, lw=1, alpha=0.5)
wb.add_top(arc, size=2)
wb.add_legends(stack_size=1)
wb.render()

# sphinx_gallery_start_ignore
if "__file__" in globals():
    from pathlib import Path

    save_path = Path(__file__).parent / "figures"
    wb.save(save_path / "arc_diagram.svg")
else:
    plt.show()
# sphinx_gallery_end_ignore
