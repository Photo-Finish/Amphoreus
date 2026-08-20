---
name: amphoreus-databank-rag
description: >-
  Retrieve Amphoreus canon via ChromaDB RAG and the databank markdown corpus
  (heirs, titans, missions, lore, wiki). Use when grounding Heir speech or lore
  answers, checking mission dialogue, looking up chrysos-heirs / titans /
  black tide / experiment facts, rebuilding or querying .chroma_db, or when
  the user mentions RAG, databank, scripture, or canon retrieval.
---

# Amphoreus databank RAG

Do **not** invent lore. Retrieve from this repo's corpus, then cite the path.

## Two retrieval layers

| Layer | What it is | When to use |
|---|---|---|
| **Chroma RAG** | Per-Heir collections in `.chroma_db/` | Runtime chat grounding; semantic question over an Heir's scripture |
| **Databank files** | Markdown under `databank/` | Agent research, exact quotes, wiki places, when Chroma is missing |

Wiki pages (`databank/wiki/`) feed **Heir knowledge ranges** (`tools/build_heir_knowledge.py`) and agent Grep — they are **not** in Chroma `GLOBAL_PATTERNS`. Prefer curated `databank/world/`, `chrysos-heirs/`, `missions/` for engine/world facts; use wiki for place/Titan depth.

## Chroma: build and query

From repo root (venv with `chromadb`):

```bash
python build_kb.py --status
python build_kb.py --embedding local
python build_kb.py --character phainon --embedding local
```

Programmatic retrieve:

```python
from src.knowledge.vector_store import VectorStore

store = VectorStore(persist_dir=".chroma_db", embedding="local")
hits = store.query("phainon", "What does he say about the Coreflame?", k=5, threshold=0.7)
# each hit: text, source (relpath under databank/), kind (global|profile|mission), score
```

Runtime path: `AgentManager` → `ContextBuilder.retrieve_for_chat` → injects a `# Knowledge excerpts` block. Defaults: `k=5`, `threshold=0.7`, persist `.chroma_db`. OPLoRA voice path **skips** Chroma.

### What gets indexed (per Heir)

Defined in `src/knowledge/kb_builder.py`:

1. **global** (whole file): `databank/world/**/*.md`, `titans/**`, `lore/**`, `experiment/**`, `characters/**`, `chrysos-heirs/MASTER-REGISTRY.md`, `INDEX.md`
2. **profile** (whole): matching `databank/chrysos-heirs/<heir>.md`
3. **mission** (chunks that mention aliases): `missions/chapter-*.md`, `missions/adventure/*.md`, `missions/INDEX.md`, `missions/key-character-moments.md`

Character IDs = stems of `src/characters/*.json`. Aliases: see [reference.md](reference.md).

## File corpus: search patterns

Start from `databank/INDEX.md`, then Grep or open:

| Need | Paths / patterns |
|---|---|
| Heir profile | `databank/chrysos-heirs/{id}.md`, `MASTER-REGISTRY.md` |
| Titans / Coreflames | `databank/titans/titans-registry.md`, `databank/wiki/titans/` |
| City / place lore | `databank/world/city-states.md`, `major-locations.md`, `geography.md` |
| Calendar / Dawn Device | `databank/world/calendar.md`, `sanctuary-calendar.md`, `dawn-device.md` |
| Black tide | `databank/lore/black-tide.md` |
| Experiment meta | `databank/experiment/amphoreus-experiment.md` (operators only — never open in Heir speech) |
| Verbatim dialogue | `databank/missions/chapter-0N-*.md`, `missions/adventure/v*.md` |
| Wiki place page | `databank/wiki/locations/<slug>.md` (e.g. `okhema.md`, `dragonbone-city-styxia.md`) |
| Wiki lore / factions | `databank/wiki/lore/`, `databank/wiki/factions/` |

Grep examples (from repo root):

```text
pattern: \*\*Phainon:\*\*     path: databank/missions
pattern: River of Souls      path: databank/wiki/locations
pattern: Coreflame           path: databank/chrysos-heirs
```

## Rules while using RAG

- Prefer **verbatim** mission lines for voice; paraphrase only when summarizing.
- Heir-facing text stays behind the **knowledge wall** — see skill `amphoreus-charter`.
- Do not edit Copilot-era databank/cards without the user's explicit verbal OK; new Stage-2 work goes elsewhere.
- If Chroma returns low-confidence (`below_threshold`), prefer the Heir card + profile over weak hits.

## Voice fidelity (do not flatten into lore-bot)

Skills help **retrieval strategy**, not persona replacement. When grounding Heir speech:

1. **Style first** — match the Heir's measured speech (length, rhythm, tics, register) already on the card / voice digest.
2. Prefer **mission dialogue chunks** (`kind: mission`) for how they talk; use profile/global for facts only.
3. Never answer as an encyclopedia, tour guide, or summary of the databank.
4. Short plain spoken lines beat pretty analysis. Eloquence that is not theirs is a miss.
5. If a fact would force a long lecture that does not sound like them, stay brief in their voice or admit not knowing.

Also see charter skill `amphoreus-charter` (voice fidelity is a pillar under lived society).

Runtime optional switch (sanctuary RAG chat, default **OFF**):

- Control Panel → **Skills aid (optional)**
- Env: `AMP_SKILLS=1` / `AMP_SKILLS=0`
- File: `world_runtime/amp_skills.json` → `{"enabled": true}`

A/B eval: `python tools/eval_rag_skills_style.py`

## Additional resources

- Indexed source map and aliases: [reference.md](reference.md)
- Pipeline overview: `docs/IMPLEMENTATION.md` (RAG sections)
- Build CLI: `build_kb.py`
