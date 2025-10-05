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
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Rust_programming_language_black_logo.svg/480px-Rust_programming_language_black_logo.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/6/6a/JavaScript-logo.png",
    ],
    align="right",
).render(ax)
