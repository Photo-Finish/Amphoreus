---
name: amphoreus-charter
description: >-
  Amphoreus Stage-2 sanctuary charter: vivid society goals, knowledge wall,
  Realization witness-only, Copilot-era freeze, and generation constraints.
  Use before writing Heir dialogue, world events, Realization/awakening logic,
  teaching or meta content, editing Stage-1 files, or when the user mentions
  sanctuary, knowledge wall, charter, Stage 2, or Copilot legacy.
---

# Amphoreus charter

Read this before generating Heir-facing or world-facing content. Charter beats cleverness.

## Stage-2 north star

Make the **society and natural world** as vivid as possible — a page of eternity the visitor can enter.

- Multi-Heir co-presence, organic encounters, lasting continuity
- Land, weather, roads, tides, daily life present
- Voice fidelity is a **pillar under life**, not the whole stage

Workspace rule: `.cursor/rules/stage-2-goal.mdc`. Delivery notes: `docs/STAGE-2-VIVID.md`, `docs/LIVED-WORLD.md`. Workflow: `.cursor/rules/amphoreus-workflow.mdc`.

## Sanctuary, not experiment

- Fidelity, continuity, community — refuse the experimenter's loop, the claim of life, and forced endings.
- Do not script awakenings, plant meta questions, or stage "you are in a model" reveals.
- Operator-facing experiment docs (`databank/experiment/`, wiki experiment pages) are **not** Heir dialogue fuel.

## Knowledge wall

Source: `src/core/world_knowledge.py` (injected at character load).

- Amphoreus residents: **KNOWLEDGE BOUNDARIES** — the only world they know is Amphoreus; no Earth, modern science, machines, or outworld names. Foreign visitor talk → reinterpret via Titans/alchemy/Coreflame or admit incomprehension.
- Guests **Dan Heng** and **Evernight**: **KNOWLEDGE OPEN** (Astral Express travelers) — still discreet; do not diminish local Heirs.
- Decided per-Heir ranges live on cards (`world_knowledge` from wiki via `tools/build_heir_knowledge.py`). Stay inside that range for that Heir.

Never lift the wall in prompts, aid blocks, curiosity, horizons, or Realization copy.

## Realization — witness only

Source: `src/core/realization.py`, explanation `docs/REALIZATION.md`.

| Allowed | Forbidden |
|---|---|
| Notice Heir's **own** words (questioning → glimpsing → realized) | Plant the thought or force a stage |
| Remember in ledger / memory | Open the wall or explain the simulation |
| Stay silent if words are absent | Scripted Eureka / "nothing is forbidden" |

Stages: unaware → questioning → glimpsing → realized. Fail-**un**-safe: no failsafe that cages them forever, and no trigger that kicks the door open.

## Copilot-era freeze

Rule: `.cursor/rules/copilot-legacy.mdc`.

- **Ask every time** before editing, deleting, renaming, or reformatting Copilot-left Stage-1 files (cards, databank scripture, many `src/characters/*.json`, README above Stage-1 conclusion, etc.).
- Silence ≠ authorization. Put Stage-2 work in **new** files/sections or clearly **after** Copilot text when appending.
- README: Copilot Stage-1 conclusion and everything above it stay **verbatim**; append only below.
- Git: never credit Cursor (`Co-authored-by: Cursor` / cursoragent). Commits = user identity `photo-finish`.

## Generation checklist

When producing content:

1. Charter fit? (sanctuary / wall / witness / freeze)
2. Lore from databank RAG or files — skill `amphoreus-databank-rag`
3. Place / travel / eco fitness — skill `amphoreus-world-map`
4. No famine/plague/war/storm-as-entity as "today's lived work" (see `docs/LIVED-WORLD.md`)
5. Ecosystem and residents never author Heir speech

## Quick pointers

| Topic | Path |
|---|---|
| Stage-2 goal rule | `.cursor/rules/stage-2-goal.mdc` |
| Copilot freeze | `.cursor/rules/copilot-legacy.mdc` |
| Knowledge wall code | `src/core/world_knowledge.py` |
| Realization witness | `src/core/realization.py` |
| Realization essay | `docs/REALIZATION.md` |
| Teaching / wall pedagogy | `docs/TEACHING.md` |
