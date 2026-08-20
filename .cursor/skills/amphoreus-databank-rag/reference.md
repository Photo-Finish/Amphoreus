# Databank RAG reference

## Character IDs → aliases (`kb_builder.CHARACTER_ALIASES`)

| Card ID | Alias tokens (mission filter) |
|---|---|
| aglaea | Aglaea |
| anaxa | Anaxa, Anaxagoras, Blasphemer |
| castorice | Castorice, Thanatos |
| cerydra | Cerydra, Empress, Imperator of the Flame-Chase |
| cipher | Cipher, Cifera, Trickery |
| cyrene | Cyrene, Demiurge, Mem |
| dan-heng-permansor-terrae | Dan Heng, Permansor, Terravox, Vidyadhara |
| evernight | Evernight, March 7th, March 7, Oronyx, Rain of Sensation |
| hyacine | Hyacine, Hyacinthia, Seliose, Aquila |
| hysilens | Hysilens, Helektra, Phagousa |
| mydei | Mydei, Mydeimos, Kremnos, Nikador |
| phainon | Phainon, Khaslana, Deliverer, Kephale |
| tribbie | Tribbie, Tribios, Trianne, Trinnon, Janus |

## GLOBAL_PATTERNS (indexed into every collection)

```
world/**/*.md
titans/**/*.md
lore/**/*.md
experiment/**/*.md
characters/**/*.md
chrysos-heirs/MASTER-REGISTRY.md
INDEX.md
```

Not indexed into Chroma: `databank/wiki/**`, `databank/build/**`, `missions/_cache/**` (unless matched by mission patterns).

## Mission chapter files

```
databank/missions/chapter-01-heroic-saga.md
databank/missions/chapter-02-light-slips.md
databank/missions/chapter-03-through-petals.md
databank/missions/chapter-04-fall-at-dawn.md
databank/missions/chapter-05-sun-set-to-die.md
databank/missions/chapter-06-before-their-deaths.md
databank/missions/chapter-07-back-to-earth.md
databank/missions/chapter-08-as-tomorrow.md
databank/missions/adventure/v30.md … v38.md
```

## Chunking

`src/utils/text_utils.chunk_markdown` — header → paragraph → sentence wrap. Metadata per chunk: `source` (posix path under `databank/`), `kind`.

## Related tools

| Tool | Role |
|---|---|
| `build_kb.py` | Build / status Chroma collections |
| `tools/fetch_wiki_amphoreus.py` | Refresh `databank/wiki/` |
| `tools/build_heir_knowledge.py` | Bake wiki-derived ranges into cards (Copilot-era — ask before editing cards) |
| `AgentManager.get_rag_context` / `rag_status` / `build_knowledge_base` | UI/operator hooks |

## Embedding modes

`local` (default ONNX MiniLM), `openai`, `ollama` (e.g. bge-m3), `hashing` (offline rough), `auto` (OpenAI if key else hashing). Match build and query mode to the same persist dir.
