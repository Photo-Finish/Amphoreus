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
    """Launch the world engine fully detached (survives Streamlit restarts)."""
    try:
        log = PROJECT_ROOT / "world_runtime" / "engine.log"
        err = PROJECT_ROOT / "world_runtime" / "engine.log.err"
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
             f"Start-Process -FilePath '{sys.executable}' "
             f"-ArgumentList '-m','src.world.world_engine','--interval','900' "
             f"-WorkingDirectory '{PROJECT_ROOT}' -WindowStyle Hidden "
             f"-RedirectStandardOutput '{log}' -RedirectStandardError '{err}'"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _engine_stop() -> bool:
    """Ask the engine to rest after its current day (it clears the flag on start)."""
    try:
        (PROJECT_ROOT / "world_runtime" / "stop.flag").write_text("stop", encoding="ascii")
        return True
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

    # ---------------- 3. World engine ----------------
    st.markdown("### 🌍 World engine")
    running = _engine_running()
    if running:
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
            st.success("A stop is requested — the engine will rest after its current day.")
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
