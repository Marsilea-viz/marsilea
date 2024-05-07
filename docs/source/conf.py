# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
from sphinx_gallery.sorting import FileNameSortKey, ExplicitOrder
from sphinx_gallery.scrapers import matplotlib_scraper
import marsilea as ma

# -- Project information -----------------------------------------------------

project = "marsilea"
copyright = "2023, Mr-Milk"
author = "Mr-Milk"

# The full version, including alpha/beta/rc tags
release = ma.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "numpydoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "matplotlib.sphinxext.plot_directive",
    "sphinx.ext.intersphinx",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx_gallery.gen_gallery",
]
autoclass_content = "class"
autodoc_docstring_signature = True
autodoc_default_options = {"members": None, "undoc-members": None}
autodoc_typehints = "none"
# setting autosummary
autosummary_generate = True
numpydoc_show_class_members = False
add_module_names = False

# setting plot direction
plot_include_source = True
plot_html_show_source_link = False
plot_html_show_formats = False
plot_formats = [("png", 220)]
plot_rcparams = {"savefig.bbox": "tight"}
plot_pre_code = (
    "import numpy as np; "
    "import pandas as pd;"
    "import matplotlib as mpl;"
    "from matplotlib import pyplot as plt;"
    "np.random.seed(0); "
    "mpl.rcParams['legend.frameon'] = False;"
    "import mpl_fontkit as fk;"
    "fk.install('Lato');"
    "fk.install_fontawesome();"
)

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]
exclude_patterns = ["Thumbs.db", ".DS_Store"]

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]
html_logo = "../../img/logo.png"
html_show_sourcelink = False
html_theme_options = {
    "github_url": "https://github.com/Marsilea-viz/marsilea",
    "navigation_with_keys": True,
}

# Remove the sidebar from following pages
html_sidebars = {"installation": []}


def matplotlib_tight_scraper(*args, **kwargs):
    return matplotlib_scraper(
        *args, bbox_inches="tight", format="png", dpi=200, **kwargs
    )


intersphinx_mapping = {
    "scipy": ("http://docs.scipy.org/doc/scipy/", None),
    "seaborn": ("https://seaborn.pydata.org/", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "legendkit": ("https://legendkit.readthedocs.io/en/stable", None),
}

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5," r"8}: "
copybutton_prompt_is_regexp = True

sphinx_gallery_conf = {
    "examples_dirs": ["../examples", "../how_to"],  # path to example scripts
    "gallery_dirs": ["examples", "how_to"],  # path to generated output
    "within_subsection_order": FileNameSortKey,  # Order by file name
    "image_srcset": ["2x"],
    "image_scrapers": (matplotlib_tight_scraper,),
    "subsection_order": ExplicitOrder(
        [
            "../examples/Basics",
            "../examples/Plotters",
            "../examples/Gallery",
            "../how_to/layout",
            "../how_to/dendrogram",
            "../how_to/legends",
            "../how_to/customization",
            "../how_to/save",
        ]
    ),
    "reference_url": {
        "marsilea": None,
        "matplotlib": "https://matplotlib.org",
    },
}


def autodoc_skip_member(app, what, name, obj, skip, options):
    methods = [
        "get_legends",
        "get_canvas_size",
        "render_ax",
        "render_axes",
        "render",
        "get_render_data",
        "get_text_params",
    ]
    attrs = [
        "render_main",
        "canvas_size_unknown",
        "no_split",
        "data",
        "deform",
        "deform_func",
    ]

    if hasattr(obj, "__qualname__"):
        cls = obj.__qualname__.split(".")[0]
        if (cls == "WhiteBoard") & (name == "render"):
            return False
        if cls != "RenderPlan":
            if name in methods:
                return True
    if what == "attribute":
        if name in attrs:
            return True
    return


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member)
