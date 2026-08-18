"""Walk the Land — stand in Amphoreus (Streamlit multipage).

Run via: streamlit run src/ui_app.py
Then open **Walk the Land** in the sidebar.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="Walk the Land — Project Amphoreus",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from src.ui_gate import enforce_auth  # noqa: E402

enforce_auth()

from src.ui_walk_land import render_walk_page  # noqa: E402

render_walk_page(key_prefix="walk")
