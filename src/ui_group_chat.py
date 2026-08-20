"""Stage 2 — Visit UI for group chat (invitation, gathering, leave Visit).

Bulk of the logic lives in `src/world/group_chat.py`. This module is the
Streamlit surface: co-presence choice, invite buttons, routing chat into the
gathering, and ending the session when the operator leaves **Visit an Heir**.
Guests may see that Heirs are together; they cannot send invitations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from src.world import group_chat as gc
from src.world.world_state import WorldState

ASSETS = Path(__file__).resolve().parent.parent / "assets"
_TAB_Q = "amp_tab"
_LEAVE_KEY = "amp_gc_leave"
_MODE_KEY = "amp_gc_mode"
_PICK_KEY = "amp_gc_invitees"


def _ss():
    import streamlit as st
    return st.session_state


def store():
    ss = _ss()
    return ss.setdefault(gc.STATE_KEY, gc.blank_session())


def group_is_active() -> bool:
    try:
        return gc.session_active(store())
    except Exception:
        return False


def group_messages() -> list:
    try:
        return list(store().get("messages") or [])
    except Exception:
        return []


def end_group_session() -> dict:
    """End the gathering (leaving Visit, or an explicit return to 1:1)."""
    try:
        ss = _ss()
        old = gc.session_end(ss)
        ss[_MODE_KEY] = "individual"
        ss["amp_gc_kind_radio"] = "Individual chat"
        return old
    except Exception:
        return gc.blank_session()


def end_if_left_visit_page() -> None:
    """Call from Streamlit multipage scripts that are not Visit (Walk, Panel)."""
    try:
        if group_is_active():
            end_group_session()
    except Exception:
        pass


def _name_of(manager, cid: str) -> str:
    try:
        return manager.get_character_info(cid)["name"]
    except Exception:
        try:
            return WorldState().name_of(cid)
        except Exception:
            return cid


def avatar_path(character_id: str) -> Optional[str]:
    folder = ASSETS / "avatars"
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = folder / f"{character_id}.{ext}"
        if p.exists():
            return str(p)
    portraits = ASSETS / "heirs"
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = portraits / f"{character_id}.{ext}"
        if p.exists():
            return str(p)
    return None


def consume_leave_signals() -> bool:
    """End the gathering when Visit is no longer the active page/tab."""
    import streamlit as st

    ended = False
    try:
        tab_q = str(st.query_params.get(_TAB_Q) or "")
    except Exception:
        tab_q = ""
    if gc.should_end_for_query(tab_q) and group_is_active():
        end_group_session()
        ended = True
        try:
            del st.query_params[_TAB_Q]
        except Exception:
            pass
    return ended


def mount_visit_session_guard() -> None:
    """Hidden leave-button + tab watcher. Call once per ui_app rerun (outside tabs).

    Streamlit renders every tab body each rerun, so Python cannot see which tab
    is visible. A parent-page watcher clicks a hidden button when the selected
    tab is no longer Visit — that rerun ends the gathering. Closing localhost
    is not an end condition.
    """
    import streamlit as st

    consume_leave_signals()

    active = group_is_active()
    st.markdown(
        "<style>.st-key-amp_gc_leave{display:none!important;height:0;}</style>",
        unsafe_allow_html=True,
    )
    if st.button("amp_gc_leave", key=_LEAVE_KEY):
        if active or group_is_active():
            end_group_session()

    _inject_tab_watcher(active)


_WATCHER = """
<script>
(function(){
  var GROUP_ON = %s;
  var doc;
  try { doc = window.parent.document; } catch (e) { return; }
  if (!doc) return;
  window.parent.__amp_gc_group_on = GROUP_ON;
  function tabName(){
    var root = doc.querySelector('[data-testid="stTabs"]') || doc;
    var t = root.querySelector('[role="tab"][aria-selected="true"]');
    return ((t && t.innerText) || '').replace(/\\s+/g, ' ').trim();
  }
  function isVisit(name){
    return name === 'Visit an Heir';
  }
  function clickLeave(){
    if (!window.parent.__amp_gc_group_on) return;
    if (window.parent.__amp_gc_leaving) return;
    window.parent.__amp_gc_leaving = true;
    var wrap = doc.querySelector('.st-key-amp_gc_leave');
    var btn = wrap && wrap.querySelector('button');
    if (btn) {
      btn.click();
      return;
    }
    var buttons = doc.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      if ((buttons[i].innerText || '').trim() === 'amp_gc_leave') {
        buttons[i].click();
        return;
      }
    }
  }
  function sync(){
    var name = tabName();
    window.parent.__amp_gc_tab = name;
    if (!isVisit(name)) clickLeave();
    else window.parent.__amp_gc_leaving = false;
  }
  if (!window.parent.__amp_gc_watch) {
    window.parent.__amp_gc_watch = true;
    doc.addEventListener('click', function(){ setTimeout(sync, 40); }, true);
    try {
      new MutationObserver(sync).observe(doc.body, {
        attributes: true, subtree: true, attributeFilter: ['aria-selected']
      });
    } catch (e) {}
  }
  sync();
})();
</script>
"""


def _inject_tab_watcher(group_on: bool) -> None:
    import streamlit as st
    try:
        import streamlit.components.v1 as components
        flag = "true" if group_on else "false"
        components.html(_WATCHER % flag, height=0, scrolling=False)
    except Exception:
        try:
            st.markdown(_WATCHER % ("true" if group_on else "false"),
                        unsafe_allow_html=True)
        except Exception:
            pass


def _world():
    return WorldState()


def render_group_chat_controls(manager, selected: str, info: dict,
                               place: str) -> None:
    """Individual vs group choice + invitations. Guests look only."""
    import streamlit as st
    from src.ui_role import is_visitor

    try:
        ws = _world()
    except Exception:
        return

    sess = store()
    if sess.get("active") and not gc.still_together(ws, sess):
        place_was = sess.get("place") or place
        end_group_session()
        st.caption(
            f"The gathering in **{place_was}** thins — not enough Heirs remain "
            "together. The hour returns to one voice."
        )
        sess = store()

    if group_is_active():
        names = ", ".join(_name_of(manager, c) for c in sess.get("members") or [])
        st.caption(
            f"Gathering in **{sess.get('place') or place}** — {names}. "
            "Leave **Visit an Heir** and the gathering ends."
        )
        if not is_visitor():
            if st.button("Return to individual chat", key="amp_gc_to_solo"):
                end_group_session()
                st.rerun()
        return

    if not gc.group_possible(ws, selected):
        if _ss().get(_MODE_KEY) == "group":
            _ss()[_MODE_KEY] = "individual"
        return

    others = gc.companions_for_group(ws, selected)
    other_names = ", ".join(_name_of(manager, c) for c in others)
    host_name = info.get("name") or _name_of(manager, selected)
    here = place or ws.location_name(selected)
    st.caption(
        f"Several Heirs stand together in **{here}**: {host_name}"
        + (f", {other_names}" if other_names else "")
        + "."
    )

    if not gc.operator_may_invite(is_visitor()):
        st.caption(
            "A gathering could form here — guests may look, not send invitations."
        )
        return

    if "amp_gc_kind_radio" not in st.session_state:
        st.session_state["amp_gc_kind_radio"] = "Individual chat"
    # Scoped chrome: transparent / hairline gold (matches Visit selectboxes).
    st.markdown(
        """
<style>
.st-key-amp_gc_mode_chrome,
.st-key-amp_gc_mode_chrome [data-testid="stRadio"],
.st-key-amp_gc_mode_chrome [data-testid="stRadioGroup"],
.st-key-amp_gc_mode_chrome [role="radiogroup"],
.st-key-amp_gc_mode_chrome [data-testid="stElementContainer"],
.st-key-amp_gc_mode_chrome [data-testid="stHorizontalBlock"] {
  background: transparent !important;
  background-color: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}
.st-key-amp_gc_mode_chrome [data-testid="stRadio"],
.st-key-amp_gc_mode_chrome [role="radiogroup"] {
  border: none !important;
  border-bottom: 1px solid rgba(232, 213, 163, 0.32) !important;
  padding: 0.1rem 0 !important;
}
.st-key-amp_gc_mode_chrome [data-testid="stWidgetLabel"] p,
.st-key-amp_gc_mode_chrome [data-testid="stRadio"] label,
.st-key-amp_gc_mode_chrome [data-testid="stRadioOption"],
.st-key-amp_gc_mode_chrome [role="radiogroup"] label {
  background: transparent !important;
  color: var(--amp-text-body, #f0e6c8) !important;
  text-shadow: var(--amp-text-shadow,
    0 0 1px rgba(0,0,0,.95), 0 1px 2px rgba(0,0,0,.88),
    0 2px 8px rgba(0,0,0,.72)) !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="amp_gc_mode_chrome"):
        kind = st.radio(
            "How will you speak?",
            ("Individual chat", "Group chat"),
            horizontal=True,
            key="amp_gc_kind_radio",
            help=(
                "Individual: the current conversation. Group: invite Heirs who are "
                "already here. The gathering ends when you leave Visit an Heir."
            ),
        )
    st.session_state[_MODE_KEY] = "group" if kind == "Group chat" else "individual"
    if kind != "Group chat":
        return

    labels = {_name_of(manager, c): c for c in others}
    picked_names = st.multiselect(
        "Who shall you invite?",
        list(labels.keys()),
        default=list(labels.keys()),
        key=f"{_PICK_KEY}_{selected}",
        help=f"{host_name} is already with you. Invite at least one other.",
    )
    invitees = [labels[n] for n in picked_names if n in labels]
    if not invitees:
        st.caption("Invite at least one other Heir who is here.")
        return
    if st.button("Send invitations", key=f"amp_gc_send_{selected}"):
        def _speak(cid, prompt):
            extra = (
                "# A gathering, not a trial\n"
                "The star-stranger asks you to sit with company already here. "
                "Answer in your own spoken words. Do not lecture about being "
                "an experiment. End with ACCEPT or DECLINE."
            )
            return gc.heir_speak(manager, cid, prompt, extra_system=extra)

        # No st.spinner — its overlay flashes white over the land.
        st.caption("Word goes out across the place…")
        result = gc.send_invitations(
            ws, selected, invitees,
            name_of=lambda c: _name_of(manager, c),
            speak=_speak,
            store=_ss(),
        )
        # Keep a trace on the 1:1 thread so returning to individual still
        # remembers that the invitation happened.
        msgs = st.session_state.setdefault("messages", {})
        hist = msgs.setdefault(selected, [])
        hist.append({
            "role": "user",
            "content": "*(you ask those here to sit together and speak)*",
        })
        for r in result.get("replies") or []:
            hist.append({
                "role": "assistant",
                "content": r.get("content") or "",
                "speaker": r.get("speaker") or "",
            })
        hist.append({
            "role": "assistant",
            "content": result.get("world_line") or "",
        })
        if result.get("started"):
            st.session_state[_MODE_KEY] = "group"
            st.session_state["amp_gc_kind_radio"] = "Group chat"
        else:
            st.session_state[_MODE_KEY] = "individual"
            st.session_state["amp_gc_kind_radio"] = "Individual chat"
            gc.session_end(_ss())
        st.rerun()


def render_group_transcript(user_avatar=None,
                            avatar_fn: Optional[Callable] = None) -> None:
    import streamlit as st

    avatar_fn = avatar_fn or avatar_path
    for msg in group_messages():
        role = msg.get("role") or "assistant"
        speaker = msg.get("speaker") or ""
        if role == "user":
            av = user_avatar
        else:
            path = avatar_fn(speaker) if speaker else None
            av = str(path) if path else None
        with st.chat_message(role, avatar=av):
            if speaker and role == "assistant":
                try:
                    nm = WorldState().name_of(speaker)
                except Exception:
                    nm = speaker
                st.caption(nm)
            st.markdown(msg.get("content") or "")


def group_input_placeholder(host_name: str) -> str:
    if group_is_active():
        return "Speak to the gathering..."
    return f"Speak to {host_name}..."


def handle_group_prompt(manager, prompt: str, *,
                        user_avatar=None,
                        avatar_fn: Optional[Callable] = None,
                        display: bool = True) -> None:
    """Route a Visit chat_input turn into the active gathering.

    ``display=False`` when a fragment will rerun and redraw the transcript.
    """
    import streamlit as st

    avatar_fn = avatar_fn or avatar_path
    try:
        WorldState().mark_visitor_present()
    except Exception:
        pass

    gc.append_message(store(), role="user", content=prompt)
    if display:
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(prompt)

    def _nm(cid):
        return _name_of(manager, cid)

    # No spinner — keeps the land from flashing white during multi-voice turns.
    lines = gc.generate_group_turn(
        manager, _ss(), prompt, world=_world(), name_of=_nm,
    )
    if display:
        for msg in lines:
            speaker = msg.get("speaker") or ""
            path = avatar_fn(speaker) if speaker else None
            av = str(path) if path else None
            with st.chat_message("assistant", avatar=av):
                if speaker:
                    st.caption(_nm(speaker))
                st.markdown(msg.get("content") or "")
    if not lines:
        world_line = (
            "The gathering holds a quiet. No one adds a word this turn."
        )
        gc.append_message(store(), role="assistant", content=world_line)
        if display:
            with st.chat_message("assistant"):
                st.markdown(world_line)


def _run_group_chat_fragment(manager, host_name: str, *,
                             user_avatar=None,
                             avatar_fn: Optional[Callable] = None) -> None:
    """Body of the group-chat fragment (defined once for stable fragment ids)."""
    import streamlit as st
    from src.ui_role import is_visitor

    avatar_fn = avatar_fn or avatar_path
    render_group_transcript(user_avatar=user_avatar, avatar_fn=avatar_fn)
    if is_visitor():
        st.caption(
            "Read-only view — sign in as the operator to speak with "
            "the gathering."
        )
        return
    prompt = st.chat_input(
        group_input_placeholder(host_name),
        key="visit_group_chat_input",
    )
    if prompt:
        handle_group_prompt(
            manager, prompt,
            user_avatar=user_avatar, avatar_fn=avatar_fn,
            display=False,
        )
        st.rerun(scope="fragment")


def render_group_conversation(
    manager,
    selected: str,
    info: dict,
    *,
    user_avatar=None,
    avatar_fn: Optional[Callable] = None,
) -> None:
    """Active gathering: transcript + docked input in a fragment.

    Fragment-scoped sends keep the land iframe mounted (no white page blink).
    """
    import streamlit as st

    host_name = (info or {}).get("name") or selected
    fragment = getattr(st, "fragment", None)
    if fragment is None:
        # Very old Streamlit — fall back to full-script path.
        render_group_transcript(user_avatar=user_avatar, avatar_fn=avatar_fn)
        return

    @fragment
    def _group_chat_fragment():
        _run_group_chat_fragment(
            manager, host_name,
            user_avatar=user_avatar, avatar_fn=avatar_fn,
        )

    _group_chat_fragment()
