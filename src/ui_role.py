"""src/ui_role.py — who is signed in: operator (full) or visitor (read-only).

The role is set by the sign-in gate in ui_app.py (st.session_state.ui_role).
These helpers let any UI module render read-only for visitors without knowing
the credential logic.
"""

import streamlit as st

OPERATOR = "operator"
VISITOR = "visitor"


def role() -> str:
    """The signed-in role, defaulting to operator when unknown."""
    return st.session_state.get("ui_role", OPERATOR)


def is_visitor() -> bool:
    """True when a read-only visitor is signed in."""
    return role() == VISITOR


def is_operator() -> bool:
    """True when the operator (or an unauthenticated local user) is signed in."""
    return not is_visitor()
