"""
StackBar
========

:class:`~marsilea.plotter.StackBar` is for plotting stacked bar chart.

"""

# %%
from marsilea.plotter import StackBar

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_, ax = plt.subplots()
data = pd.DataFrame(data=np.random.randint(0, 10, (10, 10)))
StackBar(data).render(ax)
