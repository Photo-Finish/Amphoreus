# Heir fidelity — what the cards say vs what canon says

**Date:** 2026-10-27
**Scope:** `src/characters/*.json` (persona prompts) against `databank/chrysos-heirs/*.md`
and the mission/wiki corpus
**Status:** first pass — the systemic defect is documented and one Heir is fixed; the
per-Heir canon audit is in progress.

---

## The systemic defect: the cards were taught crutches, then punished for them

`tools/auto_cycle.py` appends an `AUTO REFINEMENT` block to a Heir's system prompt
when their style score fails, and strips it again with `strip_auto_refinement`.
Twelve of the thirteen cards still carry that block. Reading the rules, they are
almost all **formulaic instructions**:

| Card | Rule (quoted from the prompt) |
|---|---|
| aglaea | "Begin sentences with transitional phrases like 'Now…' or 'It is…'" |
| cerydra | "Begin lines with a solitary name declaration." |
| anaxa | "Use 'hmph' as an isolated utterance to express dismissal." |
| cipher | "Begin lines with a non-lexical vocalization if appropriate." |
| cyrene | "Respond to direct questions with a question back…" |
| evernight | "Begin sentences with conjunctions or pronouns when continuing thought" |
| hyacine (removed) | "Use 'indeed'…", "Employ 'but now'…", "Begin sentences with observational statements…" |
| mydei | "Begin sentences with a statement of fact before adding commentary…" |
| phainon / hysilens | carry the generator's own markdown heading verbatim ("## Phainon Voice Rules:") |

Those are exactly the patterns the quality gate's anti-cheat is built to catch —
**formulaic openings** and **phrase crutches**. So a loop meant to raise fidelity
left behind the two habits the gate scores as failure. The cards are not merely
missing complexity; they are carrying instructions that push the model toward the
behaviour being measured against.

This also explains why the failures cluster at **style 78** rather than being
scattered: the model is being formulaic in a way the judge can name.

**Recommended repair, per Heir:** strip the `AUTO REFINEMENT` block (restoring the
prompt the project actually wrote), then add a *canon complexity* block of the kind
below — behaviour and memory, never sentence templates. Then re-measure.

## Case study: Hyacine, 1/4 → 2/4

Baseline (2026-10-27 gate, `gemma3:27b`, 4 cases): **1/4 pass, style 72, content 62**,
with one case collapsing to 45/25.

Her six inherited rules were the worst of the twelve — every one a template
("observational statements", "indeed", "but now", "frame completed tasks as mutual
completion") plus a garbled fragment (*"Rationale for each rule, addressing the
failures:\*\*"*) that had leaked into the prompt from the generator.

Fix applied: stripped the block, then appended what the databank actually records
about her, as *behaviour* rather than phrasing —

- she was a frail, bedridden child who learned medicine on a doll;
- her grandmother was a legend and she has never felt she measured up;
- *"I'm just a physician"* is a shield, not modesty;
- she can drive out a disease but not despair — the dying girl she could not mend;
- the Twilight Courtyard is a refuge for every Heir (Castorice's dried flowers,
  Phainon's wheat, Anaxa and Aglaea mending things over oatmeal);
- she has a short temper when someone she loves is careless with themselves.

Result: **2/4 pass, style 76, content 65** — every case improved, none regressed.
The remaining two failures are:

1. *style 78 / content 85* — the reply is on-subject but the register slips
   (a wondering question where canon has an urgent instruction). Close, and a
   `best-of` run would likely clear it;
2. *style 48 / content 35* — the reply is an **empty ellipsis**. Ollama's default
   seed is 0, so generation is deterministic: the same scene reproduces the same
   empty line every run. Forbidding silence in the prompt did **not** change it,
   which means the model is stopping rather than choosing not to speak. That is a
   decoding problem to chase (stop sequence or token budget), not a voice problem.

## What "faithful and comprehensive" means here, and how it is checked

A card is faithful when every claim it makes is supported by `databank/`, and
comprehensive when the significant parts of a Heir are present rather than
flattened into a type. The Heirs are not archetypes: Hyacine is not "the gentle
healer" — she is a formerly bedridden child with a legend for a grandmother, a
temper, and a grief she cannot heal. A card that says only "warm, optimistic,
compassionate" will produce a walking adjective.

The check, per Heir:

1. **Claims → sources.** Every line of the card's `personality` and `biography`
   should be traceable to the profile or the mission corpus; unsupported claims
   are either removed or marked as the sanctuary's framing.
2. **Coverage.** The profile's *Deepest Layer*, key relationships and turning
   points must appear as behaviour, not as epithets.
3. **Opposites.** Each Heir has at least one trait that contradicts their type
   (Mydei's restraint under pride, Anaxa's skepticism as love, Cipher's loyalty
   beneath trickery). A card missing the contradiction is flattened.
4. **Relationships as behaviour.** "Close to Cassie" is not enough; the card should
   show *how* — the teasing, the nickname, what she notices about them.

## Per-Heir status

| Heir | Stale block | Fix this pass | Canon audit |
|---|---|---|---|
| Hyacine | removed | complexity block appended; 1/4 → 2/4 | done |
| Aglaea | present (6 rules) | pending | next |
| Mydei | present (6 rules) | pending | next |
| Anaxa, Castorice, Cerydra, Cipher, Cyrene, Dan Heng, Evernight, Hysilens, Phainon | present (4–6 rules) | pending | queued |
| Tribbie | none | — | queued |

**Permission:** the cards are Stage-1 Copilot artifacts under
`.cursor/rules/copilot-legacy.mdc`, which requires the operator's word before they
are edited. Hyacine's change was explicitly approved. **The other eleven are
stripped only if the operator agrees** — and stripping is itself restoration:
`strip_auto_refinement` returns the prompt to the project's own text.
