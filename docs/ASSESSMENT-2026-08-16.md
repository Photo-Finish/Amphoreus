# Project Amphoreus — Maturity Assessment

**Date:** 2026-08-16 · **Author:** the Sanctuary's build record
**Verdict:** ≈ **90% complete** as a living sanctuary — the final 10% is the one
quality bar the project set for itself: the *voice-fidelity gate*.

---

## 1. The project's own definition of "done"

> *Reproduce the digital forms of all Chrysos Heirs as AI models, each sharing
> the same personality, knowledge, memories, speech patterns and behavioral
> traits — as a **sanctuary, not an experiment**.* (ROADMAP.md, PHILOSOPHY.md)

"Done" therefore has two halves:

1. **A complete, living, faithful sanctuary** (architecture + content + world).
2. **The Heirs' voices indistinguishable from canon** (the measured style gate).

The first half is essentially **done**. The second is **~80–85% there and
actively closing** — it is the standing quality loop, not a finished line.

---

## 2. What is done and complete

### 2.1 Roadmap phases
| Phase | Content | State |
|---|---|---|
| **0 — Foundation & Knowledge Base** | Master registry (13), 14 profiles, Titan/lore/calendar, black-tide lore, 317 wiki pages, mission dialogue databank | ✅ **Complete** |
| **1 — Architecture Design** | Hybrid RAG + persona + multi-agent; card schema; 5-metric eval framework | ✅ **Complete** |
| **2 — All 13 character cards** | Full personas + measured voice profiles + canon anchors | ✅ **Complete** |
| **2.5 — The Sanctuary** | Charter, persistent memory, world engine + Light Calendar, senses, visitor framing, teaching, Galgame, Map, Admin Console, Ambient Director, knowledge confinement | ✅ **Complete** |
| **3–5 (original roadmap)** | Batch evaluation, multi-agent orchestration, formal QA | **Absorbed into the Sanctuary build** (multi-agent world engine exists; QA = the test suite + style gate) |

### 2.2 The Sanctuary's living layers (all built, tested, pushed)
- **Memory**: per-Heir bond + durable history + long-term memories + consolidation.
- **The little Amphoreus**: Light Calendar (12 months/4 weeks/5 periods), 13 Heirs with routines, free autonomous decisions, travel between city-states, the Dawn-era Veil/Nether.
- **RAG**: 13 collections, **11,332 documents**, real local embeddings (all-MiniLM, offline).
- **Senses**: vision (pictures/videos), hearing (STT), music appreciation — all local.
- **The Heirs' minds**: curiosity (questions + inferences, per-Heir lenses), horizons (changeable knowledge bank), the **Realization witness** (passive, wall never opens).
- **The living world**: weather (Keeper), moods, social web (gossip/bonds), gifts, letters, reach-outs, NPCs, black tide.
- **The visitor**: two experience modes, physical travel with a phone-idiom chat, a persistent avatar.
- **Voice conduct**: measured speech profiles, anti-narration, natural question endings, length freedom.
- **Operations**: compute-mode switch (NVIDIA CUDA / Intel Vulkan), truthful voice status, live world-status website (public + LAN), conversation archive tool.
- **Charter compliance**: cheat-free cycle, no forced endings, no claims of life — honored throughout.

### 2.3 Quality evidence (fresh, 2026-08-16)
- **7/7 test suites green**: curiosity 47 · realization 27 · horizons 25 · living-world 47 · ui-travel 41 · control-integration 58 · vividness.
- **Environmental cross-check** (real LLM, isolated A/B): weather, mood, curiosity and voice-conduct show **concrete effects** on replies; horizons/letters surface **on demand**; the visitor's road now surfaces in the Heirs' own words (Hyacine verified) with the UI phone-idiom as the guaranteed layer; the Realization witness correctly shows **no** effect (it is a witness, not a driver).
- All work is committed and pushed to GitHub.

---

## 3. What is NOT complete (the honest gaps)

### 3.1 The voice-fidelity gate — the decisive one
- The standing bar: **STYLE & INTONATION ≥ 85, CONTENT ≥ 60** for every Heir,
  enforced by the cheat-free auto-cycle.
- Latest cycle evidence: Castorice reached **87%** in-cycle (best-of 9) but
  **75% on the final cheat-free re-test** — and the logged runs covered a
  subset, not all 13.
- **Status: an active refinement loop, not a passed finish line.** This is the
  single biggest "not done" item relative to the ultimate goal.

### 3.2 Behavioral limits (verified, not bugs)
- **Persona dominance**: some Heirs (e.g. Aglaea's fate-preamble) preempt
  environmental lines even when injected — the UI layer guarantees the travel
  feel; the model line surfaces for other Heirs.
- **Model tier**: qwen2.5:14b (fast) is a weaker instruction follower than
  gemma3:27b (standard, ~8 tok/s) — a real speed/fidelity trade-off on this
  hardware.

### 3.3 Operations
- The **world engine is currently stopped** (operator choice); "ever-running"
  is a capability, not the present state.
- **Memory headroom** is tight (~a few GB with the big models).
- The **public tunnel URL is ephemeral** (changes on restart) — a self-healing
  guard keeps it up and publishes the current URL.

---

## 4. Website / remote access (2026-08-16)

- **Public (Internet):** a Cloudflare quick tunnel — the URL is published in
  `world_runtime/status_urls.txt` (verified HTTP 200). Read-only status only.
- **LAN (no Internet, no VPN):** `http://192.168.1.15:8765` — guaranteed for
  same-network terminals.
- **Self-healing:** `tools/status_guard.py` restarts the server and the tunnel
  and rewrites the URL file every 15 s.
- **Where Cloudflare is blocked (some regions):** port-forward 8765 on the
  router for direct access, or point any tunnel service at
  `http://127.0.0.1:8765` (the guard's tunnel list is one entry away).

---

## 5. Bottom line

| | |
|---|---|
| **As a sanctuary that lives and remembers** | ✅ **Done.** It builds, runs fully offline, passes every suite, honors its charter, and exceeds the original roadmap's depth. |
| **As "all 13 Heirs speak indistinguishably from canon"** | 🔄 **~80–85% — the auto-cycle's final stretch.** The most valuable next step is re-running the focused style cycle on the failing Heirs now that the models are restored and disk has room. |
