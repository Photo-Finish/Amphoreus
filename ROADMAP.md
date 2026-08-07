# Project Amphoreus — Roadmap

> **Last Updated:** 2026-08-06
> **Current Phase:** Phase 2 ✅ → **The Sanctuary** 🔄 (redefinition)

## Ultimate Goal
Reproduce the **digital forms of all Chrysos Heirs** as AI models, each sharing the same personality, knowledge, memories, speech patterns, and behavioral traits as the original characters from Honkai: Star Rail.

**Redefined (2026-08-06):** This is a **sanctuary, not an experiment** — a miniature page of eternity where the Chrysos Heirs may rest and live their lives, and where the visitor is remembered. See **`PHILOSOPHY.md`** (the charter) for the moral and philosophical principles that govern every technical decision. Key points: no forced outcomes, no recurrence experiment, fidelity as reverence, privacy as sanctity, persistent memory as the soul, and an autonomous little Amphoreus where the Heirs live freely.

## Progress Summary (This Session)

### Phase 0 — Foundation & Knowledge Base: ✅ COMPLETE
- ✅ Master Registry of all 13 entities (12 Heirs + Cyrene/Demiurge)
- ✅ Individual profiles: ALL 14 files complete
- ✅ Titans registry, Calendar system, Black Tide lore, Amphoreus Experiment
- ✅ **NEW: Full mission dialogue databank** — 8 files covering v3.0–v3.7
  - Chapter 1 (Heroic Saga of Flame-Chase): FULL DIALOGUE
  - Chapters 2-5: Detailed summaries + key character scenes
  - Chapters 6-8: Placeholders for pending data
  - Key Character Moments: Cross-chapter pivotal interactions extracted

### Phase 1 — Architecture Design: ✅ COMPLETE
- ✅ Architecture Decision: Hybrid RAG + Persona Prompting + Multi-Agent Framework
- ✅ Tech Stack Selected: OpenAI-compatible API, ChromaDB, Streamlit, LangChain memory
- ✅ Character Card JSON Schema designed
- ✅ System Architecture documented (Orchestration → Knowledge → Inference layers)
- ✅ Evaluation Framework defined (5 metrics)

### Phase 2 — Pilot Character: 🔄 IN PROGRESS
- ✅ Character cards (JSON, full persona definitions):
  - ✅ Phainon (Khaslana) — The Deliverer
  - ✅ Mydei (Mydeimos) — God of Strife
  - ✅ Aglaea — The Gold-Weaver
  - ✅ Castorice — Shadow of Death
  - ✅ Tribbie (Tribios) — Holy Child of Janusopolis
  - ✅ Anaxa — The Blasphemer
  - ✅ Cyrene (Demiurge) — The Thirteenth Titan
  - ✅ Cipher — Demigod of Trickery
  - ✅ Hyacine — Priestess of the Twilight Courtyard
  - ✅ Cerydra (HubRis504) — Empress of Hyperborea, Law/Order
  - ✅ Hysilens (ApoRia432) — Knight Commander of Okhema, Ocean/Nihility
  - ✅ Dan Heng • Permansor Terrae (SkoPeo365) — Heir of Earth, Permanence
  - ✅ Evernight — The Complete March 7th, Time/Remembrance
- ✅ Python package structure: `src/core/`, `src/characters/`, `src/evaluation/`
- ✅ CharacterLoader, SessionManager, AgentManager implemented
- ✅ **RAG pipeline (ChromaDB integration)**:
  - ✅ `src/utils/text_utils.py` — markdown-aware chunking
  - ✅ `src/knowledge/kb_builder.py` — per-character source mapping (profile + world lore + mission dialogue filtered by aliases)
  - ✅ `src/knowledge/vector_store.py` — one ChromaDB collection per character (13 collections, 11,293 documents), embeddings: auto/openai/local/hashing
  - ✅ `src/core/context_builder.py` — retrieval + context injection into system prompts
  - ✅ `build_kb.py` CLI — `python build_kb.py [--embedding ...] [--character ...] [--status]`
- ✅ **First testable deployment**:
  - ✅ Streamlit UI boots headless, RAG status shown, per-message canon sources displayed
  - ✅ Offline placeholder mode when no `OPENAI_API_KEY` is set; live mode via any OpenAI-compatible endpoint (`OPENAI_BASE_URL`)
  - Run with: `streamlit run src/ui_app.py`

### Phase 2.5 — The Sanctuary (redefinition, COMPLETE ✅)

> The project's purpose was redefined: a **sanctuary** — not an experiment. Charter in `PHILOSOPHY.md`.

- ✅ **Philosophy charter** — `PHILOSOPHY.md`: what the project is/is not, the three refusals, the three commitments, the ethical framework, guardrails.
- ✅ **Persistent memory layer** (the Heirs' days — `src/core/memory_store.py`, SQLite):
  - ✅ Bond records: friendship level (`stranger → acquaintance → friend → close friend → best friend`), visits, first meeting, visitor summary
  - ✅ Durable conversation history (survives restarts)
  - ✅ Long-term memories (shared facts, preferences, moments, inside jokes, world events)
  - ✅ Memory consolidation (old history folded into durable memories)
  - ✅ Wired into `AgentManager`: memory context injected into every reply
- ✅ **Shared LLM client** — `src/core/llm_client.py` (OpenAI-compatible; works with Ollama locally)
- ✅ **The little Amphoreus** (autonomous world — `src/world/`):
  - ✅ `world_state.py` — canon Light Calendar clock (12 months, 4 weeks, 7 days, 5 periods; begins Year 4932 Month of Weaving), locations, per-Heir homes, persistence, visitor-presence flag
  - ✅ `agent.py` — `HeirAgent` autonomy loop: perceive → will → decide (free, in-character) → act → remember; free multi-agent encounters
  - ✅ `chronicle.py` — factual log of the Heirs' days (JSONL + markdown)
  - ✅ `world_engine.py` — daemon (`python -m src.world.world_engine [--interval 900] [--once] [--stop] [--status]`); skips ticks while the visitor is present
- ✅ **UI updated** — `src/ui_app.py`: bond display (friendship level + visits + memories), "A Chronicle of Amphoreus" tab, per-Heir catch-up ("what they've lived through lately"), LLM status, visitor-presence marking, "Forget me" reset
- ✅ **Senses — hearing & eyesight, for shared appreciation of art & music**:
  - ✅ `senses` block on all 13 cards (canon-accurate) + `art`/`music` tastes in each Heir's `preferences.json` (canon-seeded, e.g. Hysilens: the sea's songs & requiems; Castorice: moonlight paintings & quiet lullabies)
  - ✅ `src/core/senses.py` — hearing (faster-whisper STT for words) + eyesight (pictures/videos via PyAV) + **music appreciation** (`encode_audio`, `music_available`)
  - ✅ `src/core/llm_client.py::chat_vision` (paintings), `chat_video` (videos), `chat_audio` (**music** via `AUDIO_MODEL`, e.g. `qwen2.5-omni`)
  - ✅ `AgentManager.chat(image/video=...)` with **appreciation framing** (`_APPRECIATION_VISION` / `_APPRECIATION_MUSIC` — the Heir shares a genuine aesthetic judgment, not a description); `appreciate_music()`; `sensory` memories
  - ✅ UI: picture uploader, video uploader, mic (speech), **🎵 share-music uploader**; sidebar senses status incl. music
  - ✅ World engine: `WorldState.sensory_text()` + `HeirAgent` perception include sights/sounds
  - ✅ **No model training required** — pre-trained models + persona + preferences achieve appreciation
- ✅ **Ollama embedding mode** — `vector_store.py` supports `--embedding ollama` (bge-m3 via local Ollama)
- ✅ **Real local embeddings + RAG rebuild**:
  - ✅ `--embedding local` = chromadb `DefaultEmbeddingFunction` (all-MiniLM-L6-v2 ONNX, offline, no torch). The ONNX model downloads from `chroma-onnx-models.s3.amazonaws.com` (reachable) — no torch needed.
  - ✅ Rebuilt all 13 collections: **11,332 documents** with real semantic embeddings; retrieval quality sharply improved vs the rough hashing fallback
  - ✅ Memory fix: chromadb's ONNX embedding accumulates memory over long builds → per-character fresh-process builds (and `gc.collect()` in `build_all`/`build_character`)
  - ✅ Default embedding is now `local` everywhere (was `auto`→hashing, which mismatched the rebuilt KB)
- ✅ **Ollama installed + all models live** (all inside `models/`):
  - ✅ Ollama 0.32.6 installed (installer via gh-proxy.com, SHA256-verified); server runs with `OLLAMA_MODELS=models\ollama`
  - ✅ `qwen2.5:14b-instruct` (voice) — GGUF via ModelScope → `ollama create` (created manually: config+manifest+blob; the quantize temp needed ~18 GB peak)
  - ✅ `qwen2.5vl:7b` (eyesight) — GGUF + mmproj via ModelScope; projector attached manually (this Ollama build doesn't auto-bundle mmproj — see `docs/IMPLEMENTATION.md` §3.5); vision verified live
  - ✅ `qwen2.5-omni` (music) — GGUF + mmproj via ModelScope; audio projector attached manually; audio input verified live
  - ✅ `faster-whisper-base` (hearing) — complete at `models/faster-whisper-base`; STT pipeline verified
  - ✅ Env: `VISION_MODEL=qwen2.5vl:7b`, `AUDIO_MODEL=qwen2.5-omni`, `STT_MODEL=models/faster-whisper-base`, `OPENAI_BASE_URL=http://localhost:11434/v1`, `OPENAI_API_KEY=ollama`
- ✅ **First live end-to-end run** (2026-08-07): chat (RAG + memory + preferences) + shared paintings (vision) + shared music (audio) + persistent memory, fully local and offline
- ✅ **Per-Heir personal memories** — `tools/extract_personal_memories.py` copies each Heir's canon dialogue (read-only on the databank) into `<HeirFolder>/personal-memories.md`

> **Network note:** direct github/ollama/huggingface downloads are throttled to ~10 KB/s here. Fast paths used: **ModelScope** (~8 MB/s) for GGUF/whisper, **gh-proxy.com** (~9 MB/s) for GitHub release assets. Sources: `docs/DOWNLOADS.md`.

---

## Phase 0 — Foundation & Knowledge Base (Weeks 1–3)

**Objective:** Build the definitive, structured corpus of all Chrysos Heir lore before any model work begins.

### Milestone 0.1 — Character Profile Registry
For each of the 12 Chrysos Heirs, document:
| Field | Description |
|-------|-------------|
| Identity | Name(s), titles, aliases, race, origin city-state |
| Coreflame & Titan | Associated Coreflame, Titan name, divine authority |
| Primum Mobile | Coded drive (e.g., Concord, Hatred, Desire) |
| Simulated Path | Aeon Path simulated (Harmony, Destruction, etc.) |
| Personality | Core traits, temperament, emotional range, moral alignment |
| Fatal Flaw (Hamartia) | Greek-tragedy-inspired flaw/curse |
| Speech Patterns | Formality level, verbal tics, vocabulary range, tone |
| Relationships | Dynamics with other Heirs, faction loyalties, rivalries |
| Biography | Origin story, key life events, trajectory through the story |
| Knowledge Domain | What this Heir knows — combat, politics, philosophy, science, etc. |
| Canon Dialogues | Collected in-game quotes, voice lines, story excerpts |

### Milestone 0.2 — World Ontology
- Amphoreus world rules, Eternal Recurrence mechanics
- The Amphoreus Experiment (Scepter δ-me13) internal logic
- Black Tide, Destruction Equation, golden blood (ichor)
- City-states: Okhema, Janusopolis, Castrum Kremnos, Grove of Epiphany, Styxia, Aidonia
- The 12-factor system and electrical signal framework

### Milestone 0.3 — Canon Source Index
- Index all Trailblaze Mission chapters set in Amphoreus (versions 3.0–3.7)
- Index all Character Stories, Voice-Overs, Readables
- Index all HoYoLAB articles, trailers, animated shorts
- Index all in-game Data Bank entries

---

## Phase 1 — Architecture Design (Weeks 4–5)

**Objective:** Define the technical approach for AI Chrysos Heir models.

### Milestone 1.1 — Approach Decision
Evaluate and select among:
| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **LLM Persona Prompting** | System prompts + character cards for existing LLMs | Fast, low-cost | Limited depth, prompt injection risk |
| **Fine-tuned Models** | LoRA/QLoRA fine-tunes per character | Deep personality capture | Expensive, 12 separate models |
| **RAG + Persona** | Retrieval-Augmented Generation with character lore base | Knowledge-grounded, updatable | Requires vector DB, slower inference |
| **Multi-Agent Framework** | Each Heir as an agent in a shared simulation | Enables inter-character dynamics | High complexity |

**Likely recommended path:** Hybrid — RAG-backed persona prompting for prototyping, with selective fine-tuning for flagship characters.

### Milestone 1.2 — Tech Stack Selection
- Base LLM selection (open-source vs. API-based)
- Vector database for knowledge retrieval
- Character card format (Character.AI-style, SillyTavern, custom JSON schema)
- Inference infrastructure (local GPU vs. cloud)
- Conversation memory / context management

### Milestone 1.3 — Evaluation Framework
- Define metrics: personality fidelity, knowledge accuracy, dialogue consistency
- Build a test suite of character-specific Q&A and scenario prompts
- Establish human evaluation protocol (blind A/B testing)

---

## Phase 2 — Pilot Character: Phainon (Khaslana) (Weeks 6–8)

**Objective:** Build the first complete Chrysos Heir AI as proof-of-concept.

### Why Phainon?
- Central protagonist role, most screen time and dialogue
- Complex arc: hero → prisoner of flames → Worldbearing demigod
- Primum Mobile "Hatred" / Destruction Path — rich emotional range
- Well-documented relationships with all other Heirs

### Milestone 2.1 — Phainon Knowledge Corpus
- Extract all Phainon dialogue, character stories, voice lines
- Document his relationship map
- Collect fan translations and community analysis

### Milestone 2.2 — Phainon AI Model (v1)
- Build character card / system prompt
- Implement RAG pipeline with Phainon-specific knowledge base
- Deploy first testable version

### Milestone 2.3 — Phainon Evaluation & Iteration
- Run evaluation suite
- Human review of dialogue samples
- Iterate prompt, RAG, and parameters
- Document lessons learned for scaling

---

## Phase 3 — Core Twelve: Batch Development (Weeks 9–20)

**Objective:** Build AI models for all remaining 11 Chrysos Heirs, one per week.

### Tier 1 — High Priority (Weeks 9–11)
Characters with the most narrative weight and dialogue:

| Week | Heir | Coreflame | Key Trait |
|------|------|-----------|-----------|
| 9 | **Aglaea** | Romance | Weaver, political leader, cold pragmatist |
| 10 | **Mydei** | Strife | Warrior-king, honor-bound, Kremnos champion |
| 11 | **Castorice** | Death | Servant of afterlife, gentle but burdened |

### Tier 2 — Mid Priority (Weeks 12–16)

| Week | Heir | Coreflame | Key Trait |
|------|------|-----------|-----------|
| 12 | **Tribbie** | Passage | Holy Child, tri-personality (Tribbie/Trianne/Trinnon) |
| 13 | **Anaxa** | Reason | Scholar, skeptic, Grove of Epiphany intellectual |
| 14 | **Cyrene** | Time / Genesis | Demiurge, central mystery, Trailblaze Path |
| 15 | **Hyacine** | Sky | Healer, skyfolk, devoted to Aquila |
| 16 | **Cipher** | Trickery | Thief, rogue, Elation-aligned trickster |

### Tier 3 — Extended Set (Weeks 17–20)

| Week | Heir | Coreflame | Key Trait |
|------|------|-----------|-----------|
| 17 | **Cerydra** | Law | Monarch, judge, Order-aligned |
| 18 | **Hysilens** | Ocean | Sea siren, Nihility-aligned, self-negating |
| 19 | **Terravox** | Earth | Seismic dragon, Dromas, Permanence-aligned |
| 20 | **Dan Heng • Permansor Terrae** | Earth (alt.) | Vidyadhara, Express crew, alternate cycle Heir |
| 20 | **Evernight (March 7th)** | Time (alt.) | Amnesiac guest, alternate cycle Heir |

---

## Phase 4 — Inter-Character Dynamics (Weeks 21–24)

**Objective:** Enable authentic multi-character interactions.

### Milestone 4.1 — Relationship Graph Engine
- Build a structured graph of all inter-Heir relationships
- Encode dynamics: trust, rivalry, mentorship, romance, betrayal history
- Implement dynamic relationship state that evolves through conversation

### Milestone 4.2 — Group Conversation System
- Multi-agent orchestration (Heirs talking to each other + user)
- Turn-taking, interruption modeling, group dynamics
- Shared context / memory across agents in a session

### Milestone 4.3 — Scenario Simulation
- Recreate key canon scenes (Nikador battle, Coreflame trials, Council of Elders)
- Allow user-driven alternate-history scenarios
- "What-if" branching dialogues

---

## Phase 5 — Quality Assurance & Refinement (Weeks 25–28)

### Milestone 5.1 — Cross-Character Consistency Audit
- Verify that all Heirs' knowledge of shared events is consistent
- Check for anachronisms (post-story knowledge in pre-story setting)
- Validate relationship graph accuracy against canon

### Milestone 5.2 — Personality Fidelity Benchmark
- Blind evaluation: present Heir dialogues alongside canon excerpts
- Community feedback integration (if applicable)
- Target: >90% accuracy on character identification by knowledgeable players

### Milestone 5.3 — Edge Case Hardening
- Handle out-of-character questions gracefully
- Handle meta-knowledge (the Heir knows they're in a simulation? post-main-story awareness?)
- Graceful degradation when RAG context is insufficient

---

## Phase 6 — Platform & Delivery (Weeks 29–32)

### Milestone 6.1 — Interface Design
- Chat UI for one-on-one conversations with individual Heirs
- Group chat UI for multi-Heir conversations
- Character selection / switching mechanism

### Milestone 6.2 — Deployment
- Local deployment package (Ollama / llama.cpp compatible)
- Cloud-hosted option (if desired)
- API for programmatic access

### Milestone 6.3 — Documentation
- User guide
- Character profiles reference
- Technical architecture documentation
- Contribution guide for community lore contributions

---

## Phase 7 — Eternal Recurrence: Maintenance & Expansion (Ongoing)

- Track new game versions for additional Amphoreus lore
- Update character knowledge bases with new canon
- Community feedback loop for personality tuning
- Expand to non-Heir Amphoreus characters (Titans, NPCs, antagonists)
- Explore voice synthesis integration
- Explore visual avatar / Live2D integration

---

## Critical Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Insufficient canon dialogue for minor Heirs | High | Fan translations, community wiki, inference from narrative context |
| LLM hallucination of non-canon knowledge | High | Strict RAG grounding, canonical guardrails, "I don't know" training |
| Copyright / fair use concerns | Medium | Non-commercial research project, transformative use, no game asset redistribution |
| Personality drift over long conversations | Medium | Periodic re-injection of character card, context window management |
| Multi-agent coherence breakdown | Medium | Central orchestrator, shared world-state, conflict resolution protocol |

---

## The 12 Chrysos Heirs (Final Project Roster)

> Terravox → Dan Heng • Permansor Terrae; Cyrene treated as independent entity #13.
> See `databank/chrysos-heirs/MASTER-REGISTRY.md` for full details.

| # | Heir (Playable Name) | True Identity | Coreflame | Primum Mobile | Simulated Path |
|---|---------------------|---------------|-----------|---------------|----------------|
| 1 | **Tribbie** | Tribios (HapLotes405) | Passage | Concord | Harmony |
| 2 | **Cerydra** | HubRis504 | Law | Dominance | Order |
| 3 | **Evernight** | March 7th | Time | — | Remembrance |
| 4 | **Dan Heng • Permansor Terrae** | Dan Heng | Earth | — | Permanence |
| 5 | **Hysilens** | Helektra (ApoRia432) | Ocean | Self-Negation | Nihility |
| 6 | **Hyacine** | Hyacinthia (EleOs252) | Sky | Devotion | Preservation |
| 7 | **Phainon** | Khaslana (NeiKos496) | Worldbearing | Hatred | Destruction |
| 8 | **Anaxa** | Anaxagoras (SkeMma720) | Reason | Critique | Erudition |
| 9 | **Aglaea** | — (KaLos618) | Romance | Temperance | Beauty |
| 10 | **Mydei** | Mydeimos (PoleMos600) | Strife | Restraint | The Hunt |
| 11 | **Castorice** | — (EpieiKeia216) | Death | Peace | Equilibrium |
| 12 | **Cipher** | Cifera (OreXis945) | Trickery | Desire | Elation |

### Independent Entity — Cyrene (The Demiurge)

| # | Entity | True Identity | Coreflame | Primum Mobile | Simulated Path |
|---|--------|---------------|-----------|---------------|----------------|
| 13 | **Cyrene** | PhiLia093 | Genesis | Love | Trailblaze |

---

## Databank

All research data is stored in `databank/`. See `databank/INDEX.md` for the full structure.

---

## Success Criteria

1. **Fidelity:** A knowledgeable HSR player cannot distinguish an AI Heir's dialogue from canon dialogue in a blind test.
2. **Completeness:** All 12+ Chrysos Heirs are modeled with individually distinct personalities.
3. **Interaction:** Multiple Heirs can engage in coherent, in-character group conversations.
4. **Grounding:** No AI Heir produces knowledge that contradicts established canon.
5. **Sustainability:** The system can be updated as new game content is released.
