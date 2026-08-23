"""Audit Life-on-the-land scroll pass-through markup."""
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
checks = {
    "html/body pointer-events:none": "html,body{margin:0;padding:0;width:100%;height:100%;"
    "background:transparent;overflow:hidden;pointer-events:none;}" in html,
    "iframe pointer-events:none in pin_js": "pointer-events:none;" in html.split("f.style.cssText")[1][:120],
    "wheel passScroll": "passScroll" in html and "addEventListener('wheel'" in html,
    "touch pass": "addEventListener('touchmove'" in html,
    "sprite pointer-events:auto": ".amp-sprite {" in html and "pointer-events: auto;" in html,
}
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
if not all(checks.values()):
    raise SystemExit(1)

from src.ui_look import look_chrome_css
from src.ui_weather import page_backdrop_css

css = look_chrome_css() + page_backdrop_css.__doc__
weather_src = (ROOT / "src" / "ui_weather.py").read_text(encoding="utf-8")
life_block = weather_src.split("iframe[data-amp-land-life", 1)[1]
if "pointer-events: none !important;" not in life_block[:800]:
    print("FAIL: ui_weather life iframe CSS")
    raise SystemExit(1)
print("PASS: ui_weather life iframe CSS")
if "iframe[data-amp-land-life" not in look_chrome_css():
    print("FAIL: ui_look life iframe CSS")
    raise SystemExit(1)
print("PASS: ui_look life iframe CSS")
print("All audits passed.")
