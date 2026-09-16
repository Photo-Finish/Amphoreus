"""Local compute probes for the world machine (CPU ticks vs optional GPU voice).

Never imports torch, CUDA, or Ollama libraries. ``nvidia-smi`` is the only
NVIDIA check, with a short timeout, so a missing driver cannot hang the engine.

The lived world (periods, hearths, streets, eco, Keeper fallback, travel)
must run on CPU even when the RTX GPU is offline. Heir decide/talk stays
optional and is skipped when a local GPU LLM is not actually usable.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

_NVIDIA_CACHE: Optional[tuple[float, bool]] = None
_NVIDIA_TTL = 30.0


def _creation_flags() -> int:
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)


def nvidia_present(timeout: float = 3.0, *, force: bool = False) -> bool:
    """True if ``nvidia-smi -L`` lists a GPU. Never imports torch."""
    import time
    global _NVIDIA_CACHE
    now = time.time()
    if not force and _NVIDIA_CACHE is not None:
        ts, val = _NVIDIA_CACHE
        if (now - ts) < _NVIDIA_TTL:
            return val
    ok = False
    try:
        r = subprocess.run(
            ["nvidia-smi", "-L"],
            capture_output=True,
            timeout=timeout,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=_creation_flags(),
        )
        blob = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0 and "GPU" in blob
    except Exception:
        ok = False
    _NVIDIA_CACHE = (now, ok)
    return ok


def _env_flag(name: str) -> Optional[bool]:
    raw = (os.environ.get(name) or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    return None


def _compute_mode() -> str:
    try:
        from src.core.compute_mode import get_compute_mode
        return str(get_compute_mode() or "nvidia")
    except Exception:
        return "nvidia"


def local_llm_safe_for_world(timeout: float = 3.0) -> bool:
    """Whether the Keeper may call a *local* GPU LLM on a world tick.

    False when NVIDIA is missing, compute mode is CPU, or conversation is
    on the Online API. A 20s chat timeout in AmbientDirector still falls
    back if CUDA is wedged. Optional ``AMP_WORLD_CPU=1`` forces fallback.
    """
    if _env_flag("AMP_WORLD_CPU") is True:
        return False
    if _env_flag("AMP_KEEPER_LLM") is False:
        return False
    try:
        from src.core.voice_path import is_online
        if is_online():
            return False
    except Exception:
        pass
    return _local_accelerator_ok(timeout=timeout)


def heir_voice_may_use_local(timeout: float = 3.0) -> bool:
    """Whether Heir decide/talk may hit local Ollama.

    If NVIDIA is required and gone, skip voice so a wedged CUDA load cannot
    block ticks. Online API is handled separately by ``_heir_voice_ready``.
    """
    return _local_accelerator_ok(timeout=timeout)


def _local_accelerator_ok(timeout: float = 3.0) -> bool:
    mode = _compute_mode()
    if mode == "cpu":
        return False
    if mode == "intel":
        return True
    return nvidia_present(timeout=timeout)
