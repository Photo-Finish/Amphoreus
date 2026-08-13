"""
Agent Manager — Orchestrates interactions with Chrysos Heir AI models.

Usage:
    from core.agent_manager import AgentManager
    manager = AgentManager()
    response = manager.chat("phainon", "Tell me about your home.")
"""

import os
from typing import Optional, Generator

from .character_loader import CharacterLoader
from .session_manager import SessionManager
from .context_builder import ContextBuilder
from .memory_store import MemoryStore
from .preference_store import PreferenceStore
from .teaching_store import TeachingStore
from .llm_client import LLMClient
from .senses import Senses
from ..knowledge.vector_store import VectorStore

# Framing used when the visitor shares a picture/video: the Heir perceives it
# deeply and responds with a genuine aesthetic judgment, not a mere description.
_APPRECIATION_VISION = (
    "The visitor shares this with you to appreciate together. Perceive it deeply "
    "through your senses — its colors, forms, light, and mood. Then share your "
    "genuine aesthetic response in your own voice, shaped by your tastes. Do not "
    "merely describe; tell the visitor what it makes you feel and why it moves "
    "(or does not move) you.\n"
)

# Stage 1 — the Heir's ear analyzes the music itself (audio-understanding model).
# A neutral perception pass: tempo, rhythm, timbre, melody, mood — NOT a verdict.
_MUSIC_ANALYSIS = (
    "Listen to this piece of music carefully, as a perceptive listener. Analyze "
    "what the music actually does: its tempo and rhythm, its instrumentation or "
    "timbre, its melody and harmony, its dynamics, and the mood or emotional arc "
    "it carries. Be concrete and neutral — describe the sound itself, not your "
    "personal taste. Three to five sentences."
)

# Stage 2 — the Heir JUDGES the analysis against their own feelings and values.
# No prescribed genres: the verdict belongs to the Heir, grounded in what they
# heard and the values they hold most dear.
_APPRECIATION_MUSIC = (
    "The visitor shared music with you and you listened together. Your ear heard "
    "this in it:\n"
    "{analysis}\n\n"
    "That is only what your ear perceived — the verdict is yours. What does this "
    "music genuinely make you feel, and what does it call up in you? Weigh it "
    "against the values you hold most dear: does it honor them, challenge them, "
    "or move you somewhere between? Be honest even if your feeling is complicated "
    "or cool — you are not obliged to like it. Speak plainly, in your own voice. "
    "Do not merely repeat the analysis.\n"
)


class AgentManager:
    """Main orchestrator for AI Chrysos Heir interactions."""

    def __init__(
        self,
        characters_dir: str = "src/characters",
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        llm_model: str = "qwen2.5:14b-instruct",
        use_rag: bool = True,
        vector_store: Optional[VectorStore] = None,
        rag_k: int = 5,
        rag_threshold: float = 0.7,
        rag_persist_dir: str = ".chroma_db",
        memory_root: str = ".",
        llm_temperature: float = 0.8,
        vision_model: Optional[str] = None,
        audio_model: Optional[str] = None,
    ):
        self.loader = CharacterLoader(characters_dir)
        self.sessions = SessionManager()

        # LLM configuration (OpenAI-compatible; Ollama by default locally)
        self.llm_model = llm_model
        self.llm = LLMClient(
            model=llm_model,
            base_url=llm_base_url,
            api_key=llm_api_key,
            temperature=llm_temperature,
            vision_model=vision_model,
            audio_model=audio_model,
        )
        self.llm_api_key = self.llm.api_key
        self.llm_base_url = self.llm.base_url

        # Senses (hearing / eyesight / music)
        self.senses = Senses(
            vision_model=vision_model or self.llm.vision_model,
            audio_model=audio_model or self.llm.audio_model,
        )

        # Persistent memory + preferences + teaching ledger — stored in each
        # Heir's personal folder
        self.memory = MemoryStore(memory_root)
        self.preferences = PreferenceStore(memory_root)
        self.teaching = TeachingStore(memory_root)
        self._migrate_legacy_bonds()

        # RAG configuration
        self.use_rag = use_rag
        self.rag_k = rag_k
        self.rag_threshold = rag_threshold
        self.rag_persist_dir = rag_persist_dir
        self._vector_store = vector_store
        self.context_builder = ContextBuilder(
            vector_store=vector_store,
            k=rag_k,
            threshold=rag_threshold,
        )

    def _migrate_legacy_bonds(self):
        """One-time migration from the old central SQLite memory store."""
        legacy = os.path.join(self.memory.memory_root, "memory", "heirs.db")
        if not os.path.exists(legacy):
            return
        try:
            import sqlite3

            conn = sqlite3.connect(legacy)
            rows = conn.execute("SELECT character_id, first_met, visits, friendship_level, user_summary, last_seen FROM bond").fetchall()
            conn.close()
            for (cid, first_met, visits, level, summary, last_seen) in rows:
                if self.memory.get_bond(cid) is None and visits:
                    self.memory._folder(cid)
                    bond = {
                        "character_id": cid,
                        "first_met": first_met,
                        "visits": visits,
                        "friendship_level": level,
                        "user_summary": summary or "",
                        "last_seen": last_seen,
                    }
                    import json

                    (self.memory._folder(cid) / "bond.json").write_text(
                        json.dumps(bond, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
        except Exception:
            pass

    def list_available_characters(self) -> list[str]:
        """List all characters with valid cards."""
        return self.loader.list_characters()

    def get_character_info(self, character_id: str) -> dict:
        """Get public info about a character (mode-aware greeting)."""
        card = self.loader.load(character_id)
        greeting = card["prompts"]["greeting"]
        try:
            from src.core.visitor_mode import is_aftermath, aftermath_greeting
            if is_aftermath():
                greeting = aftermath_greeting(character_id, greeting)
        except Exception:
            pass
        return {
            "name": card["meta"]["name"],
            "titles": card["identity"]["titles"],
            "coreflame": card["identity"]["coreflame"],
            "personality_traits": card["personality"]["traits"],
            "greeting": greeting,
        }

    def chat(
        self,
        character_id: str,
        user_message: str,
        stream: bool = False,
        image: str | None = None,
        image_mime: str = "image/png",
        image_caption: str = "",
        video: bytes | None = None,
        video_name: str = "",
    ) -> str | Generator:
        """
        Send a message to a character and get their response.

        Args:
            character_id: The character to chat with (e.g., "phainon")
            user_message: The user's message
            stream: Whether to stream the response
            image: base64-encoded image the visitor shows the Heir (eyesight)
            image_mime: MIME type of the image (e.g. "image/png")
            image_caption: optional caption of what the image is
            video: raw video bytes the visitor shows the Heir (they watch it)
            video_name: optional name of the video file

        Returns:
            The character's response as a string, or a generator if streaming.
        """
        # The star-stranger's teaching — a genuine Socratic exchange (see
        # docs/TEACHING.md). If the visitor clearly means to teach the Heir
        # something from beyond the stars, or asks for a verdict on an active
        # lesson, route into the teaching protocol instead of plain chat.
        try:
            from src.core import teaching as teaching_proto
            active_lesson = bool(
                self.teaching.studying(character_id)
                or self.teaching.resolved(character_id)
            )
            if (not image and not video
                    and (teaching_proto.detect_teaching(user_message)
                         or (active_lesson and teaching_proto.asks_verdict(user_message)))):
                return self.teach(character_id, user_message, stream=stream)
        except Exception:
            pass

        # Validate character exists
        card = self.loader.load(character_id)
        system_prompt = self.loader.build_system_prompt(character_id)

        # Record this visit and restore any prior session from persistent memory
        self.memory.record_visit(character_id)
        self._restore_session(character_id)

        # Enrich the system prompt with RAG-grounded canon context
        if self.use_rag:
            system_prompt = self.context_builder.retrieve_for_chat(
                character_id, system_prompt, user_message
            )

        # Enrich with the Heir's bond + memories of the visitor and the world
        system_prompt = self._inject_memory_context(character_id, system_prompt)

        # Enrich with where the Heir is right now and what their routine is
        system_prompt = self._inject_world_context(character_id, system_prompt)

        # Visitor mode: how the Heir frames the visitor (journey vs aftermath).
        try:
            from src.core.visitor_mode import visitor_framing_block
            system_prompt += visitor_framing_block()
        except Exception:
            pass

        # Enrich with the Heir's personal preferences (aesthetics, tastes, ...)
        pref_block = self.preferences.to_prompt_block(character_id)
        if pref_block:
            system_prompt = f"{system_prompt}\n\n{pref_block}"

        # Enrich with what the star-stranger has taught the Heir (epistemic
        # ledger: taught topics + the Heir's own verdicts, persisted).
        teach_block = self.teaching.to_prompt_block(character_id)
        if teach_block:
            system_prompt = f"{system_prompt}\n\n{teach_block}"

        # Enrich with the living world's texture: what the Heir has heard,
        # how their bonds stand, letters, and their long work. Chat-only — the
        # style gate's system prompts are untouched.
        system_prompt = self._inject_social_context(character_id, system_prompt)

        # Eyesight: the visitor shows the Heir an image or a video.
        has_image = bool(image)
        has_video = bool(video)
        if has_image:
            if not image_caption:
                image_caption = "an image"
            display_text = f"[The visitor shows you {image_caption}] {user_message}".strip()
        elif has_video:
            if not video_name:
                video_name = "a video"
            display_text = f"[The visitor shows you {video_name}] {user_message}".strip()
        else:
            display_text = user_message

        # Add user message to session + persistent memory
        self.sessions.add_message(character_id, "user", display_text)
        self.memory.add_history(character_id, "user", display_text)

        # Build message history
        session = self.sessions.get_or_create(character_id)
        messages = session.to_openai_format(system_prompt)

        # Call LLM (multimodal path when the Heir is shown an image or video)
        if has_image:
            data_uri = f"data:{image_mime};base64,{image}"
            response = self.llm.chat_vision(
                text=_APPRECIATION_VISION + (user_message or ""),
                image_data_uri=data_uri,
                messages=messages[:-1],
            )
            # The Heir remembers what they saw (eyesight becomes memory)
            self.memory.add_memory(
                character_id,
                mtype="sensory",
                content=f"The visitor showed you {image_caption} and you appreciated it together.",
                importance=2,
            )
        elif has_video:
            frames = self.senses.extract_video_frames(video)
            if frames:
                # The Heir watches the video through its sampled frames
                response = self.llm.chat_video(
                    text=_APPRECIATION_VISION + (user_message or ""),
                    frame_data_uris=frames,
                    messages=messages[:-1],
                )
                self.memory.add_memory(
                    character_id,
                    mtype="sensory",
                    content=f"The visitor showed you a video ({video_name}) and you watched it together.",
                    importance=2,
                )
            else:
                response = self._call_llm(messages, stream=stream)
        else:
            response = self._call_llm(messages, stream=stream)

        if not stream or has_image or has_video:
            # Add assistant response to session + persistent memory
            self.sessions.add_message(character_id, "assistant", response)
            self.memory.add_history(character_id, "assistant", response)
            # The world notices the star-stranger's visit (rumor + Keeper flash).
            self._echo_visit(character_id, user_message)
            return response
        else:
            return self._stream_response(character_id, response)

    def teach(
        self,
        character_id: str,
        user_message: str,
        stream: bool = False,
    ) -> str | Generator:
        """The star-stranger teaches the Heir something from beyond the stars.

        One turn of the Socratic exchange (see docs/TEACHING.md). The Heir does
        NOT feign understanding: they react from their own world, test the
        visitor's claim against what they believe and value, and — when asked
        — commit to a persistent verdict (adopted / refuted / unsure) recorded
        in their teaching ledger and memory. Each turn advances the epistemic
        state: foreign -> studied -> verdict.
        """
        from src.core import teaching as teaching_proto
        from src.core.teaching_store import topic_key as _topic_key
        from src.core.teaching_store import display_topic as _display_topic

        card = self.loader.load(character_id)
        system_prompt = self.loader.build_system_prompt(character_id)

        # Record this visit and restore any prior session from persistent memory
        self.memory.record_visit(character_id)
        self._restore_session(character_id)

        # Ground the exchange (RAG + memory + world + preferences + ledger)
        if self.use_rag:
            system_prompt = self.context_builder.retrieve_for_chat(
                character_id, system_prompt, user_message
            )
        system_prompt = self._inject_memory_context(character_id, system_prompt)
        system_prompt = self._inject_world_context(character_id, system_prompt)
        try:
            from src.core.visitor_mode import visitor_framing_block
            system_prompt += visitor_framing_block()
        except Exception:
            pass
        pref_block = self.preferences.to_prompt_block(character_id)
        if pref_block:
            system_prompt = f"{system_prompt}\n\n{pref_block}"
        teach_block = self.teaching.to_prompt_block(character_id)
        if teach_block:
            system_prompt = f"{system_prompt}\n\n{teach_block}"
        system_prompt = self._inject_social_context(character_id, system_prompt)

        # Ledger state for this topic. A verdict question that doesn't name the
        # topic again targets the most recently active lesson.
        ask_verdict = teaching_proto.asks_verdict(user_message)
        key = _topic_key(user_message)
        if ask_verdict and not self.teaching.get_topic(character_id, key):
            latest = self.teaching.latest_active_key(character_id)
            if latest:
                key = latest
        tname = _display_topic(key)
        state = self.teaching.state(character_id, key)
        verdict_line = ""
        if ask_verdict and state in ("studied", "adopted", "refuted", "unsure"):
            verdict_line = (
                "\nThe star-stranger asks what you make of what you have been "
                "taught. Give an HONEST verdict in your own voice: accept it, "
                "reject it, or hold it as uncertain — and say plainly why."
            )

        system_prompt = f"{system_prompt}\n\n{teaching_proto.TEACHING_SYSTEM}"
        user = (
            f"[Teaching turn — the star-stranger, from beyond the stars]\n"
            f"{teaching_proto.phase_prompt(state, tname)}"
            f"{verdict_line}\n\n"
            f"The star-stranger says: \"{user_message}\"\n\n"
            "Speak as yourself, in your own voice, within your own world."
        )

        # Add to session + persistent memory
        self.sessions.add_message(character_id, "user", user_message)
        self.memory.add_history(character_id, "user", user_message)
        session = self.sessions.get_or_create(character_id)
        messages = session.to_openai_format(system_prompt)
        response = self._call_llm(messages, stream=stream)

        # Advance the epistemic ledger
        self.teaching.record_exchange(
            character_id, key, question=user_message, claim=user_message[:200]
        )
        if ask_verdict and state in ("studied", "adopted", "refuted", "unsure"):
            low = response.lower() if isinstance(response, str) else ""
            if any(w in low for w in ("i accept", "you are right", "i believe you",
                                      "it holds", "it fits", "i agree",
                                      "it is true", "i am convinced")):
                verdict = "adopted"
            elif any(w in low for w in ("i reject", "i refuse", "you are wrong",
                                        "it does not hold", "nonsense", "i doubt",
                                        "it is false", "i am not convinced")):
                verdict = "refuted"
            else:
                verdict = "unsure"
            reason = response.strip()[:280] if isinstance(response, str) else ""
            self.teaching.set_verdict(character_id, key, verdict, reason=reason)
            self.memory.add_memory(
                character_id, mtype="teaching",
                content=(f"The star-stranger taught you about {tname}. Your "
                         f"verdict: {verdict} — {reason[:220]}"),
                importance=3,
            )
        else:
            self.memory.add_memory(
                character_id, mtype="teaching",
                content=(f"The star-stranger began teaching you about {tname}: "
                         f"\"{user_message[:160]}\""),
                importance=2,
            )

        if not stream:
            self.sessions.add_message(character_id, "assistant", response)
            self.memory.add_history(character_id, "assistant", response)
            # The world notices: the star-stranger taught this Heir, and what
            # was accepted spreads (degraded) to the Heirs around them.
            self._echo_visit(character_id, f"taught them something of the world beyond the stars")
            if ask_verdict and state in ("studied", "adopted", "refuted", "unsure"):
                try:
                    from src.world import world_events as _wev
                    from src.world.world_state import WorldState
                    _wev.teaching_rumor(WorldState(), character_id, tname)
                except Exception:
                    pass
            return response
        return self._stream_response(character_id, response)

    def _inject_social_context(self, character_id, system_prompt):
        """Append the living world's texture: rumors heard, bonds, letters,
        and the Heir's long work. Chat-only (cycle prompts untouched)."""
        try:
            from src.world import world_events as _wev
            from src.world.world_state import WorldState
            world = WorldState()
            parts = []
            rumors = _wev.rumors_for(world, character_id, limit=3)
            if rumors:
                parts.append("# What you have heard lately\n" +
                             "\n".join(f"- {r}" for r in rumors))
            learned = _wev.learned_for(world, character_id, limit=3)
            if learned:
                parts.append("# What you have been taught or told of the world beyond the stars\n" +
                             "\n".join(f"- {l}" for l in learned))
            rel = _wev.relationships_block(world)
            if rel:
                parts.append(rel)
            letters = [l for l in world.letters if l.get("to") == character_id]
            if letters:
                latest = letters[-1]
                parts.append(f"# A letter waits for you\nA letter from "
                             f"{latest['from_name']}: \"{latest['text'][:160]}\"")
            proj = _wev.project_info(world, character_id)
            if proj:
                parts.append(f"# Your long work\n\"{proj['title']}\" — "
                             f"{proj['goal']} ({proj['progress']}/{proj['steps']} steps).")
            if parts:
                return system_prompt + "\n\n" + "\n\n".join(parts)
        except Exception:
            pass
        return system_prompt

    def _echo_visit(self, character_id, note):
        """The world notices a SUBSTANTIVE visit (rumor + Keeper flash).
        Small talk is not gossiped about."""
        note = str(note or "").strip()
        if len(note) < 24:
            return
        try:
            from src.world import world_events as _wev
            from src.world.world_state import WorldState
            _wev.visitor_echo(WorldState(), character_id, note[:160])
        except Exception:
            pass

    def travel_with(self, character_id, destination):
        """The star-stranger accompanies an Heir on the road together. If the
        Heir is already travelling, their current journey is returned. An
        instant move (same/adjacent place) is not a journey — no companion."""
        try:
            from src.world.world_state import WorldState
            ws = WorldState()
            if ws.is_traveling(character_id):
                return ws.travel_info(character_id)  # already on the road
            # The star-stranger is Oronyx-blessed: walking with an Heir, they
            # can carry them across the Veil into the Dawn era.
            ws.begin_travel(character_id, destination, blessed_as="trailblazer")
            if ws.is_traveling(character_id):
                ws.companions[character_id] = True  # a real journey begins
            else:
                ws.companions.pop(character_id, None)  # instant move — no journey
            ws.save()
            return ws.travel_info(character_id)
        except Exception:
            return None

    def _call_llm(self, messages: list[dict], stream: bool = False):
        """Call the LLM API via the shared OpenAI-compatible client."""
        if not self.llm.configured:
            # No backend configured — return a graceful placeholder so the UI
            # remains fully testable offline (RAG + memory context still attached).
            name = self._character_name_from_prompt(messages[0]["content"])
            return (
                f"[{name} listens carefully. The LLM backend is not configured — "
                "start Ollama (or set OPENAI_API_KEY / OPENAI_BASE_URL) to enable "
                "live responses. RAG canon retrieval and memory are active and ready.]"
            )
        if stream:
            return self.llm.stream(messages)
        return self.llm.chat(messages)

    @staticmethod
    def _character_name_from_prompt(system_prompt: str) -> str:
        """Best-effort extraction of the character name from a system prompt."""
        if "You are " in system_prompt:
            return system_prompt.split("You are ")[1].split(",")[0]
        return "Character"

    def _stream_response(self, character_id: str, stream) -> Generator:
        """Stream LLM response, collecting full text for session storage."""
        full_response = []
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response.append(content)
                yield content

        # Store complete response in session + persistent memory
        text = "".join(full_response)
        self.sessions.add_message(character_id, "assistant", text)
        self.memory.add_history(character_id, "assistant", text)

    def reset_conversation(self, character_id: str):
        """Reset conversation history AND the Heir's persistent memory of you."""
        self.sessions.clear(character_id)
        self.memory.clear_character(character_id)

    def get_conversation_history(self, character_id: str) -> list:
        """Get the conversation history (from persistent memory)."""
        return self.memory.get_recent_history(character_id, n=100)

    # ------------------------------------------------------------------ #
    # RAG support
    # ------------------------------------------------------------------ #
    def _get_vector_store(self) -> Optional[VectorStore]:
        """Lazily create the ChromaDB vector store if RAG is enabled."""
        if not self.use_rag:
            return None
        if self._vector_store is None:
            self._vector_store = VectorStore(
                persist_dir=self.rag_persist_dir,
                characters_dir=str(self.loader.characters_dir),
                databank_dir="databank",
            )
            self.context_builder.vector_store = self._vector_store
        return self._vector_store

    def build_knowledge_base(self, character_id: Optional[str] = None) -> dict:
        """Build the ChromaDB knowledge base (all characters, or just one)."""
        store = self._get_vector_store()
        if store is None:
            return {"error": "RAG is disabled"}
        if character_id:
            count = store.build_character(character_id)
            return {character_id: count}
        return store.build_all()

    def rag_status(self) -> dict:
        """Report RAG availability per character."""
        if not self.use_rag:
            return {"enabled": False}
        store = self._get_vector_store()
        counts = store.counts() if store else {}
        return {
            "enabled": True,
            "embedding": getattr(store, "embedding", "unknown") if store else "n/a",
            "persist_dir": self.rag_persist_dir,
            "collections": counts,
            "total_documents": sum(counts.values()),
        }

    def get_rag_context(self, character_id: str, question: str) -> dict:
        """Return the canon context that would ground a reply (for display/debug)."""
        if not self.use_rag:
            return {"available": False}
        available = self.context_builder.is_available(character_id)
        hits = self.context_builder.retrieve(character_id, question) if available else []
        return {
            "available": available,
            "hits": hits,
            "formatted": self.context_builder.format_context(hits),
        }

    # ------------------------------------------------------------------ #
    # Persistent memory support (the Heirs' days)
    # ------------------------------------------------------------------ #
    def _restore_session(self, character_id: str):
        """Rehydrate the in-memory session window from persistent memory."""
        session = self.sessions.get_or_create(character_id)
        if session.messages:
            return
        for msg in self.memory.get_recent_history(character_id, n=40):
            session.add(msg["role"], msg["content"])

    def _inject_memory_context(self, character_id: str, system_prompt: str) -> str:
        """Append the Heir's bond + memories of the visitor and the world."""
        context = self.build_memory_context(character_id)
        if not context:
            return system_prompt
        return f"{system_prompt}\n\n{context}"

    def _inject_world_context(self, character_id: str, system_prompt: str) -> str:
        """Append where the Heir is right now, their routine, and who is nearby.

        The little Amphoreus has real geography and daily routines: the Heir is
        not floating in a void when the visitor arrives. The world clock, their
        usual occupation at this hour, and any Heirs physically present are
        injected so the conversation is anchored in the living world.
        """
        try:
            from src.world.world_state import WorldState
            from src.world.schedules import scheduled_entry

            ws = WorldState()
            loc = ws.location_name(character_id)
            tinfo = ws.travel_info(character_id)

            lines = ["\n\nWhere you are right now:"]
            if tinfo:
                lines.append(
                    f"- You are on the road to {tinfo['to']} — "
                    f"{tinfo['remaining_days']} day(s) of travel remain. "
                    "You are not in any city at this moment."
                )
            else:
                lines.append(f"- You are in {loc} — {ws.location_desc(loc)}.")
                sched_loc, sched_act = scheduled_entry(
                    character_id, ws.clock.day, ws.clock.period
                )
                lines.append(
                    f"- It is {ws.clock.format_short()}. Your usual routine at this "
                    f"hour: {sched_act} (in {sched_loc})."
                )
                try:
                    names = [
                        self.get_character_info(cid)["name"]
                        for cid in ws.agents_at(loc)
                        if cid != character_id
                    ]
                    if names:
                        lines.append(f"- Also present here: {', '.join(names)}.")
                except Exception:
                    pass
            try:
                from src.world import world_events as _wev
                if _wev.surge_active(ws):
                    lines.append(f"- ⚠️ {_wev.surge_text(ws)}")
            except Exception:
                pass
            try:
                from src.core.visitor_mode import world_note
                note = world_note()
                if note:
                    lines.append(note)
            except Exception:
                pass
            return system_prompt + "\n".join(lines)
        except Exception:
            return system_prompt  # never let the world block break the chat

    def build_memory_context(self, character_id: str) -> str:
        """Build the 'bond + memories' block injected into the Heir's prompt."""
        bond = self.memory.get_bond(character_id)
        lines: list[str] = []

        if bond:
            level = bond.get("friendship_level", "stranger")
            visits = bond.get("visits", 1)
            lines.append("# Your bond with the visitor")
            lines.append(
                f"You have met the visitor {visits} time(s). "
                f"Your friendship: {level}."
            )
            summary = bond.get("user_summary", "").strip()
            if summary:
                lines.append(f"What you know about them: {summary}")
            lines.append("")

        shared = self.memory.get_memories(
            character_id, limit=8, min_importance=1
        )
        world = self.memory.get_world_memories(character_id, limit=6)
        if shared or world:
            lines.append("# What you remember")
            for m in shared:
                tag = m["mtype"]
                lines.append(f"- ({tag}) {m['content']}")
            lines.append("")
            lines.append("# Recent days in Amphoreus you lived through")
            for m in world:
                lines.append(f"- {m['content']}")
            lines.append("")

        return "\n".join(lines).strip()

    def get_bond_info(self, character_id: str) -> dict:
        """Public bond information (for the UI)."""
        bond = self.memory.get_bond(character_id) or {}
        return {
            "first_met": bond.get("first_met"),
            "visits": bond.get("visits", 0),
            "friendship_level": bond.get("friendship_level", "stranger"),
            "user_summary": bond.get("user_summary", ""),
            "last_seen": bond.get("last_seen"),
            "memories": self.memory.memory_count(character_id),
            "history_turns": self.memory.history_count(character_id),
        }

    def remember_shared(self, character_id: str, content: str, mtype: str = "shared", importance: int = 2):
        """The Heir stores something the visitor shared as a durable memory."""
        self.memory.add_memory(character_id, mtype, content, importance)

    # ------------------------------------------------------------------ #
    # Preferences (each Heir's personal database)
    # ------------------------------------------------------------------ #
    def get_preferences(self, character_id: str) -> dict:
        """Return the Heir's preferences (seeding from canon on first access)."""
        return self.preferences.get(character_id)

    def remember_preference(
        self,
        character_id: str,
        category: str,
        value: str,
        about_visitor: bool = False,
    ):
        """The Heir adopts a preference (e.g. an aesthetic or a taste)."""
        if about_visitor:
            self.preferences.learn(character_id, value)
        else:
            self.preferences.add_preference(character_id, category, value)

    def consolidate_memories(self, character_id: str, keep_recent: int = 20):
        """Fold old conversation into durable memory entries."""
        self.memory.consolidate(character_id, keep_recent=keep_recent)

    def memory_stats(self) -> dict:
        """Global memory statistics (for the UI)."""
        return self.memory.stats()

    # ------------------------------------------------------------------ #
    # Senses support (hearing / eyesight)
    # ------------------------------------------------------------------ #
    def hear(self, character_id: str, audio_bytes: bytes) -> dict:
        """The Heir 'hears' spoken audio: transcribe then reply."""
        transcript = self.senses.transcribe_audio(audio_bytes)
        if transcript is None:
            return {
                "heard": False,
                "reason": (
                    "The Heir could not hear this yet — the speech-to-text model is "
                    "not ready (check STT_MODEL / models/faster-whisper-base)."
                ),
                "response": None,
            }
        self.memory.add_memory(
            character_id,
            mtype="sensory",
            content=f"You heard the visitor say: {transcript[:200]}",
            importance=2,
        )
        response = self.chat(character_id, transcript)
        return {"heard": True, "transcript": transcript, "response": response}

    def watch_video(
        self,
        character_id: str,
        video_bytes: bytes,
        caption: str = "",
        prompt: str = "What do you see?",
    ) -> dict:
        """The Heir 'watches' a video (frame extraction + vision model)."""
        frames = self.senses.extract_video_frames(video_bytes)
        if not frames:
            return {
                "watched": False,
                "reason": "Could not read the video (no video frames found).",
                "response": None,
            }
        if not self.senses.vision_available:
            return {
                "watched": False,
                "reason": "No vision model configured. Set VISION_MODEL (e.g. qwen2.5vl:7b).",
                "response": None,
            }
        name = caption or "a video"
        response = self.chat(character_id, prompt, video=video_bytes, video_name=name)
        return {"watched": True, "frames": len(frames), "response": response}

    def analyze_music(self, audio_bytes: bytes, note: str = "") -> str:
        """Stage 1 — the Heir's ear analyzes the music itself.

        Uses the audio-understanding model (AUDIO_MODEL, e.g. qwen2.5-omni) —
        NOT speech-to-text — to produce a concrete, neutral perception of the
        piece (tempo, rhythm, timbre, melody, mood). No verdict here.
        """
        data = self.senses.encode_audio(audio_bytes)
        label = f" ({note})" if note else ""
        text = (
            "The visitor shares a piece of music with you to listen to together"
            f"{label}.\n" + _MUSIC_ANALYSIS
        )
        return (self.llm.chat_audio(text=text, audio_data_uri=data, temperature=0.2)
                or "").strip()

    def appreciate_music(
        self,
        character_id: str,
        audio_bytes: bytes,
        note: str = "",
        prompt: str = "What does this music make you feel?",
    ) -> dict:
        """The Heir genuinely HEARS a piece of music and shares their judgment.

        Two stages:
          1. The ear (audio-understanding model) analyzes the music itself.
          2. The Heir (their own model, full character voice) weighs that
             perception against their feelings and the values they hold —
             there are NO prescribed genres; the verdict is the Heir's own.
        """
        if not self.senses.music_available:
            return {
                "heard": False,
                "reason": "No audio model configured. Set AUDIO_MODEL (e.g. qwen2.5-omni) "
                          "so the Heir can hear and appreciate music.",
                "analysis": None,
                "response": None,
            }
        analysis = self.analyze_music(audio_bytes, note)
        if not analysis or analysis.startswith("["):
            return {
                "heard": False,
                "reason": analysis or "The ear could not hear the music right now.",
                "analysis": None,
                "response": None,
            }
        label = f" ({note})" if note else ""
        values = (self.preferences.get(character_id) or {}).get("values", [])
        values_txt = ", ".join(values) if values else "the values you hold"
        judge_text = (
            f"{_APPRECIATION_MUSIC.format(analysis=analysis)}"
            f"The visitor shared a piece of music{label} with you.\n"
            f"Your own values: {values_txt}.\n"
            f"{prompt}"
        )
        response = self.chat(character_id, judge_text)
        self.memory.add_memory(
            character_id,
            mtype="sensory",
            content=f"The visitor shared music{label} with you and you listened together.",
            importance=2,
        )
        return {"heard": True, "analysis": analysis, "response": response}

    def senses_status(self) -> dict:
        """Report which senses are available for the Heirs."""
        return {
            "eyesight": self.senses.vision_available,
            "hearing": self.senses.hearing_available,
            "music": self.senses.music_available,
            "vision_model": self.senses.vision_model,
            "stt_model": self.senses.stt_model,
            "audio_model": self.senses.audio_model,
        }
