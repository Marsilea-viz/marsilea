"""
Ranking of programming languages.
==================================

Visualize the ratings of programming languages
according to the `TIOBE index <https://www.tiobe.com/tiobe-index/>`_.


"""

# Import libraries
import matplotlib.pyplot as plt
import pandas as pd

import marsilea as ma
import marsilea.plotter as mp

# sphinx_gallery_start_ignore
import mpl_fontkit as fk

fk.install("Lato", verbose=False)
plt.rcParams["font.size"] = 12
# sphinx_gallery_end_ignore

# %%
# Load data
# ---------

data = {
    "Programming Language": [
        "Python",
        "C++",
        "C",
        "Java",
        "C#",
        "JavaScript",
        "Go",
        "Visual Basic",
        "Fortran",
        "SQL",
    ],
    "Ratings": [16.12, 10.34, 9.48, 8.59, 6.72, 3.79, 2.19, 2.08, 2.05, 2.04],
}
data = pd.DataFrame(data).set_index("Programming Language")

# Wikimedia thumbnails must use standard widths:
# 20, 40, 60, 120, 250, 330, 500, 960, 1280, 1920, 3840
# See https://w.wiki/GHai
images = {
    "Python": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/250px-Python-logo-notext.svg.png",
    "C++": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/ISO_C%2B%2B_Logo.svg/250px-ISO_C%2B%2B_Logo.svg.png",
    "C": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/C_Programming_Language.svg/250px-C_Programming_Language.svg.png",
    "Java": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Duke_%28Java_mascot%29_waving.svg/250px-Duke_%28Java_mascot%29_waving.svg.png",
    "C#": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/C_Sharp_Logo_2023.svg/250px-C_Sharp_Logo_2023.svg.png",
    "JavaScript": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/JavaScript-logo.png/250px-JavaScript-logo.png",
    "Go": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Go_Logo_Blue.svg/250px-Go_Logo_Blue.svg.png",
    "Visual Basic": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/VB.NET_Logo.svg/250px-VB.NET_Logo.svg.png",
    "Fortran": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Fortran_logo.svg/250px-Fortran_logo.svg.png",
    "SQL": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Sql_data_base_with_logo.png/250px-Sql_data_base_with_logo.png",
}

# %%
# Plot
c = ma.ZeroWidth(5)
c.add_right(mp.Image([images[lang] for lang in data.index]))
c.add_left(mp.Labels(data.index, fontweight=600), pad=0.1)
c.add_right(mp.Numbers(data["Ratings"], color="#009FBD", label="Rating"), pad=0.1)
c.add_title(
    "https://www.tiobe.com/tiobe-index/", align="left", fontsize=10, fontstyle="italic"
)
c.add_title("TIOBE Index July 2024", align="left", fontweight=600)
c.render()
