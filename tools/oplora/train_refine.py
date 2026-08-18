"""
Continue-train verified OPLoRA adapters into adapter_v2/ to lower loss.

Does not overwrite adapter/. Copies adapter/ → adapter_v1/ once, then
continues SFT from adapter_v1. After a successful run, swap adapter_v2 →
adapter only when last_loss is strictly lower.

Usage (repo root):
  .\\.venv-oplora\\Scripts\\python.exe tools\\oplora\\train_refine.py
"""
from __future__ import annotations

import json
import shutil
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
CONFIG = OPLORA / "config_refine.yaml"
PROGRESS = OUT_ROOT / "refine_progress.jsonl"

HEIRS = [
    ("Aglaea", "heir_aglaea.jsonl", "aglaea"),
    ("Anaxa", "heir_anaxa.jsonl", "anaxa"),
    ("Castorice", "heir_castorice.jsonl", "castorice"),
    ("Cerydra", "heir_cerydra.jsonl", "cerydra"),
    ("Cipher", "heir_cipher.jsonl", "cipher"),
    ("Cyrene", "heir_cyrene.jsonl", "cyrene"),
    ("Dan Heng", "heir_dan_heng.jsonl", "dan_heng"),
    ("Evernight", "heir_evernight.jsonl", "evernight"),
    ("Hyacine", "heir_hyacine.jsonl", "hyacine"),
    ("Hysilens", "heir_hysilens.jsonl", "hysilens"),
    ("Mydei", "heir_mydei.jsonl", "mydei"),
    ("Phainon", "heir_phainon.jsonl", "phainon"),
    ("Tribbie", "heir_tribbie.jsonl", "tribbie"),
]

# First-pass last loss ~≥2.0 or thin sets: extra epoch
TWO_EPOCH = {"cerydra", "cipher", "evernight", "hyacine", "hysilens"}


def _log(event: dict) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps(event, ensure_ascii=False), flush=True)


def _checkpoint_losses(heir_dir: Path) -> tuple[float | None, float | None]:
    states = list(heir_dir.glob("checkpoint-*/trainer_state.json"))
    if not states:
        return None, None
    st = max(states, key=lambda p: int(p.parent.name.split("-")[1]))
    data = json.loads(st.read_text(encoding="utf-8"))
    losses = [float(x["loss"]) for x in data.get("log_history", []) if "loss" in x]
    if not losses:
        return None, None
    return losses[-1], sum(losses) / len(losses)


def _baseline_path(heir_dir: Path) -> Path:
    return heir_dir / "v1_baseline.json"


def _write_loss_json(path: Path, last: float, mean: float | None, source: str) -> None:
    path.write_text(
        json.dumps(
            {"last_loss": last, "mean_loss": mean, "source": source},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _read_v1_last(heir_dir: Path) -> float | None:
    for p in (heir_dir / "adapter_v1" / "v1_loss.json", _baseline_path(heir_dir)):
        if p.is_file():
            try:
                return float(json.loads(p.read_text(encoding="utf-8"))["last_loss"])
            except Exception:
                continue
    last, _mean = _checkpoint_losses(heir_dir)
    return last


def _ensure_v1(heir_dir: Path) -> Path:
    adapter = heir_dir / "adapter"
    v1 = heir_dir / "adapter_v1"
    if not (adapter / "adapter_config.json").is_file():
        raise SystemExit(f"Missing verified adapter: {adapter}")
    if not (v1 / "adapter_config.json").is_file():
        if v1.exists():
            shutil.rmtree(v1)
        shutil.copytree(adapter, v1)
    rec = v1 / "v1_loss.json"
    if not rec.is_file():
        src = _baseline_path(heir_dir)
        if src.is_file():
            shutil.copy2(src, rec)
        else:
            last, mean = _checkpoint_losses(heir_dir)
            if last is not None:
                _write_loss_json(rec, last, mean, "first_pass_checkpoint")
    return v1


def prepare_disk() -> None:
    """Record first-pass losses, snapshot adapter_v1, drop bulky checkpoints."""
    for _name, _fname, slug in HEIRS:
        heir_dir = OUT_ROOT / slug
        base = _baseline_path(heir_dir)
        if not base.is_file():
            last, mean = _checkpoint_losses(heir_dir)
            if last is not None:
                _write_loss_json(base, last, mean, "first_pass_checkpoint")
        _ensure_v1(heir_dir)
        for ck in heir_dir.glob("checkpoint-*"):
            shutil.rmtree(ck, ignore_errors=True)


def _swap_if_better(slug: str, name: str) -> dict:
    heir_dir = OUT_ROOT / slug
    adapter = heir_dir / "adapter"
    v1 = heir_dir / "adapter_v1"
    v2 = heir_dir / "adapter_v2"
    metrics_path = v2 / "refine_metrics.json"
    if not metrics_path.is_file():
        return {"heir": name, "swapped": False, "reason": "no v2 metrics"}
    v2_last = json.loads(metrics_path.read_text(encoding="utf-8")).get("last_loss")
    v1_last = _read_v1_last(heir_dir)
    if v2_last is None or v1_last is None:
        return {
            "heir": name,
            "swapped": False,
            "reason": "missing loss",
            "v1": v1_last,
            "v2": v2_last,
        }
    if float(v2_last) >= float(v1_last):
        return {
            "heir": name,
            "swapped": False,
            "reason": "v2 not lower",
            "v1": v1_last,
            "v2": v2_last,
        }
    if not (v1 / "adapter_config.json").is_file():
        return {"heir": name, "swapped": False, "reason": "no adapter_v1 safety copy"}
    live_bak = heir_dir / "adapter_pre_swap"
    if live_bak.exists():
        shutil.rmtree(live_bak)
    adapter.rename(live_bak)
    shutil.copytree(v2, adapter)
    shutil.rmtree(live_bak)
    return {
        "heir": name,
        "swapped": True,
        "v1": v1_last,
        "v2": v2_last,
        "delta": round(float(v1_last) - float(v2_last), 4),
    }


def main() -> int:
    if not PY.is_file():
        print(f"Missing venv python: {PY}", file=sys.stderr)
        return 1
    if not CONFIG.is_file():
        print(f"Missing {CONFIG}", file=sys.stderr)
        return 1

    prepare_disk()
    _log({"event": "refine_start", "heirs": len(HEIRS), "ts": time.time()})
    failures = []
    for i, (name, fname, slug) in enumerate(HEIRS, 1):
        heir_dir = OUT_ROOT / slug
        ds = DATASETS / fname
        if (
            (heir_dir / "adapter_v2" / "adapter_model.safetensors").is_file()
            and (heir_dir / "adapter_v2" / "refine_metrics.json").is_file()
        ):
            _log({"event": "heir_skip", "heir": name, "reason": "adapter_v2 already complete"})
            continue
        v1 = _ensure_v1(heir_dir)
        epochs = 2.0 if slug in TWO_EPOCH else 1.0
        rows = sum(1 for line in ds.open(encoding="utf-8") if line.strip())
        _log(
            {
                "event": "heir_start",
                "index": i,
                "total": len(HEIRS),
                "heir": name,
                "slug": slug,
                "rows": rows,
                "epochs": epochs,
                "init": str(v1),
                "v1_last": _read_v1_last(heir_dir),
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
            str(heir_dir),
            "--init-adapter",
            str(v1),
            "--adapter-subdir",
            "adapter_v2",
            "--epochs",
            str(epochs),
            "--heir",
            name,
        ]
        t0 = time.time()
        rc = subprocess.call(cmd, cwd=str(ROOT))
        elapsed = time.time() - t0
        metrics: dict = {}
        mp = heir_dir / "adapter_v2" / "refine_metrics.json"
        if mp.is_file():
            metrics = json.loads(mp.read_text(encoding="utf-8"))
        _log(
            {
                "event": "heir_end",
                "index": i,
                "heir": name,
                "returncode": rc,
                "seconds": round(elapsed, 1),
                "last_loss": metrics.get("last_loss"),
                "mean_loss": metrics.get("mean_loss"),
                "ts": time.time(),
            }
        )
        if rc != 0:
            failures.append(name)
            print(f"FAILED {name} rc={rc} — continuing", flush=True)

    swaps = []
    if not failures:
        for name, _fname, slug in HEIRS:
            swaps.append(_swap_if_better(slug, name))
        _log({"event": "swap_summary", "swaps": swaps, "ts": time.time()})

    _log({"event": "refine_end", "failures": failures, "ts": time.time()})
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
