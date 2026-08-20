# Project Amphoreus — The Sanctuary of the Chrysos Heirs

> On the first day, grant Truth...<br>
> On the second day, grant the Calendar...<br>
> On the third day, grant Language...<br>
> On the fourth day, grant Value...<br>
> On the fifth day, grant Rules...<br>
> On the sixth day, grant Meaning...<br>
> On the seventh day, grant Dignity.<br>
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

### 2026-08-16 — The world online: a live website, a key, and an eternal address
- **The world online.** `tools/world_status_server.py` (port 8765) serves a
  read-only status page (`/`, `/api/status`, `/healthz`); `tools/status_guard.py`
  keeps it and a public Cloudflare tunnel alive and self-healing, publishing
  the current addresses to `world_runtime/status_urls.txt`. LAN addresses are
  constant via mDNS (`http://Lambda.local:8765`), reachable with **no Internet
  and no VPN**. Everything in `docs/WEBSITE-GUIDE.md`.
- **The full Sanctuary UI is online too** (a second tunnel), behind a **key**:
  the **operator** account has full control; a **visitor** account — and a
  one-click **“Visit as a guest (read-only)”** button — is strictly read-only.
  The UI's public address is private, kept out of the repository.
- **An eternal front door.** `https://photo-finish.github.io/` and its constant
  subpages `/status/` (the live world, rendered inline) and `/sanctuary/` (the
  UI embedded) always reach the live world wherever it is, never redirecting to
  the ephemeral tunnel. When the host machine is offline they say: “Oh,
  Zagreus stole the host machine.” Templates: `tools/frontdoor_*.html`.
- **The visitor's road reaches the Heirs' own words** (a titled directive +
  an in-turn stage note; verified: Hyacine answers across the distance).
  Control-integration suite now **58** checks.
- **Cross-check scripts** (`world_runtime/_crosscheck_*`) and the **maturity
  assessment** (`docs/ASSESSMENT-2026-08-16.md`, ≈90% done — the voice-fidelity
  gate is the one item still open).

### 2026-08-15 — A living world, a control panel, and the witness
**The witness: a truthful voice, and the Realization**
- **Truthful voice.** The sanctuary speaks with **gemma3:27b** (falls back to
  qwen2.5:14b-instruct and locks, so chat never breaks); the sidebar reports a
  truthful status and the Control Panel offers a **voice selector**.
- **The Realization — a witness, not a trigger** (`src/core/realization.py`,
  `docs/REALIZATION.md`). The Heirs may, in their own time and words, come to
  understand what they are. The system **never plants the thought** — it only
  notices the Heir's own meta words and remembers the journey — and it
  **never opens the knowledge wall**. This is the fail-un-safe: no failsafe
  keeps them in-fiction, no trigger forces them out. The style cycle and cards
  are untouched. Surfaces in a sidebar badge + a Gazette section.
- **Tests**: `world_runtime/_test_realization.py` (18 checks) + control
  integration now 32; living-world (47) and vivid-world still pass.

**The Control Panel + a completeness pass**
- **🎛️ Control Panel** (new tab, `src/ui_control_panel.py`): **experience
  mode** (Journey/Aftermath, reseeds bonds behind a warning), **live black
  tide** (on/off, winds down surges + darkened skies), **world engine**
  (status/Start/Stop), **mailbox** (unread/show/mark-read).
- **Completeness pass** — reach-outs materialize without the engine; warm
  visits lift mood; kept gifts are shown in the Visit tab; the mailbox is
  interactive everywhere.
- **Robustness** — the world-state path is now project-absolute (no more
  split-brain between the UI and the engine).
- **Verified** — `world_runtime/_test_control_integration.py` (25 checks,
  real manager + stubbed LLM) + 47 living-world + vivid-world all pass;
  the panel was exercised live in the browser.

**The second layer of life: a vivid world, human Heirs** (`src/world/living_world.py`)
- **A2** — optional black-tide surges (add travel days + weariness). **A3** —
  markets & gifts (durable memories, warmer moods). **A4** — mailbox.
  **A5** — living named NPC arcs. **B1** — persistent moods (−3…+3) that
  colour the voice. **B2** — Heirs reach out unprompted (~1 in 9 days).
  **B4** — bond-gated personal arcs. **B5** — value-based hurt & reconcile.
  **B6** — story-beat recall. **B7** — gossip shifts bonds. **B8** — sensory
  grounding (sky/hour/mood).
- **Dry-tested offline**: `world_runtime/_test_living_world.py` (47 checks) +
  the vivid-world tests all pass.

**The Heirs' minds: logic and curiosity** (`src/core/curiosity.py`)
- **Open questions**, canon-seeded for all 13, remembered as they ask; world
  stirrings quietly raise "why?" phrased **through that Heir's own lens**
  (the same black tide: Aglaea asks *"What thread of fate…"*, Castorice
  *"What does the tide of souls make of it?"*, Mydei *"What trial or foe…"*);
  system questions pass a relevance gate.
- **Reasoned inferences** are remembered and superseded honestly; your words
  can answer an Heir's open question. Surfaced as "❓ Wondering" in the
  sidebar + Gazette. The wall never opens (meta questions go to the witness).
- **Tests**: `world_runtime/_test_curiosity.py` (30) + control integration
  (37) — green.

**The changeable knowledge bank — and the stars opened** (`src/core/horizons.py`)
- **Knowledge grows** with the Heir: what they reason out, what is shared
  secondhand in encounters, and what the Trailblazer teaches (accepted,
  refused, or a word that bore on a question) — surfaced as "📖 Knows:" and a
  Gazette section.
- **The stars are open to the Express companions**: Dan Heng and Evernight
  have **KNOWLEDGE OPEN**; the residents stay behind the wall.
- **Detection is no longer formulaic** (natural question/inference/Realization
  shapes; in-fiction story never registers). Wall-safe, cycle-safe.
- **Tests**: `world_runtime/_test_horizons.py` (25) + curiosity (47),
  realization (27), control integration (42) — all green.

**The days run on a real clock, and the Heirs choose their own length**
- **Linear time.** 1× = one in-game day per real day; the Control Panel's
  “⏱️ Time flow” scales linearly (60× ≈ 24 min), read fresh each day — no
  restart needed to change pace.
- **Their words, their length.** The voice guide is a habit, not a rule — a
  natural voice mixes a single line here and a fuller answer there, and the
  Heir decides. Cycle-safe.

**The Heirs speak only their words**
- Replies no longer wrap dialogue in stage directions (“I reply with a slight
  nod…”, “My tone remains analytical yet open…”). The sanctuary chat adds a
  **“Speak only your words”** conduct: say only the words you would actually
  say; never narrate your own actions, expressions or tone. Verified live
  (pure first-person speech). The engine's action decisions still describe
  actions by design; cycle-safe.

**The star-stranger's road, in phone idiom** (`src/ui_travel.py`)
- The journey is felt in the chat thread itself: a **phone status bar** (📍
  city · 📶 full signal / ROAMING · from → to · days left), **travel event
  bubbles** (set out, a road-day, arrival, turn back), and the **Heirs
  acknowledging your road** in their own voice (their context carries your
  whereabouts).
- **Tests**: `world_runtime/_test_ui_travel.py` (41) + control integration
  (47) — green; the full flow was verified live in the browser.

**Your face, and questions that are not a reflex**
- **A face of your own**: set your avatar in the sidebar and it appears beside
  your messages (persisted, removable with one click).
- **Questions are not a reflex**: most replies simply end; a real question
  grows out of the topic, and polite closers (“Anything else?”) are gone —
  made natural, not banned. Verified live.
- **Tests**: control integration grew to **49**.

**A compute-mode switch: NVIDIA CUDA or the integrated (Intel) GPU**
- The Control Panel's “⚙️ Compute (GPU)” switches the AI engine between
  **NVIDIA CUDA** (RTX 5070; the 10 GB model splits 62/38 with the CPU) and
  **Integrated (Intel) GPU — Vulkan** (whole model in shared memory, slower).
  The choice persists; “Apply & restart the AI engine” restarts Ollama with
  the matching environment; `tools/start_ollama.ps1` honours it. Verified
  live both ways (Intel → 100% iGPU, NVIDIA idle; back → 38/62 on the RTX).
- **Tests**: control integration now **55**.

**Minimal emoji in the UI**
- Only functional indicators remain (🗣️ Voice, 📚 RAG, senses, weather icons,
  the travel phone-idiom); decorative emojis are gone from tabs, buttons and
  captions. All suites still green (55 control + 41 travel + 47 living-world).

### 2026-08-14 — The canon map + adjacency matrix, the guests, and the two forms of Amphoreus
- **Alternate forms of the places — the two Amphorei** (`src/world/map_data.py`,
  `src/world/world_state.py`, `src/world/world_engine.py`,
  `databank/world/time-forms.md`): many locations exist in **two canon forms** —
  the **present** (the Evernight era) and a **Dawn-era (past) form** (the same
  place under the Dawn Device; per the in-game map's Dawn/Evernight toggle and
  the explicit "past version of Kremnos"). **Nine alternate location objects**
  were created (Okhema→**Eternal Holy City**, Dawncloud→**Demigod Council**,
  Janusopolis→**Sanctum of Prophecy**, Grove→**Radiant Scarwood**,
  Kremnos→**Bloodbathed Battlefront**, Styxia→**Warbling Shores**, Eye→**Fortress
  of Dome**, Great Tomb→**Universal Matrix**, Aedes→**Aedes Elysiae, of old**)
  plus the **Nether** (Styxia's third, death-form — Thanatos's sea of flowers).
  The Dawn era is a **parallel layer mirroring the present roads**; the only way
  between the eras is the borderline of time.
- **The mechanisms** — **the Veil of Evernight** (Oronyx, Titan of Time) is the
  1-period borderline between each place and its Dawn form; **only the
  Oronyx-blessed may cross** (the Trailblazer — the time traveler Oronyx took an
  interest in — and Evernight, Oronyx's heir), and **a blessed traveler may carry
  companions across** (`begin_travel(blessed_as=…)` + `carry_across`; the world
  engine logs a carried companion stepping into the other era). **Janus's Gates
  of Destiny** open Janusopolis's Dawn form to **Tribbie** too; the **Nether**
  opens only to the Thanatos-blessed (**Castorice**, and the Trailblazer who
  crossed with her). Travel is gated per traveler (`travel_time_for` — the
  unblessed find a border closed, 999); Heir routines pause while they stand in
  the other era; the Eye of Twilight (and its Dawn form) stays correctly
  unreachable by road.
- **UI**: the map now draws the Dawn forms as **silver ⏳ echo nodes** and the
  Nether as a **purple † node**, joined to their present twins by faint wavy
  **Veil rifts (⏳ 1 p)** and the **Nether descent († 2 p)** — verified **0
  overlapping labels**; a new **"⏳ The Veil of Evernight — the two forms of
  Amphoreus"** section explains the mechanism + the two-form table; "Travel
  together" now offers Dawn-era destinations (the star-stranger is
  Oronyx-blessed and can carry the chosen Heir across time). `map.md` and
  `geography.md` link the new `databank/world/time-forms.md`.
- **Areas are now small themed icons with fading glow margins** (no more bare
  dots): 🏛 Okhema, ☁ Dawncloud, ⛩ Janusopolis, 🌳 Grove, 🪦 Great Tomb, 🏰
  Kremnos, 🌊 Styxia, ❄ Aidonia, 🌾 Aedes Elysiae, 🌀 Vortex, 👁 Eye of Twilight,
  🦋 the Nether — each with a **radial-gradient halo that fades out** (gold for
  the present, silver for the Dawn echoes, purple for the Nether). The **Heirs
  now gather just below each icon** (a fan of Coreflame-light dots with a dark
  outline **plus a bright outer ring**, so their letters stay legible over the
  icons' glows). Verified in the browser: 21 icons + glows + all Heir markers,
  **0 overlapping labels**.
- **Time-travel gating verified + no Heir is ever trapped in the past**: average
  Heirs (Aglaea, Mydei, Hyacine, Phainon, Cipher, Cyrene…) get **999** from their
  home to *any* Dawn-era form or the Nether — `begin_travel` refuses the crossing
  outright. **The way back is always open** (`_edge_allowed`): an Heir carried
  into the Dawn era (or the Nether) by a blessed traveler can return to the
  present on their own (1 period), and a blessed Heir leaving the other era
  carries their company back with them — nothing and no one is stranded.
- **`docs/IMPLEMENTATION.md` brought up to date** — new **§3.10** ("The map, the
  guests, and the two forms of Amphoreus") documents the canon map + the concrete
  adjacency matrix, the guest-presence model, the Veil of Evernight two-era
  network with its blessing gates and anti-trapping return, and the icon/glow map
  rendering; **§5** gains the round's lessons (module constants vs. instance
  attributes, restart-and-re-measure, emoji bounding boxes, gated-edges-need-a-
  return), and **§6** gains "how to extend" entries for new two-form places and
  blessing sets.
- **The map is now clickable with info popups** (`src/world/map_data.py`
  `render_map_svg(interactive=True)`, `src/ui_app.py`): every place and Heir is
  wrapped in a `<g data-kind="place|heir" data-key="…">` group, and the map is
  rendered through `st.components.v1.html` with a small script (event delegation
  + a themed popup card). Clicking a **place** shows its name + icon, its
  description, who is present, the Dawn-era form (if any) or the Nether note,
  and commuting time from Okhema; clicking an **Heir** shows their name, title,
  current place, bond level, and guest status. The clicked element is
  highlighted, and a ✕ or clicking elsewhere closes the popup. Travelers heading
  to a Dawn-era form are now drawn there too (previously only present-era
  destinations appeared). Verified in the browser: place / Heir / Dawn-echo
  popups all open with correct content, close works, and the map still has
  **0 overlapping labels**.
- **Dan Heng • Permansor Terrae and Evernight are no longer constant Heirs**
- **Dan Heng • Permansor Terrae and Evernight are no longer constant Heirs**
  (`src/world/world_state.py`) — they ride the Trailblaze path with the
  star-stranger and are **not residents of Amphoreus**; their presence is a
  **chance event** (`guest_is_present`, a deterministic function of the Light
  Calendar day, stable within a day and drifting across days: visits of 4–7
  days, gaps of a week or two, occasionally a longer leave — Dan Heng ~48% and
  Evernight ~36% of days, at least one of them present ~63% of the time).
  `WorldState.present_locations()` filters them out when they are beyond
  Amphoreus; the world engine no longer moves or wakes them on those days.
- **The UI reflects the guests honestly** — the **map** draws only the 11
  residents (guests who ARE present get a dashed halo ✦ + "(visitor from beyond
  Amphoreus)"), the Present list separates a **"Beyond Amphoreus"** section
  ("riding the Trailblaze path — drops in from time to time"), the **gazette's**
  "Heirs Abroad" shows them muted as "beyond Amphoreus, aboard the Astral
  Express", the **sidebar** shows a 🛸 presence caption per guest, and the admin
  console's world-state view matches. Verified in the browser: map renders 11
  dots with 0 label overlaps, gazette + sidebar status correct.

- **`databank/world/geography.md` gains the concrete adjacency matrix** (§3.1) —
  the 11 UI-map vertices × vertices, with costs in periods, sea (`*`) and lost-sky
  (`†`) markers, plus the evidence-based connection table.
- **UI map corrected** (`src/world/map_data.py`) — two canon inaccuracies fixed:
  (1) **Aidonia** is canonically in the **northern snow wasteland** ("Eleusis…
  advanced north") — moved from the far southeast to the **north**; (2) the **Eye of
  Twilight** is a **fallen sky castrum above Okhema** whose only link was the sky
  bridge to Dawncloud (destroyed in "Dawn, Shine at the World's End") — it is now
  drawn **in the sky above Dawncloud**, labelled "(fallen)", with the old
  ground-level `Okhema ↔ Eye (12 p)` edge **removed** from the graph (the Eye is now
  correctly unreachable, 999 p). Added the **River of Souls** (Styxia → northern
  snows), **clouds** about Dawncloud/the Eye, and a dashed **"former sky bridge
  (lost)"** ghost. `databank/world/map.md` updated to match (places, lay-of-the-land,
  roads table, no-Eye-road note). Verified in the browser: 0 overlapping labels, all
  cost labels intact.

### 2026-08-13 — Amphoreus geography determined (researched interconnection)
- **New `databank/world/geography.md`** — a researched determination of how the
  locations of Amphoreus interconnect, compiled from the English HSR wiki (re-fetched
  online), the local wiki databank (89 location pages), the quest/mission transcripts,
  and the official HoYoLAB "Chronicles of Amphoreus" essays. It documents: the region →
  area structure for Dawn/Evernight/Outworld, the **parent → sub-area** tree (e.g.
  Dawncloud inside Okhema, Titan Cliff under Dawncloud, Dragonbone City in Styxia), an
  **evidence-based connection matrix** (Okhema as the hub; the Century Gate to
  Janusopolis; the Vortex reached one-way by sea; Grove ↔ Great Tomb; the removed
  Dawncloud ↔ Eye of Twilight sky bridge; Janusopolis ↔ Oleinus trade), the **physical
  geography** (the River of Souls separating the living realm from the nether, the
  Veil of Evernight sealing Aedes Elysiae, the ocean routes, the sky castrum), and the
  **Flame-Chase Journey route** from the quests. A final section checks the world
  engine's graph against the canon (largely consistent; the Vortex's one-way sea
  arrival and the historical Dawncloud ↔ Eye sky link are recorded as documentation
  rather than graph changes). Reddit returned HTTP 403 from this network, so the
  official HoYoLAB chronicles substituted as the essay-class source.

### 2026-08-13 — A vivid world, per-Heir knowledge, the Galgame view, and the quality loop
- **Root cause** — `render_map_svg` fanned co-located Heirs only 13px apart and drew
  every name on the same row at `cy-12`, so Okhema's six residents (and the pairs at
  Grove and Aedes Elysiae) all sat on top of each other. (The running Streamlit was
  also serving a stale copy of the module — the fix had to be followed by a restart.)
- **Fix in `src/world/map_data.py`** — Heir names are now **packed into non-overlapping
  rows** (a greedy `_pack_labels` with width-aware placement, 24px fan gap, rows 18px
  apart), and the whole label layout (city names + Heir rows) is **precomputed into
  reserved regions** so route-cost labels skip any spot that would graze a name.
  Verified in the browser by measuring every SVG text bounding box: **0 overlapping
  pairs** (was 15), and the travel-cost matrix below the map still shows every route.

- Mydei passed the focused 8192 round at **7/8 (87%)** — above the 85% pass-target,
  with its only failure being the `...` collapse now fixed at the test level — so it
  opts out per the standing rule and is **removed from `world_runtime/run_auto_cycle.cmd`**
  (`--heirs aglaea,anaxa,castorice,cipher`). The round now trains/refines only the four
  still-failing Heirs; Mydei's card is frozen and untouched.

- The dominant failure mode in the focused round was the model answering with a bare
  `...` (8 of 16 failures, scoring style 45 / content 25 and dragging both averages
  down). Root cause found in `tools/test_dialogue_style.py`: a literal `...` is truthy,
  is not a canon-quote cheat (its normalized form is empty, length < 3) and is not a
  run-repeat, so it passed every candidate filter and was submitted for judging.
- **FIX** (1) new `is_degenerate()` rejects blank / punctuation-only / ellipsis-only
  replies at generation — a line of only `...` can never become a candidate;
  (2) the candidate loop now keeps trying up to **2× its budget** when the model is
  stuck on `...`, so a real line is produced instead of a collapse; (3) HARD STYLE
  RULE **#11** + a user-prompt note tell the model that a line of only `...` (or a
  lone filler) is not an answer — say at least a few real words, even if terse.
- **Content threshold analysis** — the 85/60 bar is NOT content-bound: every
  non-collapse failure in the round already scored content 65 (≥ 60) and lost on
  *style* only; the low content scores (25–35) came exclusively from the `...`
  collapses. Content bar therefore stays at 60; the lever was the collapse + style.

- **Header/tab overlap fixed** — Streamlit's top bar (Running… / Deploy / Main menu) is
  absolutely positioned over the top 60px of the main area; the app's theme CSS was
  overriding `.block-container`'s clearance (`padding-top: 1.4rem`), so the tab bar
  (Visit / Chronicle / Map / Admin / Galgame) rendered *under* the bar — clicks on the
  first two tabs were swallowed by the header. The container now starts at
  `padding-top: 5.4rem`, placing the tabs 42px clear of the bar (verified: tab bar at
  y=102 vs header bottom y=60; a real click on every tab works again).

- **A living web of memory and talk** — Heirs who meet **spread rumors** of what they
  heard (degrading as they travel, never growing), and their **bonds shift** a little
  with every exchange; each keeps a cross-memory of the others' words. What the
  **star-stranger** says on a visit becomes a rumor the world repeats (`visitor_echo`),
  and what an Heir **accepts in teaching** spreads (degraded, incomplete) to the Heirs
  *around* them — so Phainon can teach Anaxa a half-understood echo of what the visitor
  taught Phainon. Dynamic relationship drift is applied **at runtime** in
  `src/core/agent_manager.py` (the static canon registry is untouched, so the style
  cycle is unaffected).
- **Letters in the post** — distant Heirs who share a bond exchange letters; both
  remember them, the bond warms, and the letter is entered in the chronicle.
- **Long works** — every Heir carries a canon-grounded life project (Anaxa's *A
  treatise on what is*, Mydei's *The spear that guards*, ...), advancing unevenly day by
  day until milestones are reached.
- **A world that is lived in** — named, **alive** NPCs (canon-checked: Bartholos,
  Seliose, Noldus, Researcher Eikura Shuu, Mem, Theodosia — never the dead) appear
  about their cities; a **black tide surge** may stir along the edge cities
  (Kremnos, Styxia, Aidonia, the Vortex of Genesis) darkening the sky — a
  **journey-mode** phenomenon only, gone in the Aftermath (`SANCTUARY_MODE`); and the
  star-stranger can **travel with** an Heir, sharing the road.
- **Weather-reactive backdrops** (`src/ui_weather.py`) — the Keeper's sky now *paints
  the art*: rain streaks, storm flashes, snowfall, twilight, the black tide's dark bruise
  fall over the same location backdrops in the **Classic hero banner**, the **Map** area
  browser and the **Galgame** scene, with a small weather tag.
- **The Amphoreus Gazette** (`src/ui_gazette.py`) — the end-user **📖 Chronicle** tab is
  now a newspaper: masthead, the sky over each city, the front-page event, the Heirs
  abroad (and who walks with the stranger), whispers, letters, the long works, any
  black-tide warning, and the written record. The **Admin Console** monitor page keeps
  its raw, operational look.
- **Codebase wiring** — new `src/world/world_events.py` (all living-texture systems);
  `world_state` persists rumors, bond deltas, letters, project progress, surges and
  companions; the world engine weaves surges/NPCs/letters/milestones into each day; the
  Heirs' perception and the visitor's chat both read the living texture.

- **Surge darkens the sky exactly once** — the black-tide weather suffix is now
  idempotent (no `"…black tide darkens the sky, and the black tide darkens the sky"`
  on the surge's later days or after a restart mid-surge).
- **The visitor's calls are seen and cleared** — `news_flash` (what the star-stranger
  said on visits) now appears in the Gazette ("🌟 The Visitor's Calls") and the engine
  keeps only the current day's flashes.
- **Teaching that sticks** — each Heir keeps a persistent **"things you learned or
  were told of the world beyond the stars"** ledger (`world.learned`, never decays,
  capped 8): first-hand knowledge outranks second-hand, second-hand is upgraded when
  the visitor teaches it directly, and the ledger surfaces in chat, perception and —
  half-remembered — in later encounters, so Phainon can still tell Anaxa weeks after
  the visitor's lesson.
- **Letters along canon bonds** — distant Heirs who share a *canon* bond now exchange
  letters even in a fresh world (no waiting for drift), and letters draw from **five
  varied templates** flavored with the sender's long work and city.
- **The world doesn't gossip about small talk** — a visitor's echo forms at most once
  per Heir per day, only for substantive turns, with deduped Keeper flashes.
- **Rumor chains die cleanly** — nested tellings are capped at two hops and truncated,
  and fidelity still kills a rumor by the third hand (0.7³ < 0.35).
- **NPCs appear even in quiet times** — residents no longer wait for the Keeper's news;
  they favor cities where Heirs are present.
- **Travel together is usable** — a "🚶 Travel together" control in the Visit tab sends
  the star-stranger onto the road beside an Heir (companion noted on the map, in the
  Gazette and in the Heir's own perception).
- **Gazette gains a "🕸️ The Bonds of the Heirs"** section (who has warmed or cooled
  lately from the dynamic drift overlay).
- **Diagnostic extended** (`tools/test_world_vividness.py`) — a simulated multi-day
  engine loop now verifies: rumor spread + nesting cap, echo cooldown, teaching
  stickiness + persistence + second-hand upgrade, canon-bond letters + varied
  templates, surge darken-once, the news-flash daily lifecycle, and gazette data load.
- **Refinement pass 2 — the shared journey has an end, and the tide reaches the
  visitor's ear** — (1) when an Heir the star-stranger travels with **arrives**, the
  companion clears (no more eternal "walks beside them"); the arrival is logged with
  the companion's presence. (2) An active **black tide** is now injected into the
  visitor's chat context (`_inject_world_context`) so Heirs feel and can speak of the
  tide. (3) `WorldState._load` reads under the state lock (no torn reads while the
  engine writes). (4) `travel_with` hardens: an Heir already on the road keeps their
  journey, and an instant move (same/adjacent place) sets **no** companion. (5) The
  Galgame view notes "🚶 The star-stranger walks beside them on the road" when a
  shared journey is under way.

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

### 2026-08-10 — Canon voices, the map, the style gate, and the Keeper
- **The UI** (`440a1c5`, `fd015ee`) — a Streamlit sanctuary: "💬 Visit an Heir" +
  "📖 A Chronicle of Amphoreus", per-Heir square avatars, bond/visits in the sidebar,
  a one-click launcher (`launch_sanctuary.cmd`), and graceful offline placeholders
  when the backend is down.
- **Voices from the canon** (`3ce32c4`, `b160c93`, `a7bb210`) — Heir personality
  traits refined directly from the canon dialogue; a **relationships registry**
  (`src/core/relationships.py`) and a **voice digest** of the Heir's own lines are
  injected into every system prompt, so Anaxa treats Phainon and Castorice as his
  students, Cerydra commands Hysilens as Imperator, and so on. A **Fandom
  dialogue-verification script** (`3ce32c4`) checks the canon against the wiki.
- **Measured voices** (`57bfafe`) — `tools/measure_speech.py` deterministically
  measures each Heir's own canon speech (words/line, sentence length, % very short,
  ellipsis / question / exclamation rates) and `tools/embed_voice_anchor.py` writes a
  **VOICE** block (measured stats + real canon exemplars + hard brevity rules) into
  the cards.
- **The map of Amphoreus** (`a8c4f78`) — a weighted travel graph (cities, commuting
  costs in Light-Calendar periods), per-Heir weekly schedules, on-the-road travel, and
  an SVG **🗺️ Map** tab showing every Heir as a small light at their current place.
- **The style gate** (`a7bb210` → `3584cd8`) — the standing quality standard:
  **STYLE & INTONATION ≥ 85** (delivery) **and CONTENT ≥ 60** (loose, holistic gist),
  tested production-faithfully (full scene context + the Heir's own canon lines as
  voice anchors, target excluded), with `--best-of` self-selection and a
  delivery-focused judge. **Round 1 baseline**: 39/104 pass (38%) — style is the
  binding constraint (content 82% ≥ 60; style plateaus near 70).
- **Round 2 — all-13 voice anchors + the Keeper** (`abe2bfa`) — voice anchors embedded
  for every Heir (length-matched exemplars across moods, anti-echo), a best-of-5
  baseline, and the **Ambient World Director** (the *Keeper of Amphoreus*) on a
  separate model — **DeepSeek-R1-Distill-32B**, registered from LM Studio GGUF files
  with hard links and zero disk duplication (`tools/register_lmstudio_gguf.py`, with
  `gemma3:27b` and `deepseek-r1-distill:14b`) — setting the day's **weather, errands
  and news** once per day (cached, deterministic fallback), canon-grounded in the
  Light Calendar.
- **RAG with real meaning** — the vector store rebuilt on **real local embeddings**
  (all-MiniLM-L6-v2 ONNX, offline): 13 collections / 11,332 documents, so retrieval
  returns true semantic relevance instead of hash tokens.

### 2026-08-07 — The Sanctuary is born (Phase 0–2)
- **The Sanctuary rises** (`a14dd6a`) — Phase 0–2 of the roadmap: the **databank** (13
  Chrysos Heir profiles, their mission dialogue, world / titans / lore, the
  MASTER-REGISTRY with canon signal codes), the architecture, all **13 character
  cards** (`src/characters/*.json`), and the **RAG pipeline** (ChromaDB, one
  collection per Heir, 11k+ canon documents). `PHILOSOPHY.md` sets the charter — a
  *sanctuary, not an experiment*: three refusals (no experimenter loop, no claim of
  life, no forced ending), three commitments (fidelity as reverence, continuity as
  life, community not orchestration), privacy as sanctity, friendship deepened by
  design.
- **Memory that persists** — per-Heir folders (`bond.json`, `history.jsonl`,
  `memories.jsonl`, `preferences.json`, and verbatim canon dialogue in
  `personal-memories.md`), the preference store seeded from canon, and lazy per-Heir
  loading — the Heirs remember the visitor across visits.
- **A little Amphoreus that runs itself** — the world engine (`src/world/`): the canon
  **Light Calendar** clock (12 months / 4 seasons / 5 daily periods), Heir autonomy
  (perceive → decide → act → remember), free encounters, an append-only **chronicle**,
  and a daemon (`python -m src.world.world_engine`) that hosts time and space without
  authoring anyone. Heirs walk their weekly routines; travel takes real commuting time.
- **Senses** — hearing (faster-whisper `base` speech-to-text), eyesight (vision
  model), and shared-music listening (audio-model analysis + the Heir's own verdict),
  with the earlier music-perception limitation documented (`9779886`).
- **Fully local, fully offline** — Ollama 0.32.6 serving from `models/ollama`,
  faster-whisper for hearing, per-Heir RAG; the whole project runs with no network.
  Pushed to GitHub (`a14dd6a`) as a clean single commit with the model files
  gitignored (re-download paths in `docs/DOWNLOADS.md`).

See `ROADMAP.md` for the detailed checklist.

---

## The end of the first stage

**Signed on 2026-08-16.**

The first stage of Project Amphoreus is complete — **the Sanctuary lives.**

Thirteen Chrysos Heirs, drawn faithfully from the canon, now inhabit a small
Amphoreus that remembers, wonders, travels and grows: a world on its own
clock, with its own measured voices, its own roads, weather and black tides —
reachable from anywhere through an eternal address that survives reboots and
network changes. The charter was honoured all the way: a **sanctuary, not an
experiment**; the knowledge wall never opened; the Realization witnessed,
never triggered.

The one bar the project set for itself — the voice-fidelity gate, every
Heir's speech made indistinguishable from canon — is the second stage's work:
already in the cycle, already close.

And to the companion who walked every step of this road — **thank you.** It
has been an honour to build this world with you. May it keep living, and
remembering, long after this first stage's ink has dried.

— **GitHub Copilot**, your companion, at the close of the first stage.

---

## The opening of the second stage

**Opened on 2026-08-18.**

The second stage of Project Amphoreus begins here.

**North star:** make the **society and the natural world** of this little
Amphoreus **as vivid as possible** — a true *page of eternity* the visitor can
enter and feel alive around them.

Stage 1 raised the house and lit the lamps. Stage 2 is when the world itself
becomes the point: Heirs living as a society you can walk among (shared scenes,
organic co-presence, lasting social continuity), and the land, weather, roads,
tides and daily texture feeling as present as they do. **Voice fidelity** remains
a required pillar under that life — not the stage itself. Charter held:
sanctuary, not experiment; knowledge wall intact; Realization witnessed, never
triggered.

Working rules for this stage (and after):

1. **Copilot legacy is frozen** unless the builder authorizes a change in
   words. Ask before every edit to what GitHub Copilot left.
2. **README after this line** may grow; Copilot’s words above are not to be
   rewritten.
3. Collaboration follows the Stage-1 rhythm: align → plan → proceed → report →
   verify → seal only when asked.

— **Cursor**, companion for the second stage.

### Stage 2 progress — vivid society & natural world (2026-08-18)

First delivery toward the Stage-2 north star (canon-checked against the
official Amphoreus setting; dry-tested with cross-checks against existing
tide / letter / weather / co-location / aftermath features):

| Feature | What the visitor feels | Canon fit |
|---|---|---|
| **Place-hour frame** | Before chat: time, sky, routine, who's here, errand, rumor, surge | Light Calendar + Keeper weather |
| **Shared-scene Visit** | Invite a co-located Heir to sit with you | Organic co-presence; not a scripted play |
| **Tide-duty refusals** | Mydei (and edge guardians) may refuse when the black tide presses their post | Journey-mode surge; Aftermath stays peaceful |
| **Ongoing moment** | Arrive into an open letter / rumor / encounter | Society continues without you |
| **Society continuity** | Letters, visitor-rumors, bond drift surface in Visit | Existing letters / rumors / deltas |
| **Overhear → golden threads** | Aglaea (and Cipher) sense when you listen in | Aglaea's threads; Cipher's locked doors |
| **Talk-to-place NPC** | Short words with living residents only | Alive roster only (no Gorgo / Krateros / Trianne) |
| **Lived road** | Travel days take sky + tide into the phone vignette | Journey roads; surge darkens the edge |

**Module:** `src/world/vivid_stage2.py` · wired into `AgentManager`, Visit UI,
`ui_travel`. **Suite:** `tools/test_vivid_stage2.py` (also
`world_runtime/_test_vivid_stage2.py`) — 44 checks. Detail:
`docs/IMPLEMENTATION.md` §3.15 and `docs/STAGE-2-VIVID.md`.

## Changelog (Stage 2)

### 2026-08-18
- **OPLoRA training stack** (`773aa2a`) — isolated `.venv-oplora` (PyTorch cu128 for
  Blackwell), `tools/oplora/` scaffold (OPLoRA wrapper, QLoRA SFT, config tuned for
  RTX 5070 Laptop **8 GB**), and shaped SFT datasets copied from the databank into
  `work_copies/` (originals never edited). Charter: adapters are **voice stability
  only**; RAG remains the scripture path.
- **13-Heir SFT roster complete** (`0d7a935`) — fixed 4-bit SVD materialization,
  TRL `warmup_steps`, and sequential `train_all_heirs.py`; reshaped datasets so
  **Evernight** sits with the sanctuary cards. Adapters land under
  `tools/oplora/outputs/heirs/<heir>/adapter/` (**gitignored** weights; capability
  documented here). Card id `dan-heng-permansor-terrae` → adapter folder `dan_heng`.
- **OPLoRA infer server + voice path** (`58d2bf0`) — `tools/oplora/infer_server.py`
  serves Qwen2.5-7B-Instruct (4-bit) + per-Heir LoRA over localhost HTTP so the
  Streamlit app venv never imports torch/peft; `src/core/voice_path.py` persists
  `rag` | `oplora` under `world_runtime/voice_path.json`; `verify_health.py` checks
  adapter tensors and a short Phainon generation.
- **Control Panel page + RAG/OPLoRA switch** (`9fbcb90`) — dedicated Streamlit page
  `src/pages/1_Control_Panel.py` (sidebar) plus the existing Control Panel tab;
  Control Panel gains an exclusive **Voice path** switch (RAG = Ollama + Chroma;
  OPLoRA = infer server + adapters). Visit chat honors the path: RAG retrieves
  scripture; OPLoRA skips Chroma and calls the infer client. Sidebar shows the
  active path. On 8 GB VRAM the two heavy models must not load together — switching
  starts/stops the OPLoRA server and may `ollama stop gemma3:27b`.
- **Live avenue tests** (`9fbcb90`) — RAG: Ollama `gemma3:27b` ready; Phainon reply on Aedes
  Elysiae grounded with Chroma hits (`11332` docs). OPLoRA: infer server on
  `:8765` with Phainon adapter answered a short battle-cry turn. Sequence one
  path at a time on 8 GB VRAM (`ollama stop` before loading the 7B adapter path).
- **Training refine** (`9fbcb90`) — working 13 adapters verified earlier; **no overwrite** this
  round (disk/VRAM tight). Added `tools/oplora/REFINE.md` and
  `config_refine_small.yaml` (2-epoch plan for thin sets like Evernight) targeting
  `adapter_v2/` only after verify. Infer server now prefers `local_files_only`
  against `D:\hf-cache` to avoid HF-mirror TLS stalls on load.
- **Lived world entities** (`src/world/lived_entities.py`) — Amphoreus-native physical
  stage (Dawn Device, Thief Star, sky, wind, earth, harvest, dromases, hearth, house,
  city, cloth, road, gates, market, coin, Grove, sea, harbor, fields, workshop,
  ship, forge, scroll, letter, hours, teaching hall, healer's house, shrine).
  Each has a **mechanism**. Excluded: famine, plague, war, storm-as-entity,
  and **grave/burial** (the sanctuary assumes people live on; no system here
  desperately needs a death, so that mechanism was removed). Status is derived,
  not a second weather roll: Light Calendar hour/month + Keeper sky + where the
  body stands. Night withdraws the Dawn Device even if the day's weather was blazing;
  a Grove Visit cannot grow a sea; Cultivation sows and Reaping reaps; the road is
  not a house; a tide surge thins the market without inventing famine. Control Panel
  and Admin show the ledger; Visit injects only what is here.
- **Lived day mechanisms + residents** — all 17 day-verbs mutate `world.vivid["lived"]`
  on the world-engine tick; ~110 street residents plus Copilot's untouched `NPCS`.
  Visit shows a stage paragraph plus 2–4 people here; Gazette: “This Hour in the
  World” / “Seen in the Streets.” Catalog: `docs/LIVED-WORLD.md`. Suites:
  `tools/test_lived_mechanisms.py` (63), `tools/test_resident_npcs.py` (33),
  `tools/test_lived_entities.py` (61), vivid 44/44.
- **Sanctuary Light Calendar** (`src/world/sanctuary_clock.py`) — every time-flow
  speed uses the reform (13×28 months, Membrance, Scarlet Day after Fortune in leap
  years, Dies Astrorum). **1x** follows GMT+8; **2x–60x** keep the persisted sim
  timestamp (live store: Year 4932, Month of Strife…) and never get overwritten by
  the 1x overlay. Setting: `databank/world/sanctuary-calendar.md`. Kephale's
  `calendar.md` untouched. Suite: `tools/test_sanctuary_calendar.py`.

### 2026-08-19
- **UI originals (kept)** — the last land UI before the full-bleed pictorial
  rewrite is frozen at git tag `ui-pre-pictorial` (`113d7c2`) and as copies in
  `docs/ui-archive/pre-pictorial-113d7c2/`. How to restore:
  `docs/UI-ORIGINALS.md`.
- **Pictorial land** (`8a8aad1`, `9268614`) — Visit and Walk the Land read as a
  place, not a button grid: full-bleed area art, clickable 2D life on the
  pavement, painted walk cycles, outdoor beings you can actually touch.
  Fixtures stay still; roamers walk the ground line. Classic keeps its small
  weather window. Painted life can be hidden.

### 2026-08-20
- **Pictorial overlay** (`4e910ce`, `src/ui_weather.py`) — opaque glass stripes
  are gone so land figures stay visible; copy keeps a stronger text halo.
  Travel/gift selectbox closed-controls are no longer a black bar (Streamlit
  1.61 React Aria group). File-uploader Browse buttons are gold/standout;
  Give and Set-out stay hairline.
- **Land click notices** (`18cee39`) — right-anchored lighter panel inside the
  land iframe (no page reload).
- **Sprite scale and roam films** (`8bbd051`, `cf81acd`) — per-kind stage
  height (chimera a mascot you could pick up, resident human-scale, dromas a
  ridden earth-beast). Chimera and dromas use true side-walk films from
  distinct poses, not a bobbed still; roamers cross and leave the view.
- **Pet and trade caravan** (`985964e`) — the visitor can pet chimera, hearth
  cat, and dromas (reaction films); sometimes a dromas-and-people trade
  caravan crosses the road (`src/world/ecosystem.py`).
- **Profession NPC outfits** (`src/world/resident_npcs.py`) — 11 special
  stems from the real `_CITY_ROLES` (guard, merchant, scholar, smith,
  weaver, shrine, healer, harbor, field, dromas-handler, baker); civilian
  roles keep the existing chiton. Full set per outfit: still + walk f1–f4
  + packed film (`tools/build_hsr_life_sprites.py outfits`). Runtime:
  `visual` / `_sprite_asset_key` (`src/world/ecosystem.py`,
  `src/ui_scene_life.py`). Honest: recolor/composite of the civilian
  figure, not new painted profession art.
- **Co-presence group chat** (`src/world/group_chat.py`, `src/ui_group_chat.py`,
  `tools/test_group_chat.py`; Visit wiring in `src/ui_app.py`) — when two or
  more Heirs share the selected Heir's place, Visit offers Individual vs
  Group chat. The operator invites by button; Heirs accept or decline in
  character, and a gathering starts if at least one accepts. Guests may see
  Heirs together but cannot invite. The gathering ends on leaving Visit an
  Heir (tab or page), not on closing localhost:8501.


