"""
auto_cycle.py — automated training-cycle conductor for the style standard.

The loop (each cycle):
  1. RUN the style test on the target Heirs (subprocess; the report is the
     authoritative result).
  2. PARSE the report -> per-Heir pass rate, avg style/content, failed cases.
  3. GATE: every Heir's pass rate >= --pass-target (default 85%).
  4. MET  -> log SUCCESS and finish.
  5. NOT  -> for each failing Heir, ASK the refine model to write concrete
     voice rules from that Heir's failed cases, EMBED them into the card
     (an idempotent "AUTO REFINEMENT" block in the VOICE section), bump
     best-of if a Heir keeps failing, and RE-RUN the failing Heirs next cycle.
     Cap at --max-cycles.

This is the "keep cycling until everyone overpasses 85/60" loop, automated.

USAGE
-----
    python tools/auto_cycle.py --model gemma3:27b --judge-model qwen2.5:14b-instruct --limit 4
    python tools/auto_cycle.py --heirs cipher,cyrene --once        # single assessment
    python tools/auto_cycle.py --best-of-start 5 --best-of-max 7 --max-cycles 4

NOTES
-----
- The judge is held CONSTANT (--judge-model) so model comparisons stay fair.
- RAM constraint: gemma3:27b occupies ~11.5 GB, so it is used for the Heir,
  the judge, AND the refinement (a single-model standard). The previously
  calibrated qwen judge cannot coexist with gemma3 in 31.4 GB of RAM.
- One run is serialized by the same named-mutex the test tool uses, so two
  cycles cannot collide.
- Refinement only touches the failing Heirs' cards (idempotent, no drift).
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PYTHON = sys.executable
TEST = ROOT / "tools" / "test_dialogue_style.py"
REPORT = ROOT / "docs" / "RESEMBLANCE-STYLE-REPORT.md"
LOG = ROOT / "docs" / "AUTO-CYCLE-LOG.md"
CARDS = ROOT / "src" / "characters"

REFINE_SYSTEM = (
    "You are a dialogue-voice coach for an AI character sanctuary. Your job is "
    "to help a character's model sound EXACTLY like the original character — "
    "same rhythm, same length, same tics, same register. You write rules about "
    "HOW to speak, never about what to say."
)

# --------------------------------------------------------------------------- #
# Report parsing
# --------------------------------------------------------------------------- #
ROW_RE = re.compile(
    r"^\|\s*(.+?)\s+\(([\w-]+)\)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)%\s*\|$"
)
FAIL_RE = re.compile(r"^-\s*style\s+(\d+)\s*/\s*content\s+(\d+)\s*→\s*canon ref\s*(.*?)\s*→\s*act\s*(.*)$")


def parse_report(path: Path = REPORT) -> dict:
    """Return {heir_id: {"name", "total", "pass", "avg_style", "avg_content",
    "pass_rate", "fails": [(style, content, ref, act), ...]}}"""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    result = {}
    current = None
    for line in text.splitlines():
        m = ROW_RE.match(line)
        if m:
            name, cid, total, passed, avg_s, avg_c, rate = m.groups()
            result[cid] = {
                "name": name, "total": int(total), "pass": int(passed),
                "avg_style": int(avg_s), "avg_content": int(avg_c),
                "pass_rate": int(rate), "fails": [],
            }
            current = cid
            continue
        m = FAIL_RE.match(line.strip())
        if m and current:
            result[current]["fails"].append(
                (int(m.group(1)), int(m.group(2)), m.group(3).strip(), m.group(4).strip())
            )
    return result


# --------------------------------------------------------------------------- #
# Card refinement (idempotent AUTO REFINEMENT block in the VOICE section)
# --------------------------------------------------------------------------- #
AUTO_MARK = "\n\nAUTO REFINEMENT (written by the cycle conductor from your failed cases):"
AUTO_RE = re.compile(r"\n\nAUTO REFINEMENT \(written by the cycle conductor.*$", re.S)


def embed_auto_refinement(cid: str, rules: list) -> bool:
    path = CARDS / f"{cid}.json"
    if not path.exists():
        return False
    card = json.loads(path.read_text(encoding="utf-8"))
    sp = card.get("prompts", {}).get("system_prompt", "")
    cleaned = AUTO_RE.sub("", sp).rstrip()
    block = AUTO_MARK + "\n" + "\n".join(f"- {r}" for r in rules)
    new_sp = cleaned + block
    if new_sp == sp:
        return False
    card["prompts"]["system_prompt"] = new_sp
    path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def strip_auto_refinement(cid: str) -> bool:
    path = CARDS / f"{cid}.json"
    if not path.exists():
        return False
    card = json.loads(path.read_text(encoding="utf-8"))
    sp = card.get("prompts", {}).get("system_prompt", "")
    cleaned = AUTO_RE.sub("", sp).rstrip()
    if cleaned == sp:
        return False
    card["prompts"]["system_prompt"] = cleaned
    path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


# --------------------------------------------------------------------------- #
# Refinement generation (ask the model to write voice rules from its failures)
# --------------------------------------------------------------------------- #
_NOISE_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*%|average|approximately|roughly|about\s+\d+|over half|"
    r"at least \d+%|\d+% of|words per sentence|words per line|in \d+%|"
    r"around \d+|~\d+)",
    re.I,
)
# Rules that prescribe overusing a motif/catchphrase (caused spamming before)
# or generic terse advice that would apply to ANY Heir (homogenizes voices).
_SPAM_RE = re.compile(
    r"(frequently reference|even when irrelevant|always mention|regardless of|"
    r"in every line|every response|no matter what|repeatedly (say|use)|"
    r"don't forget to (say|mention))",
    re.I,
)
_GENERIC_RE = re.compile(
    r"(keep it short|keep (sentences|lines) (concise|short)|use interjections|"
    r"trail off|avoid (long|lengthy|complex|elaborate)|don't be (verbose|wordy)|\buse ellipses\b)",
    re.I,
)


def _is_noise_rule(rule: str) -> bool:
    """Reject statistical rules (percentages/averages), catchphrase-spam rules,
    and generic terse advice — refinement must keep only UNIQUE per-character
    behaviors grounded in the canon."""
    return bool(_NOISE_RE.search(rule) or _SPAM_RE.search(rule) or _GENERIC_RE.search(rule))


def write_refinement_rules(llm, heir_id: str, info: dict, stats: dict, exemplars: list) -> list:
    fails = info.get("fails") or []
    case_txt = "\n".join(
        f'- canon ref: "{r}" -> model said: "{a}" (style {s}, content {c})'
        for s, c, r, a in fails[:6]
    ) or "(no failed cases parsed)"
    ex_txt = "\n".join(f'- "{e}"' for e in exemplars[:5]) or "(none)"
    profile = (
        f"average {stats.get('avg_words_per_sentence', 8):.1f} words/sentence; "
        f"{stats.get('pct_short_sentences_leq6', 40):.1f}% very short (<=6 words); "
        f"trails off '...' in {stats.get('pct_lines_ellipsis', 20):.1f}% of lines; "
        f"asks questions in {stats.get('pct_lines_question', 20):.1f}%; "
        f"emphatic in {stats.get('pct_lines_exclaim', 15):.1f}%."
    )
    user = (
        f"The character is {info['name']} ({heir_id}). Their measured delivery: "
        f"{profile}\n\n"
        f"Their real canon lines:\n{ex_txt}\n\n"
        f"The style test FAILED on these cases — the model's reply did not sound "
        f"like {info['name']} (style = delivery similarity, content = scene fit):\n"
        f"{case_txt}\n\n"
        "Analyse the specific DELIVERY mistakes and write 4-6 crisp, concrete "
        "voice rules that would fix them. Every rule must name a habit that is "
        "UNIQUE to {info['name']} and GROUNDED IN THE CANON LINES above — a "
        "specific tic, word, interjection, rhythm, or pattern that DISTINGUISHES "
        "{info['name']} from every other Heir. Never write generic advice that "
        "would apply to any terse character (e.g. 'trail off with ...', 'keep it "
        "short', 'use interjections') — those are forbidden. Never prescribe "
        "repeating a motif or catchphrase. If it is not in the canon lines, do "
        "not invent it. Every rule must be something you DO in a single line. "
        "One rule per line, short and actionable, no numbering, no preamble."
    )
    reply = llm.chat(
        [{"role": "system", "content": REFINE_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.4, max_tokens=400,
    )
    rules = [ln.strip().lstrip("-•*0123456789. ") for ln in reply.splitlines()
             if ln.strip() and not ln.strip().lower().startswith(("rule", "here"))]
    # Hard filter: drop any statistical/noise rule; keep only per-line behaviors.
    rules = [r for r in rules if len(r) > 3 and not _is_noise_rule(r)][:6]
    return rules


# --------------------------------------------------------------------------- #
# The conductor
# --------------------------------------------------------------------------- #
def run_test(heir_ids, args, limit=None, best_of=None) -> int:
    cmd = [PYTHON, str(TEST), "--limit", str(limit or args.limit),
           "--best-of", str(best_of or args.best_of),
           "--temp", str(args.temp),
           "--model", args.model,
           "--style-bar", str(args.style_bar),
           "--content-bar", str(args.content_bar)]
    if args.judge_model:
        cmd += ["--judge-model", args.judge_model]
    if heir_ids:
        cmd += ["--heirs", ",".join(heir_ids)]
    print(f"    $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return proc.returncode


def main():
    ap = argparse.ArgumentParser(description="Automated style-cycle conductor.")
    ap.add_argument("--heirs", default="", help="target Heirs (default: all 13)")
    ap.add_argument("--limit", type=int, default=4, help="cases per Heir per cycle")
    ap.add_argument("--best-of-start", type=int, default=5, dest="best_of")
    ap.add_argument("--best-of-max", type=int, default=7, dest="best_of_max")
    ap.add_argument("--temp", type=float, default=0.3)
    ap.add_argument("--model", default="gemma3:27b", help="Heir model (chat model, not a reasoning model)")
    ap.add_argument("--judge-model", default="gemma3:27b",
                    help="judge model. Kept CONSTANT during a run; defaults to the "
                         "Heir model because gemma3 cannot coexist with the qwen "
                         "judge in RAM")
    ap.add_argument("--refine-model", default="gemma3:27b", help="model that writes voice rules")
    ap.add_argument("--style-bar", type=int, default=85)
    ap.add_argument("--content-bar", type=int, default=60)
    ap.add_argument("--pass-target", type=int, default=85,
                    help="per-Heir pass-rate gate (percent of cases passing)")
    ap.add_argument("--max-cycles", type=int, default=4)
    ap.add_argument("--once", action="store_true", help="single assessment, no refinement")
    # Staged escalation (raise the bars after the gate passes) with an
    # overfitting guard: validate on a DIFFERENT (larger) case sample first.
    ap.add_argument("--escalate", action="store_true",
                    help="after the gate passes, validate on a different sample; if "
                         "not overfit, raise the bars (style -> 90, content -> 65 -> 70)")
    ap.add_argument("--escalate-style", type=int, default=90)
    ap.add_argument("--escalate-content", type=int, default=65)
    ap.add_argument("--escalate-content2", type=int, default=70)
    ap.add_argument("--validate-limit", type=int, default=0,
                    help="overfitting check: re-run with this larger limit before "
                         "escalating (default: 2x --limit)")
    ap.add_argument("--overfit-tolerance", type=int, default=10,
                    help="allowed pass-rate drop (percentage points) on the validation "
                         "sample before escalation is refused")
    args = ap.parse_args()

    from src.core.heir_folders import HEIR_FOLDERS
    from src.core.llm_client import LLMClient
    from src.knowledge.kb_builder import CHARACTER_ALIASES
    from tools.test_dialogue_resemblance import sample_canon_lines

    all_heirs = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)
    targets = list(all_heirs)
    refine_llm = LLMClient(model=args.refine_model)

    log = [
        f"# Auto-cycle log — {time.strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"- Heir model: `{args.model}` · judge model: `{args.judge_model}` (constant)",
        f"- Gate: per-Heir pass rate ≥ {args.pass_target}% (style ≥ {args.style_bar} AND content ≥ {args.content_bar})",
        f"- Best-of: start {args.best_of}, max {args.best_of_max} · limit {args.limit}/Heir/cycle · max {args.max_cycles} cycles",
        "",
    ]

    cycle = 0
    best_of_start = args.best_of
    final_outcome = None
    final_reason = ""
    while cycle < args.max_cycles:
        cycle += 1
        print(f"\n{'='*70}\nCYCLE {cycle} — targets: {len(targets)} Heirs  "
              f"(bars: style ≥ {args.style_bar}, content ≥ {args.content_bar})")
        rc = run_test(targets, args)
        if rc != 0:
            print("  ! test run failed (exit", rc, ") — aborting.")
            log.append(f"## Cycle {cycle} — FAILED to run (exit {rc})")
            break

        results = parse_report()
        if not results:
            print("  ! could not parse the report — aborting.")
            break

        # Evaluate only the Heirs we targeted this cycle.
        evaluated = {cid: r for cid, r in results.items() if cid in targets}
        if not evaluated:
            print("  ! report has no rows for the targets — aborting.")
            break

        line = "| Heir | pass | rate | avg style | avg content | status |"
        line += "\n|---|---:|---:|---:|---:|---|"
        failing = []
        for cid, r in evaluated.items():
            ok = r["pass_rate"] >= args.pass_target
            status = "PASS" if ok else "FAIL"
            if not ok:
                failing.append(cid)
            line += f"\n| {r['name']} | {r['pass']}/{r['total']} | {r['pass_rate']}% | {r['avg_style']} | {r['avg_content']} | {status} |"
            print(f"    {r['name']:>28}: {r['pass']}/{r['total']} ({r['pass_rate']}%) avg style {r['avg_style']} — {status}")

        log.append(f"## Cycle {cycle} (best-of {args.best_of}; bars style≥{args.style_bar}, content≥{args.content_bar})")
        log.append(line)
        log.append("")

        # ---- Gate passed ------------------------------------------------- #
        if not failing:
            if not args.escalate or (
                args.style_bar >= args.escalate_style
                and args.content_bar >= args.escalate_content2
            ):
                print("\n🎉 ALL TARGETS PASSED the gate.")
                final_outcome = "SUCCESS"
                final_reason = (f"all targets above the gate "
                                f"(style ≥ {args.style_bar}, content ≥ {args.content_bar})")
                log.append(f"**RESULT: SUCCESS — {final_reason}.**")
                break

            # Overfitting guard: validate on a DIFFERENT (larger) sample.
            vlimit = args.validate_limit or (args.limit * 2)
            print(f"\n  Gate passed at style {args.style_bar} / content {args.content_bar}.")
            print(f"  Overfitting check: re-running on a different sample (limit {vlimit})…")
            rc = run_test(targets, args, limit=vlimit)
            vavg = 0.0
            if rc == 0:
                vres = parse_report()
                vrates = [r["pass_rate"] for cid, r in vres.items() if cid in targets]
                vavg = (sum(vrates) / len(vrates)) if vrates else 0.0
                print(f"  Validation pass rate (limit {vlimit}): {vavg:.0f}% "
                      f"(gate {args.pass_target}%, tolerance {args.overfit_tolerance}pp)")
                log.append(f"- Overfitting check (limit {vlimit}): validation {vavg:.0f}% "
                           f"(gate {args.pass_target}%, tolerance {args.overfit_tolerance}pp)")
            else:
                print("  ! validation run failed — treated as overfit risk.")
                log.append("- Overfitting check: validation run FAILED.")

            if vavg >= args.pass_target - args.overfit_tolerance:
                new_style = args.escalate_style
                new_content = (args.escalate_content
                               if args.content_bar < args.escalate_content
                               else args.escalate_content2)
                if new_content == args.content_bar and new_style == args.style_bar:
                    print("\n🎉 ALL TARGETS PASSED the gate (no higher bars configured).")
                    final_outcome = "SUCCESS"
                    final_reason = (f"all targets above the gate "
                                    f"(style ≥ {args.style_bar}, content ≥ {args.content_bar})")
                    log.append(f"**RESULT: SUCCESS — {final_reason}.**")
                    break
                print(f"  ✅ Not overfit — escalating bars to style ≥ {new_style}, "
                      f"content ≥ {new_content}.")
                args.style_bar, args.content_bar = new_style, new_content
                log.append(f"- **ESCALATED to style ≥ {new_style}, content ≥ {new_content}** "
                           f"(validation ok)")
                cycle = 0  # restart the cycle budget at the new bars
                targets = list(all_heirs)
                args.best_of = best_of_start
                continue
            print(f"\n  ⚠️ Overfitting risk: validation dropped to {vavg:.0f}% — keeping bars "
                  f"at style ≥ {args.style_bar}, content ≥ {args.content_bar} (no escalation).")
            final_outcome = "SUCCESS"
            final_reason = (f"all targets above the gate at style ≥ {args.style_bar}, "
                            f"content ≥ {args.content_bar} — escalation refused "
                            f"(overfit guard: validation {vavg:.0f}%)")
            log.append(f"**RESULT: SUCCESS at style ≥ {args.style_bar}, content ≥ {args.content_bar} "
                       f"— escalation skipped (overfit guard: validation {vavg:.0f}%).**")
            break

        if args.once:
            print("\n(--once: assessment only, no refinement.)")
            log.append("**RESULT: assessment only (--once); failing Heirs listed above.**")
            LOG.write_text("\n".join(log), encoding="utf-8")
            return 1

        # Refine each failing Heir: ask the model to write voice rules, embed.
        print(f"\n  Refining {len(failing)} Heirs…")
        for cid in failing:
            info = evaluated[cid]
            card_path = CARDS / f"{cid}.json"
            if not card_path.exists():
                continue
            card = json.loads(card_path.read_text(encoding="utf-8"))
            stats = ((card.get("speech", {}) or {}).get("style_measured") or {}).get("stats", {})
            wpl = stats.get("avg_words_per_line") or 14
            folder = ROOT / HEIR_FOLDERS.get(cid, cid)
            exemplars = sample_canon_lines(
                folder, CHARACTER_ALIASES.get(cid, [cid]), 5,
                max_words=max(12, int(wpl * 1.6)),
            )
            try:
                rules = write_refinement_rules(refine_llm, cid, info, stats, exemplars)
            except Exception as e:
                print(f"    ! {cid}: refinement LLM error {e}")
                rules = []
            if rules:
                embed_auto_refinement(cid, rules)
                print(f"    ✓ {cid}: embedded {len(rules)} auto-refinement rules")
                log.append(f"- {cid}: refined ({len(rules)} rules: {'; '.join(rules[:3])}…)")
            else:
                print(f"    = {cid}: no rules produced (kept as-is)")
                log.append(f"- {cid}: no rules produced")

        # Bump best-of if we have not yet hit the cap.
        if args.best_of < args.best_of_max:
            args.best_of += 1
            print(f"  best-of -> {args.best_of}")
        targets = failing

    if final_outcome is None:
        final_outcome = "FAILED"
        final_reason = f"max cycles ({args.max_cycles}) reached"
        print(f"\n❌ Max cycles ({args.max_cycles}) reached; still failing: {targets}")
        log.append(f"**RESULT: FAILED after {args.max_cycles} cycles; still failing: {targets}**")

    # ---- FINAL CHEAT-FREE FULL RE-TEST: ALL Heirs, no matter the outcome ----
    if not args.once:
        print(f"\n{'='*70}\nFINAL CHEAT-FREE FULL RE-TEST — all {len(all_heirs)} Heirs "
              f"(bars: style ≥ {args.style_bar}, content ≥ {args.content_bar})")
        rc = run_test(all_heirs, args)
        if rc == 0:
            fres = parse_report()
            if fres:
                ftable = "| Heir | pass | rate | avg style | avg content | status |"
                ftable += "\n|---|---:|---:|---:|---:|---|"
                fpass_all = True
                for cid in all_heirs:
                    if cid not in fres:
                        continue
                    r = fres[cid]
                    ok = r["pass_rate"] >= args.pass_target
                    fpass_all = fpass_all and ok
                    ftable += (f"\n| {r['name']} | {r['pass']}/{r['total']} | {r['pass_rate']}% | "
                               f"{r['avg_style']} | {r['avg_content']} | "
                               f"{'PASS' if ok else 'FAIL'} |")
                log.append("")
                log.append("## FINAL CHEAT-FREE FULL RE-TEST (all Heirs)")
                log.append(ftable)
                log.append("")
                log.append(f"**FINAL OUTCOME: {final_outcome}** — {final_reason}")
                print("\n" + ftable)
                print(f"\nFinal outcome: {final_outcome} — {final_reason}")
        else:
            log.append("")
            log.append(f"**FINAL CHEAT-FREE RE-TEST FAILED to run (exit {rc}); "
                       f"outcome: {final_outcome} — {final_reason}**")

    LOG.write_text("\n".join(log), encoding="utf-8")
    return 0 if final_outcome == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
