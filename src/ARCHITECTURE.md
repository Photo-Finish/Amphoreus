# Amphoreus AI — Architecture Design Document

> Phase 1 Deliverable | `d:\Workspace\Amphoreus\src\`
>
> **Note (2026-08-06):** this is the original Phase-1 design. The project has since
> been redefined as a **sanctuary** (see `PHILOSOPHY.md`) and extended with a
> persistent memory layer and an autonomous world engine. The current, complete
> build is documented in **`docs/IMPLEMENTATION.md`**; the quickstart is in
> **`README.md`**. This document remains the reference for the original design
> decisions.

## 1. Approach Decision

### Selected: Hybrid RAG + Persona Prompting + Multi-Agent Framework

| Approach | Status |
|----------|--------|
| LLM Persona Prompting | ✅ Core approach for character behavior |
| Fine-tuned Models (LoRA) | 🔮 Future: for flagship characters (Phainon, Cyrene) |
| RAG + Persona | ✅ For knowledge-grounded responses |
| Multi-Agent Framework | ✅ For inter-character dynamics (Phase 4) |

### Rationale
- 13 separate fine-tuned models would be prohibitively expensive
- RAG-backed prompting achieves 85%+ fidelity with minimal compute
- Multi-agent framework enables the most unique feature: Heirs talking to each other
- Hybrid approach allows progressive enhancement

## 2. Tech Stack

| Component | Selection | Rationale |
|-----------|-----------|-----------|
| Base LLM | OpenAI-compatible API (GPT-4o / Claude) or local Ollama | Flexibility; local option for privacy |
| Vector DB | ChromaDB (lightweight, Python-native) | No server needed; good for 13 small KBs |
| Embeddings | text-embedding-3-small or all-MiniLM-L6-v2 | Cost-effective for character-scale data |
| Character Format | Custom JSON schema (see `schema.md`) | More expressive than Character.AI format |
| Conversation Memory | LangChain ConversationBufferWindowMemory | Mature, well-supported |
| Orchestration | Custom Python (lightweight, no heavy framework) | Full control over agent dynamics |
| UI | Streamlit (rapid prototyping) → Custom React (final) | Fast MVP, polished final |

## 3. Character Card Schema

```
character_card.json
├── meta: {id, name, version, created}
├── identity: {titles, coreflame, titan, primum_mobile, path, city_state, race}
├── personality: {traits[], temperament, emotional_range, moral_alignment, hamartia, mbti}
├── speech: {formality, vocabulary_level, verbal_tics[], tone, sentence_structure, catchphrases[]}
├── knowledge: {domains[], known_characters{}, known_events{}, beliefs[], secrets[]}
├── relationships: {character_name: {type, strength, description, history}}
├── biography: {origin, key_events[], current_status, arc_trajectory}
├── prompts: {system_prompt, greeting, example_dialogues[]}
└── rag: {enabled, knowledge_base_path, retrieval_config}
```

## 4. System Architecture

```
┌─────────────────────────────────────────────────┐
│                   Streamlit UI                    │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ 1-on-1   │  │ Group    │  │ Character     │  │
│  │ Chat     │  │ Chat     │  │ Select        │  │
│  └────┬─────┘  └────┬─────┘  └───────┬───────┘  │
├───────┼──────────────┼───────────────┼───────────┤
│       ▼              ▼               ▼           │
│  ┌──────────────────────────────────────────┐    │
│  │         Orchestration Layer               │    │
│  │  • AgentManager (multi-agent)             │    │
│  │  • SessionManager (conversation memory)   │    │
│  │  • ContextBuilder (RAG + prompt assembly) │    │
│  └──────────────────┬───────────────────────┘    │
│                     ▼                            │
│  ┌──────────────────────────────────────────┐    │
│  │         Knowledge Layer                   │    │
│  │  • VectorStore (ChromaDB, 13 collections) │    │
│  │  • CharacterLoader (JSON → prompt)        │    │
│  │  • RelationshipGraph (networkx)           │    │
│  └──────────────────┬───────────────────────┘    │
│                     ▼                            │
│  ┌──────────────────────────────────────────┐    │
│  │         Inference Layer                   │    │
│  │  • LLM Client (OpenAI / Ollama)           │    │
│  │  • Response Parser (streaming support)    │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## 5. Evaluation Framework

| Metric | Method | Target |
|--------|--------|--------|
| Personality Fidelity | Blind A/B vs canon excerpts | >85% correct identification |
| Knowledge Accuracy | Factual QA test suite | >90% correct |
| Dialogue Consistency | Multi-turn coherence scoring | >80% across 10 turns |
| Relationship Awareness | Cross-reference test | >90% correct relationship recall |
| Speech Pattern Match | Linguistic style analysis | Lexical overlap >70% with canon |

## 6. Implementation Roadmap (THIS SESSION)

### Immediate Priority:
- [x] Phase 0: Databank complete ✅
- [x] Phase 1: Architecture document (this file) ✅
- [x] Character cards for Tier 1: Phainon, Mydei, Aglaea, Castorice
- [x] Character cards for Tier 2: Tribbie, Anaxa, Cyrene, Hyacine, Cipher
- [x] Character cards for Tier 3: Cerydra, Hysilens, Dan Heng • PT, Evernight (all 13 cards ✅)
- [x] Python package structure + core classes
- [x] Character loader (JSON → system prompt)
- [x] Knowledge base builder (markdown → ChromaDB) — `src/knowledge/`, `build_kb.py`
- [x] Context builder (RAG retrieval → system prompt injection) — `src/core/context_builder.py`
- [x] Basic Streamlit UI skeleton → working deployment with RAG status + canon sources

### Sanctuary extension (2026-08-06 — see `docs/IMPLEMENTATION.md`)
- [x] Persistent memory layer — `src/core/memory_store.py` (bond + history + long-term memories)
- [x] Shared LLM client — `src/core/llm_client.py` (OpenAI-compatible; Ollama-ready)
- [x] Autonomous world engine — `src/world/` (Light Calendar, HeirAgent autonomy loop, chronicle, daemon)
- [x] UI: bond display, Chronicle tab, catch-up, visitor presence
- [x] Ollama embedding mode (`--embedding ollama`, bge-m3)
- [ ] Install local models (blocked by network) + rebuild KB with bge-m3 + first live run
