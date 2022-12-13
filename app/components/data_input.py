from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


class InputBase:
    sep: str
    user_input: Any

    def __init__(self, key=None):
        self.key = f"{self.__class__.__name__}-{key}"

    def parse(self):
        pass

    def seperator(self):
        sep_options = {
            "Tab (\\t)": "\t",
            "Comma (,)": ",",
            "Space (' ')": " "
        }
        user_sep = st.selectbox("Seperator", key=self.key,
                                options=sep_options.keys())
        self.sep = sep_options[user_sep]


class FileUpload(InputBase):

    def __init__(self, key=None):
        super().__init__(key=key)
        self.user_input = st.file_uploader("Choose a table file",
                                           key=f"table_reader-{self.key}",
                                           accept_multiple_files=False,
                                           label_visibility="collapsed",
                                           type=["txt", "csv", "xlsx", "xls"])

    def parse(self):
        if self.user_input is not None:
            suffix = self.user_input.name.split(".")[-1]
            if suffix in ["csv", "txt", "tsv"]:
                reader = pd.read_csv
                sep = "," if suffix == "csv" else "\t"
                kws = dict(sep=sep, header=None)
            else:
                reader = pd.read_excel
                kws = {}
            data = reader(self.user_input, **kws)
            if len(data.columns) == 1:
                return data.to_numpy().flatten()
            return data.to_numpy()


class PasteText(InputBase):

    def __init__(self, cast_number=True, key=None):
        super().__init__(key=key)
        self.cast_number = cast_number
        self.user_input = st.text_area("Paste data here", key=self.key)
        self.seperator()

    def parse(self):
        if len(self.user_input) > 0:
            rows = self.user_input.strip().split("\n")
            raw_data = [row.split(self.sep) for row in rows]
            try:
                data = np.array(raw_data)
                if self.cast_number:
                    data = data.astype(float)
                return pd.DataFrame(data)
            except Exception:
                st.error("Your seperator seems incorrect")
