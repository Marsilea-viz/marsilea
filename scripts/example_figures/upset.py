"""
Upset plot of overlap genes in KEGG cancer pathway
"""
# %%
from pathlib import Path
import matplotlib.pyplot as plt
import mpl_fontkit as fk

fk.install("Lato")
plt.rcParams["svg.fonttype"] = "none"

import httpx
from marsilea.upset import UpsetData, Upset

# KEGG hsa_id and the name
paths = {
    "05210": "Colorectal cancer",
    "05212": "Pancreatic cancer",
    "05226": "Gastric cancer",
    "05219": "Bladder cancer",
    "05215": "Prostate cancer",
    "05224": "Breast cancer",
    # '05222': 'Small cell lung cancer',
    # '05223': 'Non-small cell lung cancer'
}

pathway_genes = {}

for hsa_id, name in paths.items():
    r = httpx.get(f"https://rest.kegg.jp/link/hsa/hsa{hsa_id}")
    genes = [i.split("\t")[1] for i in r.text.strip().split("\n")]
    pathway_genes[paths[hsa_id]] = genes

# %%
upset_data = UpsetData.from_sets(
    pathway_genes, sets_names=[paths[k] for k in paths.keys()]
)
us = Upset(
    upset_data,
    radius=35,
    linewidth=1,
    min_cardinality=4,
    size_scale=0.23,
    add_intersections=False,
    add_sets_size=False,
)
us.add_intersections("top", size=0.4, pad=0.1)
us.add_sets_size("left", size=0.4, pad=0.1)
us.highlight_subsets("Breast cancer", facecolor="#319DA0")
# us.save("scripts/example_figures/figures/upset.svg")

if "__file__" in globals():
    us.save(Path(__file__).parent / "figures" / "upset.svg")
else:
    us.render()
    plt.show()
