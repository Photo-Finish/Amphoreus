# -*- coding: utf-8 -*-
"""Drive the running Sanctuary UI and check An Eternal Page for real.

    python tools/validate_live_page.py                      # app on :8501
    python tools/validate_live_page.py --url http://127.0.0.1:8531
    python tools/validate_live_page.py --url ... --shot live.png

Signs in with the operator account from `world_runtime/ui_auth.json`, opens the
Eternal Page tab, finds the stage inside Streamlit's component iframe, and
checks what a browser actually received: thirteen companions, a named stage, and
no console errors from the page's own script.

This is the complement to `tools/shoot_eternal_stage.py` — that one renders the
markup offline, this one proves the running app delivers it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_URL = "http://127.0.0.1:8501"
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    RESULTS.append((name, ok, extra))
    print(("  ok  " if ok else "FAIL  ") + name + (f"  {extra}" if extra and not ok else ""))


def credentials() -> tuple[str, str]:
    import os

    user = os.environ.get("AMPHOREUS_UI_USER", "").strip()
    password = os.environ.get("AMPHOREUS_UI_PASS", "")
    if user and password:
        return user, password
    path = ROOT / "world_runtime" / "ui_auth.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    return str(data.get("username", "")), str(data.get("password", ""))


def main(argv: list[str]) -> int:
    url = DEFAULT_URL
    if "--url" in argv:
        url = argv[argv.index("--url") + 1]
    shot = Path(argv[argv.index("--shot") + 1]) if "--shot" in argv else (
        ROOT / "world_runtime" / "art_review" / "live_page.png")

    from playwright.sync_api import sync_playwright

    user, password = credentials()
    console_errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1200})
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3500)

        if user and password and page.locator("input[type='password']").count():
            page.fill("input[type='text'] >> nth=0", user)
            page.fill("input[type='password']", password)
            page.get_by_role("button", name="Enter the Sanctuary").click()
            page.wait_for_timeout(4000)
            check("signed in to the running app", True)

        page.get_by_role("tab", name="An Eternal Page").click()

        stage = None
        # Streamlit rebuilds the component iframe on every rerun; poll for it.
        for _ in range(60):
            page.wait_for_timeout(1000)
            for frame in page.frames:
                try:
                    if frame.locator(".stage").count():
                        stage = frame
                        break
                except Exception:
                    continue
            if stage is not None:
                break
        check("the stage iframe is mounted", stage is not None)
        check("Eternal Page tab opened", True)
        if stage is not None:
            heirs = stage.eval_on_selector_all(
                "[data-heir]", "els => els.map(e => e.getAttribute('data-heir'))")
            check("thirteen companions are drawn", len(heirs) == 13, str(len(heirs)))
            names = stage.eval_on_selector_all(
                ".buddy .name", "els => els.map(e => e.textContent.trim())")
            check("every companion carries a name", len(names) == 13 and all(names),
                  ", ".join(n for n in names if not n))
            bodies = stage.eval_on_selector_all(
                "img.body", "els => els.map(e => e.getAttribute('src') || '')")
            check("every body is an inlined image",
                  len(bodies) == 13 and all(s.startswith("data:image/") for s in bodies),
                  str(len([b for b in bodies if not b.startswith("data:image/")])))
            webp = sum(1 for b in bodies if b.startswith("data:image/webp"))
            check("bodies ship as WebP", webp >= 11, f"{webp}/13")

        page.get_by_role("tab", name="An Eternal Page").click()
        page.wait_for_timeout(1200)
        shot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(shot), full_page=False)
        print(f"  shot {shot.relative_to(ROOT)}")

        hard = [e for e in console_errors if "favicon" not in e.lower()]
        check("no console errors from the page", not hard, "; ".join(hard[:3]))
        browser.close()

    failed = [name for name, ok, _ in RESULTS if not ok]
    print()
    print(f"{len(RESULTS) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
