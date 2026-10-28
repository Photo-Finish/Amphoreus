# -*- coding: utf-8 -*-
"""Checkpoints of the world state and the collective memory.

The **saving half** is what the operator asked for and is exercised every time
`take()` runs. `restore()` exists so an administrator has a door, and it is
**unproven**: there is no lock, no integrity check, and no test that a restored world
equals the one saved. The manifest records every file, its origin and size, so a
future restore has something to check against — and so a partial snapshot restores
partially instead of half-destroying a Heir.

    from src.world import checkpoints
    checkpoints.take(keep=6)
    checkpoints.list_checkpoints()
    checkpoints.restore("2026-10-28T20-20")      # unverified by design
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "world_runtime" / "checkpoints"
FILES = ("bond.json", "history.jsonl", "memories.jsonl", "preferences.json")


def _heir_folder(store, cid: str) -> Path:
    for name in ("_folder", "folder", "heir_folder"):
        fn = getattr(store, name, None)
        if callable(fn):
            try:
                return Path(fn(cid)).resolve()
            except Exception:
                pass
    return Path(store.memory_root).resolve() / cid


def plan() -> list[tuple[Path, str]]:
    """(absolute source, relative destination) for everything a checkpoint holds."""
    from src.core.heir_folders import HEIR_FOLDERS
    from src.core.memory_store import MemoryStore

    store = MemoryStore()
    rows: list[tuple[Path, str]] = []
    state = (ROOT / "world_runtime" / "world_state.json").resolve()
    if state.is_file():
        rows.append((state, "world_state.json"))
    for cid in sorted(HEIR_FOLDERS):
        folder = _heir_folder(store, cid)
        for name in FILES:
            src = folder / name
            if src.is_file():
                rows.append((src, f"heirs/{cid}/{name}"))
    return rows


def list_checkpoints() -> list[Path]:
    if not OUT.is_dir():
        return []
    return sorted((d for d in OUT.iterdir() if d.is_dir()), key=lambda d: d.name)


def take(*, keep: int = 0, out: Path | None = None) -> Path:
    """Write a checkpoint now. Returns the directory it wrote."""
    from src.world.sanctuary_clock import GMT8, WorldClock

    rows = plan()
    stamp = datetime.now(GMT8).strftime("%Y-%m-%dT%H-%M")
    target = Path(out).resolve() if out else OUT / stamp
    total = 0
    for src, rel in rows:
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        total += src.stat().st_size
    manifest = {
        "at": datetime.now(GMT8).isoformat(timespec="seconds"),
        "clock": WorldClock.from_gmt8().format_short(),
        "files": [{"from": str(src.relative_to(ROOT)).replace("\\", "/"), "to": rel,
                   "bytes": src.stat().st_size} for src, rel in rows],
        "total_bytes": total,
        "note": "saving half: no lock, no restore verification, no integrity proof",
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    if 0 < keep < 1000:
        snaps = list_checkpoints()
        for old in snaps[: max(0, len(snaps) - keep)]:
            shutil.rmtree(old, ignore_errors=True)
    return target


def restore(name: str) -> dict:
    """Copy a checkpoint back over the live state. **Unverified by design.**

    Writes only the files named in the manifest, so a partial snapshot restores
    partially rather than leaving a Heir half-overwritten.
    """
    src_dir = OUT / name
    manifest = src_dir / "manifest.json"
    if not manifest.is_file():
        raise FileNotFoundError(f"no manifest in {src_dir}")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    rows: Iterable[dict] = data.get("files", [])
    restored = 0
    for row in rows:
        src = src_dir / row["to"]
        dst = ROOT / row["from"]
        if not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        restored += 1
    return {"checkpoint": name, "restored": restored, "at": data.get("at")}
