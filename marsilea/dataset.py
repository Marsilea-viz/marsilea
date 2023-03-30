from urllib.request import urlretrieve

import pandas as pd
from platformdirs import user_cache_path

NAME = "Marsilea"
BASE_URL = "https://raw.githubusercontent.com/marsilea-viz/marsilea-data/main"


def load_data(name, cache=True):
    """To load marsilea dataset

    - 'imdb': The IMDB Top 100 Movies
    - 'pbmc3k': single-cell RNA-seq dataset from 10X Genomics
    - 'oncoprint': Subsample of Breast Invasive Carcinoma (TCGA, PanCancer Atlas)

    Parameters
    ----------
    name : str
        The name of the dataset
    cache : bool
        Download data and cache locally

    Returns
    -------

    """
    if name == "imdb":
        return _load_imdb(cache)
    elif name == "pbmc3k":
        return _load_pbmc3k(cache)
    elif name == "oncoprint":
        return _load_oncoprint(cache)
    else:
        raise NameError("Dataset not found")


def _cache_remote(files, cache=True):
    if isinstance(files, str):
        files = [files]
    data_dir = user_cache_path(appname=NAME)
    data_dir.mkdir(exist_ok=True, parents=True)

    download_files = [f.replace("/", "_") for f in files]

    for fname, dfname in zip(files, download_files):
        url = f"{BASE_URL}/{fname}"
        # Will not download if cache and file exist
        dest = data_dir / dfname
        # Not download when cache and exist
        if not (cache and dest.exists()):
            urlretrieve(url, dest)

    if len(files) == 1:
        return data_dir / download_files[0]
    else:
        return [data_dir / f for f in download_files]


def _load_imdb(cache=True):
    imdb = _cache_remote("imdb.csv", cache=cache)
    return pd.read_csv(imdb)


def _load_pbmc3k(cache=True):
    exp, pct_cells, count = _cache_remote(['pbmc3k/exp.csv',
                                           'pbmc3k/pct_cells.csv',
                                           'pbmc3k/count.csv'],
                                          cache=cache)
    return {
        'exp': pd.read_csv(exp, index_col=0),
        'pct_cells': pd.read_csv(pct_cells, index_col=0),
        'count': pd.read_csv(count, index_col=0)
    }


def _load_oncoprint(cache=True):
    cna, mrna, methyl, clinical = _cache_remote(
        ['oncoprint/cna.csv', 'oncoprint/mrna_exp.csv',
         'oncoprint/methyl_exp.csv', 'oncoprint/clinical.csv'],
        cache=cache
    )
    return {
        'cna': pd.read_csv(cna, index_col=0),
        'mrna_exp': pd.read_csv(mrna, index_col=0),
        'methyl_exp': pd.read_csv(methyl, index_col=0),
        'clinical': pd.read_csv(clinical, index_col=0)
    }
