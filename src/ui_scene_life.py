"""Visit / Walk scene life — figures on the page art, not a second picture.

Area art is the Streamlit page backdrop. Interactive outdoor figures use
AI-painted PNGs; grass/wind/wheat/dawn are CSS or SVG. Clicks run inside
``st.components.v1.html``. Clicks open a notice card *inside* the land
iframe — no parent navigation, no Streamlit refresh.
"""
from __future__ import annotations

import html as _html
import json
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
# Built structures & fixtures — no bob, no roam.
_STATIONARY_KINDS = frozenset({
    "well", "fountain", "shrine", "market_stall", "forge", "gate",
    "mill", "pillar", "incense", "pearl", "pebble", "net", "tidepool",
    "banner", "laundry", "siren", "maze", "mosaic",
})
# Side-profile walk films; frame 1 faces this direction. True side art only.
_SPRITE_FACING: Dict[str, str] = {
    "chimera": "right",
    "dromas": "right",
    "resident": "right",
    "cicada": "left",
}
# Mobile roam uses side walk film; still PNG is front-facing for these kinds.
_PROFILE_WALK_KINDS = frozenset({"chimera", "dromas"})
# Viewport traverse spawn/despawn — only these kinds leave and re-enter view.
_ROAMER_KINDS = frozenset({"chimera", "dromas", "resident", "cicada"})
_ROAMER_DUR = {
    "dromas": (16, 24),
    "chimera": (12, 20),
    "resident": (10, 17),
    "cicada": (7, 12),
}


def _sprite_facing_class(kind: str) -> str:
    """CSS class for bidirectional roam mirroring on profile art."""
    facing = _SPRITE_FACING.get(kind)
    if facing == "left":
        return " face-l"
    if facing == "right":
        return " face-r"
    return ""


def _sprite_motion_class(kind: str) -> str:
    """CSS class: cat (film only), still, sky, or mobile (ground roam)."""
    if kind == "hearth_cat":
        return " cat"
    if kind in _STATIONARY_KINDS:
        return " still"
    if kind in _SKY_KINDS:
        return " sky"
    return " mobile"


def _sprite_roam_style(kind: str, oid: str, *, delay: float = 0.0) -> str:
    """Per-sprite horizontal path along the ground line."""
    seed = abs(hash(oid))
    span = 55 if kind in ("chimera", "dromas") else 34
    a = -(span + seed % 36)
    b = span + seed % 36
    dur = 10 + seed % 14
    return (
        f"--amp-roam-a:{a}px;--amp-roam-b:{b}px;--amp-roam-dur:{dur}s;"
        f"--amp-roam-delay:{delay:.1f}s;"
    )


def _page_window_bottom(kind: str, hotspot_bottom: str) -> str:
    """Lower border of the page window is the ground for page-layer life."""
    if kind in _SKY_KINDS:
        return hotspot_bottom or "72%"
    if kind == "laundry":
        return "18%"
    if kind == "banner":
        return "22%"
    if kind in ("cicada", "grove_leaf"):
        return hotspot_bottom or "42%"
    # Slight depth variety, still on the sill.
    table = {
        "dromas": "1%", "chimera": "2%", "hearth_cat": "2%", "resident": "2%",
        "well": "1%", "fountain": "1%", "forge": "1%", "gate": "1%",
        "shrine": "2%", "market_stall": "2%", "mill": "1%", "pillar": "1%",
        "olive": "2%", "incense": "2%", "boat": "0%", "siren": "1%",
        "pearl": "1%", "pebble": "0%", "net": "0%", "tidepool": "0%",
    }
    return table.get(kind, "2%")

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


def _sprite_markup(kind: str, *, mobile: bool = True) -> str:
    # Painted PNGs/films only for outdoor figures you can actually touch.
    if kind in _PAINTED_INTERACTIVE:
        # Profile-walk kinds: side film while roaming, front still otherwise.
        use_film = mobile if kind in _PROFILE_WALK_KINDS else True
        if use_film:
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


def _notice_line(being: dict) -> str:
    """Same copy as ``ecosystem.interact`` — computed at render, no click reload."""
    try:
        from src.world import ecosystem as eco
        from src.world.world_state import WorldState
        res = eco.interact(
            WorldState(),
            str(being.get("id") or ""),
            place=being.get("place") or None,
        )
        if res.get("ok"):
            return str(res.get("line") or "")
    except Exception:
        pass
    name = being.get("name") or being.get("kind") or "life"
    doing = being.get("doing") or ""
    return f"{name}: {doing}".strip(": ")


def _notice_acts(kind: str) -> List[dict]:
    try:
        from src.world.ecosystem import VISITOR_ACT, visitor_acts_for
        aids = visitor_acts_for(kind)
    except Exception:
        return []
    out = []
    for aid in aids:
        spec = VISITOR_ACT.get(aid) or {}
        out.append({
            "id": aid,
            "glyph": _ACT_GLYPH.get(aid, aid.replace("_", " ")),
            "note": spec.get("note") or "",
        })
    return out


def _notice_entry(being: dict) -> dict:
    kind = str(being.get("kind") or "")
    return {
        "name": str(being.get("name") or kind or "life"),
        "kind": kind,
        "status": str(being.get("status") or ""),
        "line": _notice_line(being),
        "acts": _notice_acts(kind),
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
@keyframes amp-sprite-roam {
  0%, 100% { transform: translateX(var(--amp-roam-a, -36px)); }
  50% { transform: translateX(var(--amp-roam-b, 36px)); }
}
@keyframes amp-sprite-face-r {
  0%, 49.99% { transform: scaleX(1); }
  50%, 100% { transform: scaleX(-1); }
}
@keyframes amp-sprite-face-l {
  0%, 49.99% { transform: scaleX(-1); }
  50%, 100% { transform: scaleX(1); }
}
.amp-sprite {
  --amp-cell: 92px;
  position: absolute;
  width: var(--amp-cell); height: var(--amp-cell);
  margin-left: calc(var(--amp-cell) / -2); margin-bottom: -12px;
  padding: 0; border: none; background: transparent;
  cursor: pointer; z-index: 8;
  animation: none;
  pointer-events: auto;
}
.amp-sprite.mobile {
  animation: amp-sprite-roam var(--amp-roam-dur, 12s) ease-in-out infinite;
  animation-delay: var(--amp-roam-delay, 0s);
}
.amp-sprite.mobile .amp-sprite-body {
  display: block; width: 100%; height: 100%;
}
.amp-sprite.mobile.face-r .amp-sprite-body,
.amp-sprite.mobile.face-l .amp-sprite-body {
  transform-origin: center bottom;
  animation: amp-sprite-face-r var(--amp-roam-dur, 12s) ease-in-out infinite;
  animation-delay: var(--amp-roam-delay, 0s);
}
.amp-sprite.mobile.face-l .amp-sprite-body {
  animation-name: amp-sprite-face-l;
}
.amp-sprite.still, .amp-sprite.cat {
  animation: none;
}
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
.amp-life-layer { position:absolute; inset:0; pointer-events:none; overflow:hidden; }
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
.amp-pict-inset .amp-sprite { --amp-cell: 58px; }
.amp-sprite:hover { filter: drop-shadow(0 0 14px rgba(240,230,200,.85)); }
.amp-sprite.mobile:hover { animation-play-state: paused; }
.amp-sprite.mobile.face-r:hover .amp-sprite-body,
.amp-sprite.mobile.face-l:hover .amp-sprite-body { animation-play-state: paused; }
.amp-sprite.amp-roamer {
  animation: none;
}
.amp-sprite.amp-roamer .amp-sprite-body {
  animation: none;
  transform-origin: center bottom;
}
.amp-sprite.amp-roamer.face-r .amp-sprite-body { transform: scaleX(1); }
.amp-sprite.amp-roamer.face-l .amp-sprite-body { transform: scaleX(-1); }
.amp-sprite.amp-roamer.crossing {
  animation: amp-roamer-cross var(--amp-cross-dur, 16s) linear forwards;
}
.amp-sprite.amp-roamer.crossing .amp-sprite-film {
  animation: amp-film var(--amp-film-dur, .8s) steps(var(--amp-frames, 4)) infinite;
}
@keyframes amp-roamer-cross {
  0% { transform: translateX(var(--amp-cross-from)); opacity: 0; }
  7% { opacity: 1; }
  93% { opacity: 1; }
  100% { transform: translateX(var(--amp-cross-to)); opacity: 0; }
}
.amp-sprite.ailing svg, .amp-sprite.ailing img, .amp-sprite.ailing .amp-sprite-film {
  filter: saturate(.55) brightness(.85);
}
.amp-sprite-halo {
  position: absolute; inset: -4px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(240,230,200,.28), transparent 70%);
  pointer-events: none;
}
.amp-notice {
  position: absolute; left: 50%; bottom: 4.5%;
  transform: translateX(-50%);
  z-index: 24; pointer-events: auto;
  max-width: min(420px, 88%);
  width: max-content;
}
.amp-notice[hidden] { display: none !important; }
.amp-notice-card {
  position: relative;
  background: rgba(10, 8, 20, 0.78);
  border: 1px solid rgba(232, 213, 163, 0.28);
  border-radius: 12px;
  padding: 0.7rem 1.9rem 0.75rem 0.95rem;
  color: #f0e6c8;
  text-shadow: 0 1px 8px rgba(0,0,0,.65);
  font: 15px/1.45 Georgia, "Palatino Linotype", serif;
  box-shadow: 0 10px 28px rgba(0,0,0,.35);
}
.amp-notice-x {
  position: absolute; top: 6px; right: 8px;
  border: 0; background: transparent; color: #b8a97f;
  cursor: pointer; font-size: 18px; line-height: 1; padding: 2px 6px;
}
.amp-notice-name { font-weight: 700; letter-spacing: .02em; margin: 0 0 .25rem 0; }
.amp-notice-line { color: #e8d5a3; font-style: italic; }
.amp-notice-acts { margin-top: .45rem; display: flex; flex-wrap: wrap; gap: .35rem; }
.amp-notice-act {
  border: 1px solid rgba(232, 213, 163, 0.28);
  background: rgba(232, 213, 163, 0.08);
  color: #f0e6c8; border-radius: 8px;
  padding: .2rem .55rem; cursor: pointer; font: 13px/1.2 Georgia, serif;
}
.amp-notice-act:hover { background: rgba(232, 213, 163, 0.18); }
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


def _roamer_cross_secs(kind: str, oid: str) -> float:
    """Seconds to cross the viewport for a roamer kind."""
    lo, hi = _ROAMER_DUR.get(kind, (11, 18))
    seed = abs(hash(oid))
    span = max(1, hi - lo)
    return float(lo + seed % (span + 1))


def _sprite_button_html(
    b: dict,
    *,
    page_layer: bool,
    roamer: bool = False,
) -> str:
    """One clickable stage sprite."""
    kind = str(b.get("kind") or "")
    hs = b.get("hotspot") or {}
    left = hs.get("left") or "50%"
    bottom = hs.get("bottom") or "20%"
    if page_layer:
        bottom = _page_window_bottom(kind, str(bottom))
    oid_raw = str(b.get("id") or "")
    oid = _html.escape(oid_raw, quote=True)
    title = _html.escape(str(b.get("name") or kind or "life"), quote=True)
    ailing = " ailing" if b.get("status") == "ailing" else ""
    motion = _sprite_motion_class(kind)
    sky = " sky" if kind in _SKY_KINDS else ""
    delay = abs(hash(oid_raw)) % 17 / 10.0
    facing = _sprite_facing_class(kind) if motion == " mobile" and not roamer else ""
    roam = (
        _sprite_roam_style(kind, oid_raw, delay=delay)
        if motion == " mobile" and not roamer else ""
    )
    roamer_cls = " amp-roamer" if roamer else ""
    return (
        f'<button type="button" class="amp-sprite{motion}{facing}{ailing}{sky}{roamer_cls}" '
        f'data-oid="{oid}" '
        f'title="{title}" aria-label="{title}" '
        f'style="left:{left};bottom:{bottom};{roam}">'
        f'<span class="amp-sprite-halo"></span>'
            f'<span class="amp-sprite-body">{_sprite_markup(kind, mobile=(motion == " mobile"))}</span>'
        f"</button>"
    )


def _roamer_pool(scene: List[dict], *, page_layer: bool) -> List[dict]:
    """Place-eligible roamers for client-side viewport spawn/despawn."""
    pool = []
    for b in scene or []:
        kind = str(b.get("kind") or "")
        if kind not in _ROAMER_KINDS or not b.get("clickable") or not b.get("id"):
            continue
        hs = b.get("hotspot") or {}
        bottom = hs.get("bottom") or "20%"
        if page_layer:
            bottom = _page_window_bottom(kind, str(bottom))
        oid = str(b.get("id"))
        pool.append({
            "oid": oid,
            "kind": kind,
            "name": str(b.get("name") or kind),
            "ailing": b.get("status") == "ailing",
            "bottom": bottom,
            "dur": _roamer_cross_secs(kind, oid),
            "body": _sprite_markup(kind),
            "notice": _notice_entry(b),
        })
    return pool


def _viewport_roam_js(*, max_active: int, spawn_prob: float) -> str:
    """Client-side probabilistic roamer lifecycle inside the land iframe."""
    prob = max(0.05, min(0.95, spawn_prob))
    return f"""
  (function(){{
    var el = document.getElementById('amp-roamer-pool');
    if (!el || !root) return;
    var pool = [];
    try {{ pool = JSON.parse(el.textContent || '[]'); }} catch (e) {{ return; }}
    if (!pool.length) return;

    var maxActive = {max_active};
    var spawnProb = {prob:.2f};
    var active = 0;
    var busy = {{}};

    function rand(a, b) {{ return a + Math.random() * (b - a); }}
    function stageW() {{
      return root.clientWidth || window.innerWidth || 800;
    }}
    function cellPx() {{
      var probe = root.querySelector('.amp-sprite');
      if (!probe) return 92;
      var v = getComputedStyle(probe).getPropertyValue('--amp-cell');
      return parseFloat(v) || 92;
    }}
    function pick() {{
      var avail = pool.filter(function(p) {{ return !busy[p.oid]; }});
      if (!avail.length) {{
        busy = {{}};
        avail = pool.slice();
      }}
      return avail[Math.floor(Math.random() * avail.length)];
    }}
    function spawn(force) {{
      if (active >= maxActive) return;
      if (!force && Math.random() > spawnProb) return;
      var ent = pick();
      if (!ent) return;
      busy[ent.oid] = true;
      active += 1;

      var w = stageW();
      var cell = cellPx();
      var margin = cell * 0.75;
      var anchorPct = 12 + Math.random() * 76;
      var anchorPx = w * anchorPct / 100;
      var fromLeft = Math.random() < 0.5;
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'amp-sprite amp-roamer mobile'
        + (ent.ailing ? ' ailing' : '')
        + (fromLeft ? ' face-r' : ' face-l');
      btn.setAttribute('data-oid', ent.oid);
      btn.setAttribute('title', ent.name);
      btn.setAttribute('aria-label', ent.name);
      if (ent.notice && typeof book !== 'undefined') book[ent.oid] = ent.notice;
      btn.style.left = anchorPct + '%';
      btn.style.bottom = ent.bottom;
      if (fromLeft) {{
        btn.style.setProperty('--amp-cross-from', (-anchorPx - margin) + 'px');
        btn.style.setProperty('--amp-cross-to', (w - anchorPx + margin) + 'px');
      }} else {{
        btn.style.setProperty('--amp-cross-from', (w - anchorPx + margin) + 'px');
        btn.style.setProperty('--amp-cross-to', (-anchorPx - margin) + 'px');
      }}
      btn.style.setProperty('--amp-cross-dur', (ent.dur || 14) + 's');
      btn.innerHTML = '<span class="amp-sprite-halo"></span>'
        + '<span class="amp-sprite-body">' + ent.body + '</span>';
      root.appendChild(btn);
      requestAnimationFrame(function() {{ btn.classList.add('crossing'); }});

      function done() {{
        btn.removeEventListener('animationend', done);
        if (btn.parentNode) btn.parentNode.removeChild(btn);
        delete busy[ent.oid];
        active = Math.max(0, active - 1);
        if (Math.random() < spawnProb) {{
          setTimeout(function() {{ spawn(false); }}, rand(400, 2800));
        }}
      }}
      btn.addEventListener('animationend', done);
    }}

    function tick() {{
      spawn(false);
      setTimeout(tick, rand(9000, 20000));
    }}
    if (Math.random() < 0.85) spawn(true);
    if (Math.random() < 0.45 && maxActive > 1) setTimeout(function() {{ spawn(true); }}, rand(800, 3200));
    setTimeout(tick, rand(6000, 14000));
  }})();
"""


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
            '<div class="amp-fountain" style="left:46%;bottom:2%;"></div>'
        )
    if "laundry" in kinds:
        parts.append(
            '<div class="amp-laundry" style="left:78%;bottom:18%;"></div>'
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
    inset_height: int = 0,
) -> str:
    """Weather + ambient + clickable sprites.

    ``page_layer=True`` pins figures to the viewport. The cinematic postcard
    is an ``<img>`` inside this iframe (not a page ``::before``), so Streamlit
    cannot mangle ``background-size``.
    """
    from src.ui_weather import image_data_uri, overlay_for

    art_path = image_path
    if page_layer and image_path:
        try:
            from src.ui_backgrounds import postcard_art_path
            art_path = postcard_art_path(image_path) or image_path
        except Exception:
            art_path = image_path

    uri = ""
    if art_path:
        uri = image_data_uri(art_path, max_width=max_width) or ""
        if not uri and not page_layer:
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
    roamer_pool = _roamer_pool(clickable, page_layer=page_layer) if entities else []
    max_roamers = 3 if dense else 2
    notice_book = {
        str(b.get("id")): _notice_entry(b)
        for b in clickable
        if b.get("id")
    }
    sprites = []
    for b in ranked[:max_sprites]:
        kind = str(b.get("kind") or "")
        if kind in _ROAMER_KINDS:
            continue
        sprites.append(_sprite_button_html(b, page_layer=page_layer))

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
            'background:transparent;overflow:hidden;}'
            '.amp-land-photo{position:absolute;inset:0;width:100%;height:100%;'
            'object-fit:cover;object-position:center bottom;pointer-events:none;'
            'z-index:0;display:block;}</style>'
            '<div id="amp-pict-stage" style="position:fixed;inset:0;width:100%;'
            'height:100%;overflow:hidden;background:transparent;pointer-events:none;">'
        )
        art_div = (
            f'<img class="amp-land-photo" alt="" src="{uri}">' if uri else ""
        )
    else:
        pos = "center center"
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
        # Full page window: lower border is the ground (sprites use bottom ~0–2%).
        pin_js = (
            "  var f = window.frameElement;\n"
            "  if (f) {\n"
            "    f.setAttribute('data-amp-land', '1');\n"
            "    f.removeAttribute('width'); f.removeAttribute('height');\n"
            "    f.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;"
            "border:0;z-index:0;background:transparent;pointer-events:auto;"
            "max-width:none;max-height:none;';\n"
            "    var p = f.parentElement;\n"
            "    if (p) {\n"
            "      p.setAttribute('data-amp-land-wrap', '1');\n"
            "      p.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;"
            "margin:0;padding:0;overflow:visible;z-index:0;border:none;"
            "background:transparent;pointer-events:none;';\n"
            "    }\n"
            "  }\n"
        )
    else:
        cap = int(inset_max_width or 0)
        fixed_h = max(120, int(inset_height or 405))
        pin_js = (
            f"  var maxW = {cap};\n"
            f"  var fixedH = {fixed_h};\n"
            "  var f = window.frameElement;\n"
            "  function fit(){\n"
            "    if (!f) return;\n"
            "    f.removeAttribute('width'); f.removeAttribute('height');\n"
            "    var doc = window.parent.document;\n"
            "    var sb = doc.querySelector('[data-testid=\"stSidebar\"]');\n"
            "    var sbr = sb ? sb.getBoundingClientRect() : null;\n"
            "    var left = (sbr && sbr.width > 40 && sbr.right > 0)\n"
            "      ? Math.round(sbr.right) : 0;\n"
            "    var avail = Math.max(240, Math.round(window.parent.innerWidth - left));\n"
            "    var w = (maxW > 0) ? Math.min(maxW, avail) : avail;\n"
            "    var h = fixedH;\n"
            "    f.style.cssText = 'width:'+w+'px;height:'+h+'px;border:0;"
            "display:block;margin:0;overflow:hidden;max-width:none;';\n"
            "    var p = f.parentElement;\n"
            "    if (p) {\n"
            "      p.style.marginLeft = '0px';\n"
            "      p.style.width = 'auto';\n"
            "      var pr = p.getBoundingClientRect();\n"
            "      var shift = Math.round(left - pr.left);\n"
            "      p.style.cssText = 'width:'+w+'px;height:'+h+'px;text-align:left;"
            "overflow:visible;margin:0 0 0 '+shift+'px;padding:0;max-width:none;';\n"
            "      var g = p.parentElement;\n"
            "      if (g) {\n"
            "        g.style.overflow = 'visible';\n"
            "        g.style.maxWidth = 'none';\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "  fit();\n"
            "  try { new ResizeObserver(fit).observe(f.parentElement || f); }\n"
            "  catch (e) {}\n"
            "  window.addEventListener('resize', fit);\n"
        )

    roamer_json = ""
    roam_js = ""
    if roamer_pool:
        roamer_json = (
            '<script type="application/json" id="amp-roamer-pool">'
            + json.dumps(roamer_pool, ensure_ascii=False)
            + "</script>"
        )
        roam_js = _viewport_roam_js(
            max_active=max_roamers,
            spawn_prob=0.68 if dense else 0.62,
        )

    notice_json = (
        '<script type="application/json" id="amp-notice-book">'
        + json.dumps(notice_book, ensure_ascii=False)
        + "</script>"
    )
    notice_ui = (
        '<div id="amp-notice" hidden>'
        '<div class="amp-notice-card">'
        '<button type="button" class="amp-notice-x" aria-label="close">×</button>'
        '<div class="amp-notice-name"></div>'
        '<div class="amp-notice-line"></div>'
        '<div class="amp-notice-acts"></div>'
        "</div></div>"
    )

    body = (
        f"{shell}"
        f"{art_div}"
        f"{wx}"
        f"{ambient}"
        f'{"".join(sprites)}'
        f"{read_block}"
        f"{notice_ui}"
        f"{roamer_json}"
        f"{notice_json}"
        f"</div>"
        "<script>\n"
        "(function(){\n"
        f"{pin_js}"
        "  var root = document.getElementById('amp-pict-stage');\n"
        "  if(!root) return;\n"
        "  var book = {};\n"
        "  try {\n"
        "    var nb = document.getElementById('amp-notice-book');\n"
        "    book = JSON.parse((nb && nb.textContent) || '{}');\n"
        "  } catch (e) { book = {}; }\n"
        "  var card = document.getElementById('amp-notice');\n"
        "  var nameEl = card ? card.querySelector('.amp-notice-name') : null;\n"
        "  var lineEl = card ? card.querySelector('.amp-notice-line') : null;\n"
        "  var actsEl = card ? card.querySelector('.amp-notice-acts') : null;\n"
        "  function hideNotice(){ if (card) card.hidden = true; }\n"
        "  function showNotice(oid){\n"
        "    var n = book[oid];\n"
        "    if (!n || !card || !nameEl || !lineEl || !actsEl) return;\n"
        "    nameEl.textContent = n.name || oid;\n"
        "    lineEl.textContent = n.line || '';\n"
        "    actsEl.innerHTML = '';\n"
        "    (n.acts || []).forEach(function(a){\n"
        "      var b = document.createElement('button');\n"
        "      b.type = 'button';\n"
        "      b.className = 'amp-notice-act';\n"
        "      b.textContent = a.glyph || a.id;\n"
        "      b.addEventListener('click', function(ev){\n"
        "        ev.preventDefault(); ev.stopPropagation();\n"
        "        if (a.note) lineEl.textContent = a.note;\n"
        "      });\n"
        "      actsEl.appendChild(b);\n"
        "    });\n"
        "    card.hidden = false;\n"
        "  }\n"
        "  if (card) {\n"
        "    var x = card.querySelector('.amp-notice-x');\n"
        "    if (x) x.addEventListener('click', function(ev){\n"
        "      ev.preventDefault(); ev.stopPropagation(); hideNotice();\n"
        "    });\n"
        "    card.addEventListener('click', function(ev){ ev.stopPropagation(); });\n"
        "  }\n"
        "  root.addEventListener('click', function(ev){\n"
        "    var t = ev.target.closest ? ev.target.closest('.amp-sprite') : null;\n"
        "    if(!t) { hideNotice(); return; }\n"
        "    ev.preventDefault();\n"
        "    ev.stopPropagation();\n"
        "    showNotice(t.getAttribute('data-oid'));\n"
        "  });\n"
        f"{roam_js}"
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
    inset_height: int = 0,
    key: str = "pict",
) -> bool:
    """Render the land overlay. ``page_layer`` pins figures and the postcard to the viewport."""
    from streamlit.components.v1 import html as components_html

    html = pictorial_stage_html(
        image_path, place, effect, sky, scene,
        height=height, max_width=max_width, read_line=read_line,
        dense=dense, page_layer=page_layer, entities=entities,
        inset_max_width=inset_max_width, inset_height=inset_height,
    )
    if not html:
        return False
    if page_layer:
        slot = 1
    else:
        slot = max(120, int(inset_height or height or 405))
    components_html(html, height=slot, scrolling=False)
    return True


# 16:9 height at the old Visit cap (720px). Width may grow; height does not.
CLASSIC_WINDOW_HEIGHT = 405


def render_inset_window(
    image_path,
    place: str,
    scene: List[dict],
    *,
    height: int = 0,
    dense: bool = False,
    entities: bool = True,
    box_max: int = 0,
    key: str = "inset",
) -> None:
    """Classic place window: full main-pane width, fixed height, not full-bleed."""
    import streamlit as st
    from src.ui_weather import scene_html, effect_for

    if not image_path:
        return
    try:
        from src.ui_backgrounds import postcard_art_path
        image_path = postcard_art_path(image_path) or image_path
    except Exception:
        pass
    win_h = max(120, int(height or CLASSIC_WINDOW_HEIGHT))
    effect, sky = effect_for(place)
    ok = render_pictorial_stage(
        image_path, place, effect, sky, scene or [],
        height=win_h, dense=dense, page_layer=False,
        entities=entities, inset_max_width=int(box_max or 0),
        inset_height=win_h, key=key,
    )
    if ok:
        return
    html = scene_html(
        image_path, place or "Amphoreus", effect, sky,
        height=win_h, rounded=True, full_width=True,
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
