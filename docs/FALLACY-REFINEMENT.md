# Fallacy Refinement Report

*Generated: 2026-08-10 (deterministic audit)*

## Method

- **Round 1** (LLM, `qwen2.5:14b`) refined each Heir's personality/speech/
  preferences from their canon dialogue — **73/73 evidence quotes verbatim**.
- **Round 2** attempted an LLM re-audit, but the environment could not load the
  14B that day (see `TECHNICAL-BARRIERS.md` §9), and the 7B fallback produced
  unreliable output (fabricated/empty evidence) — **fully reverted** to the
  verified state.
- Instead, a **deterministic audit** (`tools/audit_card_quotes.py`) extracted
  every quoted claim from the cards and verified it verbatim against the whole
  canon databank (personal-memories + `databank/**`). No LLM, so exact.

## Result

- **29/34** quoted claims found verbatim in canon; the 5 remaining are
  **truncated canon fragments** (each verified by grep, e.g. Aglaea's catchphrase
  is the opening of *"may we reunite in the promised new world… Farewell,
  Mydei"*) — legitimate catchphrases, not fallacies.
- **2 genuine fallacies found and fixed:**

| Heir | path | issue | fix |
|---|---|---|---|
| castorice | `speech.catchphrases[2]` | "May we reunite on the other side, where the warm west wind blows." — no support in the canon databank | replaced with the verified line *"I'm more willing to view 'death' as a peaceful farewell than a punishment."* |
| tribbie | `speech.catchphrases[1]` | "Don't worry! Leave it to us!" — a paraphrase; canon says *"It's fine. Leave it to us."* | replaced with the verbatim canon line |

## Tools to reuse

- `tools/audit_card_quotes.py` — deterministic quote-vs-canon audit; run it as a
  quality gate after any future card edit.
- `tools/refine_fallacies.py` — LLM audit tool (needs the 14B; always verify the
  `evidence` field verbatim before applying `updates`).
