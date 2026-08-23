# -*- coding: utf-8 -*-
"""Probe Walk the Land scroll with Life on."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8721"
auth_path = ROOT / "world_runtime" / "ui_auth.json"


def login(page):
    page.goto(BASE + "/?amp_guest=1", wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(3000)
    if page.get_by_role("textbox", name="Username").count():
        auth = json.loads(auth_path.read_text(encoding="utf-8"))
        page.get_by_role("textbox", name="Username").fill(auth["username"])
        page.get_by_role("textbox", name="Password").fill(auth["password"])
        page.get_by_role("button", name="Enter the Sanctuary").click()
        for _ in range(40):
            page.wait_for_timeout(800)
            if "Walk the Land" in page.inner_text("body"):
                break


def scroll_metrics(page) -> dict:
    return page.evaluate(
        """() => {
          const life = document.querySelector('iframe[data-amp-land-life="1"]');
          const pe = life ? getComputedStyle(life).pointerEvents : null;
          const candidates = [
            document.scrollingElement,
            document.documentElement,
            document.body,
            document.querySelector('[data-testid="stAppViewContainer"]'),
            document.querySelector('section[data-testid="stMain"]'),
            document.querySelector('[data-testid="stMainBlockContainer"]'),
          ].filter(Boolean);
          const tops = candidates.map((el) => ({
            tag: el.tagName + (el.dataset && el.dataset.testid ? '[' + el.dataset.testid + ']' : ''),
            scrollTop: el.scrollTop || 0,
            scrollHeight: el.scrollHeight || 0,
            clientHeight: el.clientHeight || 0,
          }));
          const doc = document.scrollingElement || document.documentElement;
          return {
            scrollTop: doc.scrollTop,
            scrollHeight: doc.scrollHeight,
            clientHeight: doc.clientHeight,
            lifeIframePe: pe,
            tops,
          };
        }"""
    )


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        login(page)
        page.get_by_role("tab", name=re.compile(r"Walk the Land", re.I)).first.click()
        page.wait_for_timeout(5000)
        # Ensure pictorial + life on
        life = page.locator('[data-testid="stToggle"], [data-testid="stCheckbox"]').filter(
            has_text=re.compile(r"Life on the land", re.I)
        )
        if life.count():
            inp = life.first.locator("input")
            if inp.count() and not inp.is_checked():
                life.first.click()
                page.wait_for_timeout(4000)
        pict = page.get_by_text(re.compile(r"Pictures on the land", re.I))
        if pict.count():
            pict.first.click()
            page.wait_for_timeout(3000)
        before = scroll_metrics(page)
        # Scroll over a life sprite in the visible Walk tab (not empty sky).
        sprite_box = page.evaluate(
            """() => {
              const panel = [...document.querySelectorAll('[data-testid="stTabPanel"]')]
                .find(p => !p.hidden && p.querySelector('iframe[data-amp-land-life="1"]'));
              const f = panel && panel.querySelector('iframe[data-amp-land-life="1"]');
              if (!f || !f.contentDocument) return null;
              const sp = f.contentDocument.querySelector('.amp-sprite');
              if (!sp) return null;
              const r = sp.getBoundingClientRect();
              if (r.width < 4 || r.height < 4) return null;
              return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }"""
        )
        if sprite_box:
            page.mouse.move(sprite_box["x"], sprite_box["y"])
        else:
            page.mouse.move(640, 360)
        for _ in range(4):
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(250)
        page.wait_for_timeout(500)
        after = scroll_metrics(page)
        browser.close()

    moved = after["scrollTop"] - before["scrollTop"]
    main_before = next((t for t in before["tops"] if t["tag"] == "SECTION[stMain]"), {})
    main_after = next((t for t in after["tops"] if t["tag"] == "SECTION[stMain]"), {})
    main_moved = main_after.get("scrollTop", 0) - main_before.get("scrollTop", 0)
    print("before:", before)
    print("after:", after)
    print("scroll_delta:", moved, "stMain_delta:", main_moved)
    ok = before["lifeIframePe"] == "none" and main_moved > 80
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
