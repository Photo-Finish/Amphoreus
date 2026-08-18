"""Print last/mean train loss from each Heir's latest checkpoint."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "outputs" / "heirs"


def main() -> None:
    for d in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        states = list(d.glob("checkpoint-*/trainer_state.json"))
        if not states:
            print(f"{d.name}: NO STATE")
            continue
        st = max(states, key=lambda p: int(p.parent.name.split("-")[1]))
        data = json.loads(st.read_text(encoding="utf-8"))
        losses = [x["loss"] for x in data.get("log_history", []) if "loss" in x]
        last = losses[-1] if losses else None
        mean = (sum(losses) / len(losses)) if losses else None
        print(
            f"{d.name:12} last={last:.4f} mean={mean:.4f} "
            f"steps={data.get('max_steps')} nlog={len(losses)} {st.parent.name}"
        )


if __name__ == "__main__":
    main()
