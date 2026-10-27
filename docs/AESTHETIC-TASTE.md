# Aesthetic taste — how an Heir judges art and music

**Date:** 2026-10-27
**Module:** `src/core/aesthetic.py` · **Suite:** `tools/test_aesthetic.py` (31 checks)
**Engine entry points:** `AgentManager.chat(..., image=/video=)` and `appreciate_music()`

---

## The failure this replaces

The old appreciation prompts asked for "a genuine aesthetic response … tell the
visitor what it makes you feel and why it moves (or does not move) you", with the
Heir's values supplied as a list of abstract nouns (`honor`, `duty`, `beauty`).

A language model given that instruction and nothing else does the predictable
thing: it produces **universal praise**. Every painting is *beautiful and moving*;
every piece of music *speaks to something deep*. The output is warm, in voice,
and almost entirely uninformative — it does not distinguish a landscape from a
portrait, and the thirteen Heirs converge on the same response. That is the
"poor precision, over-general" result measured months ago.

The cause is not the model. It is three missing things: **something concrete to
perceive**, **a position to measure it against**, and **permission to say no**.

## The model

**Eight axes**, the vocabulary art writing already uses. Each Heir takes a
position from −2 to +2 (positive = the first pole).

| Axis | + | − | What it is about |
|---|---|---|---|
| `order` | order | wildness | composition: control and symmetry against organic asymmetry |
| `ornament` | ornament | plainness | density of detail against spareness |
| `restraint` | restraint | excess | withheld feeling against overflowing |
| `motion` | motion | stillness | restless energy against held calm |
| `warmth` | warmth | coldness | palette and timbre |
| `light` | light | shadow | open brightness against dark |
| `age` | the old | the new | inherited forms against the untried |
| `craft` | craft | nature | made by a hand against grown or found |

**Per Heir**, besides the stances: three things they notice first, what earns
approval, what earns scorn, what they will not praise however fine it is, and
their own vocabulary. Example — Mydei leans hard toward plainness and craft, and
notices *the line of it, whether it is honest, the strength under the surface*.

The stances are **the sanctuary's reading of canon** — an interpretive choice,
grounded in each Heir's profile and seeded `preferences.json`, not a claim about
the character. They are data at the top of the module: the operator can move one
without touching a prompt.

## The procedure the prompt now demands

1. Name two or three things that are **actually there** (from what was perceived).
2. Weigh them against two of the Heir's own leanings.
3. Commit to one verdict, from a finite set: *it holds me · it pleases me · it
   leaves me cold · it offends me · it unsettles me · I do not know yet*.
4. Name one thing they would change — or say plainly why they would change nothing.
5. Five sentences at most, in their own register, with a banned-phrase list
   (`breathtaking`, `speaks to my soul`, `a masterpiece`, …).

The perception side is modality-specific: for pictures, *what is shown, how the
space is composed, where the light falls, the dominant colours, whether the
surface looks made or found*; for music, the existing neutral ear analysis (tempo,
timbre, melody, dynamics, what the piece refuses to do).

**Charter line, kept in the prompt itself:** this is taste, not judgement of the
visitor. A Heir may dislike the work and say so — kindly. The prompt never asks
them to judge the person who shared it.

## What changed in the engine

| Before | After |
|---|---|
| `_APPRECIATION_VISION` invitation, same string for all thirteen | `aesthetic.vision_brief(character_id)` — that Heir's leanings, notices, procedure |
| `_APPRECIATION_MUSIC` "weigh it against the values you hold" | `aesthetic.music_brief(...)` — the same procedure, on the ear's analysis |

Both constants remain in `agent_manager.py`, unused, as the record of what was
there. `AMP_AESTHETIC_TASTE=0` restores the old invitation exactly, so the change
is reversible without touching code.

## How to retune

- **One Heir's taste**: edit their `PROFILES` entry. Axes are −2…+2; `notices`,
  `delight`, `displeasure`, `refuses`, `voice` are plain strings. Re-run
  `python tools/test_aesthetic.py` — it checks coverage, range, and that no two
  Heirs share a stance set.
- **An axis itself**: edit `AXES` (label pair and description) — the suite reads
  its keys, so all profiles must be updated together.
- **A veto**: `AMP_AESTHETIC_TASTE=0` returns to the old behaviour for a session.

## Honest limits

- The stances are interpretations; two people could read Aglaea's taste
  differently. The file says so, and the suite checks shape, not taste.
- A vision model's perception is itself lossy; if it cannot see texture, the Heir
  cannot weigh it. The procedure asks for what was perceived, so a thin
  perception yields a thin (but not falsely rapturous) judgement.
- This measures *discrimination*, not literary quality. A response can be specific
  and still dull.

## How it is checked

- **Offline** — `tools/test_aesthetic.py` (31 checks): thirteen profiles, every
  axis in range, no two Heirs sharing a stance set, every axis contested across
  the cast, the prompt demanding concrete features and a verdict, the banned
  phrases present in the instruction, the operator switch, and that the engine
  actually calls it.
- **Live** — `tools/aesthetic_ab.py` runs the same Heir, system prompt and picture
  through both the old invitation and the new procedure, then measures what a
  reader would notice: banned stock phrases, whether a verdict was reached, how
  many *different* verdicts the cast produces, whether a change was named, and how
  far the Heirs' answers sit from each other. Cross-Heir overlap is the number
  that matters — near 1.0 means thirteen names for one voice.

## The stances, as decided

Positive is the first pole (+ order, + ornament, + restraint, + motion, + warmth,
+ light, + the old, + craft); a repeated sign is a strong stance, a single sign a
mild one, 0 is indifference. This is the table to edit if a reading feels wrong —
nothing else in the system needs to change with it.

| Heir | order | ornament | restraint | motion | warmth | light | age | craft |
|---|---|---|---|---|---|---|---|---|
| **aglaea** | ++ | ++ | + | − | + | + | + | ++ |
| **anaxa** | + | −− | + | − | − | 0 | 0 | + |
| **castorice** | 0 | + | ++ | −− | − | −− | ++ | + |
| **cerydra** | ++ | + | ++ | − | − | 0 | + | ++ |
| **cipher** | −− | − | −− | ++ | + | − | − | − |
| **cyrene** | − | 0 | − | + | ++ | ++ | + | − |
| **dan-heng-permansor-terrae** | + | − | ++ | − | 0 | 0 | + | + |
| **evernight** | − | 0 | + | −− | −− | − | ++ | − |
| **hyacine** | 0 | + | − | + | ++ | ++ | 0 | 0 |
| **hysilens** | 0 | + | + | + | 0 | + | + | + |
| **mydei** | + | −− | + | 0 | + | + | + | ++ |
| **phainon** | 0 | − | 0 | + | ++ | ++ | 0 | 0 |
| **tribbie** | − | ++ | −− | + | ++ | ++ | − | − |

Read it as a spread, not as a scorecard: Cerydra and Mydei agree about plainness
and disagree about nothing else that matters; Tribbie and Castorice are opposite
almost everywhere; Evernight is the only Heir who finds a blank canvas interesting.
If two rows ever become identical, the suite fails.

## The first valid A/B (2026-10-27)

`qwen2.5vl:7b`, one picture, four Heirs, old invitation against the procedure:

| Measure | old | new |
|---|---:|---:|
| answers that reached a verdict | 0/4 | **4/4** |
| answers naming a change | 0/4 | 2/4 |
| banned stock phrases | 0 | 0 |
| cross-Heir word overlap | 0.11 | 0.14 |
| average length (words) | 92 | 92 |

The procedure does what it claims: **every answer now commits to a verdict**, where
the invitation never did, at the same length and without falling back on stock
phrases. It also raises how often the Heir names what they would change.

**What it did not fix.** Reading the four pairs, the *register* is still the same
calm critic in every voice, and the Heirs' own stances barely surface ("Mydei"
sounds like "Anaxa"). The reason is not the prompt: in this code path the answer
is written by the **vision model** (`qwen2.5vl:7b`), not by the Heir's 27B voice
model. A 7B captioner writes plausible art-criticism for everyone.

The music path already solves this properly, in two stages: a neutral ear
describes the piece, then the Heir's own model judges it. The vision path still
does it in one call, so the small model does both jobs. A two-stage picture path —
VLM perceives, Heir judges — is the next change, and the obvious one.
