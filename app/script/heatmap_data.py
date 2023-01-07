import numpy as np
import pandas as pd

from random_word.random_word import RandomWords

COLUMN = 20
ROW = 20

np.random.seed(0)

matrix = np.random.randint(0, 101, (ROW, COLUMN))

gr = RandomWords()

label = [gr.get_random_word() for _ in range(ROW)]

stats_data = np.random.randn(10, ROW)

numbers = np.random.randint(10, 100, ROW)

kws = dict(sep="\t", index=False, header=None)
pd.DataFrame(data=matrix).to_csv("test_data/example_data.txt", **kws)
pd.DataFrame(data=label).to_csv("test_data/row_labels.txt", **kws)
pd.DataFrame(data=stats_data).to_csv("test_data/Stats_plot.txt", **kws)
pd.DataFrame(data=numbers).to_csv("test_data/number.txt", **kws)
