# -*- coding: utf-8 -*-
"""Offline checks for the style gate's own logic — no LLM, no GPU.

    python tools/test_style_gate.py

The gate is the instrument every voice claim rests on, and until now it had no
tests: the deterministic-retry bug lived here for weeks because nothing exercised
the filter path. These checks pin the behaviour that matters:

* a candidate is rejected for the right reason (degenerate, canon quote, repeat);
* a SHORT candidate is judged on exact repeats, not on near-duplicate ratios;
* exhaustion is a skip, never a `"..."` score;
* a fresh seed is passed per attempt (deterministic Ollama would otherwise
  return the same line forever).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        PASSED.append(name)
    else:
        FAILED.append(f"{name}" + (f"  [{detail}]" if detail else ""))


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "style_gate", ROOT / "tools" / "test_dialogue_style.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["style_gate"] = module
    spec.loader.exec_module(module)  # main() is guarded, so this only defines things
    return module


def main() -> int:
    gate = load_gate()

    print("== Degenerate replies ==")
    for text, expected in (("", True), ("...", True), ("…", True), ("  ", True),
                           ("Ah.", False), ("Hm. Fine.", False)):
        check(f"degenerate: {text!r} -> {expected}",
              gate.is_degenerate(text) is expected, repr(text))

    print("== Short lines are judged on repeats, not ratios ==")
    seen_lines = ["Stone. Good."]
    short = gate.is_run_repeat("Stone goods.", seen_lines, {}, {}, 1)
    check("a six-word-or-fewer line is not a near-duplicate", short is False)
    exact = gate.is_run_repeat("Stone. Good.", seen_lines, {}, {}, 1)
    check("an exact short repeat is still caught", exact is True)
    long_seen = ["The work is honest though the scale is careless"]
    long_new = gate.is_run_repeat(
        "The work is honest though the scale was careless", long_seen, {}, {}, 1)
    check("a long near-duplicate is still caught", long_new is True)

    print("== Canon quoting ==")
    canon = {"Kindly keep five paces distance..."}
    check("a canon line is refused",
          gate.is_quote_cheat("Kindly keep five paces distance...", canon) is True)
    check("a new line is allowed",
          gate.is_quote_cheat("Stand back, please.", canon) is False)

    print("== Trimming keeps voice discipline ==")
    trimmed = gate._trim_to_short('**Castorice**: "Stand back, please."')
    check("a name prefix is stripped", "Castorice" not in trimmed, trimmed)
    long_reply = "one two three four five six seven eight nine ten eleven twelve " \
                 "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty " \
                 "twentyone twentytwo"
    check("an over-long reply is trimmed", len(gate._trim_to_short(long_reply).split()) <= 22)

    print("== The harness never scores exhaustion ==")
    source = (ROOT / "tools" / "test_dialogue_style.py").read_text(encoding="utf-8")
    check("no literal '...' fallback is scored", 'candidates = ["..."]' not in source)
    check("exhaustion increments the skip counter", "skipped += 1" in source)
    check("the skip is reported per Heir", "skipped" in source and "skip_note" in source)

    print("== Retries draw a new sample ==")
    check("each attempt passes a seed", "seed=tries" in source)
    check("the diagnostic exists", "--debug-exhausted" in source)
    check("the report path is dated by default", "RESEMBLANCE-STYLE-REPORT-{__import__" in source)

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for name in FAILED:
        print(f"  FAIL {name}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
