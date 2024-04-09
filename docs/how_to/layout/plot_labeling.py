"""
Label plotter
=============

Marsilea provides a simple way to add a label any side plots.

In most cases, supplying the :code:`label` parameter is enough to add a label to the plot.

You can also control the location of the label using the :code:`label_loc` parameter.

The label can be customized using the :code:`label_props` parameter.

"""


# %%
# Define some data

# sphinx_gallery_start_ignore
import mpl_fontkit as fk
fk.install("Lato", verbose=False)
# sphinx_gallery_end_ignore

import numpy as np
import marsilea as ma
from marsilea.plotter import Colors, Labels

data = np.random.randint(0, 10, (10, 10))

#%%
h = ma.Heatmap(data, width=3, height=3)

label_blue = Colors(data[0], cmap="Blues", label="A Blue Heatmap", label_loc="bottom",
                    label_props={"color": "blue", "rotation": 0})
label_labels = Labels([f"Label {i}" for i in data[0]], label="Labels", label_loc="left")

h.add_left(label_blue, pad=.1)
h.add_top(label_labels)
h.render()
