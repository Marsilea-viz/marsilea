import streamlit as st
from matplotlib.image import imread

from components.example_download import ExampleDownloader

st.header("Manual")

st.markdown("## What's x-layout?")

_, img, _ = st.columns((1, 2, 1))
with img:
    st.image("app/img/x-layout.png", use_column_width=True,
             caption="Schematic of x-layout")

st.markdown(
    "Sometimes a single plot is not enough to represent the whole picture of"
    "a dataset. The idea of cross (x) layout is using plots to annotate plot, "
    "thus generate a more comprehensive representation of dataset. \n\n"
    "In the above picture, different features from the same dataset can be "
    "added as side plot to reveal unseen aspect of main feature. \n\n"
    "It's not necessary a heatmap, "
    "but heatmap is indeed the most widely use case."
)

st.markdown("## How to create an x-layout heatmap?")

st.markdown(
    "You can start by downloading our example data. "
    "It will show you what the data looks like and "
    "help you prepare yourself.")

ExampleDownloader()

st.markdown(
    "Here's what you will find inside the example data. \n"
    "- `matrix_data.txt` Use for Heatmap or Sized Heatmap. \n"
    "- `labels.txt` Labels of row and column. \n"
    "- `statistics plot.txt` 2-dimensional dataset for statistics side plots. \n"
    "- `numbers.txt` A 1-dimensional dataset"
            )

RENDER_BUTTON = "<span style='color: white; "\
    "background-color: #FF4B4B; border-radius: .25rem;"\
    "padding: .25rem .75rem;'>Apply Changes & Render</span>"

st.markdown(
    "You can select one of **Heatmap**, **Sized Heatmap** and **Mark** to start with. \n\n"
    "Let's use **Heatmap** as example. \n"
    "1. Select the **Input Data** tab within **Heatmap** tab. \n"
    "2. Upload the `matrix_data.txt`. \n"
    f"3. Now you see a {RENDER_BUTTON} pop up, "
    "click it to view your result. Remember for every changes you make to render, you need to"
    "click this button.\n"
    "4. You can adjust the styles in the **Styles** tab (same place as **Input Data**), "
    "try change the colormap. \n",
    unsafe_allow_html=True
)

st.markdown("Adding side plots")

st.markdown(
    "5. Scroll down to add the side plots, you can add side plot for the heatmap at "
    "four directions. Adjust the number of **Add plots** to determine how many"
    "plots you are going to add. \n"
    "6. In **Side plot 1**, select `Bar` as our plot to add. Upload the `numbers.txt`"
    "and click the **Add plot** button.\n"
    "7. Try add one more plots add bottom, "
    "This time let's select **Hierarchical clustering dendrogram** to cluster your heatmap.",
    unsafe_allow_html=True
)

st.markdown("Split Heatmap")

st.markdown(
    "8. Find the **General Option** above the render button, "
    "click **Heatmap Partition**. Let's try split it vertically, "
    "input **‘5,10’** in the **Split by number** and the click **Confirm**."
)

st.markdown(
    "Now you get an idea on how this work, feel free to play around."
)

st.markdown("## How to report a bug?")

st.markdown("Click the botton on the Top Right ➡️ **Report a bug**")