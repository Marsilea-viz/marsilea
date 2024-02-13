import marsilea as ma
import mpl_fontkit as fk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.cluster.hierarchy import linkage, dendrogram


class CookingOilVisualizer:
    def __init__(self, data_path):
        # Constants
        self.COLORS = {
            "red": "#cd442a",
            "yellow": "#f0bd00",
            "green": "#7e9437",
            "gray": "#eee",
            "trans_fat": "#3A98B9",
            "omega3": "#F5E9CF",
            "omega6": "#7DB9B6",
            "background": ["#e5e7eb", "#c2410c", "#fb923c", "#fca5a5", "#fecaca"],
        }
        self.FAT_CONTENTS = [
            "saturated",
            "polyunsaturated (omega 3 & 6)",
            "monounsaturated",
            "other fat",
        ]
        self.FLAVOUR_MAPPER = {0: "\uf58a", 1: "\uf11a", 2: "\uf567"}
        self.COLOUR_MAPPER = {0: "#609966", 1: "#DC8449", 2: "#F16767"}
        self.COOKING_CONDITIONS = [
            "<150 °C (Dressings)",
            "150-199 °C (Light saute)",
            "200-229 °C (Stir-frying)",
            ">230 °C (Deep-frying)",
            "Control",
        ][::-1]
        self.keys_text = [
            "Control",
            ">230 °C\nDeep-frying",
            "200-229 °C\nStir-frying",
            "150-199 °C\nLight saute",
            "<150 °C\nDressings",
        ]

        # Install fonts
        fk.install_fontawesome(verbose=False)
        fk.install("Lato", verbose=False)

        # Load data
        self.oils = ma.load_data(data_path)

    def plot_dendrogram(self, ax, group_data, c):
        """Plot dendrogram on given axes."""
        if group_data.shape[0] > 1:
            Z = linkage(
                group_data[self.FAT_CONTENTS], method="single", metric="euclidean"
            )
            dendrogram(Z, ax=ax, orientation="left")
            return dendrogram(
                Z, ax=ax, orientation="left", link_color_func=lambda k: c
            )["leaves"]
        return list(range(group_data.shape[0]))

    def plot_group(self, axs, df, group_title, color):
        """Plot each group's data."""
        reorder_index = self.plot_dendrogram(axs[0], df, color)
        df = df.iloc[reorder_index, :]

        # Background and Group Title
        axs[1].add_patch(
            Rectangle((0, 0), 1, 1, color=color, transform=axs[1].transAxes)
        )
        axs[1].text(
            0.9, 0.5, group_title, ha="right", va="center", transform=axs[1].transAxes
        )
        return df

    def plot_trans_fat(self, ax, df):
        bar = ax.barh(df["trans fat"].index, df["trans fat"] * 100, color="#3A98B9")
        ax.bar_label(bar, padding=-15, fmt=lambda x: f"{x:.1f}" if x > 0 else "")
        ax.invert_xaxis()

    def plot_fat_contents(self, ax, df):
        labels = df.index
        fat_data = df[self.FAT_CONTENTS].to_numpy()
        fat_data_cum = fat_data.cumsum(axis=1)
        for i, (fat, c) in enumerate(
            zip(
                self.FAT_CONTENTS,
                [
                    self.COLORS["red"],
                    self.COLORS["yellow"],
                    self.COLORS["green"],
                    self.COLORS["gray"],
                ],
            )
        ):
            widths = fat_data[:, i]
            starts = fat_data_cum[:, i] - widths
            ax.barh(labels, widths, left=starts, color=c)

    def plot_flavor(self, ax, df):
        flavour = df["flavour"].map(self.FLAVOUR_MAPPER).values
        flavour_colors = df["flavour"].map(self.COLOUR_MAPPER).values
        text_loc = np.linspace(0, 1, len(flavour) + 2)[1:-1]
        for text, loc, c in zip(flavour, text_loc, flavour_colors):
            ax.text(
                0.5,
                loc,
                text,
                ha="center",
                va="center",
                fontfamily="Font Awesome 6 Free",
                color=c,
            )

    def plot_oil_names(self, ax, df):
        for idx, oil_name in enumerate(df.index.str.capitalize()):
            loc = idx / len(df) + 0.5 / len(df)
            ax.text(0, loc, oil_name, ha="left", va="center", transform=ax.transAxes)

    def plot_omega3_6(self, ax, df):
        omega3 = -df["omega 3"] * 100
        omega6 = df["omega 6"] * 100
        fmt = lambda x: f"{int(x)}" if x > 0 else ""
        bar_omega3 = ax.barh(df.index, omega3, color=self.COLORS["omega3"])
        ax.bar_label(bar_omega3, labels=[fmt(-i) for i in omega3])
        bar_omega6 = ax.barh(df.index, omega6, color=self.COLORS["omega6"])
        ax.bar_label(bar_omega6, labels=[fmt(i) for i in omega6])
        lim = np.max(df[["omega 3", "omega 6"]] * 100)
        ax.set_xlim(-lim, lim)
        ax.axvline(0, 0, 1, color="k")

    def setup_and_plot(self):
        fig, axes = plt.subplots(
            nrows=5,
            ncols=7,
            figsize=(11, 12),
            dpi=250,
            gridspec_kw={
                "height_ratios": [
                    len(self.oils.groupby("cooking conditions").get_group(k))
                    for k in self.COOKING_CONDITIONS
                ],
                "width_ratios": [0.5, 1, 1, 3, 0.2, 1.5, 1.5],
                "hspace": 0.04,
            },
        )

        for ax in axes.flat:
            ax.set_axis_off()
        for ax in axes[4, [2, 3, 6]]:
            ax.set_axis_on()
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

        for i, (condition, group_axes, bg_color) in enumerate(
            zip(self.COOKING_CONDITIONS, axes, self.COLORS["background"])
        ):
            group_data = self.oils[self.oils["cooking conditions"] == condition]
            gt = self.keys_text[i]
            self.plot_group(group_axes, group_data, gt, bg_color)
            self.plot_trans_fat(group_axes[2], group_data)
            self.plot_fat_contents(group_axes[3], group_data)
            self.plot_flavor(group_axes[4], group_data)
            self.plot_oil_names(group_axes[5], group_data)
            self.plot_omega3_6(group_axes[6], group_data)

        # Additional plotting adjustments and legend setup
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
        for fat, c in zip(
            self.FAT_CONTENTS,
            [
                self.COLORS["red"],
                self.COLORS["yellow"],
                self.COLORS["green"],
                self.COLORS["gray"],
            ],
        ):
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


# Usage
visualizer = CookingOilVisualizer(data_path="cooking_oils")
visualizer.setup_and_plot()
