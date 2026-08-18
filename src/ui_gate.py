"""Shared Streamlit auth + AgentManager for multipage Sanctuary UI."""

from __future__ import annotations

import json as _json
import os as _os
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_ui_auth():
    env_u = _os.environ.get("AMPHOREUS_UI_USER", "").strip()
    env_p = _os.environ.get("AMPHOREUS_UI_PASS", "")
    try:
        _f = PROJECT_ROOT / "world_runtime" / "ui_auth.json"
        _d = _json.loads(_f.read_text(encoding="utf-8"))
    except Exception:
        _d = {}
    op = (env_u, env_p) if (env_u and env_p) else (
        str(_d.get("username", "")), str(_d.get("password", "")))
    vis = (str(_d.get("visitor_username", "Visitor")),
           str(_d.get("visitor_password", "")))
    return op, vis


def enforce_auth() -> None:
    """Block until signed in when credentials are configured."""
    (_UI_USER, _UI_PASS), (_VISITOR_USER, _VISITOR_PASS) = _load_ui_auth()
    if not (_UI_USER and _UI_PASS):
        if "ui_role" not in st.session_state:
            st.session_state.ui_role = "operator"
        return
    if st.session_state.get("ui_authed"):
        return
    st.markdown(
        "<style>.stApp{background:linear-gradient(160deg,#0b0a14,#131022)}</style>",
        unsafe_allow_html=True)
    st.title("The Sanctuary of the Chrysos Heirs")
    st.caption("This world is behind a key. Sign in to enter."
               " (Visitors: use the read-only account.)")
    _u = st.text_input("Username", key="gate_user")
    _p = st.text_input("Password", type="password", key="gate_pass")
    if st.button("Enter the Sanctuary", key="gate_enter"):
        if _u == _UI_USER and _p == _UI_PASS:
            st.session_state.ui_authed = True
            st.session_state.ui_role = "operator"
            st.rerun()
        elif _VISITOR_USER and _VISITOR_PASS \
                and _u == _VISITOR_USER and _p == _VISITOR_PASS:
            st.session_state.ui_authed = True
            st.session_state.ui_role = "visitor"
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    if _VISITOR_USER and _VISITOR_PASS:
        st.divider()
        st.caption("No key? You may look around in read-only mode:")
        if st.button("Visit as a guest (read-only)", key="gate_guest"):
            st.session_state.ui_authed = True
            st.session_state.ui_role = "visitor"
            st.rerun()
    st.stop()


@st.cache_resource
def get_manager():
    from src.core.agent_manager import AgentManager
    return AgentManager(
        characters_dir=str(PROJECT_ROOT / "src" / "characters"),
        llm_model="gemma3:27b",
        use_rag=True,
        rag_persist_dir=str(PROJECT_ROOT / ".chroma_db"),
        memory_root=str(PROJECT_ROOT),
    )
