import numpy as np
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid

ncol = st.number_input("Columns", min_value=2, step=1)
nrow = st.number_input("Rows", min_value=2, step=1)

df = pd.DataFrame(data=np.zeros((nrow, ncol)),
                  columns=np.arange(ncol).astype(str),
                  )
grid_return = AgGrid(df, editable=True)
new_df = grid_return['data']
