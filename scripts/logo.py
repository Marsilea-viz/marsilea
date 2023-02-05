from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import mpl_fontkit as fk

# Use Kanit font
fk.install("Kanit")

# Define colors
green = "#00B796"
red = "#F78076"
text = "#ECF791"

bar_colors = ["#6CE5E8", "#41B8D5", "#2D8BBA"]
circ = "#FFDE59"


def add_bg(ax, color):
    rect = Rectangle((0, 0), 1, 1, transform=ax.transAxes, color=color)
    ax.add_artist(rect)


def add_text(ax, t):
    ax.text(.5, .45, t, color=text, va="center", ha="center",
            fontsize=35, fontweight=700)


def draw_bars(ax, x, y, a1, a2, a3):
    xs = x
    for a, c in zip([a1, a2, a3], bar_colors):
        rect = Rectangle((xs, y), a, .1, color=c)
        ax.add_artist(rect)
        xs += a


if __name__ == "__main__":
    fig, axes = plt.subplots(nrows=2, ncols=6, figsize=(6, 2))
    for ax in axes.flatten():
        ax.set_aspect(1)
        ax.set_axis_off()

    ax_list = axes.flatten().tolist()

    # draw circle
    circ_ax = ax_list[0]
    add_bg(circ_ax, red)
    circle = Circle((.5, .5), .3, color=circ, transform=circ_ax.transAxes)
    ax_list[0].add_artist(circle)

    bar_ax = ax_list[5]
    add_bg(bar_ax, red)

    draw_bars(bar_ax, .1, .15, .12, .2, .1)
    draw_bars(bar_ax, .1, .35, .18, .2, .1)
    draw_bars(bar_ax, .1, .55, .27, .2, .15)
    draw_bars(bar_ax, .1, .75, .35, .25, .1)

    text_ixs = [1, 2, 3, 4, 6, 7, 8, 9, 10, 11]
    for ix, t in zip(text_ixs, "HEATGRAPHY"):
        add_bg(ax_list[ix], green)
        add_text(ax_list[ix], t)

    save_folder = Path(__file__).parent.parent / "img"

    fig.savefig(save_folder / "logo.svg", facecolor="none")
    fig.savefig(save_folder / "logo.png", dpi=150, facecolor="none")

    # draw favicon
    fig = plt.figure(figsize=(1, 1))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect(1)
    ax.set_axis_off()
    add_bg(ax, red)
    circle = Circle((.5, .5), .3, color=circ, transform=ax.transAxes)
    ax.add_artist(circle)
    fig.savefig(save_folder / "favicon.svg", facecolor="none")
    fig.savefig(save_folder / "favicon.png", facecolor="none")

