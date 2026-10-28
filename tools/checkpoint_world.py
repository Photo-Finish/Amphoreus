# -*- coding: utf-8 -*-
"""Checkpoint the world state and the collective memory - and restore it.

    python tools/checkpoint_world.py --dry-run
    python tools/checkpoint_world.py --keep 8
    python tools/checkpoint_world.py --list
    python tools/checkpoint_world.py --restore 2026-10-28T20-16 --yes

Saving is the half the operator asked for. **Restoring exists but is not proven**:
there is no lock, no integrity check, and no test that a restored world equals the
one that was saved. The manifest records exactly what was captured so a future
restore has something to check against. The admin console can call `restore()`
directly; that is the door left open, not a guarantee behind it.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

OUT = ROOT / "world_runtime" / "checkpoints"
FILES = ("bond.json", "history.jsonl", "memories.jsonl", "preferences.json")


def heir_folder(store, cid: str) -> Path:
    for name in ("_folder", "folder", "heir_folder"):
        fn = getattr(store, name, None)
        if callable(fn):
            try:
                return Path(fn(cid)).resolve()
            except Exception:
                pass
    return Path(store.memory_root).resolve() / cid


def _plan() -> tuple[Path, list[tuple[Path, str]]]:
    from src.core.heir_folders import HEIR_FOLDERS
    from src.core.memory_store import MemoryStore

    store = MemoryStore()
    plan: list[tuple[Path, str]] = []
    state = (ROOT / "world_runtime" / "world_state.json").resolve()
    if state.is_file():
        plan.append((state, "world_state.json"))
    for cid in sorted(HEIR_FOLDERS):
        folder = heir_folder(store, cid)
        for name in FILES:
            src = folder / name
            if src.is_file():
                plan.append((src, f"heirs/{cid}/{name}"))
    return ROOT, plan


def list_checkpoints() -> list[Path]:
    if not OUT.is_dir():
        return []
    return sorted((d for d in OUT.iterdir() if d.is_dir()), key=lambda d: d.name)


def restore(name: str) -> dict:
    """Copy a checkpoint back over the live state. Unverified by design.

    Callable from the admin console. It writes only the files the manifest names,
    so a partial snapshot restores partially rather than half-destroying a Heir.
    """
    src_dir = OUT / name
    manifest = src_dir / "manifest.json"
    if not manifest.is_file():
        raise FileNotFoundError(f"no manifest in {src_dir}")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    restored = 0
    for row in data.get("files", []):
        src = src_dir / row["to"]
        dst = ROOT / row["from"]
        if not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        restored += 1
    return {"checkpoint": name, "restored": restored, "at": data.get("at")}


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
        snaps = list_checkpoints()
        if not snaps:
            print("no checkpoints yet")
        for d in snaps:
            manifest = d / "manifest.json"
            note = ""
            if manifest.is_file():
                try:
                    m = json.loads(manifest.read_text(encoding="utf-8"))
                    note = f"  {m.get('clock','')}  {len(m.get('files', []))} files"
                except Exception:
                    note = "  (manifest unreadable)"
            print(f"  {d.name}{note}")
        return 0

    if args.restore:
        if not args.yes:
            print(f"Would restore {args.restore} over the live world. Re-run with --yes.")
            return 1
        print(json.dumps(restore(args.restore), ensure_ascii=False))
        return 0

    root, plan = _plan()
    from src.world.sanctuary_clock import GMT8, WorldClock

    stamp = datetime.now(GMT8).strftime("%Y-%m-%dT%H-%M")
    target = Path(args.out).resolve() if args.out else OUT / stamp
    total = sum(p.stat().st_size for p, _ in plan)
    print(f"clock {WorldClock.from_gmt8().format_short()}")
    print(f"{len(plan)} file(s), {total / 1024:.0f} KB -> {target.name}")
    if args.dry_run:
        for src, rel in plan[:8]:
            print(f"  {src} -> {rel}")
        if len(plan) > 8:
            print(f"  ... and {len(plan) - 8} more")
        return 0

    for src, rel in plan:
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    manifest = {
        "at": datetime.now(GMT8).isoformat(timespec="seconds"),
        "clock": WorldClock.from_gmt8().format_short(),
        "files": [{"from": str(src.relative_to(ROOT)).replace("\\", "/"), "to": rel,
                   "bytes": src.stat().st_size} for src, rel in plan],
        "total_bytes": total,
        "note": "saving half: no lock, no restore verification, no integrity proof",
    }
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print(f"wrote {target} ({len(plan)} files)")

    if 0 < args.keep < 1000:
        snaps = list_checkpoints()
        for old in snaps[: max(0, len(snaps) - args.keep)]:
            shutil.rmtree(old, ignore_errors=True)
            print(f"pruned {old.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
