"""Audit Life-on-the-land stacking and native scroll (no wheel hijack)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ui_scene_life import pictorial_stage_documents

scene = [
    {
        "id": "c1",
        "kind": "chimera",
        "name": "Chimera",
        "clickable": True,
        "doing": "grazing",
        "hotspot": {"left": "50%", "bottom": "18%"},
    }
]
docs = pictorial_stage_documents(
    None,
    "Okhema",
    "none",
    "",
    scene,
    page_layer=True,
    entities=True,
    dense=True,
)
html = docs[0] if docs else ""
weather_src = (ROOT / "src" / "ui_weather.py").read_text(encoding="utf-8")
checks = {
    "html/body pointer-events:none": (
        "background:transparent;overflow:hidden;pointer-events:none;}" in html
        and "pointer-events:none;" in html.split("html,body")[1][:120]
    ),
    "iframe pointer-events:none in pin_js": "pointer-events:none;" in html.split("f.style.cssText")[1][:180],
    "no wheel hijack": "passScroll" not in html and "addEventListener('wheel'" not in html,
    "parent sprite hit-test": "hitSprite" in html and "__ampLandLifeClick" in html,
    "notice host hoist": "amp-land-notice-host" in html and "syncNoticeHost" in html,
    "sprite pointer-events:auto": ".amp-sprite {" in html and "pointer-events: auto;" in html,
    "photo host mounts in app shell": "landMount" in html and "stAppViewContainer" in html,
    "life iframe z-index 55": "z-index:55" in html,
    "notice z-index 400": "var z = 400;" in html or "z-index:'+z+" in html,
    "life shell promoted": "pinLifeShell" in html,
    "pictorial copy under life": "z-index: 5 !important" in weather_src,
}
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
if not all(checks.values()):
    raise SystemExit(1)

from src.ui_look import look_chrome_css

if "stAppViewContainer" not in weather_src.split("page_backdrop_css", 1)[1][:4000]:
    print("FAIL: ui_weather app shell z-index for photo host")
    raise SystemExit(1)
print("PASS: ui_weather app shell z-index for photo host")
life_block = weather_src.split("iframe[data-amp-land-life", 1)[1]
if "z-index: 55 !important;" not in life_block[:800]:
    print("FAIL: ui_weather life iframe z-index")
    raise SystemExit(1)
print("PASS: ui_weather life iframe z-index")
if "pointer-events: none !important;" not in life_block[:800]:
    print("FAIL: ui_weather life iframe CSS")
    raise SystemExit(1)
print("PASS: ui_weather life iframe CSS")
if "#amp-land-notice-host" not in weather_src or "z-index: 400" not in weather_src:
    print("FAIL: ui_weather notice host z-index")
    raise SystemExit(1)
print("PASS: ui_weather notice host z-index")
if "iframe[data-amp-land-life" not in look_chrome_css():
    print("FAIL: ui_look life iframe CSS")
    raise SystemExit(1)
print("PASS: ui_look life iframe CSS")
print("All audits passed.")
