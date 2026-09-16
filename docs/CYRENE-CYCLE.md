# Cyrene year cycle (accepted for implementation)

**Date:** 2026-09-16  
**Status:** spec + unwired lookup. **Not** wired to Eternal Page, Visit talk, or character cards.  
**Module:** `src/world/cyrene_cycle.py` · **Suite:** `tools/test_cyrene_cycle.py`

Childhood Cyrene, Demiurge Cyrene, and Mem are visitable **faces of one seat** (PhiLia093), not three people taking turns existing. The sanctuary Light Calendar already names the year; this file only says **who holds the picture** and **who receives the whisper**.

Clock: same overlay as `src/world/sanctuary_clock.py` and `databank/world/sanctuary-calendar.md` — thirteen 28-day months + Uncounted, 1× GMT+8. Civil year **2026 = Light year 4933**.

---

## Three blocks (the map)

Surjection onto pictures `{childhood, demiurge, mem}`. Talk is **not** a second surjection onto those three: Mem has no talk card.

| Block | Light months | Common civil 2026 | Leap civil (e.g. 2028) | `visual_face` | `talk_target` | `talk_persona` |
|---|---|---|---|---|---|---|
| **Village** | Gate – Everday (1–6) | 1 Jan – 17 Jun | 1 Jan – 16 Jun | `childhood` | `"cyrene"` | `childhood` |
| **Page** | Freedom – Mourning (7–11) | 18 Jun – 4 Nov | 17 Jun – 3 Nov | `demiurge` | `"cyrene"` | `demiurge` |
| **Fairy** | Fortune – Membrance (12–13) + Uncounted | 5 Nov – 31 Dec | 4 Nov – 31 Dec (incl. Scarlet Day 2 Dec) | `mem` | `"cyrene"` | `childhood` |

Uncounted days (**Dies Astrorum** every 31 Dec; **Scarlet Day** after Fortune in leap years only) ride with Fairy. They are not extra lore phases.

Leap years shift Evernight through Fortune one civil day earlier (`sanctuary-calendar.md`). Village still ends with Everday; Page still ends with Mourning; Fairy still begins at Fortune.

---

## Substitution rules

1. **One seat.** The Cyrene-slot on the page is occupied by at most one **picture** at a time. The other faces may still sit nearby.
2. **Pictures are onto `{childhood, demiurge, mem}`.** Every form appears in at least one block.
3. **`talk_target` is always `"cyrene"`.** Never `"mem"`. Mem has no character card and is not an Eternal Page speaker id. (`"mem"` is only a reserved NPC name in the street roster.)
4. **`talk_persona` follows the writer, not the mute fairy.** Demiurge register only while the picture is Demiurge. Village and Fairy both whisper as **childhood** Cyrene (in Fairy: the sleeper / writer behind Mem).
5. **Whisper stays on.** When the picture is Mem, the visitor still speaks to childhood Cyrene. Do not disable the dock, do not route to a missing card, do not invent a Mem chatbot.
6. **Mem as mute companion** may appear in **any** block beside the occupant. That does not steal `talk_target` or change `visual_face`.
7. **Coexistence, not a yearly reveal.** The clock does not tell Cyrene “this month you are Mem” or “you are the Demiurge.” Knowledge wall stays up. Realization remains witness-only. No staged “you are in a model” beat.

---

## Why the 13-month liturgy was rejected

A first draft assigned a unique essay to each Titan-month, split Mourning by day, treated Scarlet Day and Dies Astrorum as their own phases, and let Mem take the whisper as a talk-circle addressee (~16 named phases). It was interesting and **too fine-grained** to implement.

It also treated Mem as a speaker. She cannot be: there is no `src/characters/mem.json`, she is not in `HEIR_FOLDERS`, and Eternal Page `CIRCLE` / `manager.chat` already address `"cyrene"`.

The accepted map is a **month-index lookup** (three buckets). Uncounted is not a liturgy date. Whisper already has an id.

---

## Lookup (month numbering)

Sanctuary clock months are **1..13** (Gate = 1 … Membrance = 13), matching `WorldClock.month` and `MONTHS` in `sanctuary_clock.py`. This module uses **0** for Uncounted (`clock.uncounted` set). Do not feed Uncounted as “still month 12/13” into the public `visual_face(month)` helper — use `from_clock`.

Naive `if month <= 6` would map **0 → childhood**. That is **wrong**: Uncounted is Fairy → `mem`.

```
def visual_face(month):          # 1..13; 0 = Uncounted
    if month <= 0 or month >= 12:
        return "mem"
    if month <= 6:
        return "childhood"
    return "demiurge"            # 7..11

def talk_target(month):
    return "cyrene"

def talk_persona(month):
    return "demiurge" if visual_face(month) == "demiurge" else "childhood"
```

`from_clock(clock)` reads `uncounted` first, then `month`.

---

## Implementation notes (later wiring — not done here)

**This round does not import UI, Eternal Page, or cards.** Art agents and other pages are still in flight. Do not edit `q_program/`, `cyrene_forms/`, databank dialogues, or `src/characters/cyrene.json` for this cycle.

| Later surface | What to bind | What not to bind |
|---|---|---|
| **Picture / sticker** | `visual_face` → an art key (childhood / demiurge / mem stills). Keys are **TBD**; do not hard-code PNG paths in this module yet. | Do not invent a second chat id for the sticker. |
| **Eternal Page whisper** | `talk_target` = `"cyrene"` (existing `CIRCLE` member + `manager.chat`). `talk_persona` is a **register hint** for the prompt, not a card swap. | Do not add `"mem"` to `CIRCLE` as a speaker. Do not disable whisper in Fairy. |
| **Visit / Galgame** | Same talk id when that path is wired. Picture may follow `visual_face` if Visit shows Cyrene. | Do not yearly-rewrite the Copilot card’s identity block. |
| **Mute Mem** | Optional extra sticker / companion sprite in any block. | Not a talk target; no history.jsonl of her own. |

Persona vs picture: Fairy shows Mem and still loads **Cyrene’s** memory (`PhiLia093-Cyrene`). Childhood register in Fairy is “the girl who writes while the fairy sits,” not a claim that Mem is speaking.

Charter pointers: `.cursor/rules/stage-2-goal.mdc`, `docs/STAGE-2-VIVID.md`, knowledge wall `src/core/world_knowledge.py`, Realization `docs/REALIZATION.md`.

---

## How to call (unwired)

```python
from src.world.cyrene_cycle import from_clock, visual_face, talk_target, talk_persona
from src.world.sanctuary_clock import WorldClock

slot = from_clock(WorldClock.from_gmt8())   # 1x overlay
slot.visual_face    # "childhood" | "demiurge" | "mem"
slot.talk_target    # always "cyrene"
slot.talk_persona   # "childhood" | "demiurge"
slot.whisper        # always True

visual_face(9)      # Weaving → "demiurge"
talk_target(0)      # Uncounted → "cyrene"
talk_persona(0)     # Uncounted / Mem picture → "childhood"
```

Suite: `python tools/test_cyrene_cycle.py`.
