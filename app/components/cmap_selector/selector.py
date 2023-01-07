from pathlib import Path
from functools import cache

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


@st.experimental_singleton
def generate_cmap_images():
    FIGURE_SIZE = (2.5, .5)
    DPI = 90

    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))

    cmap_mapper = {}
    for i in mpl.colormaps:
        cmap_name = i
        if i.endswith("_r"):
            cmap_name = f"{i[:-2]} (Reversed)"
        cmap_mapper[i] = cmap_name.capitalize()

    cmap_table = []
    # create images dir if not exist
    img_dir = Path(__file__).parent / "images"
    img_dir.mkdir(exist_ok=True)
    for cmap, display_name in cmap_mapper.items():
        rel_path = f"images/{cmap}.png"
        img_name = Path(__file__).parent / rel_path
        if not img_name.exists():
            fig = plt.figure(figsize=FIGURE_SIZE)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.imshow(gradient, aspect="auto", cmap=cmap)
            ax.set_axis_off()
            fig.savefig(img_name, dpi=DPI)
            plt.close(fig)

        cmap_table.append([cmap, display_name, rel_path])

    tb = pd.DataFrame(cmap_table, columns=["name", "display_name", "img_src"])
    tb = tb.sort_values("name")
    return tb.set_index("display_name")


class ColormapSelector:

    def __init__(self, default="coolwarm"):
        self.cmap_data = generate_cmap_images()
        self.cmap_options = self.cmap_data.index
        options = self.cmap_options.tolist()
        default_cmap = self.cmap_data[
            self.cmap_data['name'] == default].index.values[0]
        default_index = options.index(default_cmap)
        self.cmap = st.selectbox("Select Colormap",
                                 options=self.cmap_options,
                                 index=default_index
                                 )
        rel_path = self.cmap_data.loc[self.cmap, ["img_src"]][0]
        img = f"components/cmap_selector/{rel_path}"
        st.image(img)

    def get_cmap(self):
        return self.cmap_data.loc[self.cmap, ["name"]][0]
