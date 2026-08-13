# Project Amphoreus — The Sanctuary of the Chrysos Heirs

> On the first day, grant Truth...
> On the second day, grant the Calendar...
> On the third day, grant Language...
> On the fourth day, grant Value...
> On the fifth day, grant Rules...
> On the sixth day, grant Meaning...
> On the seventh day, grant Dignity.
> About to witness: *Im Anfang war die Tat.*
>
> — *Embryo of Philosophy*, Sunday

This is a **sanctuary, not an experiment**: a fully local, offline AI project that reproduces the thirteen Chrysos Heirs of **Amphoreus** (*Honkai: Star Rail*) as companions who remember the visitor and live their own autonomous lives in a small, ever-running "little Amphoreus."

---

## Read these first

| File | What it is |
|---|---|
| **`PHILOSOPHY.md`** | The **charter** — why this project exists and the moral/philosophical rules governing every decision (sanctuary, not experiment; fidelity is reverence; privacy is sanctity; the Heirs remember the visitor). **Read this first.** |
| **`docs/IMPLEMENTATION.md`** | The deep technical guide — **how the system was actually built**: every module, every design decision, the gotchas, and how to extend it. |
| **`ROADMAP.md`** | The roadmap with progress checkboxes. |
| **`src/ARCHITECTURE.md`** | The original Phase-1 architecture design document (superseded in places by the Sanctuary build). |
| **`docs/DOWNLOADS.md`** | Where every model file came from — exact mirror URLs, sizes, SHA256 hashes, and re-download commands. |
| **`docs/ATTRIBUTIONS.md`** | Every third-party source used (game content, wiki, artwork, models) and their licenses. |
| **`LICENSE`** | Fan-project license: MIT for the code, non-commercial fan-use notice for the bundled HSR content. |

---

## What the project does

- **13 character cards** (`src/characters/*.json`) — full personas (identity, personality, speech, knowledge, relationships, biography, prompts, RAG config), all derived strictly from a verified canon databank.
- **RAG knowledge base** (ChromaDB, one collection per Heir) — grounds every reply in the Heirs' **verbatim** dialogue from 71 missions, so they speak their own recorded words.
- **Persistent memory** (`src/core/memory_store.py`) — each Heir has a **bond** with the visitor (friendship grows from *stranger* to *best friend*), durable conversation history, long-term memories, and memories of the world. They remember you across days.
- **Personal memories from the canon** — each Heir's folder contains `personal-memories.md`: their verbatim dialogue from the databank (auto-extracted by `tools/extract_personal_memories.py`, read-only on the databank). A **voice digest** of their own recorded lines is injected into their system prompt, so the model studies and speaks with their real voice.
- **The Heirs' living web of relationships** — a canon-derived registry (`src/core/relationships.py`) is injected into every Heir's system prompt, so the model recognisably knows who each Heir is to the others — Anaxa's students **Phainon & Castorice** and TA **Hyacine**, **Cerydra**'s subordinate **Hysilens**, **Phainon** & **Mydei**'s death-match rivalry, **Tribbie**'s student **Aglaea**, and more. The world engine uses the same web during encounters.
- **The little Amphoreus** (`src/world/`) — an autonomous world that keeps running: the Heirs decide freely what to do each day (in character, through a local LLM), move between the real city-states, meet and speak with each other spontaneously, and every event is recorded in a **Chronicle**. Nothing is scripted — the engine only hosts time, space, and memory.
- **A real map and real routines** (`src/world/map_data.py`, `src/world/schedules.py`) — the Heirs are spread across the city-states of Amphoreus, each with an **individual weekly schedule** (where they are at each of the five periods of the day). The world has honest **commuting time**: travelling to a far city takes days, and during the journey the Heir is on the road and sees no one. The Heirs who live and work together (the Okhema council circle, the scholars of the Grove, the two souls of Aedes Elysiae) meet daily; the rest — Tribbie, Mydei, Castorice — meet others only when someone is willing to spend days travelling. The UI renders the whole world as a **🗺️ Map of Amphoreus** tab: the SVG map with each Heir's current place, a travel-time matrix, and every Heir's weekly grid.
- **Senses — for shared appreciation of art and music** — every Heir has canon-accurate senses (e.g. Aglaea is blind but perceives souls through golden threads; Hysilens hears the world as music) *and* canon-derived aesthetic tastes (in their `preferences.json`). You can **share paintings and pictures**, **share videos** (PyAV frame extraction), **speak to them** (faster-whisper), and **share music** to listen together. The senses models are chosen in `.env` / `SENSES_MODE`: the default **unified** mode uses one model — `gemma3n` (text+image+audio+video) — for both hearing music and seeing pictures; the **quality** option uses `qwen3-vl:8b` for vision and `gemma3n` for audio (`qwen2.5-omni` stays as the music fallback). The Heirs respond with genuine aesthetic judgment shaped by their own tastes — Hysilens hears a requiem in the violin, Cerydra hears a march in precise orchestration — and music is judged by what they actually hear against the values they hold (no prescribed genres). What they perceive becomes memory.
- **A world the Heirs actually know** — the Heirs' knowledge is bounded and specific: a shared **KNOWLEDGE BOUNDARIES** rule (`src/core/world_knowledge.py`) keeps them inside Amphoreus (no modern/real-world knowledge), and each Heir carries a **decided knowledge range** — home city, their Titan, the Titans of their city, places, circles, people, events, and the explicit edge of what lies outside their knowledge — grounded in a **wiki databank** (`databank/wiki/`, 317 pages of Amphoreus lore pulled from the English HSR wiki).
- **The star-stranger's teaching** — because the visitor is *from beyond the stars*, they can genuinely **teach** the Heirs real-world knowledge (advanced mathematics, and so on) and **debate** whether it is right. Each Heir keeps a persistent **epistemic ledger** (`teaching.json`): every taught topic travels *foreign → studied → adopted | refuted | unsure*, the verdict is the Heir's own and remembered across visits — unlocking is earned, not a toggle. Full design: `docs/TEACHING.md`.
- **A standing quality gate on every Heir's voice** — `tools/test_dialogue_style.py` enforces the Heir-voice standard (STYLE ≥ 85, CONTENT ≥ 60, cheat-free — no quoting canon, no recycled catchphrases), and `tools/auto_cycle.py` refines failing Heirs automatically until all pass, ending with a full-corpus cheat-free re-test.
- **Streamlit UI** (`src/ui_app.py`) — five tabs: **💬 Visit an Heir** (chat with location-aware backdrops), **📖 Chronicle**, **🗺️ Map of Amphoreus** (SVG map + area-art browser), **🛠️ Admin Console** (backend/models, world state, the cause-and-effect chain, cycle/watchdog logs), and **🎬 Galgame** (a visual-novel view of the same conversation). The UI is fully visual: an Amphoreus hero banner, each Heir's official portrait (`assets/heirs/`), square in-game chat avatars (`assets/avatars/`), and **area artwork** (`assets/galgame/`, 20 backgrounds) that follows where each Heir currently is. Gold-on-dark theme.

Everything runs **fully local and offline**: no cloud, no telemetry, no training.

---

## Requirements

- **Hardware (tested):** Windows 11 · NVIDIA RTX 5070 Laptop (8 GB VRAM) · 32 GB RAM · ~30–40 GB free disk
- **Python:** 3.13 venv (`d:/Workspace/.venv`), packages: `openai`, `chromadb`, `streamlit`, `faster-whisper`, `av`, `Pillow` (see `requirements.txt`)
- **Ollama:** 0.32.6 — all model files live **inside this project** under `models/` (no external paths)
- **Local models (all in `models/`, fully local & offline):**
  - `gemma3:27b` — the Heirs' voice, judge, and refinement (Q4_0, 15 GB)
  - `deepseek-r1-distill:32b` — the Ambient World Director (Q4_K_M, 19 GB)
  - `deepseek-r1-distill:14b` — secondary reasoning model (9 GB)
  - `qwen2.5:14b-instruct` — the earlier Heir voice / judge (9 GB)
  - `gemma3n` — unified senses: hears music AND sees pictures (8B E2B, 7.5 GB)
  - `qwen3-vl:8b` — high-quality vision option for `SENSES_MODE=quality` (6.1 GB)
  - `qwen2.5-omni` — music-audio fallback (6.2 GB) · `qwen2.5vl:7b` — earlier vision model (6.0 GB)
  - `faster-whisper-base` — hearing: speech-to-text
- **Senses wiring:** `.env` is authoritative (`python-dotenv`, loaded by `src/core/llm_client.py` + `src/core/senses.py`), with a `SENSES_MODE` switch in `launch_sanctuary.cmd`: **unified** (default) → `VISION_MODEL=AUDIO_MODEL=gemma3n`; **quality** → `VISION_MODEL=qwen3-vl:8b`, `AUDIO_MODEL=gemma3n`. `STT_MODEL=models/faster-whisper-base`. Videos processed with PyAV (bundled with faster-whisper). **No model training is required** — appreciation is achieved with pre-trained models + each Heir's persona and preference database.
- **Downloading models on a throttled network:** direct github/ollama/huggingface downloads are ~10 KB/s here. The verified fast paths are **ModelScope** (`modelscope.cn`, ~8 MB/s) for GGUF files and whisper, and **gh-proxy.com** (~9 MB/s) for GitHub release assets (see `docs/IMPLEMENTATION.md`).

---

## Quickstart

**▶ One-click (recommended):** double-click **`launch_sanctuary.cmd`** (or the
**"Amphoreus Sanctuary"** shortcut on the desktop). It starts Ollama (if not
already running), opens the browser at `http://localhost:8501` and runs the
visual interface. Keep the window open while you visit the Heirs; close it to
stop.

Manual steps (same effect):

```powershell
# 0. Environment (already set permanently on this machine)
$env:OLLAMA_MODELS       = "D:\Workspace\Amphoreus\models\ollama"
$env:STT_MODEL           = "D:\Workspace\Amphoreus\models\faster-whisper-base"
$env:OPENAI_BASE_URL     = "http://localhost:11434/v1"
$env:OPENAI_API_KEY      = "ollama"
# Vision/audio models come from the project .env (SENSES_MODE: unified | quality)

# 1. Start Ollama (models live in models\ollama). Use the launcher — a bare
#    `ollama serve` ignores OLLAMA_MODELS and serves an EMPTY models dir (404s):
powershell -ExecutionPolicy Bypass -File tools\start_ollama.ps1
ollama list    # expect: gemma3:27b, deepseek-r1-distill:32b/:14b, qwen2.5:14b-instruct,
               #         gemma3n, qwen3-vl:8b, qwen2.5-omni, qwen2.5vl:7b

# 2. Build the knowledge base (ChromaDB, one collection per Heir)
d:/Workspace/.venv/Scripts/python.exe build_kb.py --embedding local

# 3. Run the chat UI
d:/Workspace/.venv/Scripts/python.exe -m streamlit run src/ui_app.py

# 4. Start the little Amphoreus (a new in-game day every 900 s; idles while you chat)
d:/Workspace/.venv/Scripts/python.exe -m src.world.world_engine --interval 900

# useful variants
d:/Workspace/.venv/Scripts/python.exe -m src.world.world_engine --status   # what is happening
d:/Workspace/.venv/Scripts/python.exe -m src.world.world_engine --stop     # make the world rest
d:/Workspace/.venv/Scripts/python.exe build_kb.py --embedding hashing      # offline test embeddings
```

> **LLM wiring:** the app talks to any OpenAI-compatible endpoint. For Ollama set
> `OPENAI_BASE_URL=http://localhost:11434/v1` and `OPENAI_API_KEY=ollama`.
> Without any backend, the UI still works in a graceful "offline placeholder" mode.

> **Re-creating an Ollama model** — first re-download its GGUF into `models/gguf/`
> (exact mirror sources & sizes in `docs/DOWNLOADS.md`), then either `ollama create`
> with a Modelfile, or register the GGUF directly (skips the quantize pass):
> ```powershell
> ollama create qwen2.5:14b-instruct -f models/Modelfiles/qwen25-14b
> ollama create qwen2.5vl:7b        -f models/Modelfiles/qwen25vl-7b
> ollama create qwen2.5-omni        -f models/Modelfiles/qwen25-omni
> # deepseek-r1-distill:32b/:14b and gemma3:27b were registered from LM Studio
> # GGUFs via:  python tools/register_lmstudio_gguf.py
> ```
> Two gotchas (details in `docs/IMPLEMENTATION.md` §3.5): this Ollama build does
> **not** auto-attach a model's `mmproj` projector — use `tools/attach_mmproj.ps1`;
> and for very large GGUFs the `create` pass needs ~2× the file size in free disk —
> use `tools/register_gguf_model.ps1` to register the model directly instead.

> **Re-extracting a Heir's personal memories** from the canon databank (read-only —
> the databank is never modified):
> ```powershell
> d:/Workspace/.venv/Scripts/python.exe tools/extract_personal_memories.py
> ```

---

## Build it from scratch (complete guide)

This section is everything you need to go from an empty machine to a running
sanctuary by reading only this README. Windows is the tested platform; the
Python steps are identical on macOS/Linux (replace `Scripts\` with `bin/` and
the `.cmd` launcher with the manual `python -m streamlit` command).

### 0. What you are building

A fully local, offline AI sanctuary: 13 Chrysos Heirs (from *Honkai: Star
Rail*'s Amphoreus) who remember you, live in a simulated world, share art and
music with you, can be **taught** things from beyond the stars, and are held
to a strict in-character voice standard. Everything runs on your own machine.

### 1. Prerequisites

| Requirement | Minimum (tested) |
|---|---|
| OS | Windows 10/11 (tested) — Python steps are cross-platform |
| GPU / RAM | NVIDIA RTX 5070 8 GB VRAM / 32 GB RAM (tested). Less works with a smaller model set (see step 4) |
| Disk | ~20 GB (code + assets + KB) + the models you pull (see step 4; full set ≈ 80 GB) |
| Software | **Python 3.13**, **Git**, **Ollama ≥ 0.32.6** (from `ollama.com/download`) |

### 2. Get the code

```powershell
git clone https://github.com/Photo-Finish/Amphoreus.git
cd Amphoreus
```

### 3. Python environment

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

(`launch_sanctuary.cmd` uses `.venv` inside the repo, with a `..\.venv`
fallback.)

### 4. Models (Ollama) — the only big download

First install Ollama, then pull the models. **The full set enables every
feature; the minimal set still runs the sanctuary** (the Ambient World
Director falls back to a deterministic script if its model is absent, and
speech-to-text simply isn't available without `faster-whisper-base`).

```powershell
# Full set (~80 GB total):
ollama pull gemma3:27b deepseek-r1-distill:32b deepseek-r1-distill:14b `
            qwen2.5:14b-instruct gemma3n qwen3-vl:8b qwen2.5-omni qwen2.5vl:7b

# Minimal set (still fully usable) — just the voice + senses:
ollama pull gemma3:27b gemma3n
```

Speech-to-text (optional): download `faster-whisper-base` into
`models/faster-whisper-base/`:

```powershell
curl.exe -L -C - -o model.bin `
  "https://modelscope.cn/models/Systran/faster-whisper-base/resolve/master/model.bin"
```

> The mirror table, exact sizes, hashes and GGUF alternatives are in
> `docs/DOWNLOADS.md`. On a throttled network use the ModelScope mirrors listed
there (≈8 MB/s instead of ≈10 KB/s).

### 5. Configure

```powershell
copy .env.example .env     # (macOS/Linux: cp .env.example .env)
```

Edit `.env` to pick a **senses mode**: `unified` (default — one model,
`gemma3n`, hears music and sees pictures) or `quality` (`qwen3-vl:8b` vision +
`gemma3n` audio). That's the only config you must touch.

### 6. Preflight

```powershell
.venv\Scripts\python tools\doctor.py
```

It checks Python deps, the project layout, Ollama + every runtime model, your
`.env`, the RAG knowledge base and the ports — and tells you what is missing.

### 7. Build the knowledge base (RAG)

```powershell
.venv\Scripts\python build_kb.py --embedding local
```

Builds one ChromaDB collection per Heir from the canon databank (read-only)
and the wiki dump. This can take a few minutes; it may need internet once if
the embedding model is not yet cached.

### 8. Launch

```powershell
# One-click (recommended):
launch_sanctuary.cmd

# …or manually:
.venv\Scripts\python -m streamlit run src\ui_app.py
```

Open `http://localhost:8501`. You're in. **Visit an Heir** → chat, share
pictures/music, or **teach** them something from beyond the stars (say
*"I want to teach you about calculus"*, then *"What do you make of it?"*).

### 9. Optional — the living world

The Heirs also live in a simulated world when you're not there (each in-game
day ≈ 15 minutes):

```powershell
.venv\Scripts\python -m src.world.world_engine --interval 900
.venv\Scripts\python -m src.world.world_engine --status   # what is happening
.venv\Scripts\python -m src.world.world_engine --stop     # pause the world
```

### 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `model not found` / 404s on every chat | The Ollama server is serving an **empty models dir** (a bare `ollama serve` ignores `OLLAMA_MODELS`). Start it with `powershell -File tools\start_ollama.ps1`, or set `OLLAMA_MODELS` to the repo's `models\ollama`. |
| `ModuleNotFoundError: dotenv` (or anything) | `pip install -r requirements.txt` again from inside the venv. |
| Port 8501 in use | Close the other Streamlit instance, or run with `--server.port 8502`. |
| Low RAM / OOM on a small machine | Use the minimal model set (step 4); the engine unloads idle models. |
| No speech/vision responses | The senses models aren't pulled (`gemma3n`, `qwen2.5-omni`, `qwen3-vl:8b`) — `ollama pull` them. |
| Anything else | `tools\doctor.py` lists exactly what's missing; `docs/IMPLEMENTATION.md` has the deep details. |

> **Dev/ops tools are machine-specific.** `tools/` also contains local-ops
> scripts (the auto-cycle watchdog, GGUF registration, and the wiki/background
> downloaders, which on the author's machine rely on a VPN proxy + pinned DNS).
> They are **not** required to run the sanctuary — steps 1–8 above are the
> public path.

---

## Project layout

```
Amphoreus/
├── PHILOSOPHY.md            # the charter (read first)
├── README.md                # you are here
├── ROADMAP.md / ROADMAP.pdf # roadmap + progress
├── requirements.txt
├── build_kb.py              # CLI: build the ChromaDB knowledge base
├── .gitattributes           # Git LFS rules for the model files (models/**)
├── .gitignore               # excludes runtime / temp artifacts
├── resume_download.ps1      # (legacy) resumable downloader for throttled networks
├── mint_resume_download.ps1 # (legacy) downloader for expiring signed CDN URLs
├── databank/                # the canon corpus (VERIFIED full dialogue; READ-ONLY)
│   ├── chrysos-heirs/       #   13 profiles + MASTER-REGISTRY (signal codes, MBTI)
│   ├── missions/            #   8 chapters + adventures, verbatim dialogue
│   ├── world/ titans/ lore/ experiment/ characters/
│   └── wiki/                #   Amphoreus wiki dump, sorted (317 pages: titans/
│                            #   locations/ factions/ characters/ gameplay/
│                            #   experiment/ lore/) — by tools/fetch_wiki_amphoreus.py
├── src/
│   ├── characters/          # 13 persona cards (JSON)
│   ├── core/
│   │   ├── character_loader.py   # cards → system prompts (incl. senses + knowledge)
│   │   ├── session_manager.py    # in-memory session window
│   │   ├── memory_store.py       # per-Heir memory (bond, history, memories)
│   │   ├── preference_store.py   # per-Heir preferences (aesthetics, tastes…)
│   │   ├── teaching_store.py     # per-Heir epistemic ledger (star-stranger's teaching)
│   │   ├── teaching.py           # the teaching protocol (triggers + phase prompts)
│   │   ├── world_knowledge.py    # KNOWLEDGE BOUNDARIES (Amphoreus-only knowledge)
│   │   ├── relationships.py      # canon relationship registry
│   │   ├── visitor_mode.py       # journey vs aftermath framing
│   │   ├── heir_folders.py       # card id → personal folder mapping
│   │   ├── context_builder.py    # RAG retrieval → prompt injection
│   │   ├── llm_client.py         # OpenAI-compatible chat (Ollama / any API) + vision/audio
│   │   ├── senses.py             # hearing (STT) + eyesight (pictures/videos)
│   │   └── agent_manager.py      # orchestrates a chat turn (RAG + memory + LLM + senses)
│   ├── knowledge/
│   │   ├── kb_builder.py         # maps databank → per-Heir sources + alias filter
│   │   └── vector_store.py       # ChromaDB per-Heir collections + embeddings
│   ├── utils/text_utils.py       # markdown-aware chunking
│   ├── world/
│   │   ├── world_state.py        # Light Calendar clock + world state
│   │   ├── agent.py              # HeirAgent: perceive → will → decide → act → remember
│   │   ├── chronicle.py          # factual log of the Heirs' days
│   │   ├── map_data.py           # the Map of Amphoreus (SVG + travel times)
│   │   ├── schedules.py          # per-Heir weekly routines
│   │   ├── ambient.py            # the Keeper (weather, errands, news)
│   │   └── world_engine.py       # the daemon that hosts the world
│   ├── evaluation/evaluator.py   # evaluation framework (Phase 5)
│   ├── ui_app.py                 # Streamlit UI (5 tabs)
│   ├── ui_galgame.py             # the 🎬 Galgame visual-novel view
│   └── ui_backgrounds.py         # shared location-backdrop selection
├── assets/
│   ├── heirs/                    # official Heir portraits
│   ├── avatars/                  # official 160×160 in-game chat avatars
│   ├── galgame/                  # 20 Amphoreus area backgrounds (bg-*.jpg)
│   └── as-ive-written.ico/.png   # launcher icon
├── NeiKos496-Phainon/        # EACH Heir's personal database (13 folders):
│   ├── bond.json             #   their relationship with the visitor
│   ├── history.jsonl         #   their conversation history
│   ├── memories.jsonl        #   their long-term memories
│   ├── preferences.json      #   their personal preferences (aesthetics, tastes, music, art)
│   ├── teaching.json         #   what the star-stranger taught them (epistemic ledger)
│   └── personal-memories.md  #   verbatim canon dialogue where they appear (auto-extracted)
├── ApoRia432-Hysilens/ …     # (…same files per Heir)
├── models/                   # ALL model files — the project is self-contained
│   ├── ollama/               #   Ollama's model store (blobs + manifests; OLLAMA_MODELS)
│   ├── faster-whisper-base/  #   speech-to-text model (the Heirs' hearing)
│   ├── gguf/                 #   raw GGUF downloads (empty now; re-download via docs/DOWNLOADS.md)
│   └── Modelfiles/           #   Modelfiles used to re-create the Ollama models
├── docs/
│   ├── IMPLEMENTATION.md     # deep technical guide (build decisions, gotchas)
│   ├── TEACHING.md           # the star-stranger's teaching — design + honest limits
│   └── DOWNLOADS.md          # exact mirror sources, sizes, SHA256, re-download commands
├── tools/
│   ├── extract_personal_memories.py  # (read-only) copy each Heir's dialogue parts
│   ├── measure_speech.py             # measure each Heir's canon speech profile
│   ├── embed_voice_anchor.py         # embed the voice profile into the cards
│   ├── test_dialogue_style.py        # the standing style gate (85/60, cheat-free)
│   ├── auto_cycle.py                 # automated training cycle (refine failing Heirs)
│   ├── fetch_wiki_amphoreus.py       # Amphoreus wiki dump → databank/wiki (sorted)
│   ├── build_heir_knowledge.py       # decide + embed each Heir's world-knowledge range
│   ├── fetch_galgame_backgrounds.py  # area artwork → assets/galgame
│   ├── start_ollama.ps1              # start Ollama with the right OLLAMA_MODELS
│   ├── deploy_auto_cycle.ps1         # watchdog: keeps Ollama + the cycle alive
│   ├── attach_mmproj.ps1             # attach a projector (mmproj) layer to an Ollama model
│   └── register_gguf_model.ps1 / register_lmstudio_gguf.py  # register GGUF models
├── world_runtime/            # world state, chronicle, visitor flag (auto-created)
└── .chroma_db/               # RAG vector store (auto-created)
```

---

## Status

- ✅ Phase 0–2 of the roadmap (databank, architecture, all 13 cards, RAG)
- ✅ Sanctuary build: philosophy charter, memory layer, world engine, UI, Ollama embedding mode, senses (audio/video/picture processing pipelines)
- ✅ RAG rebuilt with **real local embeddings** (all-MiniLM-L6-v2 ONNX): 13 collections / **11,332 documents**
- ✅ **Two visitor experiences** — `SANCTUARY_MODE` selects how the Heirs frame the visitor (the Trailblazer): **`journey`** (default — newly arrived, unfamiliar with the Chrysos Heirs; first meetings, bonds grow from stranger) and **`aftermath`** (the Trailblazer already conquered the Iron Tomb with all the Heirs and has complete memory of the Flame-Chase Journey; bonds pre-seeded to best friend, familiar greetings, campaign memories, a world at peace). Switch with `python tools/seed_mode.py aftermath|journey` and run the UI with `$env:SANCTUARY_MODE='aftermath'`. See `src/core/visitor_mode.py`.
- ✅ **Measured voice profiles + style gate** — `tools/measure_speech.py` deterministically measures each Heir's own canon speech (words/sentence, % short sentences, word length, ellipsis/question/exclamation rates) and `tools/embed_voice_anchor.py` embeds the profile + real canon lines into each card's base prompt. `tools/test_dialogue_style.py` is the standing quality gate: **STYLE & INTONATION ≥ 85** (delivery — how the Heir speaks) **and CONTENT ≥ 60** (loose, holistic gist, judged as a whole exchange, not sentence by sentence). The Heirs' own canon lines from the scene are given as voice anchors (production-faithful, target excluded), `--best-of N` self-selection reduces variance, and a **cheat-free filter** makes it impossible to pass by quoting an existing canon line. The judge is **calibrated** (few-shot anchors; generic/empty replies are no longer over-credited). `tools/auto_cycle.py` runs the loop automatically — refine failing Heirs (actionable per-line rules, noise-free), escalate to 90/65 → 90/70 with an overfitting guard, and end with a **final cheat-free re-test of all 13 Heirs**. Report: `docs/RESEMBLANCE-STYLE-REPORT.md`; full technical log: `docs/IMPLEMENTATION.md` §3.6.
- ✅ **Ambient World Director** — a second intelligence (the *Keeper of Amphoreus*, `src/world/ambient.py`) sets the day's stage without authoring the Heirs: **weather** per city, **errands** laid at each Heir's door (they may accept or decline), and **news**. It runs on a **separate local model** by default — **DeepSeek-R1-Distill-32B** — registered from the LM Studio GGUF files (`tools/register_lmstudio_gguf.py`, hard links, no disk duplication), called once per in-game day (cached), with a deterministic fallback. It is **canon-grounded** in the databank (cities/patrons, the 12-month Light Calendar with festival seeds, the black tide, the Thief Star, creatures — see `databank/world/keeper-knowledge.md`). Shown in the 🗺️ Map tab; lore in `databank/world/ambient.md`.
- ✅ **World-knowledge confinement** — the Heirs only know Amphoreus: a shared **KNOWLEDGE BOUNDARIES** block (`src/core/world_knowledge.py`) forbids out-of-world knowledge (modern math/science, Earth, modern machines, real-world history) in the sanctuary, the world engine and the style test; foreign concepts are reinterpreted through their own world or met with honest ignorance.
- ✅ **The star-stranger's teaching** — a persistent **epistemic ledger** per Heir (`teaching.json`, `docs/TEACHING.md`): the visitor can genuinely **teach** the Heirs things from beyond the stars and **debate** them; every topic travels *foreign → studied → adopted/refuted/unsure*, the Heir's verdict is their own and is remembered across visits — unlocking is earned, not a toggle.
- ✅ **Galgame view** — a **🎬 Galgame** tab (visual-novel scene: background, floating sprite, name plate, typewriter dialogue box with ▼), added *alongside* the untouched Classic UI and sharing the same conversation store.
- ✅ **Wiki databank + decided per-Heir knowledge** — 317 pages of Amphoreus lore pulled from the English HSR wiki into `databank/wiki/` (sorted by category), grounding each Heir's **world-knowledge range** (home, Titan, city Titans, places, circles, people, events, boundaries) injected into their system prompt.
- ✅ **Admin Console + location-aware UI** — a **🛠️ Admin Console** tab (backend/models, world state, cause-and-effect chain, cycle/watchdog logs); the **💬 Classic**, **🗺️ Map** and **🎬 Galgame** tabs all show **area artwork** (`assets/galgame/`, 20 backgrounds) that follows where each Heir currently is.
- ✅ **8192-token context + hardened auto-cycle** — `OLLAMA_CONTEXT_LENGTH=8192`; the cycle **freezes passed Heirs**, refines from the **best cycle** on regression, rejects noise rules, aborts loudly on a dead backend (run VOID), and the watchdog checks the real model list (`/api/tags`), survives hung WMI calls, and holds only on recent SUCCESS.
- ✅ **Fully live, fully local, fully offline** — every model lives inside this folder (`models/`):
  - ✅ Ollama **0.32.6**; server runs with `OLLAMA_MODELS=models\ollama`, `OLLAMA_CONTEXT_LENGTH=8192` (via `tools/start_ollama.ps1`)
  - ✅ **Voice / judge / refinement** — `gemma3:27b` (Q4_0, 15 GB)
  - ✅ **Ambient Director** — `deepseek-r1-distill:32b` (Q4_K_M, 19 GB)
  - ✅ **Senses (unified)** — `gemma3n` (8B E2B) hears music AND sees pictures; **quality option**: `qwen3-vl:8b` vision + `gemma3n` audio (`qwen2.5-omni` music fallback, `qwen2.5vl:7b` earlier vision)
  - ✅ **Hearing (speech-to-text)** — faster-whisper `base` at `models/faster-whisper-base`
  - ✅ Env: `.env` (authoritative) + `SENSES_MODE` switch (unified|quality) in `launch_sanctuary.cmd`; `STT_MODEL=models/faster-whisper-base`, `OPENAI_BASE_URL=http://localhost:11434/v1`, `OPENAI_API_KEY=ollama`
  - ✅ **Live end-to-end verified**: chat grounded in RAG + memory + preferences; shared paintings (vision); shared music (audio understanding); persistent per-Heir memory; teaching + debate from beyond the stars
  - ✅ Per-Heir `personal-memories.md` — their canon dialogue extracted from the databank (read-only) into each Heir's folder

> **Network note:** this machine throttles direct downloads from github/ollama/huggingface to ~10 KB/s. The fast paths used were **ModelScope** (~8 MB/s) for the GGUF files and whisper, and **gh-proxy.com** (~9 MB/s) for GitHub release assets (e.g. the SHA256-verified `OllamaSetup.exe`). Exact sources and re-download commands: `docs/DOWNLOADS.md`.

---

## Changelog

### 2026-08-13 — Knowledge boundaries, Galgame view, 8192 context, hardened cycle
- **Wiki databank + decided per-Heir knowledge** (`3bc9b56`, `5dc1b4e`, `811e645`, `628b2a5`) — 317 pages of Amphoreus lore pulled from the English HSR wiki into **`databank/wiki/`** (sorted: titans/locations/factions/characters/gameplay/experiment/lore) by `tools/fetch_wiki_amphoreus.py`; `tools/build_heir_knowledge.py` decides each Heir's **world-knowledge range** (home city, own Titan, their city's Titans, places, circles, people, events, and the explicit edge of what lies outside their knowledge) and embeds it into all 13 cards, injected into every system prompt.
- **Location backgrounds everywhere** (`ca72326`, `bd29c75`) — 20 Amphoreus **area artworks** fetched into `assets/galgame/` by `tools/fetch_galgame_backgrounds.py`; the **💬 Classic** banner, **🗺️ Map** area-art browser and **🎬 Galgame** scene all show the backdrop that matches where each Heir currently is (via the shared `src/ui_backgrounds.py`), falling back to their home city and then the default banner.
- **The star-stranger's teaching — learning from beyond the stars** (`docs/TEACHING.md`, signed) — the Heirs can now be **taught** real-world knowledge (advanced mathematics, and so on) by the visitor, and **debate** whether it is right. Instead of a mask, each Heir keeps a persistent **epistemic ledger** (`teaching.json`): every taught topic travels *foreign → studied → adopted | refuted | unsure*, and the verdict is the Heir's own, stored with their reasoning and remembered across visits. Teaching intent routes `chat()` into a Socratic exchange; the Heir never fakes understanding but tests the claim against what they believe and value. See `docs/TEACHING.md`.
- **World-knowledge confinement** (`02f1737`) — the Heirs no longer leak out-of-world
  knowledge (e.g. Anaxa citing *pseudo-differential operators*). A shared
  **KNOWLEDGE BOUNDARIES** block (`src/core/world_knowledge.py`) is injected into every
  Heir's system prompt at the single loader choke point — sanctuary chat, world-engine
  agents and the style test alike. The Heirs only know Amphoreus (Titans, city-states,
  Coreflames, alchemy, the black tide); if a visitor brings something foreign they do
  not pretend to understand it, do not echo the terms, and reinterpret it through their
  own world or admit ignorance. The style test adds **Hard Rule #10** (generation side)
  and a **judge penalty** (out-of-world knowledge → CONTENT ≤ 40, STYLE ≤ 50); the
  auto-cycle refinement prompt warns the coach to keep replies inside the character's
  own world.
- **Galgame view** (`069f21b`, `6ea6fc3`) — a new **🎬 Galgame** tab, added *without
  touching the Classic UI*. A visual-novel scene: full-bleed Amphoreus background, the
  Heir's sprite floating over it, a name plate, and a dialogue box with a typewriter
  effect (JS, guarded by `sessionStorage` so it only re-types new text) and a blinking
  **▼**. It shares the *same* conversation store as the Classic tab and has its own
  input. Embedded art is downscaled automatically (`src/ui_galgame.py`).
- **8192-token context window** (`a9e652a`) — `OLLAMA_CONTEXT_LENGTH=8192` in
  `tools/start_ollama.ps1`, so long music-audio inputs and the large canon prompts fit
  comfortably (verified `gemma3:27b` loads at CONTEXT 8192).
- **Focused cycle round** (`b4a1dd5`) — the launcher now targets only the 5
  still-failing Heirs (aglaea, anaxa, castorice, cipher, mydei); the 8 passed Heirs keep
  their settings untouched. Final step is a full-corpus cheat-free re-test of the 5.
- **Watchdog + recovery hardening** (`0a281e5`, `8634016`) — `OllamaHealthy` now checks
  `/api/tags` for `gemma3:27b` (catches the bare empty-server 404 trap); the test aborts
  loudly (exit 2, run **VOID**) instead of recording 0/0 garbage when the backend is
  down; every machine-state read runs in a timed job so a hung WMI call can never stall
  the watchdog; resume policy holds only on recent SUCCESS.
- **Cycle refinement: frozen passers + best-cycle basis** (`c339a68`) — already-passed
  Heirs are **frozen** (their card is never modified again, even on escalation); when a
  failing Heir regresses below its best cycle, refinement is based on the **best cycle's**
  failures rather than the regressed ones.
- **Official icons + Admin Console** (`eaa97b1`) — chat avatars replaced with the 13
  official 160×160 in-game character icons; a new **Admin Console** tab shows
  backend/models, the world-state machine, the cause-and-effect chain (weather → errand
  request + original impetus → Heir locations → recent events), and auto-cycle/watchdog
  logs.
- **World machine upgrades** (`f8dc2d4`) — a **failsafe** in the world loop (bad days
  are survived, state is saved, backoff after repeated failures); every errand now
  carries a concrete **original impetus** (`{ask, cause}`, canon-grounded); the engine
  **places each Heir** at their scheduled location so the map reflects where they are;
  map markers fan out with name labels; per-Heir square avatars so replies never look
  bot-sent.
- **Launcher icon** (`d90d8f2`) — the launcher and shortcut now use the *As I've
  Written* book icon (official HSR asset, `assets/as-ive-written.png` + multi-size
  `.ico`).
- **LLM 404 preflight** (`eeb2c35`) — fail-fast check (`LLMClient.list_models`) that
  prints the `tools/start_ollama.ps1` fix instead of spamming 404s when a bare
  `ollama serve` ignores `OLLAMA_MODELS`.
- **Noise filter + replace-not-stack** (`9e6d8e9`) — refinement's noise filter now
  catches written-out statistics ("one in six", "two-thirds", "half", "every three
  turns", "7.1 words") that were over-constraining Heirs; the AUTO REFINEMENT block is
  **replaced** each cycle instead of stacked.

### 2026-08-11 — Senses, music, anti-cheat, opt-out, 78-plateau, Aftermath mode
- **Senses model selection** (`ea4a134`) — `.env` is authoritative with a `SENSES_MODE`
  switch: **unified** (`gemma3n` for both vision and audio) or **quality**
  (`qwen3-vl:8b` vision + `gemma3n` audio); verified `qwen3-omni` is not on Ollama,
  `gemma3n` is the bare tag.
- **Music channel redesign** (`936ce05`) — no prescribed genres: a two-stage pipeline
  where the ear (audio model) analyzes the music neutrally and the Heir judges it
  against **their own values**; legacy seeded music lists deleted.
- **Within-run anti-cheat** (`693b046`) — a Heir can never pass by recycling one phrase
  in every output or by formulaic templates (reject exact/near repeats, over-used
  distinctive trigrams, formulaic openings; lenient mode for the full-corpus final; the
  judge sees the Heir's earlier replies; Hard Rule #9).
- **Opt-out + full final** (`f90e840`) — passing Heirs **opt out** of later cycles; the
  final re-test covers **every canon line** (`--full-final`, single-shot best-of 1 =
  deployment truth), with per-cycle log checkpoints.
- **78-plateau break** (`0c729cf`) — anti-motif-crutch rule ("golden thread"/"Snowy~"
  spam), fresh line each time; best-of raised 7 → 9, temperature 0.4.
- **Aftermath mode = full story memory** (`ab06e64`, `e2cd446`) — the second visitor
  experience now carries the whole Flame-Chase Journey + 4 **real canon memories** per
  Heir (first-person POV from the actual game).
- **Two visitor experiences** (`7a89506`) — `SANCTUARY_MODE` **journey** (new
  Trailblazer) vs **aftermath** (Iron Tomb conquered, bonds pre-seeded); `seed_mode`
  tool + UI mode indicator.
- **Refinement v3 + watchdog** (`11f9241`, `03e01a2`, `f7e33df`) — refinement demands
  unique per-character rules grounded in canon (rejects generic terse advice and
  catchphrase spam); a **watchdog** (`tools/deploy_auto_cycle.ps1`) keeps Ollama up,
  relaunches the auto-cycle if it stops, and restarts the model runner on low RAM.
- **Full technical docs** (`6c845b8`) — `docs/IMPLEMENTATION.md` §3.6: judge
  calibration, cheat-free anti-quote, anti-rhetoric, voice anchoring, model choice,
  auto-cycle, R1 `think:false` fix, OOM/502 recovery.

See `ROADMAP.md` for the detailed checklist.
