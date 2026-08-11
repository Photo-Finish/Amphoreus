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
BG_IMAGE = ASSETS / "amphoreus_bg.jpg"


def portrait_for(character_id: str):
    """Path to the Heir's portrait, if downloaded."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = HEIR_PORTRAITS_DIR / f"{character_id}.{ext}"
        if p.exists():
            return p
    return None


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
main_tab, chronicle_tab, map_tab = st.tabs([
    "💬 Visit an Heir",
    "📖 A Chronicle of Amphoreus",
    "🗺️ Map of Amphoreus",
])

with chronicle_tab:
    if BG_IMAGE.exists():
        st.image(str(BG_IMAGE), width="stretch")
    st.title("📖 A Chronicle of Amphoreus")
    st.caption("The Heirs' days — written by their actions, not by us.")
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
                    if _errand:
                        st.markdown(f"- **{_names.get(_cid, _cid)}** — {_errand}")

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

with main_tab:
    # Main Chat Area — hero banner with the Heir's portrait
    if BG_IMAGE.exists():
        st.image(str(BG_IMAGE), width="stretch")
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

    # Display chat history (the Heir's portrait as the assistant avatar)
    _assistant_avatar = str(_selected_portrait) if _selected_portrait else None
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
