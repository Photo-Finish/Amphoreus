"""
Streamlit UI for Project Amphoreus — Chat with the Chrysos Heirs.

Usage:
    streamlit run src/ui_app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent_manager import AgentManager


# Page config
st.set_page_config(
    page_title="Project Amphoreus — Chrysos Heirs",
    page_icon="🔥",
    layout="wide",
)

# --------------------------------------------------------------------------- #
# Visual theme — the Sanctuary of the Chrysos Heirs
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS = PROJECT_ROOT / "assets"
HEIR_PORTRAITS_DIR = ASSETS / "heirs"
HEIR_AVATARS_DIR = ASSETS / "avatars"
BG_IMAGE = ASSETS / "amphoreus_bg.jpg"


def portrait_for(character_id: str):
    """Path to the Heir's portrait, if downloaded."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = HEIR_PORTRAITS_DIR / f"{character_id}.{ext}"
        if p.exists():
            return p
    return None


def avatar_for(character_id: str):
    """Path to the Heir's square chat avatar, falling back to the portrait."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = HEIR_AVATARS_DIR / f"{character_id}.{ext}"
        if p.exists():
            return p
    return portrait_for(character_id)


# Ethereal Amphoreus theme (dark gold, no heavy base64 in the page)
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(160deg, #0b0a14 0%, #131022 45%, #0d0b18 100%); }
    .block-container { padding-top: 1.4rem; }
    h1, h2, h3 { color: #e8d5a3; letter-spacing: .5px; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141126 0%, #0d0b18 100%);
        border-right: 1px solid rgba(232,213,163,.12);
    }
    [data-testid="stSidebar"] * { color: #d8cfa8; }
    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,.035);
        border: 1px solid rgba(232,213,163,.10);
        border-radius: 12px;
        padding: .4rem .8rem;
    }
    .stTabs [data-baseweb="tab-list"] { gap: .6rem; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #e8d5a3; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Agent Manager
@st.cache_resource
def get_manager():
    return AgentManager(
        characters_dir=str(Path(__file__).parent / "characters"),
        llm_model="qwen2.5:14b-instruct",
        use_rag=True,
        rag_persist_dir=str(Path(__file__).parent.parent / ".chroma_db"),
        memory_root=str(Path(__file__).parent.parent),  # per-Heir folders at project root
    )


manager = get_manager()

# Sidebar — Character Selection
st.sidebar.title("🏛️ Project Amphoreus")
st.sidebar.markdown("### The Sanctuary of the Chrysos Heirs")

# LLM status
if manager.llm.configured:
    st.sidebar.success(f"🗣️ Voice: Ready ({manager.llm.model})")
else:
    st.sidebar.warning(
        "🗣️ Voice: Offline — start Ollama (`ollama serve`) or set OPENAI_BASE_URL "
        "to hear the Heirs speak."
    )

# RAG status
try:
    rag = manager.rag_status()
    if rag.get("enabled"):
        n_docs = rag.get("total_documents", 0)
        st.sidebar.success(
            f"📚 RAG: Ready\n\n{n_docs} canon documents indexed\n({rag.get('embedding', 'auto')} embeddings)"
        )
        if st.sidebar.button("🔄 Rebuild Knowledge Base"):
            with st.spinner("Rebuilding RAG index..."):
                manager.build_knowledge_base()
            st.rerun()
    else:
        st.sidebar.warning("📚 RAG: Disabled")
except Exception as e:
    st.sidebar.warning(f"📚 RAG: Unavailable ({e})")

characters = manager.list_available_characters()
if not characters:
    st.sidebar.warning("No character cards found in src/characters/")
    st.stop()

selected = st.sidebar.selectbox(
    "Select a Chrysos Heir to speak with:",
    characters,
    format_func=lambda x: manager.get_character_info(x)["name"],
)

# Portrait of the chosen Heir
_selected_portrait = portrait_for(selected)
if _selected_portrait:
    st.sidebar.image(str(_selected_portrait), width=190)

# Display character info
info = manager.get_character_info(selected)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**{info['name']}**")
st.sidebar.markdown(f"*{', '.join(info['titles'])}*")
st.sidebar.markdown(f"Coreflame: **{info['coreflame']}**")
st.sidebar.markdown(f"Traits: {', '.join(info['personality_traits'])}")

# Bond with the visitor
level_emoji = {
    "stranger": "🌫️", "acquaintance": "🌤️", "friend": "🌿",
    "close friend": "🌙", "best friend": "⭐",
}
# Visitor mode (journey vs aftermath — see src/core/visitor_mode.py)
try:
    from src.core.visitor_mode import current_mode
    _mode = current_mode()
    if _mode == "aftermath":
        st.sidebar.caption("✨ Mode: **Aftermath** — the Iron Tomb is conquered; the Heirs remember you as a war-companion.")
    else:
        st.sidebar.caption("🗺️ Mode: **Journey** — you are newly arrived; the Heirs do not know you yet.")
except Exception:
    pass
try:
    bond = manager.get_bond_info(selected)
    level = bond.get("friendship_level", "stranger")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Bond with you:** {level_emoji.get(level, '🌫️')} {level}")
    st.sidebar.markdown(
        f"Visits: **{bond.get('visits', 0)}** · Memories: **{bond.get('memories', 0)}**"
    )
    if bond.get("first_met"):
        st.sidebar.caption(f"First met: {bond.get('first_met')[:16].replace('T', ' ')}")
except Exception:
    pass

# Reset button — this is a heavy act: it erases the Heir's memory of you
if st.sidebar.button("🗑️ Forget me (reset)"):
    manager.reset_conversation(selected)
    st.rerun()

# Senses status (hearing / eyesight / music)
try:
    sn = manager.senses_status()
    st.sidebar.markdown("---")
    eye = "👁️ Eyes: Ready" if sn.get("eyesight") else "👁️ Eyes: offline (set VISION_MODEL)"
    ear = "👂 Ears: Ready" if sn.get("hearing") else "👂 Ears: offline (no STT model)"
    music = "🎵 Music: Ready" if sn.get("music") else "🎵 Music: offline (set AUDIO_MODEL)"
    st.sidebar.caption(f"{eye}\n\n{ear}\n\n{music}")
except Exception:
    pass

st.sidebar.markdown("---")
try:
    ms = manager.memory_stats()
    st.sidebar.caption(
        f"🧠 The Heirs hold **{ms['memories']}** memories across **{ms['heirs_with_bonds']}** bonds"
    )
except Exception:
    pass
st.sidebar.caption("*Project Amphoreus — the Sanctuary*")
st.sidebar.caption("*Databank: Complete ✅*")
st.sidebar.caption("*See PHILOSOPHY.md for the charter*")

# Main Area
main_tab, chronicle_tab, map_tab, admin_tab, game_tab = st.tabs([
    "💬 Visit an Heir",
    "📖 A Chronicle of Amphoreus",
    "🗺️ Map of Amphoreus",
    "🛠️ Admin Console",
    "🎬 Galgame",
])

with game_tab:
    # 🎬 Galgame view — an OPTIONAL visual-novel rendering of the same
    # conversation. The Classic interface above is untouched.
    try:
        from src.ui_galgame import render_galgame
        render_galgame(manager, selected, info)
    except Exception as e:
        st.error(f"Could not render the galgame view: {e}")


with chronicle_tab:
    if BG_IMAGE.exists():
        st.image(str(BG_IMAGE), width="stretch")
    # The end-user edition: the Gazette gathers the whole world's news into
    # one readable page. (The Admin Console's monitor page keeps its raw,
    # operational look — it is not changed here.)
    try:
        from src.ui_gazette import render_gazette
        render_gazette(manager, characters)
    except Exception as e:
        st.error(f"The gazette could not be composed: {e}")
        try:
            from src.world.chronicle import Chronicle
            ch = Chronicle(str(Path(__file__).parent.parent / "world_runtime" / "chronicle"))
            st.markdown(ch.read_markdown(60))
        except Exception:
            st.info("The chronicle is not written yet — the world engine has not begun its days.\n\nStart it with: `python -m src.world.world_engine --interval 900`")

with map_tab:
    # 🗺️ The Map of Amphoreus — geography, commuting time, and daily routines.
    try:
        from src.world.world_state import WorldState
        from src.world import map_data as _map
        from src.world import schedules as _sched

        _ws = WorldState()
        st.title("🗺️ Map of Amphoreus")
        st.caption(
            "The Heirs are spread across a wide world. Each dot is an Heir at their "
            "present place; crossed dots are on the road between cities. Travel is "
            "measured in Light-Calendar periods (5 = one full day)."
        )

        _names = {c: manager.get_character_info(c)["name"] for c in characters}
        _svg = _map.render_map_svg(
            heir_locations=_ws.agent_location,
            traveling=_ws.agent_travel,
            heir_names=_names,
            highlight=None,
        )
        st.markdown(_svg, unsafe_allow_html=True)

        # Current clock + who's where / who's travelling
        st.markdown(f"### ⏳ Now: {_ws.clock.format()}")

        # Today's stage, set by the Keeper (the Ambient World Director)
        _weather = (_ws.ambient.get("weather") or {})
        _errands = (_ws.ambient.get("errands") or {})
        _news = _ws.ambient.get("news", "")
        if _weather or _errands or _news:
            st.markdown("### 🌤️ Today's sky")
            for _city, _sky in _weather.items():
                if _sky:
                    st.markdown(f"- **{_city}** — {_sky}")
            if _news:
                st.markdown(f"*News from the wider world: {_news}*")
            with st.expander("📜 Errands laid at the Heirs' doors today"):
                for _cid, _errand in _errands.items():
                    if not _errand:
                        continue
                    if isinstance(_errand, dict):
                        _ask = (_errand.get("ask") or "").strip()
                        _cause = (_errand.get("cause") or "").strip()
                        _txt = _ask + (f" — *cause:* {_cause}" if _cause else "")
                    else:
                        _txt = str(_errand)
                    st.markdown(f"- **{_names.get(_cid, _cid)}** — {_txt}")

        col_w, col_t = st.columns(2)
        with col_w:
            st.markdown("**Present**")
            present_rows = []
            for cid, loc in _ws.agent_location.items():
                if cid in _ws.agent_travel:
                    continue
                present_rows.append(f"- {_names.get(cid, cid)} — {loc}")
            st.markdown("\n".join(present_rows) if present_rows else "*Everyone is on the road.*")
        with col_t:
            st.markdown("**On the road**")
            if _ws.agent_travel:
                for cid, info in _ws.agent_travel.items():
                    st.markdown(
                        f"- {_names.get(cid, cid)} → {info['to']} "
                        f"({info['remaining_days']} day(s) left)"
                    )
            else:
                st.markdown("*No one is travelling right now.*")

        # Travel-time matrix
        st.markdown("### 🚶 Commuting time (in periods, 5 = a day)")
        _locs = list(_map.LOCATION_POS.keys())
        table = []
        for a in _locs:
            row = {"From": a}
            for b in _locs:
                row[b] = _map.travel_time(a, b)
            table.append(row)
        import pandas as pd
        st.dataframe(
            pd.DataFrame(table).set_index("From"),
            use_container_width=True,
            height=min(40 + 32 * len(_locs), 420),
        )

        # Area art — browse the places of Amphoreus (wiki area backgrounds).
        try:
            from src.ui_backgrounds import available_backgrounds, location_slug as _locslug
            _areas = available_backgrounds()
            if _areas:
                _default = None
                for _cid, _loc in _ws.agent_location.items():
                    if _cid in _ws.agent_travel:
                        continue
                    _default = _locslug(_loc)
                    if _default:
                        break
                _map_slug = dict(_areas)
                _opts = list(_map_slug)
                _labels = {s: s.replace("-", " ").title() for s in _opts}
                if _default in _opts:
                    _idx = _opts.index(_default)
                else:
                    _idx = 0
                st.markdown("### 🖼️ Area art")
                _sel = st.selectbox(
                    "Choose a place to view", _opts, format_func=lambda s: _labels[s],
                    index=_idx, key="map_area_sel",
                )
                # The area's art, wearing today's weather (set by the Keeper).
                try:
                    from src.ui_weather import render_scene as _wx_scene
                    _wx_scene(_sel, image_path=_map_slug[_sel], title=_labels[_sel], height=320)
                except Exception:
                    st.image(str(_map_slug[_sel]), width="stretch")
                st.caption(f"**{_labels[_sel]}** — Amphoreus, as the wiki's area art shows it.")
        except Exception:
            pass

        # Individual weekly schedules
        st.markdown("### 📅 Individual weekly routines")
        st.caption(
            "Each Heir keeps a routine of their own. Heirs who live and work together "
            "(the Okhema council circle, the scholars of the Grove, the two souls of "
            "Aedes Elysiae) cross paths often; the rest meet only when someone is "
            "willing to spend days on the road."
        )
        sched_sel = st.selectbox(
            "Whose week?",
            characters,
            format_func=lambda x: manager.get_character_info(x)["name"],
            key="map_sched_sel",
        )
        sched_name = manager.get_character_info(sched_sel)["name"]
        rows = _sched.week_overview(sched_sel)
        acts = _sched.week_activity_overview(sched_sel)
        st.markdown(f"**{sched_name}** — home in **{_sched.home_of(sched_sel)}**")
        grid = []
        for d, (row, act_row) in enumerate(zip(rows, acts), 1):
            for p, (place, act) in enumerate(zip(row, act_row)):
                grid.append({
                    "Day": f"Day {d}",
                    "Period": _sched.PERIOD_NAMES[p],
                    "Place": place,
                    "Occupation": act,
                })
        st.dataframe(
            pd.DataFrame(grid),
            use_container_width=True,
            height=min(40 + 29 * 35, 520),
        )
    except Exception as e:
        st.error(f"Could not render the map: {e}")

with admin_tab:
    # 🛠️ Admin Console — the machine under the world: models, world-state,
    # cause-and-effect chain, and the automation loop that keeps the Heirs
    # converging on their voices. Read-only; nothing here changes the world.
    st.title("🛠️ Admin Console — the machine under the world")
    st.caption("Backend, world-state, cause-and-effect, and the quality loop.")

    # ---- 1. Backend & models ----
    st.markdown("### ⚙️ Backend & models")
    try:
        sn = manager.senses_status()
        c1, c2, c3 = st.columns(3)
        c1.metric("Heir model", manager.llm.model)
        c2.metric("Vision (eyes)", sn.get("vision_model") or "off")
        c3.metric("Audio (music)", sn.get("audio_model") or "off")
        st.caption(f"STT (hearing): {sn.get('stt_model')} · judge/refine: gemma3:27b")
    except Exception as e:
        st.caption(f"(backend status unavailable: {e})")
    try:
        rag = manager.rag_status()
        st.markdown(f"**RAG:** {'on' if rag.get('enabled') else 'off'} · "
                    f"{rag.get('total_documents', 0)} canon docs · {rag.get('embedding', '')}")
    except Exception as e:
        st.caption(f"(rag unavailable: {e})")

    # ---- 2. World-state machine ----
    try:
        from src.world.world_state import WorldState as _WS
        _ws2 = _WS()
        st.markdown("### 🌍 World state")
        st.markdown(f"**Clock:** {_ws2.clock.format()}")
        st.markdown("**Where the Heirs are right now**")
        for _cid, _loc in _ws2.agent_location.items():
            if _cid in _ws2.agent_travel:
                continue
            st.markdown(f"- {manager.get_character_info(_cid)['name']} — {_loc}")
        if _ws2.agent_travel:
            st.markdown("**On the road**")
            for _cid, _ti in _ws2.agent_travel.items():
                st.markdown(f"- {manager.get_character_info(_cid)['name']} → {_ti['to']} "
                            f"({_ti['remaining_days']} day(s) left)")
        _ev = _ws2.recent_events_text(limit=10)
        if _ev:
            with st.expander("⚡ Recent events — the causal trail"):
                st.markdown(_ev)
    except Exception as e:
        st.caption(f"(world state unavailable: {e})")

    # ---- 3. Cause & effect: why today is what it is ----
    try:
        st.markdown("### 🔗 Cause & effect — why today is what it is")
        st.markdown(f"**Season:** {_ws2.clock.season} · **Month:** {_ws2.clock.month_name} "
                    f"(patron {_ws2.clock.patron_titan})")
        _amb = _ws2.ambient
        _w = _amb.get("weather") or {}
        if _w:
            with st.expander("🌤️ Weather — the sky's cause"):
                for _city, _sky in _w.items():
                    st.markdown(f"- **{_city}** — {_sky}")
        _e = _amb.get("errands") or {}
        if _e:
            with st.expander("📜 Errands — request + original impetus"):
                for _cid2, _er in _e.items():
                    if not _er:
                        continue
                    if isinstance(_er, dict):
                        _ask = (_er.get("ask") or "").strip()
                        _cause = (_er.get("cause") or "").strip()
                        st.markdown(f"**{manager.get_character_info(_cid2)['name']}**")
                        st.markdown(f"&nbsp;&nbsp;*ask:* {_ask}")
                        if _cause:
                            st.markdown(f"&nbsp;&nbsp;*cause (impetus):* {_cause}")
                    else:
                        st.markdown(f"- {manager.get_character_info(_cid2)['name']} — {_er}")
        if _amb.get("news"):
            st.markdown(f"*News from the wider world:* {_amb['news']}")
    except Exception as e:
        st.caption(f"(ambient unavailable: {e})")

    # ---- 4. The automation loop ----
    st.markdown("### 🔄 The quality loop (auto-cycle)")
    try:
        import time as _time
        _root = Path(__file__).parent.parent
        _log = _root / "docs" / "AUTO-CYCLE-LOG.md"
        _report = _root / "docs" / "RESEMBLANCE-STYLE-REPORT.md"
        _wdlog = _root / "world_runtime" / "watchdog.log"
        _now = _time.time()

        def _age_min(p):
            return int((_now - p.stat().st_mtime) // 60) if p.exists() else None
        _l, _r, _w = _age_min(_log), _age_min(_report), _age_min(_wdlog)
        st.markdown(f"- AUTO-CYCLE-LOG last written **{_l if _l is not None else 'never'} min ago**")
        st.markdown(f"- Style report last written **{_r if _r is not None else 'never'} min ago**")
        st.markdown(f"- Watchdog last event **{_w if _w is not None else 'never'} min ago**")
        if _log.exists():
            with st.expander("📋 Auto-cycle log (tail)"):
                st.code("\n".join(_log.read_text(encoding="utf-8").splitlines()[-45:]))
        if _wdlog.exists():
            with st.expander("🐕 Watchdog log (tail)"):
                st.code("\n".join(_wdlog.read_text(encoding="utf-8").splitlines()[-20:]))
        if _report.exists():
            with st.expander("📊 Latest style report (tail)"):
                st.code("\n".join(_report.read_text(encoding="utf-8").splitlines()[-25:]))
    except Exception as e:
        st.caption(f"(loop status unavailable: {e})")

    # ---- 5. Chronicle — the written record ----
    try:
        from src.world.chronicle import Chronicle as _Chr
        _ch = _Chr(str(Path(__file__).parent.parent / "world_runtime" / "chronicle"))
        with st.expander("📖 Chronicle — what has happened (the record)"):
            st.markdown(_ch.read_markdown(30))
    except Exception as e:
        st.caption(f"(chronicle unavailable: {e})")

with main_tab:
    # Main Chat Area — hero banner with the Heir's portrait + where they are.
    # The backdrop follows the Heir's CURRENT place in the little Amphoreus
    # (falling back to their home city, then the default banner).
    try:
        from src.ui_backgrounds import bg_path as _loc_bg, current_location as _loc_now
        _chat_bg = _loc_bg(selected)
        _chat_place = _loc_now(selected)
    except Exception:
        _chat_bg = BG_IMAGE if BG_IMAGE.exists() else None
        _chat_place = ""
    if _chat_bg:
        # The backdrop follows the Heir's current place AND today's weather
        # (the Keeper's sky), so the same art changes mood with the world.
        try:
            from src.ui_weather import render_scene as _wx_scene
            _wx_scene(_chat_place, image_path=_chat_bg,
                      title=f"{info['name']} — {_chat_place}" if _chat_place else info["name"],
                      height=300)
        except Exception:
            st.image(str(_chat_bg), width="stretch")
        if _chat_place:
            st.caption(f"📍 {info['name']} is in **{_chat_place}** — the backdrop shows where they are.")
    hero_l, hero_r = st.columns([1, 3], gap="large")
    with hero_l:
        if _selected_portrait:
            st.image(str(_selected_portrait), width="stretch")
        else:
            st.markdown("### 🔥")
    with hero_r:
        st.title(f"{info['name']}")
        st.caption(f"*{', '.join(info['titles'])}*")
        st.caption(f"Coreflame: **{info['coreflame']}**")
    st.markdown("---")

    # Catch-up: what this Heir has lived through since you were last here
    try:
        world_mem = manager.memory.get_world_memories(selected, limit=3)
        if world_mem:
            with st.expander(f"🕯️ What {info['name']} has lived through lately"):
                for wm in world_mem:
                    st.markdown(f"- {wm['content']}")
    except Exception:
        pass

    # Travel together — the star-stranger accompanies this Heir on the road
    try:
        from src.world import map_data as _map_data
        _here = _loc_now(selected) if "_loc_now" in dir() else ""
        _dests = [l for l in _map_data.LOCATION_POS if l != _here]
        if _dests:
            with st.expander("🚶 Travel together"):
                _dest = st.selectbox("Where shall you walk together?", _dests,
                                     key=f"travel_dest_{selected}")
                if st.button(f"Set out for {_dest} with {info['name']}",
                             key=f"travel_btn_{selected}"):
                    _ti = manager.travel_with(selected, _dest)
                    if _ti:
                        st.success(f"You walk with {info['name']} on the road to "
                                   f"{_ti['to']} — {_ti['remaining_days']} day(s).")
                        st.rerun()
                    else:
                        st.error("The road could not be taken just now.")
    except Exception:
        pass

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = {}

    if selected not in st.session_state.messages:
        st.session_state.messages[selected] = []
        # Add greeting
        greeting = info["greeting"]
        st.session_state.messages[selected].append({
            "role": "assistant",
            "content": greeting,
        })

    # Display chat history (the Heir's own square avatar — never a generic bot)
    _assistant_avatar = str(avatar_for(selected)) if avatar_for(selected) else None
    for msg in st.session_state.messages[selected]:
        with st.chat_message(msg["role"], avatar=_assistant_avatar if msg["role"] == "assistant" else None):
            st.markdown(msg["content"])

    # Senses: eyesight (picture / video) and hearing (speak)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        uploaded = st.file_uploader(
            "🖼️ Show a picture",
            type=["png", "jpg", "jpeg", "webp", "gif"],
            key=f"img_{selected}",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            st.session_state["pending_image"] = {
                "bytes": uploaded.getvalue(),
                "mime": uploaded.type or "image/png",
                "name": uploaded.name,
            }
    with c2:
        uploaded_video = st.file_uploader(
            "🎬 Show a video",
            type=["mp4", "mov", "avi", "mkv", "webm"],
            key=f"vid_{selected}",
            label_visibility="collapsed",
        )
        if uploaded_video is not None:
            st.session_state["pending_video"] = {
                "bytes": uploaded_video.getvalue(),
                "name": uploaded_video.name,
            }
    with c3:
        spoken = st.audio_input("👂 Speak to them", key=f"aud_{selected}")

    # A second row: music for shared appreciation
    music_file = st.file_uploader(
        "🎵 Share music to listen together",
        type=["mp3", "wav", "ogg", "flac", "m4a"],
        key=f"music_{selected}",
    )
    if music_file is not None:
        with st.spinner(f"{info['name']} is listening to the music..."):
            result = manager.appreciate_music(selected, music_file.getvalue(), note=music_file.name)
        if result.get("heard"):
            st.session_state.messages[selected].append({
                "role": "user", "content": f"*(shares music: {music_file.name})*",
            })
            with st.chat_message("user"):
                st.markdown(f"*(shares music: {music_file.name})*")
            with st.chat_message("assistant", avatar=_assistant_avatar):
                st.markdown(result["response"])
            st.session_state.messages[selected].append({
                "role": "assistant", "content": result["response"],
            })
        else:
            st.info(result.get("reason", "Music appreciation is not yet available."))

    if st.session_state.get("pending_image"):
        pimg = st.session_state["pending_image"]
        st.caption(f"🖼️ You are showing {info['name']}: **{pimg['name']}** — send a message to appreciate it together.")
    if st.session_state.get("pending_video"):
        pvid = st.session_state["pending_video"]
        st.caption(f"🎬 You are showing {info['name']}: **{pvid['name']}** — send a message to watch it together.")

    if spoken is not None:
        with st.spinner(f"{info['name']} is listening..."):
            result = manager.hear(selected, spoken.read())
        if result.get("heard"):
            st.session_state.messages[selected].append({
                "role": "user", "content": f"*(spoken)* {result['transcript']}",
            })
            with st.chat_message("user"):
                st.markdown(f"*(spoken)* {result['transcript']}")
            with st.chat_message("assistant", avatar=_assistant_avatar):
                st.markdown(result["response"])
            st.session_state.messages[selected].append({
                "role": "assistant", "content": result["response"],
            })
        else:
            st.info(result.get("reason", "Hearing is not yet available."))

    # Chat input
    if prompt := st.chat_input(f"Speak to {info['name']}..."):
        # Let the world know the visitor is here
        try:
            from src.world.world_state import WorldState

            WorldState().mark_visitor_present()
        except Exception:
            pass

        # Attach a pending image (eyesight) if the visitor brought one
        image_b64 = None
        image_mime = "image/png"
        image_caption = ""
        video_bytes = None
        video_name = ""
        pending = st.session_state.pop("pending_image", None)
        pending_video = st.session_state.pop("pending_video", None)
        if pending_video is not None:
            video_bytes = pending_video["bytes"]
            video_name = pending_video["name"]
            st.session_state.messages[selected].append({
                "role": "user",
                "content": f"*(shows a video: {pending_video['name']})* {prompt}",
            })
            with st.chat_message("user"):
                st.markdown(f"*(shows a video: {pending_video['name']})* {prompt}")
        elif pending:
            import base64

            image_b64 = base64.b64encode(pending["bytes"]).decode("ascii")
            image_mime = pending["mime"]
            image_caption = f"a picture ({pending['name']})"
            st.session_state.messages[selected].append({
                "role": "user",
                "content": f"*(shows an image: {pending['name']})* {prompt}",
            })
            with st.chat_message("user"):
                st.markdown(f"*(shows an image: {pending['name']})* {prompt}")
        else:
            # Display user message
            st.session_state.messages[selected].append({
                "role": "user",
                "content": prompt,
            })
            with st.chat_message("user"):
                st.markdown(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner(f"{info['name']} is thinking..."):
                try:
                    response = manager.chat(
                        selected,
                        prompt,
                        image=image_b64,
                        image_mime=image_mime,
                        image_caption=image_caption,
                        video=video_bytes,
                        video_name=video_name,
                    )
                    st.markdown(response)
                    st.session_state.messages[selected].append({
                        "role": "assistant",
                        "content": response,
                    })
                except Exception as e:
                    error_msg = f"*[Error: {str(e)}]*"
                    st.markdown(error_msg)
                    st.session_state.messages[selected].append({
                        "role": "assistant",
                        "content": error_msg,
                    })

        # Show canon sources that grounded the reply
        try:
            ctx = manager.get_rag_context(selected, prompt)
            if ctx.get("available") and ctx.get("hits"):
                with st.expander(f"📜 Canon sources used ({len(ctx['hits'])})"):
                    for h in ctx["hits"]:
                        st.markdown(f"**`{h['source']}`** — score {h['score']}")
                        st.caption(h["text"][:400] + ("…" if len(h["text"]) > 400 else ""))
        except Exception:
            pass
