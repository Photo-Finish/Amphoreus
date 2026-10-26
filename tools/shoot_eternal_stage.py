# -*- coding: utf-8 -*-
"""Render the Eternal Page stage to PNG — the art QA loop, without Streamlit.

    python tools/shoot_eternal_stage.py                 # idle and all-near
    python tools/shoot_eternal_stage.py --out my.png    # one shot, idle
    python tools/shoot_eternal_stage.py --no-browser    # just write the HTML

Builds exactly the markup `render_eternal_page` hands to `st.components.html`
(same `stage_art_uris`, same `build_stage_html`), writes it beside the PNG, and
screenshots it with Playwright's Chromium. This is how the sill is judged: the
Read tool ignores PNG alpha, so a composite is the only honest look at the art.

Output goes to `world_runtime/art_review/` (gitignored) unless `--out` says
otherwise. Needs `playwright` + its Chromium; skips the screenshot and keeps the
HTML when they are missing.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

VIEWPORT = {"width": 1100, "height": 560}


def build_html(selected: list[str]) -> str:
    from src.world import art_cache
    from src.world import eternal_page as ep
    from src.ui_eternal_page import _data_uri, build_stage_html, stage_art_uris

    parchment = ep.parchment_path()
    return build_stage_html(
        selected=selected,
        art=stage_art_uris({}),
        names={cid: ep.short_name(cid) for cid in ep.all_ids()},
        parchment_uri=(
            _data_uri(parchment, max_px=art_cache.PARCHMENT_MAX_PX) if parchment else ""
        ),
        emotions={},
        layout={},
        gestures={},
    )


def main(argv: list[str]) -> int:
    from src.world import eternal_page as ep

    out_dir = ROOT / "world_runtime" / "art_review"
    if "--out" in argv:
        target = Path(argv[argv.index("--out") + 1])
        out_dir = target.parent
        shots = [("idle", [], target)]
    else:
        shots = [
            ("idle", [], out_dir / "stage_idle.png"),
            ("all", list(ep.all_ids()), out_dir / "stage_all.png"),
        ]
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = []
    for name, selected, png in shots:
        html = out_dir / f"{png.stem}.html"
        html.write_text(build_html(selected), encoding="utf-8")
        pages.append((name, html, png))
        print(f"wrote {html.relative_to(ROOT)}  ({html.stat().st_size / 1024:.0f} KB)")

    if "--no-browser" in argv:
        return 0
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("playwright not installed — HTML written, no screenshot")
        return 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)
            for name, html, png in pages:
                page.goto(html.resolve().as_uri())
                page.wait_for_timeout(400)
                page.screenshot(path=str(png))
                print(f"shot  {png.relative_to(ROOT)}  ({name})")
            browser.close()
    except Exception as exc:
        print(f"screenshot failed ({exc.__class__.__name__}: {exc}) — HTML kept")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
