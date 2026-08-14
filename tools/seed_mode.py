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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.core.memory_store import MemoryStore  # noqa: E402
from src.core.character_loader import CharacterLoader  # noqa: E402
from src.core.visitor_mode import reseed_for_mode  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["aftermath", "journey"])
    args = ap.parse_args()

    memory = MemoryStore(str(ROOT))
    loader = CharacterLoader(str(ROOT / "src" / "characters"))
    if args.mode == "aftermath":
        print("Seeding AFTERMATH mode (Iron Tomb conquered — bonds at best friend)…")
    else:
        print("Resetting to JOURNEY mode (Trailblazer new to Amphoreus)…")
    summary = reseed_for_mode(args.mode, memory, loader)
    for cid, s in summary.items():
        print(f"  ✓ {s['name']} ({cid}): {s['level']} + {s['memories']} campaign memories")
    print("Done. The in-app Control Panel reflects the same mode.")


if __name__ == "__main__":
    main()
