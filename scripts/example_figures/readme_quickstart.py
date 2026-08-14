"""Render the README quickstart snippet into img/quickstart{,-dark}.png."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import marsilea as ma
import marsilea.plotter as mp

save_path = Path(__file__).parents[2] / "img"
# GitHub's dark theme canvas, so the figure blends into the README.
DARK_BG = "#0d1117"


def build(dendrogram_color=None):
    """The README snippet, verbatim except for the dendrogram color."""
    data = np.random.default_rng(0).standard_normal((10, 10))

    h = ma.Heatmap(data, linewidth=0.5, height=4, width=4)
    h.add_top(mp.Bar(data.mean(axis=0)), size=0.8, pad=0.1)
    h.add_left(mp.Labels([f"Gene{i}" for i in range(10)]), pad=0.05)
    # ponytail: Dendrogram hardcodes ".1", so dark_background alone
    # would draw it invisible against the dark canvas.
    h.add_dendrogram("right", colors=dendrogram_color, meta_color=dendrogram_color)
    h.add_legends()
    return h.render()


if __name__ == "__main__":
    build().save(save_path / "quickstart.png", dpi=150, facecolor="white")

    # dark_background paints axes pure black, which shows up as a patch
    # against the figure canvas; repaint both with the canvas color.
    dark = ["dark_background", {"axes.facecolor": DARK_BG, "figure.facecolor": DARK_BG}]
    with plt.style.context(dark):
        build(dendrogram_color=".9").save(
            save_path / "quickstart-dark.png", dpi=150, facecolor=DARK_BG
        )
