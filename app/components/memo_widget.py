import streamlit as st

from .state import State

s = State()


def radio(label,
          options,
          key,
          index=0,
          horizontal=True,
          label_visibility="visible",
          format_func=lambda x: x,
          help=None,
          on_change=None,
          ):
    s.add_state(key, index)
    print("Default display value", key, options[s.get_state(key)])

    user_option = st.radio(label=label,
                           label_visibility=label_visibility,
                           options=options,
                           horizontal=horizontal,
                           index=s.get_state(key),
                           key="__" + key,
                           format_func=format_func,
                           help=help,
                           on_change=None,
                           )
    print("Get user option", user_option)
    s.set_state(key, options.index(user_option))
    print("User selected value", key, options[s.get_state(key)])
    return user_option


def checkbox(label,
             key,
             index=0,
             label_visibility="visible",
             format_func=lambda x: x,
             help=None,
             on_change=None,
             disabled=False,
             ):
    s.add_state(key, index)

    user_check = st.checkbox(label=label,
                             value=s.get_state(key),
                             label_visibility=label_visibility,
                             key=f"__{key}",
                             format_func=format_func,
                             help=help,
                             on_change=on_change,
                             disabled=disabled,
                             )

    s.set_state(key, user_check)
    return user_check
