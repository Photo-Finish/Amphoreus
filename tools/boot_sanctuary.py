# -*- coding: utf-8 -*-
"""One-click Sanctuary boot used by launch_sanctuary.cmd.

Starts the interface first. Ollama and the world engine are background.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def main(argv: list[str] | None = None) -> int:
    from src.core.sanctuary_boot import (
        UI_URL,
        ensure_interface,
        find_python,
        last_ui_errors,
        open_browser,
        project_root,
        start_ollama_background,
        start_status_guard,
        start_world_engine,
        ui_healthy,
    )

    argv = list(argv if argv is not None else sys.argv[1:])
    skip_engine = "--no-engine" in argv
    skip_ollama = "--no-ollama" in argv
    skip_guard = "--no-guard" in argv
    no_browser = "--no-browser" in argv

    root = project_root()
    python = find_python(root)
    os.environ.setdefault("AMPHOREUS_ROOT", str(root))
    os.chdir(root)

    print("============================================================")
    print("  Project Amphoreus - The Sanctuary of the Chrysos Heirs")
    print("============================================================")

    os.environ.setdefault("SENSES_MODE", "unified")

    print("[1/4] Starting the interface...")

    def _tick(elapsed: float) -> None:
        print(f"      still starting... {int(elapsed)}s", flush=True)

    ok = ensure_interface(root, python, wait_s=90.0, on_tick=_tick)
    if not ok:
        print("      The interface did not answer on port 8501.")
        err = last_ui_errors(root)
        if err:
            print("      Last ui.log.err lines:")
            print(err)
        return 1
    print(f"      Ready at {UI_URL}")

    if not skip_engine:
        print("[2/4] World engine (background)...")
        try:
            start_world_engine(root, python)
            print("      Engine start requested.")
        except Exception as e:
            print(f"      Engine skipped ({e}). The page still opens.")
    else:
        print("[2/4] World engine skipped.")

    if not skip_ollama:
        print("[3/4] Ollama (background, does not block the page)...")
        start_ollama_background(root)
    else:
        print("[3/4] Ollama skipped.")

    if not skip_guard:
        print("[4/4] Public front door (github.io / tunnels, background)...")
        try:
            start_status_guard(root, python)
            print("      Status guard start requested.")
        except Exception as e:
            print(f"      Status guard skipped ({e}). Local UI still opens.")
    else:
        print("[4/4] Public front door skipped.")

    if not no_browser:
        open_browser()

    print("============================================================")
    print(f"  The Sanctuary is open: {UI_URL}")
    print("  Closing this window does not stop Streamlit.")
    print("============================================================")
    if ui_healthy():
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
