# -*- coding: utf-8 -*-
"""Download DistilRoBERTa emotion weights into models/visitor_emotion/.

Uses Hugging Face ``j-hartmann/emotion-english-distilroberta-base``.
Requires ``transformers`` and CPU ``torch`` in the active venv::

    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install transformers
    # If huggingface.co is slow/blocked (common here), use the mirror:
    set HF_ENDPOINT=https://hf-mirror.com
    python tools/download_visitor_emotion_model.py

Weights stay under ``models/`` (gitignored). Chat falls back to a lexicon
when the snapshot is missing.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODEL_ID = "j-hartmann/emotion-english-distilroberta-base"
OUT = ROOT / "models" / "visitor_emotion"


def main() -> int:
    # Prefer local HF home on D:; optional China mirror when HF_ENDPOINT unset
    # and huggingface.co is unreachable (operator can override).
    os.environ.setdefault("HF_HOME", r"D:\hf-cache")
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"D:\hf-cache\hub")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    if not (os.environ.get("HF_ENDPOINT") or "").strip():
        # Best-effort default for this machine's network; disable with HF_ENDPOINT=
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        print(
            "FAIL: transformers not installed.\n"
            "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
            "  pip install transformers"
        )
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {MODEL_ID} -> {OUT}")
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    tok.save_pretrained(OUT)
    model.save_pretrained(OUT)
    print("OK: visitor emotion model saved.")
    # Smoke classify
    from src.core.visitor_emotion import classify, model_on_disk

    # Reset lazy pipe so it picks up the new folder
    import src.core.visitor_emotion as ve

    ve._pipe = None
    ve._pipe_failed = False
    assert model_on_disk(), "config/weights missing after save"
    hit = classify("I am so happy to see you again!")
    print(f"Smoke: label={hit.get('label')} conf={hit.get('confidence'):.2f} "
          f"backend={hit.get('backend')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
