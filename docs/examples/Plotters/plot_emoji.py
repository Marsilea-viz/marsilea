"""
Emoji
======

:class:`~marsilea.plotter.Emoji` is a plotter that displays funny emoji.

"""

# %%

from marsilea.plotter import Emoji

# %%
import numpy as np
import matplotlib.pyplot as plt

_, ax = plt.subplots()
Emoji("😆😆🤣😂😉😇🐍🦀🦄").render(ax)
