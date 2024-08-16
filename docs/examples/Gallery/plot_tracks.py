"""
Track Plot
==========
"""
import marsilea as ma
import marsilea.plotter as mp

# sphinx_gallery_start_ignore
import mpl_fontkit as fk

fk.install("Lato", verbose=False)
# sphinx_gallery_end_ignore

# %%
# Load data and define some constants
# -----------------------------------
tracks = ma.load_data("track")

colors = {
    "H3K9me1": "#DD6E42",
    "H3K9me2": "#E8DAB2",
    "H3K9me3": "#4F6D7A",
    "Background": "#C0D6DF",
}

lims = {
    "H3K9me1": 20,
    "H3K9me2": 35,
    "H3K9me3": 35,
    "Background": 20,
}

TRACK_HEIGHT = 0.5
TRACK_PAD = 0.1

# %%
# Create the track plot
canvas = ma.ZeroHeight(5, name="track")

for _, row in tracks.iterrows():
    cond, enz, track = row
    name = f"{cond}{enz}"
    color = colors[enz]
    canvas.add_bottom(
        mp.Area(track, color=color, add_outline=False, alpha=1,
                label=cond, label_loc="right"),
        size=TRACK_HEIGHT,
        pad=TRACK_PAD,
        name=name,
    )

enz_canvas = ma.ZeroHeight(1, name="enz")
for enz in tracks["enz"].drop_duplicates():
    enz_canvas.add_bottom(
        mp.Title(f"‎ ‎ {enz}", align="left"),
        size=TRACK_HEIGHT * 2,
        pad=TRACK_PAD * 2,
        name=enz,
    )

comp = canvas + 0.8 + enz_canvas
comp.render()

for enz in tracks["enz"].drop_duplicates():
    ax = comp.get_ax("enz", enz)
    ax.axvline(x=0, color="k", lw=4)

# Modify the limits
for _, row in tracks.iterrows():
    name = f"{row['cond']}{row['enz']}"
    lim = lims[row["enz"]]
    ax = comp.get_ax("track", name)
    ax.set_ylim(0, lim)
    ax.set_yticks([lim])
