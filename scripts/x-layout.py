from pathlib import Path

import heatgraphy as hg

import mpl_fontkit as fk
from matplotlib.patches import Rectangle

fk.install("Kanit")


def add_bg(ax, color):
    rect = Rectangle((0, 0), 1, 1, transform=ax.transAxes, color=color)
    ax.add_artist(rect)


def add_text(ax, t):
    ax.text(.5, .5, t, color=text, va="center", ha="center",
            fontsize=10)


green = "#00B796"
red = "#F78076"
text = "#ECF791"

if __name__ == "__main__":

    wb = hg.WhiteBoard(width=1.2, height=1, name="main")

    chunk_kws = dict(fill_colors=red, text_pad=2, props=dict(color=text))

    for side in ["top", "bottom", "left", "right"]:
        wb.add_plot(side, hg.plotter.Chunk([f"{side.capitalize()} feature 1"],
                                           **chunk_kws), pad=.05)
        wb.add_plot(side, hg.plotter.Chunk([f"{side.capitalize()} feature 2"],
                                           **chunk_kws), pad=.05)

    wb.render()

    main_ax = wb.get_ax("main")
    main_ax.set_axis_off()
    add_bg(main_ax, green)
    add_text(main_ax, "Main Feature")

    save_folder = Path(__file__).parent.parent / "img"

    wb.save(save_folder / "x-layout.png", dpi=300)
