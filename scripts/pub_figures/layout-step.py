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


mpl.rcParams['font.size'] = 8

pbmc3k = hg.load_data("pbmc3k")
exp = pbmc3k['exp']
pct_cells = pbmc3k['pct_cells']
count = pbmc3k['count']

matrix = normalize(exp.to_numpy(), axis=0)

cell_cat = ['Lymphoid', 'Myeloid', 'Lymphoid', 'Lymphoid',
            'Lymphoid', 'Myeloid', 'Myeloid', 'Myeloid']

if __name__ == "__main__":
    # Step 1a
    h = hg.Heatmap(
        matrix, cmap="Greens", label="Normalized\nExpression",
        width=3, height=3.5)
    h.save(SAVE_PATH / 'layout-step-1a.png', dpi=300)

    # Step 1b
    size_mesh = SizedMesh(
        pct_cells, size_norm=Normalize(vmin=0, vmax=100),
        color="none", edgecolor="#6E75A4",
        size_legend_kws=dict(
            title="% of cells", show_at=[.3, .5, .8, 1]
        ))
    marker_mesh = MarkerMesh(matrix > 0.7, color="#DB4D6D", label="High")
    h.add_layer(size_mesh)
    h.add_layer(marker_mesh)
    h.save(SAVE_PATH / 'layout-step-1b.png', dpi=300)

    # Step 2
    bar = Numbers(count['Value'], color="#fac858", label="Cell Count")
    violin = Violin(exp, label="Expression", linewidth=0, color="#ee6666")
    h.add_right(bar, pad=.1, size=.7)
    h.add_top(violin, pad=.1, size=.75)
    h.save(SAVE_PATH / 'layout-step-2.png', dpi=300)

    # Step 3
    h.add_left(hg.plotter.Labels(exp.index, align="center"))
    h.add_bottom(hg.plotter.Labels(exp.columns, text_pad=.2))
    h.hsplit(labels=cell_cat, order=['Lymphoid', 'Myeloid'])
    h.add_left(hg.plotter.Chunk(['Lymphoid', 'Myeloid'],
                                fill_colors=["#33A6B8", "#B481BB"],
                                color="white",
                                text_pad=1.2), pad=.05)
    h.save(SAVE_PATH / 'layout-step-3.png', dpi=300)

    # Step 4
    h.add_dendrogram("left", colors=["#33A6B8", "#B481BB"])
    h.add_dendrogram("bottom")
    h.add_legends(pad=.1)
    h.save(SAVE_PATH / 'layout-step-4.png', dpi=300)
