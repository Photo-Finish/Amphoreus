"""An Eternal Page — Beyond Time (Streamlit multipage).

Run via: streamlit run src/ui_app.py
Then open **An Eternal Page** in the sidebar.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="An Eternal Page — Project Amphoreus",
    page_icon="📜",
    layout="wide",
)

from src.ui_gate import enforce_auth, get_manager  # noqa: E402

enforce_auth()
try:
    from src.ui_group_chat import end_if_left_visit_page
    end_if_left_visit_page()
except Exception:
    pass

st.sidebar.title("The Sanctuary")
st.sidebar.caption("Beyond Time — companions on the page, not the land.")

manager = get_manager()
from src.ui_eternal_page import render_eternal_page  # noqa: E402

render_eternal_page(manager, key_prefix="eternal_page")
