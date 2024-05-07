# %%
import matplotlib.pyplot as plt
import seaborn as sns

data = sns.load_dataset("penguins").dropna()
data = data.pivot(columns=["species", "island", "sex"], values="bill_length_mm")

# %%

penguin_colors = {
    "Chinstrap": "#B462C4",
    "Adelie": "#EE7A30",
    "Gentoo": "#347074",
}

island_colors = {
    "Torgersen": "#0079FF",
    "Biscoe": "#00DFA2",
    "Dream": "#F6FA70",
}

sex_colors = {
    "Female": "#EF6262",
    "Male": "#1D5B79",
}

import marsilea as ma
import marsilea.plotter as mp

species = data.columns.get_level_values(0)
uni_species = list(species.unique())
species_colors = [penguin_colors[s] for s in uni_species]

islands = data.columns.get_level_values(1)
sex = data.columns.get_level_values(2)

wb = ma.ClusterBoard(data.fillna(0).to_numpy(), margin=0.2, height=3)
wb.add_layer(
    mp.Violin(
        data, linewidth=1, density_norm="width", group_kws=dict(color=species_colors)
    )
)
wb.add_layer(mp.Swarm(data, color="k", size=2))
wb.add_title("Penguin Bill Lengths (mm)")

wb.group_cols(species, order=uni_species)
wb.add_top(mp.Chunk(uni_species, species_colors))
wb.add_bottom(
    mp.Colors(islands, palette=island_colors, label="Island"), size=0.2, pad=0.1
)
wb.add_bottom(mp.Colors(sex, palette=sex_colors, label="Sex"), size=0.2, pad=0.1)
wb.add_dendrogram(
    "top",
    method="ward",
    colors=species_colors,
    meta_ratio=0.25,
    meta_color="#005874",
    linewidth=1.5,
)
wb.add_legends()
wb.render()


if "__file__" in globals():
    from pathlib import Path

    plt.rcParams["svg.fonttype"] = "none"
    save_path = Path(__file__).parent / "figures"
    wb.save(save_path / "penguin_violin_swarm.svg")
else:
    plt.show()
