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
main_tab, chronicle_tab = st.tabs(["💬 Visit an Heir", "📖 A Chronicle of Amphoreus"])

with chronicle_tab:
    st.title("📖 A Chronicle of Amphoreus")
    st.caption("The Heirs' days — written by their actions, not by us.")
    try:
        from src.world.chronicle import Chronicle

        ch = Chronicle(str(Path(__file__).parent.parent / "world_runtime" / "chronicle"))
        st.markdown(ch.read_markdown(60))
    except Exception:
        st.info("The chronicle is not written yet — the world engine has not begun its days.\n\nStart it with: `python -m src.world.world_engine --interval 900`")

with main_tab:
    # Main Chat Area
    st.title(f"💬 {info['name']}")
    st.caption(f"*{info['coreflame']}*")

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

    # Display chat history
    for msg in st.session_state.messages[selected]:
        with st.chat_message(msg["role"]):
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
            with st.chat_message("assistant"):
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
            with st.chat_message("assistant"):
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
