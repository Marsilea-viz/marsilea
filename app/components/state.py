import numpy as np
import streamlit as st


def init_state(**mapping):
    for key, value in mapping.items():
        if key not in st.session_state:
            st.session_state[key] = value


class State:

    def __init__(self, key=None):
        self._state_keys = set()
        if key is None:
            key = ""
        self._salt = key

    def real_key(self, k):
        return f"{self._salt}{k}"

    def init_state(self, **kwargs):
        for key, value in kwargs.items():
            self.add_state(key, value)

    def add_state(self, key, value):
        key = self.real_key(key)
        if key not in st.session_state:
            st.session_state[key] = value
        self._state_keys.add(key)

    def get_state(self, key):
        return self.__getitem__(key)

    def set_state(self, key, value):
        self.__setitem__(key, value)

    def __getitem__(self, item):
        ritem = self.real_key(item)
        if ritem in self._state_keys:
            return st.session_state[ritem]
        else:
            raise AttributeError(f"{item} is not initialized")

    def __setitem__(self, item, value):
        ritem = self.real_key(item)
        if ritem in self._state_keys:
            st.session_state[ritem] = value
        else:
            raise AttributeError(f"{item} is not initialized")


class DataStorage:

    def __init__(self, key=None):
        self.state = State(key=key)
        self.state.init_state(datasets_names=[],
                              datasets={},
                              datasets_dims={},
                              h_chunk=1,
                              v_chunk=1,
                              )
        self.visible_datasets = None
        self.main_data_name = None

    def add_dataset(self, name, data):
        if (name != "") & (name not in self.state['datasets_names']):
            self.state['datasets_names'].append(name)
            self.state['datasets'][name] = data
            self.state['datasets_dims'][name] = data.ndim
            return True
        else:
            return False

    def set_visible_datasets(self, datasets):
        self.visible_datasets = datasets

    def get_names(self, subset=None):
        if self.visible_datasets is not None:
            names = self.visible_datasets
        else:
            names = self.get_all_names()

        if subset is None:
            return names
        elif subset == "1d":
            sub_names = []
            for n in names:
                if self.state['datasets_dims'][n] == 1:
                    sub_names.append(n)
            return sub_names
        elif subset == "2d":
            sub_names = []
            for n in names:
                if self.state['datasets_dims'][n] == 2:
                    sub_names.append(n)
            return sub_names
        else:
            raise ValueError("subset can only be 1d or 2d")

    def get_all_names(self):
        return self.state['datasets_names']

    def get_datasets(self, name):
        return self.state['datasets'][name]

    def set_main_data(self, name):
        self.main_data_name = name

    def get_main_data(self):
        return self.get_datasets(self.main_data_name)

    def align_main(self, side, other_data: np.ndarray):
        main_data = self.get_main_data()
        if side == "main":
            if other_data.shape != main_data.shape:
                st.error(f"Selected dataset {other_data.shape} "
                         f"does not match cluster data {main_data.shape}")
                return False
        ms = main_data.shape

        if side in ["left", "right"]:
            match_to = ms[0]
            axis = "rows"
        else:
            match_to = ms[1]
            axis = "columns"

        if other_data.ndim == 1:
            if other_data.size != match_to:
                st.error(f"The size of input data ({other_data.size}) "
                         f"does not match ({match_to}) {axis} in main plot",
                         icon="🚫")
                return False
        if other_data.ndim == 2:
            check_size = other_data.shape[1]
            if check_size != match_to:
                st.error(f"({check_size}) columns of input data "
                         f"does not match ({match_to}) {axis} in main plot",
                         icon="🚫")
                return False
        return True

    def set_chunk(self, orient, chunk):
        """To record if the current main data is split"""
        key = "h_chunk" if orient == "h" else "v_chunk"
        self.state[key] = chunk

    def get_chunk(self, side):
        if side in ["left", "right"]:
            return self.state["h_chunk"]
        else:
            return self.state["v_chunk"]
