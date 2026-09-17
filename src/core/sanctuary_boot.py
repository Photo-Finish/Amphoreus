# -*- coding: utf-8 -*-
"""Reliable Sanctuary boot: Streamlit first, localhost checks, no proxy.

The old .cmd waited on Invoke-WebRequest / Get-NetTCPConnection. Those honor
a stale IE proxy (127.0.0.1:12000) and can sit on “Waiting for the interface”
while Streamlit is either not started or already healthy. This module:

- probes 127.0.0.1 with raw TCP + urllib (proxy disabled)
- starts Streamlit with the file watcher off (transformers must not be scanned)
- does not wait for Ollama before the UI
- replaces an occupant of :8501 that is not healthy
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

UI_PORT = 8501
OLLAMA_PORT = 11434
HEALTH_URL = f"http://127.0.0.1:{UI_PORT}/_stcore/health"
UI_URL = f"http://127.0.0.1:{UI_PORT}"


def project_root() -> Path:
    env = os.environ.get("AMPHOREUS_ROOT", "").strip()
    if env:
        p = Path(env)
        if (p / "src" / "ui_app.py").is_file():
            return p.resolve()
    here = Path(__file__).resolve()
    for c in (here.parents[2], Path(r"D:\Workspace\Amphoreus")):
        if (c / "src" / "ui_app.py").is_file():
            return c.resolve()
    raise SystemExit("Could not find Amphoreus (src/ui_app.py).")


def find_python(root: Path) -> Path:
    for rel in (
        Path(".venv") / "Scripts" / "python.exe",
        Path("..") / ".venv" / "Scripts" / "python.exe",
    ):
        p = (root / rel).resolve()
        if p.is_file():
            return p
    sib = Path(r"D:\Workspace\.venv\Scripts\python.exe")
    if sib.is_file():
        return sib
    raise SystemExit(f"No Python venv found near {root}.")


def tcp_open(port: int, host: str = "127.0.0.1", timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _no_proxy_opener() -> urllib.request.OpenerDirector:
    # Passing ProxyHandler({}) replaces urllib's default handler (IE / env
    # proxies). An empty map has no protocol methods, so traffic goes direct.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def ui_healthy(timeout: float = 1.5) -> bool:
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with _no_proxy_opener().open(req, timeout=timeout) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            return 200 <= int(code) < 300
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def pids_listening(port: int) -> list[int]:
    """PIDs bound to TCP port (Windows netstat; empty if unknown)."""
    found: list[int] = []
    try:
        out = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return found
    needle = f":{port} "
    for line in (out.stdout or "").splitlines():
        if "LISTENING" not in line.upper() or needle not in line:
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        if pid > 0 and pid not in found:
            found.append(pid)
    return found


def kill_pids(pids: list[int]) -> None:
    for pid in pids:
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                capture_output=True,
                timeout=12,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            pass


def clear_unhealthy_ui() -> None:
    if ui_healthy():
        return
    if not tcp_open(UI_PORT):
        return
    kill_pids(pids_listening(UI_PORT))
    time.sleep(0.6)


def streamlit_cmd(python: Path, root: Path) -> list[str]:
    app = root / "src" / "ui_app.py"
    return [
        str(python),
        "-m",
        "streamlit",
        "run",
        str(app),
        "--server.headless",
        "true",
        "--server.port",
        str(UI_PORT),
        "--server.address",
        "127.0.0.1",
        "--server.fileWatcherType",
        "none",
        "--browser.gatherUsageStats",
        "false",
    ]


def _ui_env(root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = "127.0.0.1,localhost"
    env.setdefault("SENSES_MODE", "unified")
    env.setdefault("AMPHOREUS_ROOT", str(root))
    env.setdefault("STREAMLIT_BROWSER_SERVER_ADDRESS", "127.0.0.1")
    env.setdefault("STREAMLIT_BROWSER_SERVER_PORT", str(UI_PORT))
    env.pop("HTTP_PROXY", None)
    env.pop("HTTPS_PROXY", None)
    env.pop("ALL_PROXY", None)
    env.pop("http_proxy", None)
    env.pop("https_proxy", None)
    return env


def start_streamlit(root: Path, python: Path) -> Optional[subprocess.Popen]:
    runtime = root / "world_runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    log = open(runtime / "ui.log", "a", encoding="utf-8")
    err = open(runtime / "ui.log.err", "a", encoding="utf-8")
    proc = subprocess.Popen(
        streamlit_cmd(python, root),
        cwd=str(root),
        env=_ui_env(root),
        stdout=log,
        stderr=err,
        creationflags=creation,
    )
    (runtime / "ui.pid").write_text(str(proc.pid), encoding="ascii")
    return proc


def wait_ui(
    seconds: float = 90.0,
    proc: Optional[subprocess.Popen] = None,
    on_tick=None,
) -> bool:
    start = time.time()
    deadline = start + seconds
    last_tick = -10.0
    while time.time() < deadline:
        if ui_healthy():
            return True
        if proc is not None and proc.poll() is not None:
            return False
        elapsed = time.time() - start
        if on_tick is not None and elapsed - last_tick >= 3.0:
            on_tick(elapsed)
            last_tick = elapsed
        time.sleep(0.3)
    return False


def _pid_alive(pid_file: Path) -> bool:
    try:
        pid = int(pid_file.read_text(encoding="ascii").strip())
        if pid > 0:
            os.kill(pid, 0)
            return True
    except OSError:
        pass
    except Exception:
        pass
    return False


def start_world_engine(root: Path, python: Path) -> None:
    runtime = root / "world_runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    pid_file = runtime / "engine.pid"
    if _pid_alive(pid_file):
        return
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.Popen(
        [str(python), "-m", "src.world.world_engine", "--interval", "900"],
        cwd=str(root),
        stdout=open(runtime / "engine.log", "a", encoding="utf-8"),
        stderr=open(runtime / "engine.log.err", "a", encoding="utf-8"),
        env=env,
        creationflags=creation,
    )
    try:
        pid_file.write_text(str(proc.pid), encoding="ascii")
    except Exception:
        pass


def start_status_guard(root: Path, python: Path) -> None:
    """Keep github.io pointed at live tunnels. Background; never blocks boot."""
    script = root / "tools" / "status_guard.py"
    if not script.is_file():
        return
    runtime = root / "world_runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    pid_file = runtime / "status_guard.pid"
    if _pid_alive(pid_file):
        return
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    for key in list(env):
        if key.upper() in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}:
            env.pop(key, None)
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.Popen(
        [str(python), str(script)],
        cwd=str(root),
        stdout=open(runtime / "status_guard.log", "a", encoding="utf-8"),
        stderr=open(runtime / "status_guard.log.err", "a", encoding="utf-8"),
        env=env,
        creationflags=creation,
    )
    try:
        pid_file.write_text(str(proc.pid), encoding="ascii")
    except Exception:
        pass


def start_ollama_background(root: Path) -> None:
    if tcp_open(OLLAMA_PORT):
        return
    ps1 = root / "tools" / "start_ollama.ps1"
    if not ps1.is_file():
        return
    try:
        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ps1),
            ],
            cwd=str(root),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        pass


def open_browser() -> None:
    try:
        if sys.platform == "win32":
            os.startfile(UI_URL)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", UI_URL])
    except Exception:
        pass


def ensure_interface(
    root: Path,
    python: Path,
    *,
    wait_s: float = 90.0,
    on_tick=None,
) -> bool:
    """Make Streamlit healthy on :8501. Returns True if the UI answers."""
    if ui_healthy():
        return True
    clear_unhealthy_ui()
    if ui_healthy():
        return True
    proc = start_streamlit(root, python)
    return wait_ui(wait_s, proc=proc, on_tick=on_tick)


def last_ui_errors(root: Path, n: int = 24) -> str:
    path = root / "world_runtime" / "ui.log.err"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-n:])
    except Exception:
        return ""
