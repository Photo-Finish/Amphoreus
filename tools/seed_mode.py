"""
seed_mode.py — switch the sanctuary experience between the two modes.

  python tools/seed_mode.py aftermath   # Trailblazer conquered the Iron Tomb:
                                        # bonds = best friend, full shared
                                        # memories of the campaign, aftermath
                                        # framing (SANCTUARY_MODE=aftermath).
  python tools/seed_mode.py journey     # Trailblazer new to Amphoreus:
                                        # bonds reset to stranger, seeded
                                        # memories removed (SANCTUARY_MODE=journey).

The chat-time framing follows the SANCTUARY_MODE environment variable (see
src/core/visitor_mode.py). Start the UI with the chosen mode, e.g.:

  $env:SANCTUARY_MODE='aftermath'; python -m streamlit run src/ui_app.py
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402
from src.core.memory_store import MemoryStore  # noqa: E402
from src.core.visitor_mode import (  # noqa: E402
    AFTERMATH_MEMORY_SEEDS, AFTERMATH_SUMMARY,
)
from src.core.character_loader import CharacterLoader  # noqa: E402

MARKER = "aftermath:iron-tomb"


def _read_memories(path: Path) -> list:
    if not path.exists():
        return []
    return [
        json.loads(ln)
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]


def _write_memories(path: Path, mems: list):
    with open(path, "w", encoding="utf-8") as f:
        for m in mems:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")


def seed_aftermath(memory: MemoryStore, loader: CharacterLoader):
    print("Seeding AFTERMATH mode (Iron Tomb conquered — bonds at best friend)…")
    now = datetime.now().isoformat(timespec="seconds")
    for cid in HEIR_FOLDERS:
        folder = memory._folder(cid)
        name = loader.load(cid)["meta"]["name"]
        # Bond: war-companion.
        bond = {
            "character_id": cid,
            "first_met": "2025-08-11T10:00:00",
            "visits": 64,
            "friendship_level": "best friend",
            "user_summary": AFTERMATH_SUMMARY,
            "last_seen": now,
        }
        (folder / "bond.json").write_text(
            json.dumps(bond, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # Memories: remove old seeded aftermath entries, then add fresh ones.
        path = folder / "memories.jsonl"
        mems = [m for m in _read_memories(path) if MARKER not in (m.get("content") or "")]
        seed = AFTERMATH_MEMORY_SEEDS.get(cid, "")
        if seed:
            mems.append({
                "mtype": "moment",
                "content": f"[{MARKER}] {seed}",
                "importance": 3,
                "ts": "2025-08-11T10:00:00",
            })
        _write_memories(path, mems)
        print(f"  ✓ {name} ({cid}): best friend + campaign memory")
    print("Done. Start the UI with:  $env:SANCTUARY_MODE='aftermath'")


def seed_journey(memory: MemoryStore, loader: CharacterLoader):
    print("Resetting to JOURNEY mode (Trailblazer new to Amphoreus)…")
    now = datetime.now().isoformat(timespec="seconds")
    for cid in HEIR_FOLDERS:
        folder = memory._folder(cid)
        name = loader.load(cid)["meta"]["name"]
        bond = {
            "character_id": cid,
            "first_met": now,
            "visits": 0,
            "friendship_level": "stranger",
            "user_summary": "",
            "last_seen": now,
        }
        (folder / "bond.json").write_text(
            json.dumps(bond, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        path = folder / "memories.jsonl"
        mems = [m for m in _read_memories(path) if MARKER not in (m.get("content") or "")]
        _write_memories(path, mems)
        print(f"  ✓ {name} ({cid}): reset to stranger")
    print("Done. Start the UI with:  $env:SANCTUARY_MODE='journey' (or unset)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["aftermath", "journey"])
    args = ap.parse_args()

    memory = MemoryStore(str(ROOT))
    loader = CharacterLoader(str(ROOT / "src" / "characters"))
    if args.mode == "aftermath":
        seed_aftermath(memory, loader)
    else:
        seed_journey(memory, loader)


if __name__ == "__main__":
    main()
