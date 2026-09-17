# -*- coding: utf-8 -*-
"""Front door / status guard: publish github.io when the host is actually up."""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from tools.status_guard import should_publish_front_door  # noqa: E402

PASSED, FAILED = [], []


def check(name, cond, extra=""):
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}  {extra}")


def main():
    print("== publish gate ==")
    check(
        "status tunnel alone is enough",
        should_publish_front_door(
            "https://a.trycloudflare.com", "", "http://Lambda.local:8765", "",
        ),
    )
    check(
        "empty status is not published",
        not should_publish_front_door(
            "", "https://ui.trycloudflare.com", "http://Lambda.local:8765",
            "http://Lambda.local:8501",
        ),
    )
    check(
        "full pair still publishes",
        should_publish_front_door(
            "https://a.trycloudflare.com", "https://b.trycloudflare.com",
            "http://Lambda.local:8765", "http://Lambda.local:8501",
        ),
    )

    print("== templates ==")
    status_html = open(
        os.path.join(ROOT, "tools", "frontdoor_status_template.html"),
        encoding="utf-8",
    ).read()
    sanctuary_html = open(
        os.path.join(ROOT, "tools", "frontdoor_sanctuary_template.html"),
        encoding="utf-8",
    ).read()
    check("status page retries live fetch", "tries < 6" in status_html)
    check("status page cache-busts", "Date.now()" in status_html)
    check("status page still has Zagreus copy", "Zagreus stole the host" in status_html)
    check("sanctuary probes healthz", "/healthz" in sanctuary_html)
    check("sanctuary probes Streamlit health", "/_stcore/health" in sanctuary_html)
    check("sanctuary retries", "tries < 6" in sanctuary_html)
    check(
        "sanctuary does not Zagreus on missing UI tunnel only",
        "waitingDoor" in sanctuary_html and "The host is awake" in sanctuary_html,
    )

    print("== server CORS ==")
    srv = open(
        os.path.join(ROOT, "tools", "world_status_server.py"), encoding="utf-8",
    ).read()
    check("status server answers OPTIONS", "def do_OPTIONS" in srv)
    check("status server allows origin *", 'Access-Control-Allow-Origin", "*"' in srv)

    print("== _push retry safety ==")
    guard = open(
        os.path.join(ROOT, "tools", "status_guard.py"), encoding="utf-8",
    ).read()
    check("_push initializes ok", "ok = False" in guard.split("def _push")[1][:200])
    check("clone uses check=True", '"clone"' in guard and "check=True" in guard)
    check("git ignores stale local proxy", "http.proxy=" in guard and "_git_env" in guard)

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
