import streamlit as st


def init_state(**mapping):
    for key, value in mapping.items():
        if key not in st.session_state:
            st.session_state[key] = value


class State:

    def __init__(self, **kwargs):
        self._state_keys = set()
        for key, value in kwargs.items():
            self.add_state(key, value)

    def add_state(self, key, value):
        if key not in st.session_state:
            st.session_state[key] = value
        self._state_keys.add(key)

    def get_state(self, key):
        return self.__getitem__(key)

    def set_state(self, key, value):
        self.__setitem__(key, value)

    def __getitem__(self, item):
        if item in self._state_keys:
            return st.session_state[item]
        else:
            raise AttributeError(f"{item} is not initialized")

    def __setitem__(self, item, value):
        if item in self._state_keys:
            st.session_state[item] = value
        else:
            raise AttributeError(f"{item} is not initialized")


class DataStorage:

    def __init__(self):
        self.state = State(datasets_names=[],
                           datasets={},)

    def add_dataset(self, name, data):
        if (name != "") & (name not in self.state['datasets_names']):
            self.state['datasets_names'].append(name)
            self.state['datasets'][name] = data
            return True
        else:
            return False

    def get_names(self):
        return self.state['datasets_names']

    def get_datasets(self, name):
        return self.state['datasets'][name]



