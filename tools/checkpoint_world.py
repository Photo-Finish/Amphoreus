# -*- coding: utf-8 -*-
"""CLI over `src.world.checkpoints`.

    python tools/checkpoint_world.py --dry-run
    python tools/checkpoint_world.py --keep 8
    python tools/checkpoint_world.py --list
    python tools/checkpoint_world.py --restore 2026-10-28T20-20 --yes

Saving is the half the operator asked for. Restoring exists so an administrator has
a door, and is **unproven**: no lock, no integrity check, no round-trip test.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world import checkpoints  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep", type=int, default=0)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--restore", default="")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if args.list:
        snaps = checkpoints.list_checkpoints()
        if not snaps:
            print("no checkpoints yet")
        for d in snaps:
            manifest = d / "manifest.json"
            note = ""
            if manifest.is_file():
                try:
                    m = json.loads(manifest.read_text(encoding="utf-8"))
                    note = f"  {m.get('clock', '')}  {len(m.get('files', []))} files"
                except Exception:
                    note = "  (manifest unreadable)"
            print(f"  {d.name}{note}")
        return 0

    if args.restore:
        if not args.yes:
            print(f"Would restore {args.restore} over the live world. Re-run with --yes.")
            return 1
        print(json.dumps(checkpoints.restore(args.restore), ensure_ascii=False))
        return 0

    rows = checkpoints.plan()
    total = sum(src.stat().st_size for src, _ in rows)
    print(f"{len(rows)} file(s), {total / 1024:.0f} KB")
    if args.dry_run:
        for src, rel in rows[:8]:
            print(f"  {src} -> {rel}")
        if len(rows) > 8:
            print(f"  ... and {len(rows) - 8} more")
        return 0
    target = checkpoints.take(keep=args.keep,
                              out=Path(args.out) if args.out else None)
    print(f"wrote {target} ({len(rows)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
