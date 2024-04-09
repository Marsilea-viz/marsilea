"""
SeqLogo
=======

:class:`~marsilea.plotter.SeqLogo` is for plotting sequence logo.

"""

# %%
from marsilea.plotter import SeqLogo

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

matrix = pd.DataFrame(data=np.random.randint(1, 10, (4, 10)),
                      index=list("ACGT"))
_, ax = plt.subplots()
colors = {"A": "r", "C": "b", "G": "g", "T": "black"}
SeqLogo(matrix, color_encode=colors).render(ax)
