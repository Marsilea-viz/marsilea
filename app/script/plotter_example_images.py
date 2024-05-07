from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np
import seaborn as sns

from marsilea.plotter import (
    Bar,
    Box,
    Boxen,
    Strip,
    Point,
    Violin,
    AnnoLabels,
    Colors,
    Swarm,
)
from marsilea.dendrogram import Dendrogram


def close_ticks(ax):
    ax.tick_params(
        bottom=False,
        top=False,
        left=False,
        right=False,
        labelbottom=False,
        labeltop=False,
        labelleft=False,
        labelright=False,
    )
    sns.despine(ax=ax, left=True, bottom=True)


if __name__ == "__main__":
    np.random.seed(0)
    save_folder = Path(__file__).parent.parent / "img"
    rcParams["figure.figsize"] = (1, 1)
    rcParams["savefig.bbox"] = "tight"
    rcParams["savefig.dpi"] = 300

    # Draw dendrogram
    den_data = np.random.randn(10, 10)
    fig, ax = plt.subplots()
    Dendrogram(den_data, method="ward").draw(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "dendrogram.svg")

    # Draw Colors
    data = ["1", "1", "2", "2", "1", "3", "3"]
    fig, ax = plt.subplots(figsize=(2, 0.2))
    Colors(data).render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "colors.png")

    # Draw Annolabels
    data = np.arange(1, 50)
    fig, ax = plt.subplots()
    al = AnnoLabels(data, mark=[10, 11, 20])
    al.set_side("right")
    al.render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "annolabels.png")

    # Draw Bar
    data = [20, 65, 35]

    fig, ax = plt.subplots()
    Bar(data).render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "bar.png")

    # Draw Box
    data1 = np.random.rand(10) * 80 + 20
    data2 = np.random.rand(10) * 105 + 65
    data3 = np.random.rand(10) * 95 + 35
    box_data = np.vstack([data1, data2, data3]).T
    fig, ax = plt.subplots()
    Box(box_data, linewidth=1).render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "box.png")

    # Boxen
    fig, ax = plt.subplots()
    Boxen(box_data, linewidth=1, flier_kws={"s": 1}).render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "boxen.png")

    # Point
    fig, ax = plt.subplots()
    Point(box_data).render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "point.png")

    # Violin
    fig, ax = plt.subplots()
    Violin(box_data, linewidth=1).render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "violin.png")

    # Strip
    data1 = np.random.rand(100) * 80 + 20
    data2 = np.random.rand(100) * 105 + 65
    data3 = np.random.rand(100) * 95 + 35
    strip_data = np.vstack([data1, data2, data3]).T
    fig, ax = plt.subplots()
    Strip(strip_data, size=1).render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "strip.png")

    # Swarm
    fig, ax = plt.subplots()
    Swarm(strip_data, size=1).render(ax)
    close_ticks(ax)
    fig.savefig(save_folder / "swarm.png")
