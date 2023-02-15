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


@st.cache_resource
def parse_file(file, export="ndarray", header=False, index=False):
    header = None if not header else "infer"
    index_col = None if not index else 0
    suffix = file.name.split(".")[-1]
    if suffix in ["csv", "txt", "tsv"]:
        reader = pd.read_csv
        sep = "," if suffix == "csv" else "\t"
        kws = dict(sep=sep, header=header, index_col=index_col)
    else:
        reader = pd.read_excel
        kws = {}
    data = reader(file, **kws)
    if export == "ndarray":
        if len(data.columns) == 1:
            return data.to_numpy().flatten()
        return data.to_numpy()
    else:
        return data


class FileUpload(InputBase):

    def __init__(self, key=None, header=False, index=False):
        super().__init__(key=key)
        self.header = False
        self.index = False

        self.user_input = st.file_uploader("Choose a table file",
                                           key=f"table_reader-{self.key}",
                                           accept_multiple_files=False,
                                           label_visibility="collapsed",
                                           type=["txt", "csv", "xlsx"])

        if index & header:
            h1, h2 = st.columns(2)
            with h1:
                self.header = self._header_checkbox()
            with h2:
                self.index = self._index_checkbox()

        elif header:
            self.header = self._header_checkbox()

        elif index:
            self.index = self._index_checkbox()

    def _header_checkbox(self):
        return st.checkbox("Use header?", key=f"select-header-{self.key}")

    def _index_checkbox(self):
        return st.checkbox("Use row labels?", key=f"select-index-{self.key}")

    def parse(self):
        if self.user_input is not None:
            return parse_file(self.user_input, header=self.header)

    def parse_dataframe(self, header=True, index=False):
        if self.user_input is not None:
            return parse_file(self.user_input, export="dataframe",
                              header=header, )


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
