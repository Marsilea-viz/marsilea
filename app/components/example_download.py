import base64
import io
import zipfile

import numpy as np
import pandas as pd
import streamlit as st
from random_word.random_word import RandomWords


class ExampleDataGenerator:
    def __init__(self, col, row):
        np.random.seed(0)
        self.col = col
        self.row = row
        self.words = RandomWords()
        self.export_kws = dict(sep="\t", index=False, header=None)

    def matrix(self):
        return np.random.randint(0, 101, (self.row, self.col))

    def col_labels(self):
        labels = [self.words.get_random_word() for _ in range(self.col)]
        return np.array(labels)

    def row_labels(self):
        labels = [self.words.get_random_word() for _ in range(self.row)]
        return np.array(labels)

    def stats_data(self):
        return np.random.randn(10, self.row)

    def numbers(self):
        return np.random.randint(10, 100, self.row)

    def get_text(self, data):
        return pd.DataFrame(data=data).to_csv(**self.export_kws)

    def to_zip(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a") as z:
            z.writestr("matrix_data.txt", self.get_text(self.matrix()))
            z.writestr("labels (row).txt", self.get_text(self.row_labels()))
            z.writestr("labels (col).txt", self.get_text(self.col_labels()))
            z.writestr("statistic plot.txt", self.get_text(self.stats_data()))
            z.writestr("numbers.txt", self.get_text(self.numbers()))
        return zip_buffer

    def to_base64(self):
        zip_bytes = self.to_zip()
        return base64.b64encode(zip_bytes.getvalue()).decode()


@st.cache_resource
def get_base64():
    g = ExampleDataGenerator(20, 20)
    return g.to_base64()


class ExampleDownloader:
    def __init__(self):
        self.b64 = get_base64()
        href = (
            f'<a href="data:file/zip;base64,{self.b64}" '
            f'download="example.zip">Example Data</a>'
        )
        st.markdown(href, unsafe_allow_html=True)


if __name__ == "__main__":
    g = ExampleDataGenerator(20, 20)
