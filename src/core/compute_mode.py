"""Compute-mode switch: NVIDIA CUDA vs the integrated (Intel) GPU via Vulkan.

Ollama picks its backend automatically (CUDA on this machine) and it disables
integrated GPUs unless ``OLLAMA_IGPU_ENABLE=1``. This module persists the end
user's choice (``world_runtime/compute_mode.json``) and restarts the Ollama
server with the matching environment:

  nvidia  -> backend autodetect (CUDA), integrated GPUs disabled (default)
  intel   -> OLLAMA_LLM_LIBRARY=vulkan, OLLAMA_IGPU_ENABLE=1

Empirically verified on this machine (2026-08-15):
  nvidia -> qwen2.5:14b-instruct at 38%/62% CPU/GPU on the RTX 5070
            (8 GB VRAM limit splits the 10 GB model; llama-server on GPU 0)
  intel  -> 100% GPU on the integrated Intel GPU (shared system memory can
            hold the whole model), NVIDIA GPU completely idle.
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "world_runtime" / "compute_mode.json"

MODES = {
    "nvidia": {
        "label": "NVIDIA CUDA",
        "library": None,   # backend autodetect -> CUDA
        "igpu": "0",
    },
    "intel": {
        "label": "Integrated (Intel) GPU — Vulkan",
        "library": "vulkan",
        "igpu": "1",
    },
}


def get_compute_mode() -> str:
    """The persisted compute mode ('nvidia' by default)."""
    try:
        d = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if d.get("mode") in MODES:
            return d["mode"]
    except Exception:
        pass
    return "nvidia"


def set_compute_mode(mode: str):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps({"mode": mode if mode in MODES else "nvidia"},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")


def _base_env() -> dict:
    """The environment the project's Ollama server always needs."""
    e = os.environ.copy()
    e["OLLAMA_MODELS"] = str(PROJECT_ROOT / "models" / "ollama")
    e["OLLAMA_HOST"] = "127.0.0.1:11434"
    e["OLLAMA_CONTEXT_LENGTH"] = "8192"
    e["OLLAMA_FLASH_ATTENTION"] = "1"
    e["OLLAMA_KV_CACHE_TYPE"] = "q8_0"
    return e


def restart_ollama(mode: str) -> dict:
    """Stop the running Ollama server and start it with the chosen compute
    mode's environment. Returns {'mode', 'label', 'up'}."""
    mode = mode if mode in MODES else "nvidia"
    ollama_exe = os.environ.get("OLLAMA_EXE")
    if not ollama_exe:
        ollama_exe = shutil.which("ollama")
    if not ollama_exe:
        ollama_exe = str(Path(os.environ.get(
            "LOCALAPPDATA", r"C:\Users\default")) /
            "Programs" / "Ollama" / "ollama.exe")

    # 1. stop stale servers + orphaned model children (they keep VRAM)
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process -Name '*ollama*','llama-server' "
             "-ErrorAction SilentlyContinue | Stop-Process -Force "
             "-ErrorAction SilentlyContinue"],
            capture_output=True, timeout=60)
    except Exception:
        pass
    time.sleep(3)

    # 2. start a detached server with the mode's environment
    env = _base_env()
    m = MODES[mode]
    if m["library"]:
        env["OLLAMA_LLM_LIBRARY"] = m["library"]
    else:
        env.pop("OLLAMA_LLM_LIBRARY", None)
    env["OLLAMA_IGPU_ENABLE"] = m["igpu"]
    try:
        subprocess.Popen([ollama_exe, "serve"], env=env,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        return {"mode": mode, "label": MODES[mode]["label"], "up": False}

    # 3. wait for it to listen and see the models
    up = False
    for _ in range(15):
        time.sleep(2)
        try:
            r = subprocess.run(
                ["curl.exe", "-s", "--max-time", "5",
                 "http://127.0.0.1:11434/api/tags"],
                capture_output=True, timeout=15)
            if b"qwen2.5:14b-instruct" in r.stdout or b"gemma3:27b" in r.stdout:
                up = True
                break
        except Exception:
            pass
    return {"mode": mode, "label": MODES[mode]["label"], "up": up}
