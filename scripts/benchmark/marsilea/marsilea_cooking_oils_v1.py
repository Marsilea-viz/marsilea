# Improved version for clarity and modularity

# Import libraries
from matplotlib import pyplot as plt
import marsilea as ma
import marsilea.plotter as mp
import mpl_fontkit as fk

# Install fonts
fk.install_fontawesome(verbose=False)
fk.install("Lato", verbose=False)

# Load data
oils = ma.load_data("cooking_oils")

# Define constants
COLORS = {"red": "#cd442a", "yellow": "#f0bd00", "green": "#7e9437", "gray": "#eee"}
CMAPPER = {0: "#609966", 1: "#DC8449", 2: "#F16767"}
MAPPER = {0: "\uf58a", 1: "\uf11a", 2: "\uf567"}

# Process data
flavour = oils["flavour"].map(lambda x: MAPPER[x])
flavour_colors = oils["flavour"].map(lambda x: CMAPPER[x])
fat_content = oils[
    ["saturated", "polyunsaturated (omega 3 & 6)", "monounsaturated", "other fat"]
]


# Plot configuration
# Create stack bar for fat content
contents = mp.StackBar(
    fat_content.T * 100,
    colors=[COLORS["red"], COLORS["yellow"], COLORS["green"], COLORS["gray"]],
    width=0.8,
    orient="h",
    label="Fat Content (%)",
    legend_kws={"ncol": 2, "fontsize": 10},
)

# Create numbers for trans fat
trans_fat = mp.Numbers(
    oils["trans fat"] * 100,
    fmt=lambda x: f"{x:.1f}" if x > 0 else "",
    label="Trans Fat (%)",
    color="#3A98B9",
)

# Create center bar for omega comparison
o3vso6 = mp.CenterBar(
    (oils[["omega 3", "omega 6"]] * 100).astype(int),
    names=["Omega 3 (%)", "Omega 6 (%)"],
    colors=["#7DB9B6", "#F5E9CF"],
    fmt=lambda x: f"{int(x)}" if x > 0 else "",
    show_value=True,
)

# Create chunk for temperature control
chunk_text = [
    "Control",
    ">230 °C\nDeep-frying",
    "200-229 °C\nStir-frying",
    "150-199 °C\nLight saute",
    "<150 °C\nDressings",
]
colors = ["#e5e7eb", "#c2410c", "#fb923c", "#fca5a5", "#fecaca"]
title = mp.Chunk(chunk_text, colors, rotation=0, padding=10)

# Initialize and configure ClusterBoard
cb = ma.ClusterBoard(fat_content.to_numpy(), height=10)
cb.add_layer(contents)
cb.add_left(trans_fat, pad=0.2, name="trans fat")
cb.add_right(
    mp.Labels(
        flavour,
        fontfamily="Font Awesome 6 Free",
        text_props={"color": flavour_colors},
    )
)
cb.add_right(mp.Labels(oils.index.str.capitalize()), pad=0.1)
cb.add_right(o3vso6, size=2, pad=0.2)

# Configure sections and dendrogram
order = [
    "Control",
    ">230 °C (Deep-frying)",
    "200-229 °C (Stir-frying)",
    "150-199 °C (Light saute)",
    "<150 °C (Dressings)",
]
cb.hsplit(labels=oils["cooking conditions"], order=order)
cb.add_left(title, pad=0.1)
cb.add_dendrogram(
    "left", add_meta=False, colors=colors, linewidth=1.5, size=0.5, pad=0.02
)
cb.add_title(top="Fat in Cooking Oils", fontsize=16)
cb.add_legends("bottom", pad=0.3)
cb.render()

# Adjust axes for trans fat
axes = cb.get_ax("trans fat")
for ax in axes:
    ax.set_xlim(4.2, 0)

# Display plot
plt.show()
