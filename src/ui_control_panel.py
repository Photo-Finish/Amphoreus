"""The Control Panel — the visitor chooses how to play Amphoreus.

Everything the end user may want to steer, in one place: the experience mode
(journey / aftermath), the live black tide, the world engine, and their
mailbox. All choices persist in the world state.
"""

import subprocess
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# World engine helpers (the engine itself is a separate daemon)
# --------------------------------------------------------------------------- #
def _engine_running() -> bool:
    try:
        import psutil
        for p in psutil.process_iter(["name", "cmdline"]):
            try:
                nm = (p.info.get("name") or "").lower()
                cl = " ".join(p.info.get("cmdline") or [])
            except Exception:
                continue
            if "python" in nm and "world_engine" in cl:
                return True
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "if (Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'world_engine' }) { exit 0 } "
             "else { exit 1 }"],
            capture_output=True, timeout=25)
        return out.returncode == 0
    except Exception:
        return False


def _engine_start() -> bool:
    """Launch the world engine fully detached (survives Streamlit restarts).
    Refuses to double-start: if an engine is already alive, nothing is spawned.
    The base interval is one real day (1x); the Control Panel's time flow
    multiplies it linearly."""
    if _engine_running():
        return False
    try:
        log = PROJECT_ROOT / "world_runtime" / "engine.log"
        err = PROJECT_ROOT / "world_runtime" / "engine.log.err"
        from src.world.world_engine import REAL_DAY_SECONDS
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
             f"Start-Process -FilePath '{sys.executable}' "
             f"-ArgumentList '-m','src.world.world_engine','--interval','{REAL_DAY_SECONDS}' "
             f"-WorkingDirectory '{PROJECT_ROOT}' -WindowStyle Hidden "
             f"-RedirectStandardOutput '{log}' -RedirectStandardError '{err}'"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _engine_stop() -> bool:
    """Ask the engine to rest (it notices the flag within seconds now)."""
    try:
        (PROJECT_ROOT / "world_runtime" / "stop.flag").write_text("stop", encoding="ascii")
        return True
    except Exception:
        return False


def _engine_stopping() -> bool:
    """A stop has been requested but the engine is still finishing up."""
    try:
        return (PROJECT_ROOT / "world_runtime" / "stop.flag").exists()
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# The panel
# --------------------------------------------------------------------------- #
def render_control_panel(manager, characters):
    st.title("🎛️ Control Panel")
    st.caption("Choose how you play Amphoreus. Changes take effect immediately and persist.")

    from src.world.world_state import WorldState
    from src.world import living_world as lw
    from src.core.visitor_mode import current_mode
    from src.core.agent_manager import AgentManager

    ws = WorldState()
    # Today's reach-outs materialize here (idempotent, deduped per Heir per day)
    # so the mailbox stays alive even when the world engine is not running.
    try:
        lw.materialize_reach_outs(ws)
        ws.save()
    except Exception:
        pass

    # ---------------- 1. Experience mode ----------------
    st.markdown("### 🗺️ Experience mode")
    mode = current_mode()
    st.caption(
        ("✨ **Aftermath** — the Heirs remember you as a war-companion."
         if mode == "aftermath" else
         "🗺️ **Journey** — you are newly arrived; the Heirs do not know you yet.")
    )
    choice = st.radio(
        "Choose how the Heirs know you",
        ["journey", "aftermath"],
        index=0 if mode == "journey" else 1,
        format_func=lambda m: ("🗺️ Journey — a new arrival"
                               if m == "journey" else "✨ Aftermath — a war-companion"),
        key="ctl_mode",
    )
    if choice != mode:
        st.warning(
            "Switching mode **reseeds every Heir's bond and rewrites their "
            "campaign memories**: Journey makes everyone a stranger; Aftermath "
            "makes everyone a best friend with the shared Flame-Chase Journey."
        )
        if st.button(f"Switch to {choice}", type="primary", key="ctl_mode_btn"):
            res = manager.switch_mode(choice)
            if res.get("switched"):
                st.success(f"Now in **{choice}** mode — {res['heirs']} Heirs reseeded.")
                st.rerun()
            else:
                st.error(res.get("error", "The switch failed."))

    st.markdown("---")

    # ---------------- 2. Live black tide ----------------
    st.markdown("### 🕳️ Live black tide")
    st.caption(
        "**On** — the tide can stir along the edge cities: travel into a surged "
        "city takes an extra day, and the Heirs there grow weary. **Off** — the "
        "world rests at peace (an active surge winds down)."
    )
    bt = st.toggle("Live black tide", value=bool(ws.black_tide_enabled), key="ctl_bt",
                   help="Turning it off also clears any active surge and its darkened skies.")
    if bt != bool(ws.black_tide_enabled):
        ws.set_black_tide(bt)
        st.rerun()

    st.markdown("---")

    # ---------------- Heir voice ----------------
    st.markdown("### 🗣️ Heir voice")
    _voices = list(AgentManager._VOICE_CHAIN)
    _current_voice = manager.voice_model()
    st.caption(
        "The model that speaks for the Heirs. **gemma3:27b** is the refined "
        "standard voice (the one the style cycle tunes the cards to), but it is "
        "slower on this machine (~1–2 min for a long reply). **qwen2.5:14b-instruct** "
        "is faster and lighter. If the big model cannot load (tight memory), the "
        "other one takes over automatically."
    )
    _voice = st.radio(
        "Who speaks for the Heirs?",
        _voices,
        index=_voices.index(_current_voice) if _current_voice in _voices else 0,
        format_func=lambda v: ("✨ gemma3:27b — the standard voice (slower)"
                               if v == "gemma3:27b" else "⚡ qwen2.5:14b-instruct — fast"),
        key="ctl_voice",
    )
    if _voice != _current_voice:
        _res = manager.set_heir_voice(_voice)
        st.success(f"The Heirs will now speak in {_res['voice']}.")
        st.rerun()

    st.markdown("---")

    # ---------------- 3. Your whereabouts (physical movement) ----------------
    st.markdown("### 📍 Your whereabouts")
    st.caption(
        "You are physically in Amphoreus. Move from city to city — the road "
        "takes whole in-game days, and it advances while the world runs "
        "(pausing only while you are mid-conversation with an Heir)."
    )
    vp = ws.visitor_place()
    if vp["kind"] == "traveling":
        st.info(f"🚶 You are on the road to **{vp['to']}** — **{vp['remaining']}** day(s) left.")
        _here = vp["from"]
        if st.button(f"↩️ Cancel journey (return to {vp['from']})", key="ctl_cancel"):
            ws.visitor_cancel_travel()
            st.success(f"You turn back and return to {vp['from']}.")
            st.rerun()
    else:
        st.success(f"📍 You are in **{vp['at']}**.")
        _here = vp["at"]
    try:
        from src.world import map_data as _md
        _dests = [l for l in _md.ALL_POS
                  if l != _here and _md.travel_time_for(_here, l, "trailblazer") < 999]
    except Exception:
        _dests = []
    if _dests:
        _dest = st.selectbox("Where will you set out for?", _dests, key="ctl_dest")
        _days = _md.travel_days(_here, _dest)
        try:
            from src.world.living_world import surge_travel_penalty as _stp
            _surge_days = _stp(ws, _dest)
        except Exception:
            _surge_days = 0
        if _surge_days:
            _days += _surge_days
            st.caption(f"The road takes **{_days}** in-game day(s) — the black tide "
                       f"adds **{_surge_days}** onto the way into {_dest}.")
        else:
            st.caption(f"The road takes **{_days}** in-game day(s).")
        if st.button("🚶 Set out", key="ctl_setout"):
            ws.visitor_set_out(_dest, _days)
            if _days == 0:
                st.success(f"You are already there — welcome to {_dest}.")
            else:
                st.success(f"You set out for {_dest} — {_days} day(s) on the road.")
            st.rerun()

    st.markdown("---")

    # ---------------- 4. World engine + time flow ----------------
    st.markdown("### 🌍 World engine")
    running = _engine_running()
    stopping = _engine_stopping()
    if running and stopping:
        st.warning("⏹ A stop is in progress — the engine rests as soon as its current "
                   "moment's work allows (a few seconds now).")
    elif running:
        st.success("The world engine is running — Amphoreus lives while you are away.")
    else:
        st.info("The world engine is not running — the Heirs wait for you. Start it to "
                "let the world move on its own (it uses the GPU/RAM for the Ambient "
                "Director and the Heirs' free days).")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶️ Start the world", disabled=running, key="ctl_eng_start"):
            if _engine_start():
                st.success("The world engine is starting… (give it a minute to load)")
                st.rerun()
            else:
                st.error("Could not start the engine.")
    with c2:
        if st.button("⏹ Stop the world", disabled=not running, key="ctl_eng_stop"):
            _engine_stop()
            st.success("A stop is requested — the engine will rest within seconds.")
            st.rerun()

    st.markdown("### ⏱️ Time flow")
    st.caption(
        "How fast the world elapses while the engine runs, measured linearly "
        "against real time: **1x** = one in-game day per real day; **60x** = "
        "24 real minutes per in-game day (each day still needs a little time "
        "to be lived — every Heir decides for themselves)."
    )
    _scales = [("1x", 1), ("2x", 2), ("5x", 5), ("10x", 10), ("30x", 30), ("60x", 60)]
    _cur_scale = float(ws.time_scale or 1.0)
    _cur_idx = min(range(len(_scales)), key=lambda i: abs(_scales[i][1] - _cur_scale))
    _chosen = st.radio("How fast should the world move?", _scales, index=_cur_idx,
                       format_func=lambda s: s[0], key="ctl_time")
    if float(_chosen[1]) != _cur_scale:
        ws.set_time_scale(_chosen[1])
        st.rerun()

    st.markdown("---")

    # ---------------- 4. Mailbox ----------------
    st.markdown("### 📬 Your mailbox")
    unread = lw.unread_count(ws, "visitor")
    notes = lw.mailbox_for(ws, "visitor")
    st.caption(f"{len(notes)} note(s), **{unread} unread** — also shown in the Gazette.")
    if st.button("Mark all read", disabled=unread == 0, key="ctl_mail"):
        lw.mark_all_read(ws, "visitor")
        ws.save()
        st.rerun()
    if notes:
        with st.expander("Show notes"):
            for n in notes[-8:][::-1]:
                st.markdown(f"- **{n.get('from')}** — {n.get('text')} *({n.get('ts')})*")

    st.markdown("---")
    st.caption("Everything here persists in the world state and is safe to change any time.")
