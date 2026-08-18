"""
Train one OPLoRA adapter per sanctuary Heir (13 cards), sequentially.

Uses tools/oplora/datasets/heir_*.jsonl produced by shape_training_data.py.
Restarts the Python process per Heir to keep 8GB VRAM clean.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPLORA = Path(__file__).resolve().parent
DATASETS = OPLORA / "datasets"
OUT_ROOT = OPLORA / "outputs" / "heirs"
PY = ROOT / ".venv-oplora" / "Scripts" / "python.exe"
TRAIN = OPLORA / "train_sft.py"
CONFIG = OPLORA / "config.yaml"
PROGRESS = OUT_ROOT / "progress.jsonl"

# Must match src/characters/*.json (13 cards)
HEIRS = [
    ("Aglaea", "heir_aglaea.jsonl"),
    ("Anaxa", "heir_anaxa.jsonl"),
    ("Castorice", "heir_castorice.jsonl"),
    ("Cerydra", "heir_cerydra.jsonl"),
    ("Cipher", "heir_cipher.jsonl"),
    ("Cyrene", "heir_cyrene.jsonl"),
    ("Dan Heng", "heir_dan_heng.jsonl"),
    ("Evernight", "heir_evernight.jsonl"),
    ("Hyacine", "heir_hyacine.jsonl"),
    ("Hysilens", "heir_hysilens.jsonl"),
    ("Mydei", "heir_mydei.jsonl"),
    ("Phainon", "heir_phainon.jsonl"),
    ("Tribbie", "heir_tribbie.jsonl"),
]


def _log_progress(event: dict) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps(event, ensure_ascii=False), flush=True)


def main() -> int:
    if not PY.is_file():
        print(f"Missing venv python: {PY}", file=sys.stderr)
        return 1

    man_path = DATASETS / "manifest.json"
    if not man_path.is_file():
        print("Missing manifest — run shape_training_data.py first", file=sys.stderr)
        return 1
    man = json.loads(man_path.read_text(encoding="utf-8"))
    print("=" * 60, flush=True)
    print("Amphoreus OPLoRA — train all 13 Heirs", flush=True)
    print(f"Manifest training_13_total={man.get('training_13_total')}", flush=True)
    print(f"Missing={man.get('training_13_missing')}", flush=True)
    print("=" * 60, flush=True)

    missing_files = []
    for name, fname in HEIRS:
        path = DATASETS / fname
        if not path.is_file() or path.stat().st_size == 0:
            missing_files.append(name)
    if missing_files:
        print(f"NOT READY — empty/missing datasets: {missing_files}", file=sys.stderr)
        return 1

    _log_progress({"event": "run_start", "heirs": len(HEIRS), "ts": time.time()})
    failures = []
    for i, (name, fname) in enumerate(HEIRS, 1):
        ds = DATASETS / fname
        out = OUT_ROOT / name.lower().replace(" ", "_")
        rows = sum(1 for line in ds.open(encoding="utf-8") if line.strip())
        _log_progress(
            {
                "event": "heir_start",
                "index": i,
                "total": len(HEIRS),
                "heir": name,
                "rows": rows,
                "dataset": str(ds),
                "output": str(out),
                "ts": time.time(),
            }
        )
        cmd = [
            str(PY),
            str(TRAIN),
            "--config",
            str(CONFIG),
            "--dataset",
            str(ds),
            "--output-dir",
            str(out),
            "--heir",
            name,
        ]
        t0 = time.time()
        rc = subprocess.call(cmd, cwd=str(ROOT))
        elapsed = time.time() - t0
        _log_progress(
            {
                "event": "heir_end",
                "index": i,
                "total": len(HEIRS),
                "heir": name,
                "returncode": rc,
                "seconds": round(elapsed, 1),
                "ts": time.time(),
            }
        )
        if rc != 0:
            failures.append(name)
            print(f"FAILED {name} rc={rc} — continuing to next Heir", flush=True)

    _log_progress(
        {
            "event": "run_end",
            "failures": failures,
            "ok": [h for h, _ in HEIRS if h not in failures],
            "ts": time.time(),
        }
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
