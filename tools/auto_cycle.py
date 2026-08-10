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
        "voice rules that would fix them: rhythm, sentence length, punctuation "
        "(ellipsis, exclamation, trailing), word simplicity, interjections, "
        "register — never about content. One rule per line, short and actionable, "
        "no numbering, no preamble."
    )
    reply = llm.chat(
        [{"role": "system", "content": REFINE_SYSTEM}, {"role": "user", "content": user}],
        temperature=0.4, max_tokens=400,
    )
    rules = [ln.strip().lstrip("-•*0123456789. ") for ln in reply.splitlines()
             if ln.strip() and not ln.strip().lower().startswith(("rule", "here"))]
    return [r for r in rules if len(r) > 3][:6]


# --------------------------------------------------------------------------- #
# The conductor
# --------------------------------------------------------------------------- #
def run_test(heir_ids, args) -> tuple:
    cmd = [PYTHON, str(TEST), "--limit", str(args.limit),
           "--best-of", str(args.best_of),
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
    ap.add_argument("--model", default="qwen2.5:14b-instruct", help="Heir model")
    ap.add_argument("--judge-model", default="qwen2.5:14b-instruct", help="judge model (keep constant!)")
    ap.add_argument("--refine-model", default="qwen2.5:14b-instruct", help="model that writes voice rules")
    ap.add_argument("--style-bar", type=int, default=85)
    ap.add_argument("--content-bar", type=int, default=60)
    ap.add_argument("--pass-target", type=int, default=85,
                    help="per-Heir pass-rate gate (percent of cases passing)")
    ap.add_argument("--max-cycles", type=int, default=4)
    ap.add_argument("--once", action="store_true", help="single assessment, no refinement")
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

    for cycle in range(1, args.max_cycles + 1):
        print(f"\n{'='*70}\nCYCLE {cycle} — targets: {len(targets)} Heirs")
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

        log.append(f"## Cycle {cycle} (best-of {args.best_of})")
        log.append(line)
        log.append("")

        if not failing:
            print("\n🎉 ALL TARGETS PASSED the gate.")
            log.append("**RESULT: SUCCESS — all targets above the gate.**")
            LOG.write_text("\n".join(log), encoding="utf-8")
            return 0

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

    print(f"\n❌ Max cycles ({args.max_cycles}) reached; still failing: {targets}")
    log.append(f"**RESULT: FAILED after {args.max_cycles} cycles; still failing: {targets}**")
    LOG.write_text("\n".join(log), encoding="utf-8")
    return 1


if __name__ == "__main__":
    sys.exit(main())
