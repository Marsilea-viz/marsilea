import numpy as np
import pandas as pd


def parse_file(tb_file, sep):
    autosep = False
    if sep == "":
        autosep = True
    if tb_file is not None:
        suffix = tb_file.name.split(".")[-1]
        if autosep:
            if suffix == "csv":
                sep = ","
            if suffix == "txt":
                sep = "\t"

        if suffix in ["csv", "txt"]:
            reader = pd.read_csv
            kws = dict(sep=sep)
        else:
            reader = pd.read_excel
            kws = {}
        data = reader(tb_file, **kws)
        return data


def parse_text(text, sep=",", as_number=True):
    if len(text) > 0:
        rows = text.strip().split("\n")
        raw_data = [[r for r in row.split(sep)] for row in rows]
        data = np.array(raw_data)
        if as_number:
            data = data.astype(float)
        return pd.DataFrame(data)
