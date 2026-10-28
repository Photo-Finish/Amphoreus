# Session handoff — 2026-10-28

Written so the next session can pick up **without re-deriving anything**. If a claim
below is wrong, trust the tool output, not this file — but check here first.

## Where the code is

- `HEAD` at handoff: `52a860b` (on `origin/main`).
- **Retrace point:** tag `retrace-before-admin-ui` → `52a860b`.
  `git reset --hard retrace-before-admin-ui` is the escape hatch for a bad edit.
- **World checkpoints:** `world_runtime/checkpoints/2026-10-28T20-16` and `…20-20`
  (49 files, ~879 KB each, with `manifest.json`).
- Working tree clean at handoff.

## What is running

| Process | What | Log |
|---|---|---|
| `tools/backfill_lore.py --from 2026-09-17 --to 2026-10-21` (pid 24624 + child) | writing the 35 days the 7-day catch-up could not reach | `world_runtime/backfill_then_voice.log` |
| same chained job, steps 2–3 | after the backfill: the Aglaea/Hysilens gate, then the engine restarts (`--interval 900 --catch-up`) | same log, then `world_runtime/engine_run.log` |

**The world engine is deliberately stopped** while the backfill runs: one writer per
chronicle. Chronicle at handoff: **~3796 lines** and climbing.

## If the chain was killed

```
python tools/backfill_lore.py --from 2026-09-17 --to 2026-10-21      # resume the gap
python -m src.world.world_engine --interval 900 --catch-up          # bring the world back
```

`--catch-up` refuses to start if `engine.pid` names a live engine (guard added
2026-10-28; `--force` overrides). Stop gracefully with
`powershell -File tools\start_world.ps1 -Stop`, which records the rest so the next
start fills the gap.

## State of the suites

`python tools/run_all_tests.py` → **1842 passed, 30 failed across 29 suites**.

**All 30 failures are `test_sanctuary_live`**, and they are stale assertions, not
regressions: the test hard-codes *Year 4932, Month of Strife (10)* while the world is
correctly at *4933, Month of Mourning (11)*. It also fails while the backfill walks the
clock backwards through September. **Fix it first** — replace the frozen numbers with
relations (a valid clock, within N periods of GMT+8) — because everything else's
credibility rests on the suite being green.

## What was completed this session

- **All thirteen Heir cards** rebuilt: 69 inherited `AUTO REFINEMENT` crutch rules
  removed, canon-complexity blocks added, claims audit (`tools/audit_heir_claims.py`)
  green, three wrong identities corrected.
- **Voice gate instrument fixed**: deterministic retries (seed per attempt), exhaustion
  counted as a skip not a 45/25 score, dated reports (`--report`), `--debug-exhausted`.
  Last full run: **45/50 scored (90 %), 1 skip**. Aglaea 3/4 (one 22-style line),
  Hysilens 2/4 (two 78s) — both still open, near-misses on register.
- **Four canon decisions** settled against sources (Castorice's twin is **Polyxia, a
  sister**; Hyacine's "unnamed Heir" descent removed; Mydei's Gorgo/Eurypon kept
  ambiguous and said so; Castorice's famous line is a quotation, not a script).
- **UI restyled** to the in-game *As I've Written* book (`src/ui_theme.py`,
  `docs/UI-AIW.md`): app chrome, every Streamlit widget, Eternal Page menu, galgame
  panel. Rendered and inspected, not just compiled. Motion audit: **0 pixels changed**
  over 3 s at idle on the Eternal Page.
- **World operations**: calendar verified against GMT+8 by comparing the stored clock
  with `WorldClock.from_gmt8()`; ten stale engines found and stopped; engine guard
  added (with a liveness check that cannot kill its subject — `os.kill(pid, 0)` on
  Windows is `TerminateProcess`); jittered cadence (`AMP_WORLD_JITTER`, default 1.8).
- **Lore**: 7 days by catch-up + 35 by backfill. The backfill anomaly is in all
  thirteen Heirs' memories as a `world` memory (importance 4). Collective memory
  logging: `tools/log_collective_memory.py` (40 memories per Heir at first snapshot).
- **Checkpoints**: `tools/checkpoint_world.py` (saving half; `--list`, `--keep`,
  `restore()` — restore deliberately unproven, no lock/integrity check).
- **Lorebook**: `src/knowledge/lorebook.py` + `tools/test_lorebook.py` (17 checks),
  **not wired** into retrieval.
- **Research**: `docs/EXTERNAL-RESEARCH.md` — firefly-skill, Firefly-Companion-AI,
  Cyrene-Agent, SillyTavern lorebooks. Voice cloning **rejected** on consent/licensing.

## Next, in the order I would take them

1. **Repair `test_sanctuary_live`** (relational clock assertions).
2. **Admin checkpoint panel** — list → confirm → restore in the admin console, then
   **boot the real UI** (`streamlit run` + Playwright) rather than trusting compile.
3. **Aglaea + Hysilens gate**, then a full 13-Heir re-run once the GPU is free.
4. **Period-aware day generation** — `run_day()` advances a whole day in one
   generation, so prose can still put an Heir at work at Curtain-Fall.
5. **Phone app** — it loads the same network UI, so the AIW theme reaches it through
   the app; the work is verifying the new widgets at 360 px and that the checkpoint
   panel is reachable, not new Java.
6. **Lorebook wiring** in front of vector retrieval, with retrieval tests in view.

## Obstructions, unchanged

- **One GPU, one writer**: the backfill owns it; a 27B judge against a 14B generator
  produces numbers I would not defend.
- **No breakpoint snapshot exists** for the world state (only an Aug 11 memory backup),
  so the earliest backfilled days carry October's bonds and projects. Permanent; the
  memory note is the mitigation.
- **Restore is unproven by instruction** — any UI must say so in the interface.
- **Session room** was exhausted; work was stopped at the retrace point rather than
  half-done.

## Authority for the next session

See the "Operator authority (granted 2026-10-28, standing)" section in
`.cursor/rules/amphoreus-workflow.mdc`: it lists what may be done without asking
(cards, gate, lore, world start/stop, checkpoints, theme, commit-and-push), what still
needs a fresh word (voice cloning, deleting assets, renaming records, changing the pass
bars, settling conflicting canon), and the false claims that have already cost time.

---

## Update — 2026-10-29 00:20 (same session, continued)

Everything below the "Next" list in the original note has moved. Current truth:

- **Suites: 1878 passed, 0 failed across 29 suites** (`python tools/run_all_tests.py`).
- **`test_sanctuary_live` repaired** — 163/163. It froze Year 4932 / Month of Strife and
  failed whenever the world legitimately advanced; it now asserts relations (plausible
  year, month in range, overlay == `WorldClock.from_gmt8()`, sim untouched).
- **Admin checkpoint panel built and proven in a booted app** — Control Panel lists the
  last five, takes one on demand, and gates Restore behind a confirmation box with the
  warning above it. Verified by `streamlit run src/ui_app.py --server.port 8502` plus
  Chromium sign-in; zero console errors.
- **The handset view was broken and is fixed** — the sidebar was forced `expanded`, so at
  360 px it lay over the content and intercepted every tap (Playwright could not click
  one tab). Now `"auto"`; verified at 360×740 with a mobile UA: nine tabs, no
  horizontal overflow, checkpoint section reachable, zero console errors.
- **Night was already gated** — `is_rest_time()` covers Curtain-Fall and Entry Hour and
  `run_day()` returns before Heir speech, errands or projects. My "period-aware day"
  queue item rested on a misreading. The real defect was the night branch doing
  `return [night]` and dropping the hour's facts; it now returns `lines + [night]`.
- **The canon-quote check only knew the current scene** — Aglaea answered with a verbatim
  `chapter-03` line and scored 22 instead of being refused. A cached global corpus per
  Heir now feeds the check. **Full gate: 48 of 49 scored (98 %), one skipped**; Aglaea
  and Hysilens both at their best.
- **The lorebook is wired** into `ContextBuilder.retrieve()` — pinned entries first,
  vector results filling the budget, `AMP_LOREBOOK=0` to disable. 23 checks.
- **Reports are unique per run** (`…-YYYY-MM-DDTHHMM.md`), so a second run on the same
  day no longer replaces the first.
- **Backfill completed** — 35 days written (done 21:05), chronicle 4399+ lines,
  **73 distinct in-world days**, engine running at `--interval 900 --catch-up`, clock
  verified in sync with GMT+8.

**Still open:** Cyrene (78), Evernight (58) and Hysilens (78) — register near-misses, not
defects. Nothing else from the earlier list is outstanding.
