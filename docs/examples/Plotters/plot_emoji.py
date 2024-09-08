"""
Emoji
======

:class:`~marsilea.plotter.Emoji` is a plotter that displays funny emoji.

"""

# %%

# %%
import matplotlib.pyplot as plt

from marsilea.plotter import Emoji

_, ax = plt.subplots()
Emoji("😆😆🤣😂😉😇🐍🦀🦄").render(ax)
