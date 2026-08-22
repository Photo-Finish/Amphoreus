# -*- coding: utf-8 -*-
"""Amphoreus Sanctuary — desktop window shell (Stage 2).

Opens the existing Streamlit UI inside a native OS window (pywebview),
while leaving ``launch_sanctuary.cmd`` / browser tabs fully intact.

Thin shell: Streamlit still runs from the project venv on localhost:8501.
This process only hosts the window and (optionally) starts/stops the UI.

Usage (from repo root)::

    D:\\Workspace\\.venv\\Scripts\\python.exe tools\\desktop_sanctuary.py

Or the built ``AmphoreusSanctuary.exe`` next to / inside the project.
"""
from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

UI_PORT = 8501
OLLAMA_PORT = 11434
URL = f"http://127.0.0.1:{UI_PORT}"
CREATION_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_started_ui: subprocess.Popen | None = None
_started_engine = False


def _frozen_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def find_root() -> Path:
    """Locate the Amphoreus repo (must contain src/ui_app.py)."""
    env = os.environ.get("AMPHOREUS_ROOT", "").strip()
    if env:
        p = Path(env)
        if (p / "src" / "ui_app.py").is_file():
            return p.resolve()

    here = _frozen_dir()
    candidates = [
        here,
        here.parent,
        here.parent.parent,
        Path(r"D:\Workspace\Amphoreus"),
    ]
    # Walk up a few levels from the exe / script.
    cur = here
    for _ in range(5):
        candidates.append(cur)
        cur = cur.parent

    for c in candidates:
        try:
            if (c / "src" / "ui_app.py").is_file():
                return c.resolve()
        except OSError:
            continue
    raise SystemExit(
        "Could not find Amphoreus (src/ui_app.py).\n"
        "Place AmphoreusSanctuary.exe inside the project folder, or set "
        "AMPHOREUS_ROOT."
    )


def find_python(root: Path) -> Path:
    for rel in (
        Path(".venv") / "Scripts" / "python.exe",
        Path("..") / ".venv" / "Scripts" / "python.exe",
    ):
        p = (root / rel).resolve()
        if p.is_file():
            return p
    # Sibling Workspace venv (historical layout).
    sib = Path(r"D:\Workspace\.venv\Scripts\python.exe")
    if sib.is_file():
        return sib
    raise SystemExit(
        f"No Python venv found near {root}.\n"
        "Expected .venv\\Scripts\\python.exe (or D:\\Workspace\\.venv)."
    )


def port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def wait_port(port: int, seconds: float = 90.0) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if port_open(port):
            return True
        time.sleep(0.4)
    return False


def ensure_ollama(root: Path) -> None:
    if port_open(OLLAMA_PORT):
        return
    ps1 = root / "tools" / "start_ollama.ps1"
    if not ps1.is_file():
        return
    try:
        subprocess.Popen(
            [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(ps1),
            ],
            cwd=str(root),
            creationflags=CREATION_FLAGS,
        )
        wait_port(OLLAMA_PORT, 45)
    except Exception:
        pass


def ensure_world_engine(root: Path, python: Path) -> None:
    global _started_engine
    try:
        out = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | "
                "Where-Object { $_.CommandLine -match 'world_engine' } | "
                "Select-Object -First 1",
            ],
            capture_output=True, text=True, timeout=20,
        )
        if (out.stdout or "").strip():
            return
    except Exception:
        pass
    runtime = root / "world_runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.Popen(
            [
                str(python), "-m", "src.world.world_engine",
                "--interval", "900",
            ],
            cwd=str(root),
            stdout=open(runtime / "engine.log", "a", encoding="utf-8"),
            stderr=open(runtime / "engine.log.err", "a", encoding="utf-8"),
            creationflags=CREATION_FLAGS,
        )
        _started_engine = True
    except Exception:
        pass


def ensure_streamlit(root: Path, python: Path) -> None:
    global _started_ui
    if port_open(UI_PORT):
        return
    runtime = root / "world_runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("SENSES_MODE", "unified")
    ui_app = root / "src" / "ui_app.py"
    _started_ui = subprocess.Popen(
        [
            str(python), "-m", "streamlit", "run", str(ui_app),
            "--server.headless", "true",
            "--server.port", str(UI_PORT),
            "--browser.gatherUsageStats", "false",
            "--server.address", "127.0.0.1",
        ],
        cwd=str(root),
        env=env,
        stdout=open(runtime / "ui_desktop.log", "a", encoding="utf-8"),
        stderr=open(runtime / "ui_desktop.log.err", "a", encoding="utf-8"),
        creationflags=CREATION_FLAGS,
    )
    (runtime / "ui_desktop.pid").write_text(
        str(_started_ui.pid), encoding="ascii")
    if not wait_port(UI_PORT, 90):
        raise SystemExit(
            f"Streamlit did not open on port {UI_PORT}.\n"
            f"See {runtime / 'ui_desktop.log.err'}"
        )


def cleanup() -> None:
    global _started_ui
    if _started_ui is not None:
        try:
            _started_ui.terminate()
            try:
                _started_ui.wait(timeout=8)
            except Exception:
                _started_ui.kill()
        except Exception:
            pass
        _started_ui = None
        # Also clear anything still bound to the UI port if we started it.
        try:
            out = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    f"(Get-NetTCPConnection -LocalPort {UI_PORT} -State Listen "
                    "-ErrorAction SilentlyContinue).OwningProcess",
                ],
                capture_output=True, text=True, timeout=15,
            )
            for tok in (out.stdout or "").split():
                try:
                    pid = int(tok.strip())
                    if pid > 0:
                        subprocess.run(
                            ["taskkill", "/PID", str(pid), "/F", "/T"],
                            capture_output=True, timeout=10,
                        )
                except Exception:
                    pass
        except Exception:
            pass


def open_window(title: str = "Amphoreus Sanctuary") -> None:
    try:
        import webview
    except ImportError as e:
        raise SystemExit(
            "pywebview is required for the desktop window.\n"
            "Install:  python -m pip install pywebview\n"
            f"({e})"
        ) from e

    window = webview.create_window(
        title,
        URL,
        width=1280,
        height=860,
        min_size=(900, 600),
        confirm_close=False,
        text_select=True,
    )
    # Edge WebView2 on Windows; falls back if needed.
    webview.start(gui="edgechromium", debug=False)
    # When the window closes, start() returns.
    _ = window


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    skip_engine = "--no-engine" in argv
    skip_ollama = "--no-ollama" in argv
    browser_also = "--also-browser" in argv

    root = find_root()
    python = find_python(root)
    os.chdir(root)
    # Help Streamlit / Ollama find project paths.
    os.environ.setdefault("AMPHOREUS_ROOT", str(root))

    atexit.register(cleanup)

    if not skip_ollama:
        ensure_ollama(root)
    if not skip_engine:
        ensure_world_engine(root, python)
    ensure_streamlit(root, python)

    if browser_also:
        try:
            os.startfile(URL)  # type: ignore[attr-defined]
        except Exception:
            pass

    open_window()
    cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
