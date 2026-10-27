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

## All thirteen cards (2026-10-27, second pass)

Every card lost its inherited `AUTO REFINEMENT` block and gained a
**CANON COMPLEXITY** block drawn from `databank/chrysos-heirs/`. The rules are
behaviour and memory — what the Heir notices, carries, hides, and cannot do — not
sentence templates, because templates are what the gate penalises.

| Heir | Crutch rules removed | Complexity now carried |
|---|---:|---|
| Aglaea | 6 | blindness read through voice and thread; the childhood fear of the dark; plain clothes because beauty is the future, not cloth; scraps of the fallen; the threads that watch; "Agy" before Lady Goldweaver |
| Anaxa | 5 | the eye that sees souls; the temples that threw him out; Diotima's books and the black tide; the students who silence him; the dromases |
| Castorice | 6 | the touch that kills; the soft things made so they can be kept untouched; ice sculptures and a thousand years of names; the nightmare of every Heir dying; the nether realm she chose |
| Cerydra | 4 | the beggar girl dressed as a princess and used as a pawn; the board she took; chess as thought, not decoration; the cost of her sacrifices; the titles she gives her Heirs |
| Cipher | 6 | the starving Dolos childhood; aquaphobia under the fish jokes; the three hundred Rogues as family; theft she denies; the Gem that was a plan; the chocolate that makes her ill |
| Cyrene | 6 | love as her prime mover; deaths she calls the price; the loop she went back to close; memory as craft; the child and the Demiurge as one person; the weight of Phainon |
| Dan Heng | 6 | the archiver who stopped pretending the journey was cold entries; the farewells; the nightmares he does not volunteer; protection as his answer to grief |
| Evernight | 4 | March's other aspect doing the cruel work; the flat in her signature; the cleansing she refused and keeps re-deciding; memory as evidence |
| Hyacine | 6 | the bedridden childhood; the legend for a grandmother; "I'm just a physician" as a shield; the despair she cannot cure; the courtyard as refuge; the short temper |
| Hysilens | 6 | the siren who chose silence; the violin that became blades; self-negation stated plainly; the hand that ended Cerydra's flame; the nicknames she can afford |
| Mydei | 6 | ten thousand deaths taken without drama; mortal companions carried as names; a king who never flew his banner; single-word annotations; pride kindness cannot talk him out of |
| Phainon | 6 | ease that costs him; carving himself into the shape people need; grief that arrives as work; a banked hatred that is not polite; the Flame Reaver he does not disown |
| Tribbie | 0 | a thousand years in a child's body; the thousand messengers of whom three remain; the shift between Tribbie, Trianne and Trinnon; a diary whose hand weakens; "see you tomorrow" meant every time |

## A second defect, found while wiring the picture path

**The Heirs could not see at all.** `.env` sets `VISION_MODEL=gemma3n` — the
"unified" senses model — and Ollama refuses images for it: *"model does not
support multimodal requests."* Every shared picture raised that error, so the
appreciation feature was not weak, it was **broken**. `chat_vision` and
`chat_video` now try the configured model and fall back to one that can see
(`AMP_VISION_FALLBACK`, default `qwen2.5vl:7b`), remembering what worked for the
life of the process. Verified live: the configured model is still `gemma3n`, the
working one reported `qwen2.5vl:7b`, and the perception came back as a real
description of the image.

## Picture appreciation is now two stages

The single call made the *vision* model write the Heir's judgement, which is why
thirteen Heirs produced one captioner's prose. It is now:

1. **Perceive** — a neutral eye (`PERCEPTION_SYSTEM`) describes what is there and
   judges nothing;
2. **Judge** — the Heir's own model receives that description plus their taste
   procedure and answers in their voice.

The one-call path remains as the fallback when perception is unavailable. Suite:
`tools/test_aesthetic.py` (41 checks, including that the judgement carries the
perception and that a multimodal refusal is recognised).

## Measured: the thirteen-card pass, before and after

Full gate, `gemma3:27b`, 4 cases per Heir, best-of 1, temp 0.4, anti-cheat **on** —
the same protocol as the 2026-10-27 baseline, so the columns are comparable.

| Heir | before | after | style | content | change |
|---|---:|---:|---:|---:|---|
| Aglaea | 2/4 | 3/4 | 74 | 69 | +1 |
| Anaxa | 3/4 | 3/4 | 86 | 73 | = |
| Castorice | 3/4 | 1/4 | 61 | 58 | −2 |
| Cerydra | 4/4 | 3/4 | 86 | 70 | −1 |
| Cipher | 4/4 | 4/4 | 88 | 70 | = |
| Cyrene | 3/4 | 4/4 | 90 | 74 | +1 |
| Dan Heng | 3/4 | 4/4 | 88 | 70 | +1 |
| Evernight | 3/4 | 3/4 | 86 | 71 | = |
| Hyacine | 1/4 | 2/4 | 75 | 62 | +1 |
| Hysilens | 3/4 | 3/4 | 76 | 68 | = |
| Mydei | 2/4 | 1/4 | 73 | 67 | −1 |
| Phainon | 3/4 | 2/4 | 64 | 56 | −1 |
| Tribbie | 3/4 | 3/4 | 86 | 69 | = |
| **total** | **37/52** | **36/52** | | | **−1** |

**The honest reading: the card work did not move the metric.** Four Heirs improved,
four regressed, five held, and the total fell by one case. The canon blocks make the
prompts more faithful to the databank and they removed 69 crutch rules, but the
gate — which judges a single line against a canon line — does not reward either.

## What the measurement itself revealed

Two artefacts in the instrument now matter more than the card text:

1. **The `...` replies are the harness's own exhaustion signal**, not a stray model
   output. `test_dialogue_style.py` rejects degenerate and anti-cheat-failing
   candidates for up to twelve attempts, then falls back to the literal `"..."` and
   judges it — scoring 45/25. Five of this run's sixteen failures are that artefact.
2. **The anti-cheat is suppressing genuinely terse Heirs.** Re-running Mydei with
   `--no-anti-cheat` lifts him from **1/4 to 3/4**. His lines are being rejected as
   *run repeats* — short, formulaic-sounding utterances that are, for him, in voice.
   Castorice does not recover the same way (1/4 either way), so her failure is real.

So the next lever is not the cards but the **judging harness**: either a better
diversity requirement than "reject and retry", or a product-level guard (done: a
silent reply is now retried once) plus a judge that can score a quiet line as the
quiet line it is.

## The product-level fix that came out of it

A Heir now never stores silence as its reply: `chat()` detects a response with no
letters or digits and asks once, plainly, for the line. Suite:
`tools/test_aesthetic.py` (48 checks).

## The mechanical claims audit (2026-10-27)

`tools/audit_heir_claims.py` compares each card's identity field against
`databank/chrysos-heirs/` — Coreflame, Titan, MBTI, race, hometown, titles and
nickname vocabulary. It found **three real inaccuracies**, not just omissions:

| Heir | Card said | Databank says |
|---|---|---|
| Hyacine | race `Human (golden blood / Chrysos Heir)` | **Skyfolk** |
| Cipher | city-state `Okhema (nomadic)` | **Dolos** — the fallen bandit city she starved in |
| Anaxa | city-state `Grove of Epiphany` | a **remote, unnamed city-state**; the Grove is where he studied |

Each was a place or a people flattened into a convenient label — exactly the
failure mode this audit exists to catch. All three are corrected, and the tool
now exits non-zero if any structural claim drifts again.

It also showed that **no card recorded what its Heir calls the others**, though
that is how the Heirs address each other throughout the databank. Six cards gained
the vocabulary: Aglaea (Deliverer, Kitty, Seamstress), Cerydra (her eight Dux
titles), Cipher (Seamstress/the Mom, Ciphy, Kitten Fish), Castorice (Cassie, Cas,
Princess Homebody, Dux Florum), Anaxa (Prof Nax, One-eyed Boy, Dux Sagax, Naxy),
Hyacine (Skyfolk of the Twilight Courtyard, named as such).

Still missing, honestly: Mydei, Phainon, Tribbie, Hysilens, Dan Heng and Evernight
carry no outgoing-nickname vocabulary beyond what their complexity blocks already
say, because the databank does not record more for them.
