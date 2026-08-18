"""Client for the OPLoRA infer server (.venv-oplora subprocess).

Streamlit / AgentManager must not import torch or peft — they talk HTTP only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INFER_SCRIPT = PROJECT_ROOT / "tools" / "oplora" / "infer_server.py"
OPLORA_PY = PROJECT_ROOT / ".venv-oplora" / "Scripts" / "python.exe"
# 8765 is the public world-status server (photo-finish.github.io/status/).
_STATUS_PORT = 8765
_requested_port = int(os.environ.get("AMPHOREUS_OPLORA_PORT", "8766"))
DEFAULT_PORT = 8766 if _requested_port == _STATUS_PORT else _requested_port
DEFAULT_BASE = f"http://127.0.0.1:{DEFAULT_PORT}"
PID_FILE = PROJECT_ROOT / "world_runtime" / "oplora_infer.pid"
LOG_FILE = PROJECT_ROOT / "world_runtime" / "oplora_infer.log"
LOG_ERR = PROJECT_ROOT / "world_runtime" / "oplora_infer.log.err"


def base_url() -> str:
    return os.environ.get("AMPHOREUS_OPLORA_URL", DEFAULT_BASE).rstrip("/")


def health(timeout: float = 2.0) -> dict[str, Any]:
    try:
        req = urllib.request.Request(f"{base_url()}/health", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def is_up() -> bool:
    h = health()
    return bool(h.get("ok"))


def generate(
    character_id: str,
    messages: list[dict],
    max_new_tokens: int = 256,
    timeout: float = 600.0,
) -> str:
    payload = json.dumps(
        {
            "character_id": character_id,
            "messages": messages,
            "max_new_tokens": max_new_tokens,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url()}/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            raise RuntimeError(f"OPLoRA infer HTTP {e.code}: {body}") from e
        raise RuntimeError(data.get("error") or body) from e
    except Exception as e:
        raise RuntimeError(
            f"OPLoRA infer unreachable ({base_url()}): {e}. "
            "Start it from the Control Panel, or run: "
            f"{OPLORA_PY} {INFER_SCRIPT}"
        ) from e
    if not data.get("ok"):
        raise RuntimeError(data.get("error") or "OPLoRA generate failed")
    return str(data.get("text") or "").strip()


def unload(timeout: float = 30.0) -> dict:
    try:
        req = urllib.request.Request(
            f"{base_url()}/unload", data=b"{}", method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def start_server() -> dict[str, Any]:
    """Detach-start infer_server with .venv-oplora. No-op if already up."""
    if is_up():
        return {"started": False, "already": True, "health": health()}
    if not OPLORA_PY.is_file():
        return {"started": False, "error": f"missing {OPLORA_PY}"}
    if not INFER_SCRIPT.is_file():
        return {"started": False, "error": f"missing {INFER_SCRIPT}"}
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]
    log_out = open(LOG_FILE, "a", encoding="utf-8")
    log_err = open(LOG_ERR, "a", encoding="utf-8")
    try:
        proc = subprocess.Popen(
            [str(OPLORA_PY), str(INFER_SCRIPT)],
            cwd=str(PROJECT_ROOT),
            stdout=log_out,
            stderr=log_err,
            creationflags=creationflags,
            close_fds=True,
        )
        PID_FILE.write_text(str(proc.pid), encoding="ascii")
    except Exception as e:
        return {"started": False, "error": str(e)}
    # First load can take a while; health before model load still returns ok.
    for _ in range(40):
        time.sleep(0.5)
        if is_up():
            return {"started": True, "pid": proc.pid, "health": health()}
    return {
        "started": True,
        "pid": proc.pid,
        "warning": "process launched but /health not yet answering",
        "log": str(LOG_FILE),
    }


def stop_server() -> dict[str, Any]:
    """Ask unload, then kill the pid if known."""
    unload_res = unload()
    killed = False
    pid: Optional[int] = None
    try:
        if PID_FILE.is_file():
            pid = int(PID_FILE.read_text(encoding="ascii").strip())
    except Exception:
        pid = None
    if pid:
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F", "/T"],
                    capture_output=True,
                    timeout=15,
                )
            else:
                os.kill(pid, 15)
            killed = True
        except Exception:
            pass
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
    return {"ok": True, "unload": unload_res, "killed": killed, "pid": pid}
