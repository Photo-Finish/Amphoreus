"""Dedicated Control Panel page (Streamlit multipage).

Run via: streamlit run src/ui_app.py
Then open **Control Panel** in the sidebar page list.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="Control Panel — Project Amphoreus",
    page_icon="🎛️",
    layout="wide",
)

from src.ui_gate import enforce_auth, get_manager  # noqa: E402

enforce_auth()
manager = get_manager()
characters = manager.list_available_characters()

from src.ui_control_panel import render_control_panel  # noqa: E402

render_control_panel(manager, characters)
