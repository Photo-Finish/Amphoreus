# What other Chrysos Heirs projects do — and what is worth taking

**Date:** 2026-10-28
**Method:** web search, not local assumption. Every claim below is tied to a source
I read the title/description of; where I did **not** open the code I say so.

---

## What exists

| Project | What it is | Source |
|---|---|---|
| **firefly-skill** | a *character skill package*: game dialogue and plot distilled into a portable skill file for immersive chat | [HeartEase1/firefly-skill](https://github.com/HeartEase1/firefly-skill) |
| **Firefly-Companion-AI** | desktop companion: Live2D presence, streaming chat, **local ONNX semantic memory**, a **second "proactive care" engine**, **GPT-SoVITS TTS in the character's own voice**, agent tasks, MCP tool chain, skill plugins | [hhjk21/Firefly-Companion-AI-](https://github.com/hhjk21/Firefly-Companion-AI-) |
| **Cyrene-Agent** | an agent built specifically around **Cyrene** — the same thirteenth entity this Sanctuary treats separately | [Playa-Cyrene/Cyrene-Agent](https://github.com/Playa-Cyrene/Cyrene-Agent) |
| **SillyTavern World Info** | the lorebook pattern: keyword-triggered entries with activation rules, insertion order, recursion, position and depth | [docs.SillyTavern](https://docs.sillytavern.app/usage/core-concepts/worldinfo/) |
| **Lorebook Compendium** | a documented lorebook architecture (entries, keys, groups) | [architecture](https://aceeenvw.github.io/lorebook-compendium/architecture.html) |
| Hosted platforms — Hi Waifu, JanitorAI, Zeta | character chat as a service: persona + scenario + greeting card, no persistent world | [Hi Waifu](https://www.hiwaifu.com/zh-CN/robot/14519522), [JanitorAI](https://janitorai.com/characters/c9f0caf7-5363-4048-bb38-4d741fcc5521_character-hysilens) |
| A per-character static page | one page per Heir, lore-first | [bronya-rand.github.io/…/aglaea](http://bronya-rand.github.io/reimagined-couscous/aglaea) |

I did **not** read the source of firefly-skill, Firefly-Companion or Cyrene-Agent —
only their descriptions. Treat the architecture notes as "what the project claims",
not as verified code.

## What this Sanctuary already has that they mostly lack

- **A world that runs without the visitor**: a calendar, a clock at GMT+8, a
  chronicle, a daily tick, catch-up for missed days. The companion projects are
  conversation-first; the chat ends when you close the window.
- **A knowledge wall** (`src/core/world_knowledge.py`): a Heir may not know Earth
  facts they were never taught. None of the above advertises that.
- **Thirteen distinct taste profiles** and a two-stage picture path.
- **A voice gate**: a measured standard per Heir, not vibes.

## What is genuinely worth absorbing

1. **Keyword activation from the lorebook pattern** (SillyTavern, Compendium). Our
   retrieval is vector-only: right-now, a question about "Kremnos" may surface a
   passage about Okhema because they are semantically close. Lorebook entries
   activate on **keys**, with a priority and a sticky/cooldown life — cheap, and it
   fixes exactly the failure our RAG has. This is the single most transferable idea.
2. **Portable character skill packages** (firefly-skill). Our cards are already
   personality + measured voice + canon anchors; exporting them in a skill-shaped
   format costs little and makes the work usable outside this repo — the opposite of
   a lock-in.
3. **A second engine that initiates** (Firefly-Companion's "proactive care"). We have
   letters, invites and errands, but everything that reaches the visitor is the
   *world* speaking, never a Heir deciding to write first. Worth checking how they
   separate "care" from "spam" — that is the hard part.
4. **Local ONNX semantic memory.** We use ChromaDB + Ollama embeddings. Theirs is
   lighter and fully offline; if the Sanctuary ever ships as a single binary, that is
   the pattern to evaluate.
5. **TTS in the character's own voice** (GPT-SoVITS). Real value, real risk: cloning a
   performer's voice raises consent and licensing questions the charter should answer
   before any code exists. **Not adopted** — flagged, not smuggled in.

## What I would not copy

- **Hosted chat platforms' card model** — persona, scenario, greeting, no memory of
  yesterday. It is the thing this project was built to avoid.
- **Live2D desktop presence on top of everything else** — large surface, and the
  parchment/bust sill already carries presence honestly.
- **Unmeasured "immersion" claims** — several descriptions use "natural, immersive"
  where we have a style gate. The measure is the contribution.

## Next change I would make from this

**Keyed lorebook activation in front of the vector store**, because it addresses a
concrete defect rather than adding a feature: a Heir currently cannot be *prevented*
from retrieving the wrong city, only *lucky* about it.
