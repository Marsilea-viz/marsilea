from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import heatgraphy as hg
from heatgraphy.plotter import MarkerMesh


if __name__ == "__main__":

    np.random.seed(0)
    heat_data = np.random.randint(0, 10, (5, 5))
    size_data = np.random.randint(0, 10, (5, 5))
    mark_data = np.random.randint(0, 2, (5, 5))

    save_folder = Path(__file__).parent.parent / 'img'

    h = hg.Heatmap(heat_data, width=2, height=2)
    h.render()
    h.save(save_folder / "heatmap.png", dpi=300)

    sh = hg.SizedHeatmap(size_data, width=2, height=2)
    sh.render()
    sh.save(save_folder / "sized_onlymap.png", dpi=300)

    sh = hg.SizedHeatmap(size_data, heat_data, width=2, height=2)
    sh.render()
    sh.save(save_folder / "sized_heatmap.png", dpi=300)

    _, ax = plt.subplots(figsize=(2, 2))
    mark = MarkerMesh(mark_data, color="red", marker="x")
    mark.render(ax)
    plt.savefig(save_folder / "mark_map.png", dpi=300)
