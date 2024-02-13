import marsilea as ma
import mpl_fontkit as fk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from scipy.cluster.hierarchy import linkage, dendrogram

# Install fonts
fk.install_fontawesome(verbose=False)
fk.install("Lato", verbose=False)

# Constants
COLORS = {
    "red": "#cd442a",
    "yellow": "#f0bd00",
    "green": "#7e9437",
    "gray": "#eee",
    "trans_fat": "#3A98B9",
    "omega3": "#F5E9CF",
    "omega6": "#7DB9B6",
    "background": ["#e5e7eb", "#c2410c", "#fb923c", "#fca5a5", "#fecaca"],
}
FAT_CONTENTS = [
    "saturated",
    "polyunsaturated (omega 3 & 6)",
    "monounsaturated",
    "other fat",
]
FLAVOUR_MAPPER = {0: "\uf58a", 1: "\uf11a", 2: "\uf567"}
COLOUR_MAPPER = {0: "#609966", 1: "#DC8449", 2: "#F16767"}
COOKING_CONDITIONS = [
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

# Load data
oils = ma.load_data("cooking_oils")


def plot_dendrogram(ax, group_data, c):
    """Plot dendrogram on given axes."""
    if group_data.shape[0] > 1:
        Z = linkage(group_data[FAT_CONTENTS], method="single", metric="euclidean")
        dendrogram(Z, ax=ax, orientation="left")
        return dendrogram(Z, ax=ax, orientation="left", link_color_func=lambda k: c)[
            "leaves"
        ]
    return list(range(group_data.shape[0]))


def plot_group(axs, df, group_title, color):
    """Plot each group's data."""
    # Reorder based on dendrogram (if applicable)
    reorder_index = plot_dendrogram(axs[0], df, color)
    df = df.iloc[reorder_index, :]

    # Background and Group Title
    axs[1].add_patch(Rectangle((0, 0), 1, 1, color=color, transform=axs[1].transAxes))
    axs[1].text(
        0.9, 0.5, group_title, ha="right", va="center", transform=axs[1].transAxes
    )

    # Plot Trans Fat
    trans_fat = df["trans fat"] * 100
    bars = axs[2].barh(trans_fat.index, trans_fat, color=COLORS["trans_fat"])
    axs[2].bar_label(
        bars, labels=[f"{x:.1f}" if x > 0 else "" for x in trans_fat], padding=3
    )
    axs[2].invert_xaxis()

    # Plot Fat Contents
    fat_data = df[FAT_CONTENTS].to_numpy()
    fat_data_cum = np.cumsum(fat_data, axis=1)
    for i, (content, color) in enumerate(
        zip(
            FAT_CONTENTS,
            [COLORS["red"], COLORS["yellow"], COLORS["green"], COLORS["gray"]],
        )
    ):
        starts = fat_data_cum[:, i] - fat_data[:, i]
        axs[3].barh(y=range(len(df)), width=fat_data[:, i], left=starts, color=color)

    # Plot Flavor
    for idx, (oil_name, flavor, color) in enumerate(
        zip(
            df.index.str.capitalize(),
            df["flavour"].map(FLAVOUR_MAPPER),
            df["flavour"].map(COLOUR_MAPPER),
        )
    ):
        loc = idx / len(df) + 0.5 / len(df)
        axs[4].text(
            0.5,
            loc,
            flavor,
            ha="center",
            va="center",
            fontfamily="Font Awesome 6 Free",
            color=color,
        )
        axs[5].text(
            0, loc, oil_name, ha="left", va="center", transform=axs[5].transAxes
        )

    # Plot Omega-3 and Omega-6
    omega3 = -df["omega 3"] * 100
    omega6 = df["omega 6"] * 100
    ax = axs[6]
    bar_o3 = ax.barh(y=range(len(df)), width=omega3, color=COLORS["omega3"])
    ax.bar_label(
        bar_o3,
        labels=[f"{abs(x):.0f}" if abs(x) > 0 else "" for x in omega3],
        label_type="edge",
        padding=3,
    )
    bar_o6 = ax.barh(y=range(len(df)), width=omega6, left=0, color=COLORS["omega6"])
    ax.bar_label(
        bar_o6,
        labels=[f"{x:.0f}" if x > 0 else "" for x in omega6],
        label_type="edge",
        padding=3,
    )
    lim = (
        max(max(abs(omega3)), max(omega6)) * 1.1
    )  # Ensure some space around the largest bar
    ax.set_xlim(-lim, lim)
    ax.axvline(0, color="black", lw=1)


# Plot setup
fig, axes = plt.subplots(
    nrows=5,
    ncols=7,
    figsize=(11, 12),
    dpi=250,
    gridspec_kw={
        "height_ratios": [
            len(oils.groupby("cooking conditions").get_group(k))
            for k in COOKING_CONDITIONS
        ],
        "width_ratios": [0.5, 1, 1, 3, 0.2, 1.5, 1.5],
        "hspace": 0.04,
    },
)

for ax in axes.flat:
    ax.set_axis_off()

# Plotting
for i, (condition, group_axes, bg_color) in enumerate(
    zip(COOKING_CONDITIONS, axes, COLORS["background"])
):
    group_data = oils[oils["cooking conditions"] == condition]
    gt = keys_text[i]
    plot_group(group_axes, group_data, gt, bg_color)

# Adjustments (like axis limits, labels, legends) would go here
for ax in axes[:, 2]:
    ax.set_xlim(4.2, 0)
for ax in axes[:, -1]:
    ax.set_xlim(-75, 75)


def turn_on_x_axis(ax, xlabel):
    ax.set_axis_on()
    ax.set_xlabel(xlabel)
    ax.tick_params(
        left=False,
        top=False,
        right=False,
        labelleft=False,
        labeltop=False,
        labelright=False,
    )
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)


turn_on_x_axis(axes[-1, 2], "Trans Fat (%)")
turn_on_x_axis(axes[-1, 3], "Fat Content (%)")
turn_on_x_axis(axes[-1, -1], "")


axes[0, 3].set_title("Fat in cooking oils")
axes[-1, 2].set_xlabel("Trans Fat (%)")
axes[-1, 3].set_xlabel("Fat Content (%)")
ax = axes[0, -1]
ax.text(0.45, 1, "Omega 3 (%)", ha="right", va="bottom", transform=ax.transAxes)
ax.text(0.55, 1, "Omega 6 (%)", ha="left", va="bottom", transform=ax.transAxes)

ax = axes[-1, 3]
handles = []
labels = []

for fat, c in zip(
    [
        "saturated",
        "polyunsaturated (omega 3 & 6)",
        "monounsaturated",
        "other fat",
    ],
    [COLORS["red"], COLORS["yellow"], COLORS["green"], COLORS["gray"]],
):
    handles.append(Patch(color=c))
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
