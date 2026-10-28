# -*- coding: utf-8 -*-
"""Snapshot the collective memory of all thirteen Heirs, now and then.

    python tools/log_collective_memory.py                 # one snapshot
    python tools/log_collective_memory.py --every 3600    # keep logging hourly

Each snapshot is a timestamped JSON of every Heir's stored memories plus a short
markdown digest, under world_runtime/collective_memory/. Logging the collective
memory is not decoration: the world now generates days in batches, and the only
record of what the Heirs actually carry is that store.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

OUT = ROOT / "world_runtime" / "collective_memory"


def snapshot() -> Path:
    from src.core.heir_folders import HEIR_FOLDERS
    from src.core.memory_store import MemoryStore
    from src.world.sanctuary_clock import GMT8, WorldClock

    store = MemoryStore()
    blob = {}
    for cid in sorted(HEIR_FOLDERS):
        try:
            blob[cid] = store.get_memories(cid) if hasattr(store, "get_memories") else None
        except Exception as exc:
            blob[cid] = {"error": f"{type(exc).__name__}: {exc}"}
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(GMT8).strftime("%Y-%m-%dT%H-%M")
    payload = {
        "at": datetime.now(GMT8).isoformat(timespec="seconds"),
        "clock": WorldClock.from_gmt8().format_short(),
        "heirs": blob,
    }
    path = OUT / f"{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = ", ".join(f"{k}={len(v) if isinstance(v, list) else '?'}" for k, v in blob.items())
    (OUT / "digest.md").open("a", encoding="utf-8").write(
        f"- {payload['at']} · {payload['clock']} — {counts}\n")
    print(f"snapshot {path.name} · {payload['clock']} · {counts}")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=0, help="seconds between snapshots; 0 = once")
    args = ap.parse_args()
    snapshot()
    if args.every <= 0:
        return 0
    while True:
        time.sleep(max(60, args.every))
        try:
            snapshot()
        except Exception as exc:
            print(f"snapshot failed: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
