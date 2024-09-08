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

images = {
    "Python": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png",
    "C++": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/ISO_C%2B%2B_Logo.svg/1822px-ISO_C%2B%2B_Logo.svg.png",
    "C": "https://upload.wikimedia.org/wikipedia/commons/1/19/C_Logo.png",
    "Java": "https://static-00.iconduck.com/assets.00/java-icon-1511x2048-6ikx8301.png",
    "C#": "https://upload.wikimedia.org/wikipedia/commons/4/4f/Csharp_Logo.png",
    "JavaScript": "https://upload.wikimedia.org/wikipedia/commons/6/6a/JavaScript-logo.png",
    "Go": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Go_gopher_favicon.svg/2048px-Go_gopher_favicon.svg.png",
    "Visual Basic": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/VB.NET_Logo.svg/2048px-VB.NET_Logo.svg.png",
    "Fortran": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Fortran_logo.svg/2048px-Fortran_logo.svg.png",
    "SQL": "https://upload.wikimedia.org/wikipedia/commons/4/44/SQL_%D0%BB%D0%BE%D0%B3%D0%BE%D1%82%D0%B8%D0%BF.png",
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
