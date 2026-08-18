"""Voice path choice: Stage-1 RAG (Ollama + Chroma) vs OPLoRA (7B + Heir adapter).

Persisted under world_runtime/voice_path.json so Copilot-era WorldState stays
untouched. Default is RAG.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = PROJECT_ROOT / "world_runtime" / "voice_path.json"
ADAPTERS_ROOT = PROJECT_ROOT / "tools" / "oplora" / "outputs" / "heirs"

PATH_RAG = "rag"
PATH_OPLORA = "oplora"
VALID_PATHS = (PATH_RAG, PATH_OPLORA)

# Card id (src/characters/*.json stem) → adapter folder under outputs/heirs/
CARD_TO_ADAPTER: dict[str, str] = {
    "aglaea": "aglaea",
    "anaxa": "anaxa",
    "castorice": "castorice",
    "cerydra": "cerydra",
    "cipher": "cipher",
    "cyrene": "cyrene",
    "dan-heng-permansor-terrae": "dan_heng",
    "evernight": "evernight",
    "hyacine": "hyacine",
    "hysilens": "hysilens",
    "mydei": "mydei",
    "phainon": "phainon",
    "tribbie": "tribbie",
}


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


def get_voice_path() -> str:
    """Active avenue: 'rag' (default) or 'oplora'."""
    path = str(_read().get("path") or PATH_RAG).strip().lower()
    return path if path in VALID_PATHS else PATH_RAG


def set_voice_path(path: str) -> str:
    path = str(path or PATH_RAG).strip().lower()
    if path not in VALID_PATHS:
        path = PATH_RAG
    data = _read()
    data["path"] = path
    _write(data)
    return path


def is_oplora() -> bool:
    return get_voice_path() == PATH_OPLORA


def adapter_id_for(character_id: str) -> Optional[str]:
    return CARD_TO_ADAPTER.get(character_id)


def adapter_dir(character_id: str) -> Optional[Path]:
    aid = adapter_id_for(character_id)
    if not aid:
        return None
    return ADAPTERS_ROOT / aid / "adapter"


def adapter_ready(character_id: str) -> bool:
    d = adapter_dir(character_id)
    if d is None:
        return False
    return (d / "adapter_config.json").is_file() and (
        (d / "adapter_model.safetensors").is_file()
        or (d / "adapter_model.bin").is_file()
    )


def adapters_status() -> dict:
    """Per-card adapter presence for the Control Panel."""
    rows = {}
    ready_n = 0
    for cid, aid in CARD_TO_ADAPTER.items():
        ok = adapter_ready(cid)
        if ok:
            ready_n += 1
        rows[cid] = {"adapter_id": aid, "ready": ok, "path": str(adapter_dir(cid))}
    return {
        "ready_count": ready_n,
        "total": len(CARD_TO_ADAPTER),
        "heirs": rows,
        "adapters_root": str(ADAPTERS_ROOT),
        "venv_oplora": str(PROJECT_ROOT / ".venv-oplora" / "Scripts" / "python.exe"),
        "venv_exists": (PROJECT_ROOT / ".venv-oplora" / "Scripts" / "python.exe").is_file(),
    }


def label(path: Optional[str] = None) -> str:
    p = path or get_voice_path()
    if p == PATH_OPLORA:
        return "OPLoRA (Qwen2.5-7B + Heir adapter)"
    return "RAG (Ollama + Chroma scripture)"
