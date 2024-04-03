"""
Size and spacing
================

Unlike other matplotlib plotting library,
Marsilea gives you fine control over the size of the plot and the main canvas.

You don't have to suffer from fixing the figure size and try to maintain the ratio among plots.

.. note::
    The unit of the size is in **inches**.

"""

# sphinx_gallery_start_ignore
import mpl_fontkit as fk
fk.install("Lato", verbose=False)
# sphinx_gallery_end_ignore

# %%
# The size main canvas can be controlled via the `width` and `height` parameters.
import numpy as np
import marsilea as ma
data = np.random.randint(0, 10, (10, 10))
h = ma.Heatmap(data, width=1, height=1.5)
h.add_title(top="width=1", left="height=1.5")
h.render()

# %%
# Let's switch the width and height.
h = ma.Heatmap(data, width=2, height=1)
h.add_title(top="width=2", left="height=1")
h.render()


# %%
# The size of the plotter can be controlled via the `size` parameter when you add to the main canvas.

blue = ma.plotter.ColorMesh(data[0], cmap="Blues", label="size=0.1")
green = ma.plotter.ColorMesh(data[1], cmap="Greens", label="size=0.2")

h = ma.Heatmap(data, width=1, height=1)
h.add_top(blue, size=.1, pad=.05)
h.add_top(green, size=.2, pad=.05)
h.render()

# %%
# The size of text in Marsilea is automatically adjusted based on the content. But you can also set the size explicitly.
text = ma.plotter.Labels([f"Label {i}" for i in data[0]])

h = ma.Heatmap(data, width=3, height=3)
h.add_left(text)
h.render()
