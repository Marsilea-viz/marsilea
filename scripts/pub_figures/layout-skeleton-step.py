from pathlib import Path

import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle

import mpl_fontkit as fk
import heatgraphy as hg
from heatgraphy.plotter import SizedMesh, MarkerMesh, Numbers, Violin
from sklearn.preprocessing import normalize
SAVE_PATH = Path(__file__).parent.parent.parent / 'img' / 'publication'
SAVE_PATH.mkdir(exist_ok=True)
fk.install('Lato')

green = "#00B796"
red = "#F78076"
text = "#ECF791"


def add_bg(ax, color):
    rect = Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                     facecolor=color, edgecolor="gray", lw=2)
    ax.add_artist(rect)


def add_letter(ax, t):
    ax.text(.5, .45, t, )


fontdict = dict(color=text, va="center", ha="center",
                fontsize=10, fontweight=500)


def side_block(ax, text, side, color=None):
    if color is None:
        color = red
    ax.set_axis_off()
    add_bg(ax, color)

    rotation = 0
    if side == "left":
        rotation = 90
    if side == "right":
        rotation = -90
    ax.text(.5, .5, text, transform=ax.transAxes, rotation=rotation,
            **fontdict)


def increment_render(step):
    wb = hg.WhiteBoard(width=1.5, height=1.5)
    if step >= 2:
        wb.add_canvas("top", name="violin", size=.5, pad=.1)
        wb.add_canvas("right", name="bar", size=.5, pad=.1)
    if step >= 3:
        wb.add_canvas("bottom", name="col_label", size=.5, pad=.1)
        wb.add_canvas("left", name="row_label", size=.5, pad=.1)
        wb.add_canvas("left", name="chunk", size=.3, pad=.1)
    if step >= 4:
        wb.add_canvas("bottom", name="col_den", size=.5, pad=.1)
        wb.add_canvas("left", name="row_den", size=.5, pad=.1)
        wb.add_canvas("right", name="legend", size=.5, pad=.1)

    wb.render()

    if step >= 1:
        main_ax = wb.get_main_ax()
        main_ax.set_axis_off()
        add_bg(main_ax, green)
        main_ax.text(.5, .5, "Main Plot", **fontdict)

    # Step 2
    if step >= 2:
        violin_ax = wb.get_ax("violin")
        side_block(violin_ax, "Violin Plot", "top")

        bar_ax = wb.get_ax("bar")
        side_block(bar_ax, "Bar Plot", "right")

    # Step 3
    if step >= 3:
        col_label_ax = wb.get_ax("col_label")
        side_block(col_label_ax, "Columns' Labels", "bottom")

        row_label_ax = wb.get_ax("row_label")
        side_block(row_label_ax, "Rows' Labels", "left")

        chunk_ax = wb.get_ax("chunk")
        side_block(chunk_ax, "Summary Text", "left")

    # Step 4
    if step >= 4:

        col_den_ax = wb.get_ax("col_den")
        side_block(col_den_ax, "Column Dendrogram", "bottom")

        row_den_ax = wb.get_ax("row_den")
        side_block(row_den_ax, "Row Dendrogram", "left")

        legend_ax = wb.get_ax("legend")
        side_block(legend_ax, "Legend", "right", "#9E7A7A")
    plt.savefig(SAVE_PATH / f'layout-skeleton-step{step}.png', dpi=300)


if __name__ == "__main__":
    for step in [1, 2, 3, 4]:
        increment_render(step)
