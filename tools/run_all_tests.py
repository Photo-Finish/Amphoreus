# -*- coding: utf-8 -*-
"""Run every offline suite and report one total.

    python tools/run_all_tests.py            # everything that needs no LLM
    python tools/run_all_tests.py -v         # show each suite's own output

Suites that need a live model or GPU are listed in NEEDS_BACKEND and skipped by
default — they are measurements, not regression tests, and running them costs
minutes of GPU time.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NEEDS_BACKEND = {
    "test_dialogue_style",       # gemma3:27b + a judge, ~40 minutes
    "test_dialogue_resemblance", # same
    "test_llm_client",           # talks to Ollama
}

SUM_RE = re.compile(r"(\d+) passed, (\d+) failed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    suites = sorted(p for p in (ROOT / "tools").glob("test_*.py")
                    if p.stem not in NEEDS_BACKEND)
    total_pass = total_fail = 0
    slow_or_missing: list[str] = []

    for path in suites:
        proc = subprocess.run([sys.executable, str(path)], cwd=ROOT,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=900)
        out = proc.stdout + proc.stderr
        m = SUM_RE.search(out)
        if args.verbose or not m:
            print(f"--- {path.name} ---")
            print(out.strip()[-1500:])
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
            total_pass += passed
            total_fail += failed
            flag = "ok  " if failed == 0 and proc.returncode == 0 else "FAIL"
            print(f"{flag} {path.stem:28s} {passed:4d} passed {failed:3d} failed")
        else:
            slow_or_missing.append(path.stem)
            print(f"???  {path.stem:28s} no summary (exit {proc.returncode})")

    print()
    print(f"TOTAL: {total_pass} passed, {total_fail} failed "
          f"across {len(suites) - len(slow_or_missing)} suites")
    if slow_or_missing:
        print("no summary from: " + ", ".join(slow_or_missing))
    print(f"skipped (need a live model): {', '.join(sorted(NEEDS_BACKEND))}")
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
