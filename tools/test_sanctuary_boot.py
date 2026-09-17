# -*- coding: utf-8 -*-
"""Sanctuary boot: Streamlit first, no-proxy health, watcher off."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from src.core.sanctuary_boot import (  # noqa: E402
    HEALTH_URL,
    UI_PORT,
    _no_proxy_opener,
    _ui_env,
    start_status_guard,
    streamlit_cmd,
    tcp_open,
    ui_healthy,
    wait_ui,
)

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def main():
    python = Path(sys.executable)
    root = Path(ROOT)

    print("== streamlit command ==")
    cmd = streamlit_cmd(python, root)
    check("runs src/ui_app.py", str(root / "src" / "ui_app.py") in cmd)
    check("binds 127.0.0.1", "127.0.0.1" in cmd)
    check("port 8501", str(UI_PORT) in cmd)
    check("file watcher off", "--server.fileWatcherType" in cmd and "none" in cmd)
    check("headless", "true" in cmd)

    print("== UI env ==")
    env = _ui_env(root)
    check("watcher env off", env.get("STREAMLIT_SERVER_FILE_WATCHER_TYPE") == "none")
    check("NO_PROXY localhost", "127.0.0.1" in env.get("NO_PROXY", ""))
    check("HTTP_PROXY stripped", "HTTP_PROXY" not in env and "http_proxy" not in env)
    check("senses default unified", env.get("SENSES_MODE") == "unified")

    print("== health probe ==")
    opener = _no_proxy_opener()
    proxy_maps = [getattr(h, "proxies", None) for h in opener.handlers]
    proxy_maps = [p for p in proxy_maps if p]
    check("opener has no proxy URLs", not proxy_maps, str(proxy_maps))
    check("health URL is loopback", HEALTH_URL.startswith("http://127.0.0.1:8501/"))
    check("closed high port is not TCP-open", not tcp_open(9, timeout=0.2))
    # Nothing required on 8501 for this assertion: a refused port is unhealthy.
    if not tcp_open(UI_PORT, timeout=0.3):
        check("refused 8501 is not healthy", ui_healthy(timeout=0.6) is False)
    else:
        print("  skip refused-port healthy check (8501 is already listening)")

    print("== wait_ui fail-fast ==")
    class Dead:
        def poll(self):
            return 1
    with mock.patch("src.core.sanctuary_boot.ui_healthy", return_value=False):
        check("dead process fails wait immediately",
              wait_ui(5.0, proc=Dead()) is False)

    print("== wait_ui healthy short-circuit ==")
    with mock.patch("src.core.sanctuary_boot.ui_healthy", return_value=True):
        check("healthy UI returns at once", wait_ui(30.0) is True)

    print("== cmd launcher ==")
    cmd_text = (root / "launch_sanctuary.cmd").read_text(encoding="utf-8")
    check("cmd calls Python boot", "tools\\boot_sanctuary.py" in cmd_text)
    check("cmd does not Invoke-WebRequest", "Invoke-WebRequest" not in cmd_text)
    check("cmd does not Get-NetTCPConnection", "Get-NetTCPConnection" not in cmd_text)
    check("cmd does not wait-loop label", ":wait_ui" not in cmd_text)
    check("cmd still sets SENSES_MODE", "SENSES_MODE=unified" in cmd_text)

    print("== public front door hook ==")
    boot_py = (root / "tools" / "boot_sanctuary.py").read_text(encoding="utf-8")
    desk_py = (root / "tools" / "desktop_sanctuary.py").read_text(encoding="utf-8")
    check("boot starts status guard", "start_status_guard" in boot_py)
    check("boot has --no-guard", "--no-guard" in boot_py)
    check("desktop starts status guard", "start_status_guard" in desk_py)
    check(
        "start_status_guard is callable",
        callable(start_status_guard),
    )
    guard_src = (root / "src" / "core" / "sanctuary_boot.py").read_text(encoding="utf-8")
    check(
        "guard pid file is recorded",
        "status_guard.pid" in guard_src and "tools" in guard_src
        and "status_guard.py" in guard_src,
    )

    print("== streamlit config ==")
    cfg = (root / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    check("config disables file watcher", 'fileWatcherType = "none"' in cfg)

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
