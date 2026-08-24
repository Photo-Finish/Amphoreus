"""Visitor-message emotion for Heir awareness (Stage 2).

Uses DistilRoBERTa emotion classification (j-hartmann) when available, with a
lexicon fallback so chat never stalls. Prompt language is Amphoreus-native —
tone of voice / colour — never BERT, models, or Earth psychology jargon
(knowledge wall).

Toggle: Control Panel / ``world_runtime/visitor_emotion.json`` /
``AMP_VISITOR_EMOTION=1|0``. Default **ON** (feature is part of Visit life).
"""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = PROJECT_ROOT / "world_runtime" / "visitor_emotion.json"
MODEL_DIR = PROJECT_ROOT / "models" / "visitor_emotion"
HF_MODEL_ID = "j-hartmann/emotion-english-distilroberta-base"

# Model labels → Amphoreus-facing colour (never clinical).
_LABEL_COLOUR = {
    "anger": ("heated", "a sharp edge under the words"),
    "disgust": ("recoiling", "a distaste they do not quite hide"),
    "fear": ("wary", "an unsteady thread in the voice"),
    "joy": ("bright", "a glad warmth in how they speak"),
    "neutral": ("even", "a plain, steady tone"),
    "sadness": ("heavy", "a low weight behind the words"),
    "surprise": ("startled", "a wonder-struck lift in the voice"),
}

_LEXICON: Dict[str, Tuple[str, ...]] = {
    "anger": (
        "angry", "furious", "hate", "idiot", "stupid", "damn", "pissed",
        "annoyed", "rage", "outraged", "shut up",
    ),
    "disgust": (
        "disgusting", "gross", "revolting", "sickening", "nasty", "repulsed",
    ),
    "fear": (
        "afraid", "scared", "terrified", "worried", "anxious", "panic",
        "frightened", "nervous", "dread",
    ),
    "joy": (
        "happy", "glad", "love", "wonderful", "delight", "thank", "grateful",
        "excited", "joy", "cheer", "missed you", "miss you",
    ),
    "sadness": (
        "sad", "sorry", "cry", "lonely", "miss", "grief", "hurt", "pain",
        "heartbroken", "depressed", "weep",
    ),
    "surprise": (
        "wow", "whoa", "surprised", "unexpected", "cannot believe",
        "can't believe", "amazing", "astonishing",
    ),
}

_pipe_lock = threading.Lock()
_pipe: Any = None
_pipe_failed = False


def _read() -> dict:
    try:
        if RUNTIME_PATH.is_file():
            data = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _write(data: dict) -> None:
    RUNTIME_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _env_override() -> Optional[bool]:
    raw = (os.environ.get("AMP_VISITOR_EMOTION") or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return None


def emotion_enabled() -> bool:
    """Whether to inject visitor-emotion colour into chat. Default ON."""
    env = _env_override()
    if env is not None:
        return env
    return bool(_read().get("enabled", True))


def set_emotion_enabled(enabled: bool) -> bool:
    data = _read()
    data["enabled"] = bool(enabled)
    _write(data)
    return bool(enabled)


def model_on_disk() -> bool:
    """True when a local snapshot exists under models/visitor_emotion."""
    if not MODEL_DIR.is_dir():
        return False
    if not (MODEL_DIR / "config.json").is_file():
        return False
    # transformers save_pretrained leaves config.json + weights
    return bool(
        list(MODEL_DIR.glob("*.safetensors"))
        or list(MODEL_DIR.glob("pytorch_model*.bin"))
        or list(MODEL_DIR.glob("tf_model*"))
    )


def model_available() -> bool:
    """Local snapshot or importable transformers (can pull from cache)."""
    if model_on_disk():
        return True
    try:
        import transformers  # noqa: F401
        return True
    except Exception:
        return False


def backend_label() -> str:
    if not emotion_enabled():
        return "Visitor emotion OFF"
    if model_on_disk() or model_available():
        try:
            import transformers  # noqa: F401
            return "Visitor emotion ON (DistilRoBERTa)"
        except Exception:
            pass
    return "Visitor emotion ON (lexicon fallback)"


def label(enabled: Optional[bool] = None) -> str:
    on = emotion_enabled() if enabled is None else bool(enabled)
    if not on:
        return "Visitor emotion OFF"
    return backend_label().replace("Visitor emotion ON", "ON").replace(
        "Visitor emotion OFF", "OFF"
    )


def _normalize_label(raw: str) -> str:
    key = (raw or "neutral").strip().lower()
    if key in _LABEL_COLOUR:
        return key
    aliases = {
        "happy": "joy",
        "happiness": "joy",
        "sad": "sadness",
        "fearful": "fear",
        "angry": "anger",
        "surprised": "surprise",
    }
    return aliases.get(key, "neutral")


def _lexicon_scores(text: str) -> Dict[str, float]:
    low = (text or "").lower()
    scores = {k: 0.0 for k in _LABEL_COLOUR}
    for emo, words in _LEXICON.items():
        for w in words:
            if w in low:
                scores[emo] += 1.0
    if sum(scores.values()) <= 0:
        scores["neutral"] = 1.0
    return scores


def _lexicon_classify(text: str) -> Dict[str, Any]:
    scores = _lexicon_scores(text)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_label, top_n = ranked[0]
    total = sum(scores.values()) or 1.0
    confidence = top_n / total
    if top_label != "neutral" and confidence < 0.34:
        top_label, confidence = "neutral", 0.5
    return {
        "label": top_label,
        "confidence": float(confidence),
        "scores": {k: float(v / total) for k, v in scores.items()},
        "backend": "lexicon",
    }


def _get_pipeline():
    """Lazy DistilRoBERTa pipeline on CPU (never steals Ollama GPU)."""
    global _pipe, _pipe_failed
    if _pipe_failed:
        return None
    if _pipe is not None:
        return _pipe
    with _pipe_lock:
        if _pipe_failed:
            return None
        if _pipe is not None:
            return _pipe
        try:
            from transformers import pipeline
            src = str(MODEL_DIR) if model_on_disk() else HF_MODEL_ID
            _pipe = pipeline(
                "text-classification",
                model=src,
                tokenizer=src,
                top_k=None,
                device=-1,  # CPU only
            )
            return _pipe
        except Exception:
            _pipe_failed = True
            return None


def classify(text: str) -> Dict[str, Any]:
    """Return ``{label, confidence, scores, backend}`` for a visitor line."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return {
            "label": "neutral",
            "confidence": 1.0,
            "scores": {"neutral": 1.0},
            "backend": "empty",
        }
    # Cap length — DistilRoBERTa max; chat turns are short.
    snippet = cleaned[:512]
    pipe = _get_pipeline()
    if pipe is not None:
        try:
            raw = pipe(snippet)
            # pipeline(top_k=None) → [[{label, score}, ...]]
            rows = raw[0] if raw and isinstance(raw[0], list) else raw
            scores: Dict[str, float] = {}
            for row in rows or []:
                lab = _normalize_label(str(row.get("label") or ""))
                scores[lab] = max(scores.get(lab, 0.0), float(row.get("score") or 0.0))
            if not scores:
                return _lexicon_classify(snippet)
            best = max(scores.items(), key=lambda kv: kv[1])
            return {
                "label": best[0],
                "confidence": float(best[1]),
                "scores": scores,
                "backend": "distilroberta",
            }
        except Exception:
            pass
    return _lexicon_classify(snippet)


def colour_for(label_name: str) -> Tuple[str, str]:
    return _LABEL_COLOUR.get(_normalize_label(label_name), _LABEL_COLOUR["neutral"])


def visitor_emotion_block(
    user_message: str,
    *,
    force: Optional[bool] = None,
    min_confidence: float = 0.28,
) -> str:
    """Prompt block: how the visitor seems — colour, not command.

    Empty when disabled, empty message, or low-confidence neutral.
    """
    on = emotion_enabled() if force is None else bool(force)
    if not on:
        return ""
    result = classify(user_message)
    lab = _normalize_label(str(result.get("label") or "neutral"))
    conf = float(result.get("confidence") or 0.0)
    if lab == "neutral" and conf < 0.55:
        return ""
    if conf < min_confidence:
        return ""
    adjective, phrase = colour_for(lab)
    # Soften weak non-neutral reads so Heirs are not over-steered.
    hedge = ""
    if conf < 0.45 and lab != "neutral":
        hedge = " (a faint reading — do not force it)"
    return (
        "\n\n# How the visitor seems\n"
        f"Their voice carries a {adjective} turn — {phrase}{hedge}.\n"
        "Let it colour how you answer; do not name the feeling as a diagnosis, "
        "and do not invent Earth notions. You remain yourself."
    )


def maybe_inject(
    system_prompt: str,
    user_message: str,
    *,
    force: Optional[bool] = None,
) -> str:
    block = visitor_emotion_block(user_message, force=force)
    if not block:
        return system_prompt
    return f"{system_prompt}{block}"
