# Auto-cycle log — 2026-08-13 21:08

- Heir model: `gemma3:27b` · judge model: `gemma3:27b` (constant)
- Gate: per-Heir pass rate ≥ 85% (style ≥ 85 AND content ≥ 60)
- Best-of: start 7, max 9 · limit 8/Heir/cycle · max 6 cycles
- Opt-out: a Heir that passes a cycle declines participation in later cycles (shortens the loop).
- Final re-test: FULL — every canon line of every Heir, best-of 1 (single-shot deployment measure)
- Anti-cheat: ON — no canon quoting, no repeated line, no phrase-crutch, no formulaic opening (within-run filter)

## Cycle 1 (best-of 7; bars style≥85, content≥60)
| Heir | pass | rate | avg style | avg content | status |
|---|---:|---:|---:|---:|---|
| Aglaea | 6/8 | 75% | 80 | 68 | FAIL |
| Anaxa | 4/8 | 50% | 78 | 65 | FAIL |
| Castorice | 4/8 | 50% | 69 | 59 | FAIL |
| Cipher | 5/8 | 62% | 75 | 61 | FAIL |
| Mydei | 7/8 | 87% | 83 | 64 | PASS |
- Opted out this cycle (already passed): mydei

- aglaea: refined (6 rules: Begin sentences with conjunctions like 'Now', 'It is', or 'Concerning'.; Use ‘please’ when directly addressing groups ('Heroes, your attention please').; Frame observations as incomplete thoughts trailing off with '...'…)
- anaxa: refined (6 rules: Begin each response with "Anaxa Voice Rules:"; Anaxa Voice Rules:; Start lines with a dismissive interjection like “Hmph” when reacting to information.…)
- castorice: refined (5 rules: Use 'and...' to begin welcoming statements.; End sentences trailing off with ellipsis even when not posing questions.; If asking a question, phrase it as checking for completeness or order.…)
- cipher: refined (6 rules: Begin sentences with non-lexical sounds when reacting to immediate stimuli.; Frame requests as confirmations of ability rather than direct questions.; Include a conditional benefit or obligation within longer statements.…)