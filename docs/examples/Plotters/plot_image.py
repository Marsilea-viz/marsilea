"""
Image
======

:class:`~marsilea.plotter.Image` is a plotter that displays static images.

"""

# %%

# %%
import matplotlib.pyplot as plt

from marsilea.plotter import Image

_, ax = plt.subplots()
Image(
    [
        "https://www.iconfinder.com/icons/4375050/download/png/512",
        "https://www.iconfinder.com/icons/8666426/download/png/512",
        "https://www.iconfinder.com/icons/652581/download/png/512",
    ],
    align="right",
).render(ax)
