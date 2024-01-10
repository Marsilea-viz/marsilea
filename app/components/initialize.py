import functools

import streamlit as st
from streamlit import cursor
from streamlit.delta_generator import DeltaGenerator, Block_pb2
from streamlit.delta_generator import _enqueue_message
from streamlit.elements.form import FormData, current_form_id
from streamlit.proto import ForwardMsg_pb2
from streamlit.runtime import caching


def _nestable_block(
        self,
        block_proto: Block_pb2.Block = Block_pb2.Block(),
) -> "DeltaGenerator":
    # Operate on the active DeltaGenerator, in case we're in a `with` block.
    dg = self._active_dg

    # Prevent nested columns & expanders by checking all parents.
    block_type = block_proto.WhichOneof("type")
    # Convert the generator to a list, so we can use it multiple times.
    # parent_block_types = frozenset(dg._parent_block_types)
    # if block_type == "column" and block_type in parent_block_types:
    #     raise StreamlitAPIException(
    #         "Columns may not be nested inside other columns."
    #     )
    # if block_type == "expandable" and block_type in parent_block_types:
    #     raise StreamlitAPIException(
    #         "Expanders may not be nested inside other expanders."
    #     )

    if dg._root_container is None or dg._cursor is None:
        return dg

    msg = ForwardMsg_pb2.ForwardMsg()
    msg.metadata.delta_path[:] = dg._cursor.delta_path
    msg.delta.add_block.CopyFrom(block_proto)

    # Normally we'd return a new DeltaGenerator that uses the locked cursor
    # below. But in this case we want to return a DeltaGenerator that uses
    # a brand new cursor for this new block we're creating.
    block_cursor = cursor.RunningCursor(
        root_container=dg._root_container,
        parent_path=dg._cursor.parent_path + (dg._cursor.index,),
    )
    block_dg = DeltaGenerator(
        root_container=dg._root_container,
        cursor=block_cursor,
        parent=dg,
        block_type=block_type,
    )
    # Blocks inherit their parent form ids.
    # NOTE: Container form ids aren't set in proto.
    block_dg._form_data = FormData(current_form_id(dg))

    # Must be called to increment this cursor's index.
    dg._cursor.get_locked_cursor(last_index=None)
    _enqueue_message(msg)

    caching.save_block_message(
        block_proto,
        invoked_dg_id=self.id,
        used_dg_id=dg.id,
        returned_dg_id=block_dg.id,
    )

    return block_dg


@functools.cache
def enable_nested_columns():
    DeltaGenerator._block = _nestable_block


def inject_css():
    # Hack the style of elements in streamlit
    st.markdown("""
    <style>

        # .main .block-container {
        #     min-width: 1000px;
        #     max-width: 1200px;
        # }

        div[data-testid='stImage']>img {
            max-height: 600px;
            object-fit: contain;
        }

        .streamlit-expanderContent {
            padding-right: 0rem;
            padding-left: 0rem;
        }

        .streamlit-expanderHeader {
            font-weight: bold;
            padding-right: 0rem;
            padding-left: 0rem;
        }

        .streamlit-expander {
            border-left: none;
            border-right: none;
            border-radius: 0rem;
        }

    </style>
    """, unsafe_allow_html=True)


def init_page(title):
    IMG_ROOT = "https://raw.githubusercontent.com/" \
               "Marsilea-viz/marsilea/main/app/img"

    st.set_page_config(
        page_title=title,
        layout="centered",
        page_icon=f"{IMG_ROOT}/favicon.png",
        # initial_sidebar_state="collapsed",
        menu_items={
            'Report a bug': 'https://github.com/Marsilea-viz/marsilea/issues/new/choose',
            'About': 'A web interface for Marsilea'
        }
    )
