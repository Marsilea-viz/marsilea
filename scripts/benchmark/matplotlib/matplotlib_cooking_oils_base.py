import marsilea as ma
import mpl_fontkit as fk
import numpy as np

fk.install_fontawesome(verbose=False)
fk.install("Lato", verbose=False)

# %%
# Load data
# ---------
oils = ma.load_data("cooking_oils")

red = "#cd442a"
yellow = "#f0bd00"
green = "#7e9437"
gray = "#eee"

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.cluster.hierarchy import linkage, dendrogram

groups = oils.groupby("cooking conditions")

keys = [
    "<150 °C (Dressings)",
    "150-199 °C (Light saute)",
    "200-229 °C (Stir-frying)",
    ">230 °C (Deep-frying)",
    "Control",
][::-1]
keys_text = [
    "Control",
    ">230 °C\nDeep-frying",
    "200-229 °C\nStir-frying",
    "150-199 °C\nLight saute",
    "<150 °C\nDressings",
]
fat_contents = [
    "saturated",
    "polyunsaturated (omega 3 & 6)",
    "monounsaturated",
    "other fat",
]

colors = ["#e5e7eb", "#c2410c", "#fb923c", "#fca5a5", "#fecaca"]

height_ratios = [len(groups.get_group(k)) for k in keys]
width_ratios = [0.5, 1, 1, 3, 0.2, 1.5, 1.5]

fig, axes = plt.subplots(
    nrows=5,
    ncols=7,
    figsize=(11, 12),
    dpi=250,
    gridspec_kw=dict(
        height_ratios=height_ratios, width_ratios=width_ratios, hspace=0.04
    ),
)

for irow, (group, axs, c, gt) in enumerate(zip(keys, axes, colors, keys_text)):
    if irow != 4:
        for ax in axs:
            ax.set_axis_off()
    else:
        for ix in [0, 1, 4, 5]:
            axs[ix].set_axis_off()
        for ix in [2, 3, 6]:
            axs[ix].tick_params(
                left=False,
                top=False,
                right=False,
                labelleft=False,
                labeltop=False,
                labelright=False,
            )
            axs[ix].spines["right"].set_visible(False)
            axs[ix].spines["left"].set_visible(False)
            axs[ix].spines["top"].set_visible(False)
    df = groups.get_group(group)

    # Add dendrogram
    if df.shape[0] > 1:
        Z = linkage(df[fat_contents], method="single", metric="euclidean")
        plot = dendrogram(Z, ax=axs[0], orientation="left", link_color_func=lambda k: c)

        reorder_index = plot["leaves"]
        df = df.iloc[reorder_index, :]

    # Add text and background
    bg = Rectangle((0, 0), 1, 1, transform=axs[1].transAxes, color=c)
    axs[1].add_artist(bg)
    axs[1].text(x=0.9, y=0.5, s=gt, ha="right", va="center")

    # Add transfat
    fmt = lambda x: f"{x:.1f}" if x > 0 else ""
    bar = axs[2].barh(df["trans fat"].index, df["trans fat"] * 100, color="#3A98B9")
    axs[2].bar_label(bar, padding=-15, fmt=fmt)
    axs[2].invert_xaxis()

    # Add fat contents
    labels = df.index
    fat_data = df[fat_contents].to_numpy()
    fat_data_cum = fat_data.cumsum(axis=1)
    for i, (fat, c) in enumerate(zip(fat_contents, [red, yellow, green, gray])):
        widths = fat_data[:, i]
        starts = fat_data_cum[:, i] - widths
        axs[3].barh(labels, widths, left=starts, color=c)

    # Add flavor
    mapper = {0: "\uf58a", 1: "\uf11a", 2: "\uf567"}
    cmapper = {0: "#609966", 1: "#DC8449", 2: "#F16767"}
    flavour = df["flavour"].map(mapper).values
    flavour_colors = df["flavour"].map(cmapper).values

    text_loc = np.linspace(0, 1, len(flavour) + 2)[1:-1]
    for text, loc, c in zip(flavour, text_loc, flavour_colors):
        axs[4].text(
            x=0.5,
            y=loc,
            s=text,
            ha="center",
            va="center",
            fontfamily="Font Awesome 6 Free",
            color=c,
            transform=axs[4].transAxes,
        )

    # Add Label
    for text, loc in zip(df.index.str.capitalize(), text_loc):
        axs[5].text(
            x=0, y=loc, s=text, ha="left", va="center", transform=axs[5].transAxes
        )

    # Add Omega3 and 6
    ax = axs[6]
    fmt = lambda x: f"{int(x)}" if x > 0 else ""
    bar_o3 = ax.barh(df["omega 3"].index, -df["omega 3"] * 100, color="#F5E9CF")
    labels = [fmt(i) for i in df["omega 3"] * 100]
    ax.bar_label(bar_o3, labels=labels)
    bar_o6 = ax.barh(df["omega 6"].index, df["omega 6"] * 100, color="#7DB9B6")
    labels = [fmt(i) for i in df["omega 6"] * 100]
    ax.bar_label(bar_o6, labels=labels)
    lim = np.max(df[["omega 3", "omega 6"]] * 100)
    ax.set_xlim(-lim, lim)
    ax.axvline(0, 0, 1, color="k")

# Unify the limit

for ax in axes[:, 2]:
    ax.set_xlim(4.2, 0)
for ax in axes[:, -1]:
    ax.set_xlim(-75, 75)

axes[0, 3].set_title("Fat in cooking oils")
axes[-1, 2].set_xlabel("Trans Fat (%)")
axes[-1, 3].set_xlabel("Fat Content (%)")

ax = axes[0, -1]
ax.text(0.45, 1, "Omega 3 (%)", ha="right", va="bottom", transform=ax.transAxes)
ax.text(0.55, 1, "Omega 6 (%)", ha="left", va="bottom", transform=ax.transAxes)

ax = axes[-1, 3]
handles = []
labels = []
for fat, c in zip(fat_contents, [red, yellow, green, gray]):
    handles.append(Rectangle((0, 0), 1, 1, color=c))
    labels.append(fat)
ax.legend(
    handles=handles,
    labels=labels,
    title="Fat Content (%)",
    ncol=2,
    alignment="left",
    title_fontproperties=dict(weight=600),
    bbox_to_anchor=(0.5, -0.5),
    bbox_transform=ax.transAxes,
    loc="upper center",
)

plt.show()
