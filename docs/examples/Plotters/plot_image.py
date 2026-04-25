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
# Wikimedia thumbnails must use standard widths (120, 250, 500, etc.)
# See https://w.wiki/GHai
Image(
    [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/250px-Python-logo-notext.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Rust_programming_language_black_logo.svg/250px-Rust_programming_language_black_logo.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/JavaScript-logo.png/250px-JavaScript-logo.png",
    ],
    align="right",
).render(ax)
