"""Visit / Walk scene life — figures on the page art, not a second picture.

Area art is the Streamlit page backdrop. Interactive outdoor figures use
AI-painted PNGs; grass/wind/wheat/dawn are CSS or SVG. Clicks run inside
``st.components.v1.html`` and set ``?amp_notice=`` on the parent (preserving
``amp_guest``). Readable copy sits in glass panels.
"""
from __future__ import annotations

import html as _html
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------- #
# SVG silhouettes (viewBox 0 0 40 40) — one glyph per kind
# --------------------------------------------------------------------- #

_SPRITE_PATHS: Dict[str, str] = {
    "chimera": (
        '<ellipse cx="20" cy="24" rx="12" ry="8" fill="#e8d5a3"/>'
        '<circle cx="14" cy="16" r="5" fill="#f0e6c8"/>'
        '<circle cx="26" cy="16" r="5" fill="#f0e6c8"/>'
        '<circle cx="13" cy="15" r="1.2" fill="#1a1428"/>'
        '<circle cx="25" cy="15" r="1.2" fill="#1a1428"/>'
    ),
    "dromas": (
        '<ellipse cx="20" cy="26" rx="14" ry="9" fill="#c9a86a"/>'
        '<rect x="28" y="10" width="5" height="16" rx="2" fill="#b8955a"/>'
        '<circle cx="31" cy="9" r="3.5" fill="#d4b87a"/>'
    ),
    "hearth_cat": (
        '<ellipse cx="20" cy="26" rx="10" ry="7" fill="#d8c8a8"/>'
        '<circle cx="20" cy="18" r="6" fill="#e6d6b6"/>'
        '<polygon points="14,14 12,6 18,12" fill="#e6d6b6"/>'
        '<polygon points="26,14 28,6 22,12" fill="#e6d6b6"/>'
    ),
    "well": (
        '<ellipse cx="20" cy="28" rx="12" ry="5" fill="#6a8a9a"/>'
        '<rect x="10" y="14" width="20" height="14" fill="#8a7a68"/>'
        '<ellipse cx="20" cy="14" rx="10" ry="4" fill="#4a6a7a"/>'
    ),
    "fountain": (
        '<ellipse cx="20" cy="30" rx="14" ry="5" fill="#7a9aaa"/>'
        '<circle cx="20" cy="18" r="4" fill="#a8c8d8"/>'
        '<path d="M20 8 Q24 14 20 18 Q16 14 20 8" fill="#c0dce8"/>'
    ),
    "olive": (
        '<ellipse cx="20" cy="22" rx="11" ry="14" fill="#4a7a48"/>'
        '<ellipse cx="16" cy="20" rx="3" ry="4" fill="#6a9a58"/>'
        '<ellipse cx="24" cy="24" rx="3" ry="4" fill="#3a6a38"/>'
    ),
    "cicada": (
        '<ellipse cx="20" cy="22" rx="6" ry="10" fill="#8a9a5a"/>'
        '<ellipse cx="14" cy="20" rx="5" ry="8" fill="#a8b878" opacity=".85"/>'
        '<ellipse cx="26" cy="20" rx="5" ry="8" fill="#a8b878" opacity=".85"/>'
    ),
    "boat": (
        '<path d="M6 22 L34 22 L28 30 L12 30 Z" fill="#8a6a48"/>'
        '<line x1="20" y1="8" x2="20" y2="22" stroke="#c9b896" stroke-width="2"/>'
        '<path d="M20 8 L30 20 L20 20 Z" fill="#e8d5a3" opacity=".7"/>'
    ),
    "pearl": (
        '<circle cx="20" cy="20" r="9" fill="#e8f0f4"/>'
        '<circle cx="17" cy="17" r="3" fill="#fff" opacity=".7"/>'
    ),
    "pebble": (
        '<ellipse cx="20" cy="22" rx="10" ry="7" fill="#9a9080"/>'
        '<ellipse cx="17" cy="20" rx="3" ry="2" fill="#b0a898" opacity=".5"/>'
    ),
    "shore": (
        '<path d="M4 24 Q12 18 20 24 Q28 30 36 22 L36 34 L4 34 Z" fill="#5a8aaa"/>'
        '<path d="M4 26 Q14 20 22 26 Q30 32 36 24" fill="none" stroke="#a8d0e0" stroke-width="1.5"/>'
    ),
    "siren": (
        '<path d="M8 28 Q20 8 32 28" fill="none" stroke="#c9a8d8" stroke-width="2"/>'
        '<circle cx="20" cy="14" r="4" fill="#e0c8f0"/>'
    ),
    "forge": (
        '<rect x="8" y="18" width="24" height="14" fill="#4a3a30"/>'
        '<path d="M12 18 L20 8 L28 18" fill="#c95a3a"/>'
        '<rect x="16" y="22" width="8" height="6" fill="#1a1010"/>'
    ),
    "banner": (
        '<line x1="12" y1="6" x2="12" y2="34" stroke="#c9b896" stroke-width="2"/>'
        '<path d="M12 8 L30 12 L12 20 Z" fill="#c94a4a"/>'
    ),
    "lamp": (
        '<rect x="17" y="22" width="6" height="10" fill="#6a5a48"/>'
        '<ellipse cx="20" cy="16" rx="8" ry="7" fill="#e8c86a"/>'
        '<circle cx="20" cy="14" r="3" fill="#fff0c0"/>'
    ),
    "hearth": (
        '<path d="M8 30 L12 14 L28 14 L32 30 Z" fill="#5a4030"/>'
        '<ellipse cx="20" cy="20" rx="6" ry="8" fill="#e87830"/>'
        '<ellipse cx="20" cy="18" rx="3" ry="5" fill="#f0c060"/>'
    ),
    "shrine": (
        '<rect x="12" y="18" width="16" height="14" fill="#8a7a68"/>'
        '<path d="M8 18 L20 8 L32 18 Z" fill="#c9b896"/>'
        '<circle cx="20" cy="24" r="2.5" fill="#e8d5a3"/>'
    ),
    "market_stall": (
        '<path d="M6 16 L20 8 L34 16" fill="#c94a4a"/>'
        '<rect x="10" y="16" width="20" height="14" fill="#d8c8a8"/>'
        '<line x1="10" y1="16" x2="10" y2="32" stroke="#6a5a48" stroke-width="2"/>'
        '<line x1="30" y1="16" x2="30" y2="32" stroke="#6a5a48" stroke-width="2"/>'
    ),
    "gate": (
        '<path d="M8 34 L8 12 Q20 4 32 12 L32 34" fill="none" stroke="#c9b896" stroke-width="3"/>'
        '<line x1="20" y1="10" x2="20" y2="34" stroke="#a89070" stroke-width="2"/>'
    ),
    "scroll": (
        '<rect x="10" y="8" width="20" height="24" rx="2" fill="#e8dcc0"/>'
        '<line x1="14" y1="14" x2="26" y2="14" stroke="#8a7a68" stroke-width="1.5"/>'
        '<line x1="14" y1="20" x2="26" y2="20" stroke="#8a7a68" stroke-width="1.5"/>'
        '<line x1="14" y1="26" x2="22" y2="26" stroke="#8a7a68" stroke-width="1.5"/>'
    ),
    "loom": (
        '<rect x="8" y="8" width="24" height="4" fill="#8a6a48"/>'
        '<line x1="12" y1="12" x2="12" y2="32" stroke="#c9b896" stroke-width="2"/>'
        '<line x1="28" y1="12" x2="28" y2="32" stroke="#c9b896" stroke-width="2"/>'
        '<path d="M12 18 H28 M12 24 H28" stroke="#e8d5a3" stroke-width="1.5"/>'
    ),
    "laundry": (
        '<line x1="4" y1="14" x2="36" y2="14" stroke="#c9b896" stroke-width="2"/>'
        '<rect x="8" y="14" width="8" height="14" fill="#e8e0d0"/>'
        '<rect x="20" y="14" width="10" height="12" fill="#d0d8e8"/>'
    ),
    "net": (
        '<path d="M8 12 L32 12 L28 30 L12 30 Z" fill="none" stroke="#a8c0d0" stroke-width="1.5"/>'
        '<path d="M12 12 L14 30 M20 12 L20 30 M28 12 L26 30 M8 18 H32 M8 24 H32" '
        'stroke="#a8c0d0" stroke-width="1"/>'
    ),
    "ribbon": (
        '<path d="M12 8 Q20 20 12 32" fill="none" stroke="#e87898" stroke-width="3"/>'
        '<path d="M28 8 Q20 20 28 32" fill="none" stroke="#e87898" stroke-width="3"/>'
        '<circle cx="20" cy="20" r="4" fill="#f0a0b8"/>'
    ),
    "mosaic": (
        '<rect x="6" y="10" width="12" height="10" fill="#6a8aaa"/>'
        '<rect x="22" y="10" width="12" height="10" fill="#c9a86a"/>'
        '<rect x="6" y="22" width="12" height="10" fill="#c94a4a"/>'
        '<rect x="22" y="22" width="12" height="10" fill="#4a7a48"/>'
    ),
    "courier": (
        '<ellipse cx="20" cy="22" rx="12" ry="5" fill="#c9b896"/>'
        '<path d="M8 22 Q14 12 22 18" fill="none" stroke="#a89070" stroke-width="2"/>'
        '<circle cx="30" cy="18" r="3" fill="#d8c8a8"/>'
    ),
    "incense": (
        '<rect x="18" y="10" width="4" height="22" fill="#8a6a48"/>'
        '<circle cx="20" cy="8" r="3" fill="#c9b896" opacity=".6"/>'
        '<path d="M20 6 Q24 0 20 -4" fill="none" stroke="#e8d5a3" stroke-width="1.5"/>'
    ),
    "kite": (
        '<path d="M20 6 L32 20 L20 28 L8 20 Z" fill="#e87860"/>'
        '<line x1="20" y1="28" x2="24" y2="36" stroke="#c9b896" stroke-width="1.5"/>'
    ),
    "mill": (
        '<rect x="16" y="22" width="8" height="12" fill="#8a7a68"/>'
        '<circle cx="20" cy="18" r="3" fill="#c9b896"/>'
        '<line x1="20" y1="18" x2="8" y2="8" stroke="#e8d5a3" stroke-width="3"/>'
        '<line x1="20" y1="18" x2="34" y2="12" stroke="#e8d5a3" stroke-width="3"/>'
        '<line x1="20" y1="18" x2="14" y2="32" stroke="#e8d5a3" stroke-width="3"/>'
    ),
    "tidepool": (
        '<ellipse cx="20" cy="22" rx="14" ry="10" fill="#4a7a8a"/>'
        '<ellipse cx="18" cy="20" rx="6" ry="4" fill="#7ab0c0" opacity=".6"/>'
    ),
    "pillar": (
        '<rect x="14" y="10" width="12" height="24" fill="#c9b896"/>'
        '<rect x="10" y="8" width="20" height="4" fill="#e8d5a3"/>'
        '<rect x="10" y="32" width="20" height="4" fill="#e8d5a3"/>'
    ),
    "dawn": (
        '<circle cx="20" cy="20" r="12" fill="#e8c86a" opacity=".85"/>'
        '<circle cx="20" cy="20" r="6" fill="#fff0c0"/>'
    ),
    "thief_star": (
        '<polygon points="20,4 23,16 36,16 26,24 30,36 20,28 10,36 14,24 4,16 17,16" '
        'fill="#e8d5a3"/>'
    ),
    "wheat": (
        '<line x1="20" y1="34" x2="20" y2="12" stroke="#c9a86a" stroke-width="2"/>'
        '<ellipse cx="20" cy="10" rx="5" ry="8" fill="#e8d080"/>'
    ),
    "grass": (
        '<path d="M10 34 Q12 16 10 8" fill="none" stroke="#6a9a48" stroke-width="2"/>'
        '<path d="M20 34 Q22 14 20 6" fill="none" stroke="#5a8a40" stroke-width="2"/>'
        '<path d="M30 34 Q28 18 32 10" fill="none" stroke="#7aaa58" stroke-width="2"/>'
    ),
    "grove_leaf": (
        '<path d="M20 6 Q32 20 20 34 Q8 20 20 6" fill="#4a8a48"/>'
        '<line x1="20" y1="8" x2="20" y2="32" stroke="#2a5a28" stroke-width="1"/>'
    ),
    "wind": (
        '<path d="M6 14 H28 Q34 14 34 18" fill="none" stroke="#c8d8e8" stroke-width="2"/>'
        '<path d="M10 22 H30 Q36 22 36 26" fill="none" stroke="#a8c0d8" stroke-width="2"/>'
        '<path d="M8 30 H24" fill="none" stroke="#88a8c8" stroke-width="2"/>'
    ),
    "bath": (
        '<ellipse cx="20" cy="26" rx="14" ry="8" fill="#7a9aaa"/>'
        '<path d="M8 22 Q20 14 32 22" fill="#a8c8d8"/>'
    ),
    "maze": (
        '<rect x="6" y="6" width="28" height="28" fill="none" stroke="#8a7a98" stroke-width="2"/>'
        '<path d="M6 20 H18 V34 M22 6 V22 H34" fill="none" stroke="#a898b8" stroke-width="2"/>'
    ),
    "resident": (
        '<circle cx="20" cy="12" r="6" fill="#e8d5a3"/>'
        '<path d="M10 34 Q10 20 20 20 Q30 20 30 34" fill="#c9b896"/>'
    ),
}

_DEFAULT_SPRITE = (
    '<circle cx="20" cy="20" r="12" fill="rgba(232,213,163,.55)" '
    'stroke="#e8d5a3" stroke-width="2"/>'
)

_SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "life_sprites"

# AI-painted sprites are only for outdoor beings you can walk up to and touch.
# Ambient (grass, wind, wheat, dawn) is CSS/SVG. Indoor furniture is not staged.
_PAINTED_INTERACTIVE = frozenset({
    "chimera", "dromas", "hearth_cat", "resident",
    "well", "fountain", "shrine", "market_stall", "forge", "gate",
    "courier", "boat", "kite", "olive", "cicada", "pearl", "pebble",
    "mill", "laundry", "banner", "incense", "pillar",
})
_AMBIENT_STAGE = frozenset({
    "grass", "wind", "wheat", "grove_leaf", "shore", "mosaic",
    "bath", "hearth", "loom", "scroll", "lamp",
})
_SKY_KINDS = frozenset({"kite", "courier", "dawn", "thief_star", "wind"})

# Painted walk/fly cycles — consecutive frames stitched L→R.
_FILM_DUR = {
    "chimera": "0.64s",
    "dromas": "1.35s",
    "hearth_cat": "2.1s",
    "resident": "0.88s",
    "cicada": "0.28s",
    "courier": "0.42s",
    "kite": "1.7s",
}


@lru_cache(maxsize=64)
def sprite_png_uri(kind: str) -> str:
    """data-URI for a painted hotspot PNG, or '' if none on disk."""
    p = _SPRITE_DIR / f"{kind}.png"
    if not p.is_file():
        return ""
    import base64
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


@lru_cache(maxsize=32)
def sprite_film_uri(kind: str) -> str:
    """data-URI for a 4-frame motion strip, or ''."""
    p = _SPRITE_DIR / f"{kind}_film.png"
    if not p.is_file():
        return ""
    import base64
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def _sprite_markup(kind: str) -> str:
    # Painted PNGs/films only for outdoor figures you can actually touch.
    if kind in _PAINTED_INTERACTIVE:
        film = sprite_film_uri(kind)
        if film:
            dur = _FILM_DUR.get(kind, "0.8s")
            return (
                f'<span class="amp-sprite-film" style="'
                f"background-image:url('{film}');"
                f"--amp-frames:4;--amp-film-dur:{dur};\"></span>"
            )
        uri = sprite_png_uri(kind)
        if uri:
            return f'<img src="{uri}" alt="" draggable="false" />'
    inner = _SPRITE_PATHS.get(kind) or _DEFAULT_SPRITE
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" '
        f'aria-hidden="true">{inner}</svg>'
    )

# Short labels for visitor acts (shown only after a figure is noticed).
_ACT_GLYPH: Dict[str, str] = {
    "pick_keepsake": "◇ pocket",
    "leave_offering": "▣ thanks",
    "sit_hearth": "▣ sit",
    "wave": "⌒ wave",
    "drink": "○ drink",
    "touch_air": "≈ air",
    "pet_cat": "◠ pet",
    "scratch_ear": "◠ ear",
    "greet_dromas": "⌒ greet",
    "soak": "≈ soak",
    "look_up": "☆ look",
    "step_through": "⊓ step",
    "listen_iron": "▣ iron",
    "watch_thread": "┊ thread",
    "trail_maze": "▦ trail",
    "brush_grain": "┊ grain",
    "rest_shade": "⌒ shade",
    "hang_ribbon": "⌒ ribbon",
    "watch_water": "≈ water",
    "follow_bird": "⌒ bird",
    "read_cloth": "▣ cloth",
    "breathe_incense": "⌒ scent",
    "listen_cicada": "⌒ listen",
    "glance_hull": "⌒ hull",
    "trace_mosaic": "▦ trace",
    "hum_mill": "⌒ mill",
    "linger_lamp": "☆ lamp",
    "read_page": "▣ page",
}


def _css() -> str:
    return """
<style>
@keyframes amp-grass-sway {
  0%,100% { transform: rotate(-4deg) translateY(0); }
  50% { transform: rotate(5deg) translateY(-2px); }
}
@keyframes amp-chimera-wander {
  0% { left: 8%; opacity: 0; }
  10% { opacity: .92; }
  50% { left: 55%; }
  90% { opacity: .92; }
  100% { left: 88%; opacity: 0; }
}
@keyframes amp-leaf-drift {
  0% { transform: translateY(0) rotate(0deg); opacity: .0; }
  15% { opacity: .7; }
  100% { transform: translateY(110px) rotate(40deg); opacity: 0; }
}
@keyframes amp-shore-glint {
  0%,100% { opacity: .15; }
  50% { opacity: .45; }
}
@keyframes amp-wheat-nod {
  0%,100% { transform: skewX(-2deg); }
  50% { transform: skewX(3deg); }
}
@keyframes amp-courier-arc {
  0% { left: 8%; top: 18%; opacity: 0; }
  12% { opacity: .85; }
  88% { opacity: .85; }
  100% { left: 88%; top: 10%; opacity: 0; }
}
@keyframes amp-fountain-glint {
  0%,100% { opacity: .2; }
  50% { opacity: .55; }
}
@keyframes amp-laundry-sway {
  0%,100% { transform: rotate(-6deg); }
  50% { transform: rotate(7deg); }
}
@keyframes amp-sprite-breathe {
  0%,100% { transform: translateY(0); filter: drop-shadow(0 0 6px rgba(232,213,163,.35)); }
  50% { transform: translateY(-3px); filter: drop-shadow(0 0 12px rgba(232,213,163,.65)); }
}
.amp-life-layer { position:absolute; inset:0; pointer-events:none; overflow:hidden; }
.amp-grass-blade {
  position:absolute; bottom:0; width:3px; height:18px;
  background: linear-gradient(180deg, rgba(120,160,80,.0), rgba(90,130,55,.75));
  transform-origin: bottom center;
  animation: amp-grass-sway 2.8s ease-in-out infinite;
}
.amp-chimera-dot {
  position:absolute; bottom:18%; width:22px; height:16px;
  border-radius: 10px 10px 6px 6px;
  background: radial-gradient(circle at 30% 40%, #f2e6c9, #c9a86a 70%);
  box-shadow: 0 0 0 1px rgba(0,0,0,.25);
  animation: amp-chimera-wander 14s linear infinite;
}
.amp-chimera-dot.ailing { background: radial-gradient(circle at 30% 40%, #d8c8a8, #8a7060 70%); filter:saturate(.6); }
.amp-leaf {
  position:absolute; top:8%; width:10px; height:14px; border-radius:2px 10px;
  background: rgba(70,120,60,.65);
  animation: amp-leaf-drift 7s ease-in infinite;
}
.amp-shore-band {
  position:absolute; left:0; right:0; bottom:0; height:28%;
  background: linear-gradient(180deg, transparent, rgba(80,140,170,.35));
  animation: amp-shore-glint 4s ease-in-out infinite;
}
.amp-wheat-row {
  position:absolute; left:5%; right:5%; bottom:6%; height:22px;
  background: repeating-linear-gradient(90deg,
    rgba(200,170,70,.0) 0 6px, rgba(210,180,80,.55) 6px 9px);
  animation: amp-wheat-nod 3.2s ease-in-out infinite;
  transform-origin: bottom center;
}
.amp-fountain {
  position:absolute; width:28px; height:18px; border-radius:50%;
  background: radial-gradient(circle, rgba(160,200,220,.55), transparent 70%);
  animation: amp-fountain-glint 3.4s ease-in-out infinite;
}
.amp-laundry {
  position:absolute; width:36px; height:3px;
  background: rgba(220,210,190,.55);
  transform-origin: left center;
  animation: amp-laundry-sway 3.6s ease-in-out infinite;
}
.amp-courier {
  position:absolute; width:10px; height:6px; border-radius: 6px 2px;
  background: #c9b896;
  animation: amp-courier-arc 11s linear infinite;
}
.amp-life-tag {
  position:absolute; bottom:10px; right:12px; font-size:11px;
  color:#f0e6c8; letter-spacing:.4px;
  text-shadow:0 1px 6px rgba(0,0,0,.85);
  background:rgba(10,8,20,.5); padding:2px 10px; border-radius:999px;
}
@keyframes amp-film {
  to { background-position: calc(var(--amp-frames, 4) * var(--amp-cell, 92px) * -1) 0; }
}
.amp-pict-inset .amp-sprite { --amp-cell: 58px; }
.amp-sprite {
  --amp-cell: 92px;
  position: absolute;
  width: var(--amp-cell); height: var(--amp-cell);
  margin-left: calc(var(--amp-cell) / -2); margin-bottom: -12px;
  padding: 0; border: none; background: transparent;
  cursor: pointer; z-index: 8;
  animation: amp-sprite-breathe 3.2s ease-in-out infinite;
  pointer-events: auto;
}
.amp-sprite::after {
  content: "";
  position: absolute; left: 18%; right: 18%; bottom: 6%;
  height: 10px;
  background: radial-gradient(ellipse, rgba(0,0,0,.42), transparent 72%);
  pointer-events: none;
}
.amp-sprite.sky { animation: none; }
.amp-sprite.sky::after { display: none; }
.amp-sprite svg, .amp-sprite img { width: 100%; height: 100%; display: block; pointer-events: none; }
.amp-sprite img { object-fit: contain; filter: drop-shadow(0 2px 5px rgba(0,0,0,.55)); }
.amp-sprite-film {
  display: block; width: 100%; height: 100%;
  background-repeat: no-repeat;
  background-position: 0 0;
  background-size: calc(var(--amp-frames, 4) * var(--amp-cell, 92px)) var(--amp-cell, 92px);
  pointer-events: none;
  filter: drop-shadow(0 2px 5px rgba(0,0,0,.55));
  animation: amp-film var(--amp-film-dur, .8s) steps(var(--amp-frames, 4)) infinite;
}
.amp-sprite:hover { transform: scale(1.12); filter: drop-shadow(0 0 14px rgba(240,230,200,.85)); }
.amp-sprite.ailing svg, .amp-sprite.ailing img, .amp-sprite.ailing .amp-sprite-film {
  filter: saturate(.55) brightness(.85);
}
.amp-sprite-halo {
  position: absolute; inset: -4px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(240,230,200,.28), transparent 70%);
  pointer-events: none;
}
.amp-stage-read {
  position: absolute; left: 12px; right: 12px; top: 44px; z-index: 7;
  max-width: 420px;
  background: rgba(10,8,20,.72);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(232,213,163,.22);
  border-radius: 10px;
  padding: 10px 14px;
  color: #f0e6c8;
  font: 13px/1.45 Georgia, serif;
  pointer-events: none;
}
.amp-stage-read .kicker { color: #b8a97f; font-size: 11px; letter-spacing: .04em; }
</style>
"""


def _sprite_inner(kind: str) -> str:
    return _SPRITE_PATHS.get(kind) or _DEFAULT_SPRITE


def life_overlay_html(scene: List[dict], place: str = "", *, dense: bool = False) -> str:
    """CSS/HTML layer for ambient motion — visual only (no clicks)."""
    kinds = {b.get("kind") for b in (scene or [])}
    parts = ['<div class="amp-life-layer">']

    grass_xs = (6, 14, 22, 31, 40, 52, 61, 70, 78, 88)
    if dense:
        grass_xs = grass_xs + (10, 18, 26, 35, 45, 56, 65, 74, 82, 92)
    if "grass" in kinds or "wind" in kinds:
        for i, x in enumerate(grass_xs):
            delay = (i * 0.17) % 2.5
            parts.append(
                f'<div class="amp-grass-blade" style="left:{x}%;'
                f'animation-delay:{delay:.2f}s;height:{14 + (i % 5) * 3}px;"></div>'
            )

    if "grove_leaf" in kinds:
        leaf_xs = (18, 42, 67, 81) if not dense else (12, 28, 44, 58, 72, 86)
        for i, left in enumerate(leaf_xs):
            parts.append(
                f'<div class="amp-leaf" style="left:{left}%;'
                f'animation-delay:{i * 1.4}s;"></div>'
            )

    if "shore" in kinds:
        parts.append('<div class="amp-shore-band"></div>')

    if "wheat" in kinds:
        parts.append('<div class="amp-wheat-row"></div>')

    if "fountain" in kinds:
        parts.append(
            '<div class="amp-fountain" style="left:46%;bottom:16%;"></div>'
        )
    if "laundry" in kinds:
        parts.append(
            '<div class="amp-laundry" style="left:78%;bottom:34%;"></div>'
        )
    if "courier" in kinds:
        parts.append('<div class="amp-courier"></div>')

    parts.append("</div>")
    return _css() + "".join(parts)


def inject_into_scene_html(scene_html: str, scene: List[dict], place: str = "",
                           *, dense: bool = False) -> str:
    """Slip the ambient life layer into an existing weather scene container."""
    if not scene_html:
        return life_overlay_html(scene, place, dense=dense)
    overlay = life_overlay_html(scene, place, dense=dense)
    idx = scene_html.rfind("</div>")
    if idx < 0:
        return scene_html + overlay
    return scene_html[:idx] + overlay + scene_html[idx:]


def pictorial_stage_html(
    image_path,
    place: str,
    effect: str,
    sky: str,
    scene: List[dict],
    *,
    height: int = 520,
    max_width: int = 1920,
    read_line: str = "",
    dense: bool = True,
    page_layer: bool = False,
    entities: bool = True,
    inset_max_width: int = 960,
) -> str:
    """Weather + ambient + clickable sprites.

    ``page_layer=True`` is a transparent viewport overlay — the JPEG lives on
    the Streamlit page (``page_backdrop_css``) so the art is not shown twice.
    """
    from src.ui_weather import image_data_uri, overlay_for

    uri = ""
    if image_path and not page_layer:
        uri = image_data_uri(image_path, max_width=max_width) or ""
        if not uri:
            return ""

    ambient = life_overlay_html(scene, place, dense=dense) if entities else ""
    # Cap on-stage figures so the art stays readable (full list lives in eco).
    _PRIORITY = (
        "chimera", "dromas", "hearth_cat", "resident",
        "well", "fountain", "forge", "boat", "siren", "olive", "cicada",
        "pearl", "shrine", "gate", "market_stall",
        "laundry", "mill", "kite", "courier", "banner", "pillar", "incense",
        "dawn", "thief_star",
    )
    clickable = [
        b for b in (scene or [])
        if entities
        and b.get("clickable") and b.get("id")
        and str(b.get("kind") or "") not in _AMBIENT_STAGE
    ]
    ranked = sorted(
        clickable,
        key=lambda b: (
            _PRIORITY.index(b.get("kind"))
            if b.get("kind") in _PRIORITY else 80,
            str(b.get("id")),
        ),
    )
    max_sprites = 10 if dense else 7
    sprites = []
    for b in ranked[:max_sprites]:
        kind = str(b.get("kind") or "")
        hs = b.get("hotspot") or {}
        left = hs.get("left") or "50%"
        bottom = hs.get("bottom") or "20%"
        oid = _html.escape(str(b.get("id")), quote=True)
        title = _html.escape(str(b.get("name") or kind or "life"), quote=True)
        ailing = " ailing" if b.get("status") == "ailing" else ""
        sky = " sky" if kind in _SKY_KINDS else ""
        delay = abs(hash(oid)) % 17 / 10.0
        sprites.append(
            f'<button type="button" class="amp-sprite{ailing}{sky}" data-oid="{oid}" '
            f'title="{title}" aria-label="{title}" '
            f'style="left:{left};bottom:{bottom};animation-delay:{delay:.1f}s;">'
            f'<span class="amp-sprite-halo"></span>'
            f'{_sprite_markup(kind)}'
            f"</button>"
        )

    read_block = ""
    if read_line:
        read_block = (
            '<div class="amp-stage-read">'
            '<div class="kicker">This hour</div>'
            f"{_html.escape(read_line[:280])}"
            "</div>"
        )

    try:
        from src.ui_weather import _overlay_html as _wx_layers
        wx = _wx_layers(
            effect or "none", sky or "", place or "Amphoreus",
            show_place_tag=not page_layer,
        )
    except Exception:
        wx = overlay_for(
            place or "Amphoreus", place or "Amphoreus",
            show_place_tag=not page_layer,
        )

    if page_layer:
        shell = (
            '<style>html,body{margin:0;padding:0;width:100%;height:100%;'
            'background:transparent;overflow:hidden;}</style>'
            '<div id="amp-pict-stage" style="position:fixed;inset:0;width:100%;'
            'height:100%;overflow:hidden;background:transparent;pointer-events:none;">'
        )
        art_div = ""
    else:
        pos = "center center"
        cap = max(320, int(inset_max_width or 960))
        shell = (
            '<style>html,body{margin:0;padding:0;width:100%;height:100%;'
            'background:transparent;overflow:hidden;}'
            '.amp-pict-inset .amp-sprite{--amp-cell:58px;}</style>'
            '<div id="amp-pict-stage" class="amp-pict-inset" '
            'style="position:relative;width:100%;height:100%;'
            'overflow:hidden;border:1px solid rgba(232,213,163,.16);'
            'border-radius:14px;background:#0a0814;">'
        )
        art_div = (
            f'<div style="position:absolute;inset:0;background-image:url(\'{uri}\');'
            f'background-size:cover;background-position:{pos};'
            f'background-repeat:no-repeat;"></div>'
        )

    pin_js = ""
    if page_layer:
        pin_js = (
            "  var f = window.frameElement;\n"
            "  if (f) {\n"
            "    f.setAttribute('data-amp-land', '1');\n"
            "    f.removeAttribute('width'); f.removeAttribute('height');\n"
            "    var topPx = 136;\n"
            "    try {\n"
            "      var doc = window.parent.document;\n"
            "      var sels = ['[data-testid=\"stTabs\"]','[role=\"tablist\"]',\n"
            "        '[role=\"radiogroup\"]','[role=\"switch\"]'];\n"
            "      for (var s = 0; s < sels.length; s++) {\n"
            "        var els = doc.querySelectorAll(sels[s]);\n"
            "        for (var i = 0; i < els.length; i++) {\n"
            "          var b = els[i].getBoundingClientRect().bottom;\n"
            "          if (b > 48 && b < 320) topPx = Math.max(topPx, Math.ceil(b + 8));\n"
            "        }\n"
            "      }\n"
            "      doc.documentElement.style.setProperty('--amp-land-top', topPx + 'px');\n"
            "    } catch (e) {}\n"
            "    var top = topPx + 'px';\n"
            "    var h = 'calc(100vh - ' + top + ')';\n"
            "    f.style.cssText = 'position:fixed;top:'+top+';left:0;right:0;bottom:0;"
            "width:100vw;height:'+h+';border:0;z-index:0;"
            "background:transparent;pointer-events:auto;"
            "max-width:none;max-height:none;';\n"
            "    var p = f.parentElement;\n"
            "    if (p) {\n"
            "      p.setAttribute('data-amp-land-wrap', '1');\n"
            "      p.style.cssText = 'position:fixed;top:'+top+';left:0;right:0;bottom:0;"
            "width:100vw;height:'+h+';"
            "margin:0;padding:0;overflow:visible;z-index:0;border:none;"
            "background:transparent;pointer-events:none;';\n"
            "    }\n"
            "  }\n"
            "  try {\n"
            "    window.parent.Function(\n"
            "      'if(window.__ampNoticeBound)return;window.__ampNoticeBound=true;'\n"
            "      + 'window.addEventListener(\"message\",function(ev){try{var d=ev.data;'\n"
            "      + 'if(!d||d.amp!==\"notice\"||!d.oid)return;var u=new URL(location.href);'\n"
            "      + 'u.searchParams.set(\"amp_notice\",String(d.oid));location.href=u.toString();}'\n"
            "      + 'catch(e){}});'\n"
            "    )();\n"
            "  } catch (e) {}\n"
        )
    else:
        cap = max(320, int(inset_max_width or 960))
        pin_js = (
            f"  var maxW = {cap};\n"
            "  var f = window.frameElement;\n"
            "  function fit(){\n"
            "    if (!f) return;\n"
            "    f.removeAttribute('width'); f.removeAttribute('height');\n"
            "    var p = f.parentElement;\n"
            "    var avail = (p && p.clientWidth) ? p.clientWidth : maxW;\n"
            "    var w = Math.max(240, Math.min(maxW, avail));\n"
            "    var h = Math.round(w * 9 / 16);\n"
            "    f.style.cssText = 'width:'+w+'px;height:'+h+'px;border:0;"
            "display:block;margin:0 auto;overflow:hidden;max-width:100%;';\n"
            "    if (p) {\n"
            "      p.style.cssText = 'width:100%;height:'+h+'px;text-align:center;"
            "overflow:visible;margin:0 auto;padding:0;';\n"
            "    }\n"
            "  }\n"
            "  fit();\n"
            "  try { new ResizeObserver(fit).observe(f.parentElement || f); }\n"
            "  catch (e) {}\n"
            "  window.addEventListener('resize', fit);\n"
            "  try {\n"
            "    window.parent.Function(\n"
            "      'if(window.__ampNoticeBound)return;window.__ampNoticeBound=true;'\n"
            "      + 'window.addEventListener(\"message\",function(ev){try{var d=ev.data;'\n"
            "      + 'if(!d||d.amp!==\"notice\"||!d.oid)return;var u=new URL(location.href);'\n"
            "      + 'u.searchParams.set(\"amp_notice\",String(d.oid));location.href=u.toString();}'\n"
            "      + 'catch(e){}});'\n"
            "    )();\n"
            "  } catch (e) {}\n"
        )

    body = (
        f"{shell}"
        f"{art_div}"
        f"{wx}"
        f"{ambient}"
        f'{"".join(sprites)}'
        f"{read_block}"
        f"</div>"
        "<script>\n"
        "(function(){\n"
        f"{pin_js}"
        "  function go(oid){\n"
        "    try { window.parent.postMessage({amp:'notice', oid:oid}, '*'); } catch (e) {}\n"
        "    try {\n"
        "      var u = new URL(window.parent.location.href);\n"
        "      u.searchParams.set('amp_notice', oid);\n"
        "      window.parent.location.href = u.toString();\n"
        "    } catch (e) {}\n"
        "  }\n"
        "  var root = document.getElementById('amp-pict-stage');\n"
        "  if(!root) return;\n"
        "  root.addEventListener('click', function(ev){\n"
        "    var t = ev.target.closest ? ev.target.closest('.amp-sprite') : null;\n"
        "    if(!t) return;\n"
        "    ev.preventDefault();\n"
        "    go(t.getAttribute('data-oid'));\n"
        "  });\n"
        "})();\n"
        "</script>\n"
    )
    return body


def render_pictorial_stage(
    image_path,
    place: str,
    effect: str,
    sky: str,
    scene: List[dict],
    *,
    height: int = 520,
    max_width: int = 1920,
    read_line: str = "",
    dense: bool = True,
    page_layer: bool = True,
    entities: bool = True,
    inset_max_width: int = 960,
    key: str = "pict",
) -> bool:
    """Render the land overlay. ``page_layer`` pins figures to the viewport."""
    from streamlit.components.v1 import html as components_html

    html = pictorial_stage_html(
        image_path, place, effect, sky, scene,
        height=height, max_width=max_width, read_line=read_line,
        dense=dense, page_layer=page_layer, entities=entities,
        inset_max_width=inset_max_width,
    )
    if not html:
        return False
    if page_layer:
        slot = 1
    else:
        cap = max(320, int(inset_max_width or 960))
        slot = max(height, int(round(cap * 9 / 16)) + 8)
    components_html(html, height=slot, scrolling=False)
    return True


def render_inset_window(
    image_path,
    place: str,
    scene: List[dict],
    *,
    height: int = 300,
    dense: bool = False,
    entities: bool = True,
    box_max: int = 960,
    key: str = "inset",
) -> None:
    """The pre-pictorial weather card — a 16:9 backdrop window, not full-bleed."""
    import streamlit as st
    from src.ui_weather import scene_html, effect_for

    if not image_path:
        return
    try:
        from src.ui_backgrounds import postcard_art_path
        image_path = postcard_art_path(image_path) or image_path
    except Exception:
        pass
    cap = max(320, int(box_max or 960))
    effect, sky = effect_for(place)
    if entities:
        ok = render_pictorial_stage(
            image_path, place, effect, sky, scene or [],
            height=int(round(cap * 9 / 16)), dense=dense, page_layer=False,
            entities=True, inset_max_width=cap, key=key,
        )
        if ok:
            return
    html = scene_html(
        image_path, place or "Amphoreus", effect, sky,
        height=height, rounded=True,
        box_max=cap, aspect="16 / 9",
    )
    if html:
        st.markdown(html, unsafe_allow_html=True)


def _do_notice(*, oid: str, heir_id: str, place: Optional[str],
               key_prefix: str) -> None:
    import streamlit as st
    from src.world import ecosystem as eco
    from src.world.world_state import WorldState

    res = eco.interact(
        WorldState(), oid, character_id=heir_id or None, place=place)
    noticed = st.session_state.setdefault("eco_noticed", {})
    if not isinstance(noticed, dict):
        noticed = {}
        st.session_state["eco_noticed"] = noticed
    if res.get("ok"):
        tb = res.get("textbox") or res.get("line") or ""
        st.session_state[f"{key_prefix}_flash"] = res.get("line") or tb
        b = res.get("being") or {}
        noticed[oid] = {
            "id": oid,
            "name": b.get("name"),
            "kind": b.get("kind"),
            "status": b.get("status"),
            "line": res.get("line"),
            "sound": res.get("sound"),
            "heir": heir_id,
            "place": place or b.get("place") or "",
        }
        st.session_state["eco_noticed"] = noticed
        st.session_state["eco_focus"] = oid
    else:
        st.session_state[f"{key_prefix}_flash"] = res.get("reason")


def render_presence_chips(
    scene: List[dict],
    *,
    heir_id: str = "",
    key_prefix: str,
    place: Optional[str] = None,
) -> None:
    """Classic land: named buttons under the inset picture. No overlays."""
    import streamlit as st

    try:
        from src.ui_look import show_entities
        if not show_entities():
            return
    except Exception:
        pass

    flash = st.session_state.pop(f"{key_prefix}_flash", None)
    if flash:
        st.info(str(flash))
    _render_pocket()

    skip = {
        "grass", "wind", "wheat", "grove_leaf", "shore", "mosaic",
        "bath", "hearth", "loom", "scroll", "lamp",
    }
    beings = [
        b for b in (scene or [])
        if b.get("id")
        and (b.get("clickable") or b.get("kind"))
        and str(b.get("kind") or "") not in skip
    ]
    st.markdown("#### Presence")
    if not beings:
        st.caption("Quiet here this hour.")
        return
    st.caption("Touch a name to notice who or what is here.")
    shown = beings[:12]
    for row_i in range(0, len(shown), 4):
        chunk = shown[row_i:row_i + 4]
        cols = st.columns(len(chunk))
        for col, b in zip(cols, chunk):
            oid = str(b.get("id") or "")
            name = str(b.get("name") or b.get("kind") or "life")
            with col:
                if st.button(name, key=f"{key_prefix}_chip_{oid}"):
                    _do_notice(
                        oid=oid, heir_id=heir_id, place=place,
                        key_prefix=key_prefix,
                    )
                    st.rerun()


def render_stage_bar(
    scene: List[dict],
    *,
    heir_id: str = "",
    key_prefix: str,
    place: Optional[str] = None,
) -> None:
    """Compat shim — focus strip after a figure is noticed."""
    render_focus_strip(
        scene, heir_id=heir_id, key_prefix=key_prefix, place=place,
        read_only=not heir_id,
    )


def _render_pocket() -> None:
    import streamlit as st
    try:
        from src.world.world_state import WorldState
        from src.world import ecosystem as eco
        pocket = list((eco.eco_bucket(WorldState()).get("pocket") or []))
    except Exception:
        pocket = []
    if pocket:
        names = [str(p.get("name") or "a small thing") for p in pocket[-6:]]
        st.caption("In your pocket: " + " · ".join(names))


def render_focus_strip(
    scene: List[dict],
    *,
    heir_id: str = "",
    heir_name: str = "",
    key_prefix: str,
    place: Optional[str] = None,
    read_only: bool = False,
) -> None:
    """After a pictorial click: show the noticed being + touch/care glyphs."""
    import streamlit as st
    from src.world import ecosystem as eco
    from src.world.world_state import WorldState

    try:
        from src.ui_look import show_entities
        if not show_entities():
            return
    except Exception:
        pass

    flash = st.session_state.pop(f"{key_prefix}_flash", None)
    if flash:
        st.markdown(
            f'<div class="amp-read">{_html.escape(str(flash))}</div>',
            unsafe_allow_html=True,
        )
    _render_pocket()

    focus_id = st.session_state.get("eco_focus") or ""
    noticed = st.session_state.get("eco_noticed") or {}
    if not focus_id and noticed:
        # Prefer last notice at this place / heir.
        for oid, row in reversed(list(noticed.items())):
            if place and row.get("place") and row.get("place") != place:
                continue
            if heir_id and row.get("heir") and row.get("heir") != heir_id:
                continue
            focus_id = oid
            break

    being = None
    for b in (scene or []):
        if b.get("id") == focus_id:
            being = b
            break
    if being is None and focus_id and focus_id in noticed:
        # Scene may have refreshed; synthesize a minimal row.
        row = noticed[focus_id]
        being = {
            "id": focus_id,
            "name": row.get("name"),
            "kind": row.get("kind"),
            "status": row.get("status"),
            "visitor_acts": [],
        }

    if not being:
        st.caption("Touch a figure on the picture to notice what lives here.")
        return

    oid = being.get("id") or focus_id
    label = being.get("name") or being.get("kind") or "life"
    status = being.get("status") or ""
    mark = f" · {status}" if status and status != "resting" else ""
    st.markdown(
        f'<div class="amp-read"><strong>{_html.escape(str(label))}</strong>'
        f'{_html.escape(mark)}'
        f'<div class="sub">{_html.escape(str(being.get("doing") or ""))}</div></div>',
        unsafe_allow_html=True,
    )

    acts = list(being.get("visitor_acts") or [])
    if not acts:
        try:
            acts = eco.visitor_acts_for(str(being.get("kind") or ""))
        except Exception:
            acts = []

    if acts:
        cols = st.columns(min(4, len(acts)))
        for i, aid in enumerate(acts):
            glyph = _ACT_GLYPH.get(aid, aid.replace("_", " "))
            with cols[i % len(cols)]:
                if st.button(glyph, key=f"{key_prefix}_v_{oid}_{aid}"):
                    ws = WorldState()
                    touch = eco.visitor_touch(
                        ws, oid, aid, place=place, save=True)
                    if touch.get("ok"):
                        st.session_state[f"{key_prefix}_flash"] = touch.get("note")
                        noticed = st.session_state.setdefault("eco_noticed", {})
                        noticed[oid] = {
                            "id": oid, "name": label, "kind": being.get("kind"),
                            "status": status, "line": touch.get("note"),
                            "heir": heir_id, "place": place or "",
                            "touched": aid,
                        }
                        st.session_state["eco_focus"] = oid
                        st.rerun()
                    else:
                        st.session_state[f"{key_prefix}_flash"] = touch.get("reason")
                        st.rerun()

    if read_only or not heir_id:
        return

    actions = eco.authorized_actions(heir_id, being)
    if not actions:
        return
    care_cols = st.columns(min(3, len(actions)))
    for i, a in enumerate(actions):
        btn = f"◇ {a['label']} ({heir_name})"
        with care_cols[i % len(care_cols)]:
            if st.button(btn, key=f"{key_prefix}_c_{oid}_{a['id']}"):
                ws = WorldState()
                care = eco.apply_care(ws, heir_id, oid, a["id"], save=True)
                if care.get("ok"):
                    st.session_state[f"{key_prefix}_flash"] = (
                        f"{heir_name}: {care.get('note')}"
                    )
                    msgs = st.session_state.setdefault("messages", {})
                    hist = msgs.setdefault(heir_id, [])
                    hist.append({
                        "role": "user",
                        "content": (
                            f"*(you ask {heir_name} to {a['label']} "
                            f"{label})*"
                        ),
                    })
                    hist.append({
                        "role": "assistant",
                        "content": (
                            f"*(the living world records: {care.get('note')})*"
                        ),
                    })
                    noticed = st.session_state.setdefault("eco_noticed", {})
                    noticed[oid] = {
                        "id": oid,
                        "name": label,
                        "kind": being.get("kind"),
                        "status": (care.get("being") or {}).get("status") or status,
                        "line": care.get("note"),
                        "cared": True,
                        "heir": heir_id,
                        "place": place or "",
                    }
                    st.session_state["eco_focus"] = oid
                    st.rerun()
                else:
                    st.session_state[f"{key_prefix}_flash"] = care.get("reason")
                    st.rerun()


def render_life_interactions(
    scene: List[dict],
    *,
    heir_id: str,
    heir_name: str,
    manager,
    key_prefix: str,
    read_only: bool = False,
    place: Optional[str] = None,
) -> None:
    """Focus strip after pictorial notice."""
    render_focus_strip(
        scene,
        heir_id=heir_id,
        heir_name=heir_name,
        key_prefix=key_prefix,
        place=place,
        read_only=read_only,
    )
    if heir_id:
        import streamlit as st
        noticed = st.session_state.get("eco_noticed") or {}
        bits = [
            v.get("name") for v in noticed.values()
            if v.get("heir") == heir_id
        ][:4]
        if bits:
            st.caption(
                "You have noticed: " + " · ".join(str(b) for b in bits if b)
                + " — ask the Heir about them in chat."
            )


def noticed_prompt_addon(heir_id: str) -> str:
    """Extra injector from what the visitor clicked this session."""
    try:
        import streamlit as st
        noticed = st.session_state.get("eco_noticed") or {}
    except Exception:
        return ""
    rows = [
        v for v in noticed.values()
        if v.get("heir") == heir_id
    ]
    if not rows:
        return ""
    lines = ["# What the visitor just pointed at on the stage"]
    for v in rows[-5:]:
        lines.append(
            f"- {v.get('name')} ({v.get('kind')}, {v.get('status')}): "
            f"{v.get('line') or v.get('sound') or 'noticed'}"
        )
    lines.append(
        "If they ask who someone is, or about that chimera / grass / shore, "
        "answer from these facts. Do not invent other cities' life."
    )
    return "\n".join(lines)


def consume_notice_query(*, place: Optional[str] = None, heir_id: str = "",
                         key_prefix: str = "walk") -> None:
    """Handle a click on a scene hotspot (`?amp_notice=`)."""
    try:
        import streamlit as st
        from urllib.parse import unquote
        from src.world.world_state import WorldState
        from src.world import ecosystem as eco
    except Exception:
        return
    raw = st.query_params.get("amp_notice")
    if not raw:
        return
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    oid = unquote(str(raw or ""))
    if not oid:
        return
    res = eco.interact(
        WorldState(), oid, character_id=heir_id or None, place=place)
    if res.get("ok"):
        st.session_state[f"{key_prefix}_flash"] = res.get("line")
        noticed = st.session_state.setdefault("eco_noticed", {})
        b = res.get("being") or {}
        noticed[oid] = {
            "id": oid,
            "name": b.get("name"),
            "kind": b.get("kind"),
            "status": b.get("status"),
            "line": res.get("line"),
            "sound": res.get("sound"),
            "heir": heir_id,
            "place": place or b.get("place") or "",
        }
        st.session_state["eco_noticed"] = noticed
        st.session_state["eco_focus"] = oid
    else:
        st.session_state[f"{key_prefix}_flash"] = res.get("reason")
    try:
        del st.query_params["amp_notice"]
    except Exception:
        pass
