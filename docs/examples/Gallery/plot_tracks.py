"""
Sequence Alignment Plot
=======================
"""
from collections import Counter
import numpy as np
import pandas as pd

import marsilea as ma
import matplotlib as mpl

# sphinx_gallery_start_ignore
import mpl_fontkit as fk

fk.install("Roboto Mono", verbose=False)

mpl.rcParams["font.size"] = 30
# sphinx_gallery_end_ignore

# %%
# Generate random data
# --------------------


