"""Weather-reactive backdrop overlays for the Sanctuary UI.

The Ambient World Director (Keeper) keeps a per-city sky map in
``world.ambient["weather"]`` (city -> sky description). This module classifies
a place's sky into a visual mood (clear / cloud / rain / storm / snow /
twilight / black tide) and renders the location art as a CSS scene with a
matching overlay, so the same backdrop changes with the world.

Used by the Classic hero banner, the Map tab's area art, and the Galgame view.
"""

import base64
import io
import re
from pathlib import Path

import streamlit as st

from src.ui_backgrounds import GALGAME_DIR, DEFAULT_BG, location_slug

# --------------------------------------------------------------------- #
# Reading the world's sky
# --------------------------------------------------------------------- #


def weather_text(location) -> str:
    """The raw sky description for a place ('' if the Keeper said nothing)."""
    try:
        from src.world.world_state import WorldState
        ws = WorldState()
        w = (ws.ambient.get("weather") or {})
        loc = (location or "").strip().lower()
        if not w or not loc:
            return ""
        # exact city name
        for city, sky in w.items():
            if city and city.strip().lower() == loc:
                return str(sky or "")
        # the location slug ("okhema", "bg-okhema") vs each city's slug
        slug = loc.replace("bg-", "")
        for city, sky in w.items():
            if city and location_slug(city) == f"bg-{slug}":
                return str(sky or "")
        # substring (area inside a city)
        for city, sky in w.items():
            if city and city.strip().lower() in loc:
                return str(sky or "")
        return ""
    except Exception:
        return ""


def _has(s: str, *words) -> bool:
    """Whole-word presence — so 'ripe gr**ain**' never reads as 'rain'."""
    return any(re.search(rf"\b{re.escape(w)}\b", s) for w in words)


def _pre(s: str, *stems) -> bool:
    """Prefix presence at a word start — 'cloud' matches clouds/cloudy, but
    'grain' still never matches 'rain' (no boundary before it)."""
    return any(re.search(rf"\b{re.escape(w)}", s) for w in stems)


def classify(sky) -> str:
    """Map a sky description to a visual effect key (word-aware matching)."""
    s = (sky or "").lower()
    if "black tide" in s or "darkens the sky" in s:
        return "blacktide"
    if _has(s, "storm", "thunder", "lightning", "tempest"):
        return "storm"
    if _pre(s, "rain", "drizzle", "downpour"):
        return "rain"
    if _pre(s, "snow", "frost", "hail"):
        return "snow"
    if _has(s, "twilight", "dusk", "night", "eclipse", "dim"):
        return "twilight"
    if _pre(s, "cloud", "overcast", "mist", "fog", "haze"):
        return "cloud"
    if _has(s, "clear", "sun", "warm", "bright", "calm", "golden", "still", "serene"):
        return "clear"
    return "none"


EFFECT_LABEL = {
    "clear": ("☀️", "clear"),
    "cloud": ("☁️", "overcast"),
    "rain": ("🌧️", "rain"),
    "storm": ("⛈️", "storm"),
    "snow": ("❄️", "snowfall"),
    "twilight": ("🌆", "twilight"),
    "blacktide": ("🕳️", "the black tide stirs"),
    "none": ("🌫️", "still air"),
}


def effect_for(location) -> tuple:
    """(effect_key, sky_text) for a place, or ("none", "")."""
    sky = weather_text(location)
    return classify(sky), sky


# --------------------------------------------------------------------- #
# Rendering a scene with the weather overlay
# --------------------------------------------------------------------- #


@st.cache_data(show_spinner=False)
def _data_uri_jpeg(path, max_width=1280):
    if not Path(path).exists():
        return None
    try:
        from PIL import Image
        im = Image.open(path)
        if im.width > max_width:
            h = int(im.height * max_width / im.width)
            im = im.resize((max_width, h), Image.LANCZOS)
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=82)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None
    return f"data:image/jpeg;base64,{b64}"


# --------------------------------------------------------------------- #
# Layered, animated scenes — no JS (CSS keyframes + SVG/SMIL particles)
#
# Every effect is built from stacked layers inside one full-bleed overlay:
#   1. a colour grade (tint),
#   2. an animated particle layer (SVG: real raindrops / snowflakes /
#      stars / clouds / black-tide fog — staggered in depth and speed),
#   3. a light source layer (sun / moon / lightning flash / pulse),
#   4. the place label.
# Particles are deterministic per (effect, place) and cached, so the same
# scene never flickers between renders.
# --------------------------------------------------------------------- #
_TINT = {
    "clear": "linear-gradient(180deg,rgba(255,214,130,.12),rgba(255,180,80,.05) 45%,rgba(10,8,20,.32))",
    "cloud": "linear-gradient(180deg,rgba(140,150,175,.26),rgba(90,100,125,.20) 50%,rgba(10,8,20,.50))",
    "rain": "linear-gradient(180deg,rgba(70,95,150,.30),rgba(50,70,120,.26) 50%,rgba(6,8,20,.55))",
    "storm": "linear-gradient(180deg,rgba(28,36,72,.45),rgba(14,18,46,.50) 55%,rgba(4,5,14,.66))",
    "snow": "linear-gradient(180deg,rgba(205,218,235,.20),rgba(180,195,220,.16) 50%,rgba(10,12,26,.46))",
    "twilight": "linear-gradient(180deg,rgba(110,60,150,.22),rgba(55,28,88,.32) 55%,rgba(5,5,16,.60))",
    "blacktide": "linear-gradient(180deg,rgba(95,8,60,.40),rgba(42,4,42,.55) 55%,rgba(4,2,10,.72))",
    "none": "linear-gradient(180deg,rgba(10,8,20,0),rgba(10,8,20,.35))",
}

# The shared keyframes used by the light-source layers.
_BASE_KEYS = (
    "@keyframes ampwxflash{0%,84%,100%{opacity:0}87%{opacity:.55}90%{opacity:.08}93%{opacity:.4}}"
    "@keyframes ampwxpulse{0%,100%{opacity:.45}50%{opacity:1}}"
    "@keyframes ampwxsun{0%,100%{opacity:.45}50%{opacity:.85}}"
)


def _det_hash(s: str) -> int:
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0x7FFFFFFF
    return h


def _svg(inner: str, view: str = "0 0 300 360") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" '
        f'preserveAspectRatio="xMidYMid slice" width="100%" height="100%" '
        f'style="position:absolute;inset:0;display:block;overflow:hidden">{inner}</svg>'
    )


def _rain_svg(r, count=60, wind=-16.0, stroke="#d7e3ff"):
    """Individual falling raindrops, staggered in length/speed/opacity."""
    parts = []
    for _ in range(count):
        x = r.uniform(0, 300)
        y0 = r.uniform(-360, 0)
        ln = r.uniform(12, 34)
        dur = r.uniform(0.45, 1.15)
        op = r.uniform(0.10, 0.5)
        w = r.uniform(0.8, 1.6)
        dx = wind * ln / 300.0
        parts.append(
            f'<line x1="{x:.1f}" y1="{y0:.1f}" x2="{x+dx:.1f}" y2="{y0+ln:.1f}" '
            f'stroke="{stroke}" stroke-width="{w:.2f}" opacity="{op:.2f}">'
            f'<animate attributeName="y1" from="{y0:.1f}" to="380" dur="{dur:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" from="{y0+ln:.1f}" to="{380+ln:.1f}" dur="{dur:.2f}s" repeatCount="indefinite"/>'
            f'</line>'
        )
    return _svg("".join(parts))


def _storm_svg(r):
    """Denser, faster rain with a wilder wind."""
    return _rain_svg(r, count=88, wind=-26.0, stroke="#dfe8ff")


def _snow_svg(r, count=46):
    """Soft snowflakes that fall and sway a little."""
    parts = []
    for _ in range(count):
        x = r.uniform(0, 300)
        y0 = r.uniform(-380, 0)
        rad = r.uniform(1.0, 2.6)
        dur = r.uniform(4.5, 9.5)
        op = r.uniform(0.35, 0.9)
        sway = r.uniform(-14, 14)
        parts.append(
            f'<circle cx="{x:.1f}" cy="{y0:.1f}" r="{rad:.2f}" fill="#fff" opacity="{op:.2f}">'
            f'<animate attributeName="cy" from="{y0:.1f}" to="380" dur="{dur:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cx" values="{x:.1f};{x+sway:.1f};{x:.1f}" dur="{dur*1.3:.2f}s" repeatCount="indefinite"/>'
            f'</circle>'
        )
    return _svg("".join(parts))


def _twilight_svg(r):
    """A low amber moon with a soft halo, and twinkling stars above."""
    stars = []
    for _ in range(64):
        x = r.uniform(0, 300)
        y = r.uniform(0, 150)
        rad = r.uniform(0.4, 1.1)
        dur = r.uniform(2, 6)
        op = r.uniform(0.2, 0.9)
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.2f}" fill="#ffe9c9" opacity="{op:.2f}">'
            f'<animate attributeName="opacity" values="0.12;{op:.2f};0.12" dur="{dur:.2f}s" repeatCount="indefinite"/>'
            f'</circle>'
        )
    moon = (
        '<circle cx="236" cy="52" r="70" fill="#f6e7c8" opacity="0.05"/>'
        '<circle cx="236" cy="52" r="46" fill="#f6e7c8" opacity="0.10"/>'
        '<circle cx="236" cy="52" r="26" fill="#f6e7c8" opacity="0.90"/>'
    )
    return _svg("".join(stars) + moon)


def _cloud_svg(r, count=3, dark=False, uid="c"):
    """Large soft clouds drifting slowly across the sky."""
    blur = f'<filter id="{uid}blur"><feGaussianBlur stdDeviation="16"/></filter>'
    base = "#e8ecf2" if not dark else "#59637a"
    parts = []
    for _ in range(count):
        cx = r.uniform(-50, 350)
        cy = r.uniform(16, 130)
        rx = r.uniform(60, 150)
        ry = r.uniform(16, 42)
        op = r.uniform(0.14, 0.3)
        dur = r.uniform(28, 60)
        dist = r.uniform(140, 280)
        parts.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="{base}" opacity="{op:.2f}" filter="url(#{uid}blur)">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 0" to="{dist:.1f} 0" dur="{dur:.1f}s" repeatCount="indefinite"/>'
            f'</ellipse>'
        )
    return blur + "".join(parts)


def _blacktide_svg(r, count=5):
    """Dark smoke and fog rising from below, slow and heavy."""
    parts = []
    for _ in range(count):
        cx = r.uniform(0, 300)
        rx = r.uniform(90, 190)
        ry = r.uniform(22, 48)
        op = r.uniform(0.10, 0.3)
        dur = r.uniform(9, 18)
        parts.append(
            f'<ellipse cx="{cx:.1f}" cy="360" rx="{rx:.1f}" ry="{ry:.1f}" fill="#3a0710" opacity="{op:.2f}">'
            f'<animate attributeName="cy" values="380;260;110" dur="{dur:.1f}s" repeatCount="indefinite"/>'
            f'</ellipse>'
        )
    return _svg("".join(parts))


def _light_layer(effect) -> str:
    """The light-source layer (sun / moon / lightning / pulse) or ''."""
    if effect == "clear":
        return ('<div style="position:absolute;inset:0;pointer-events:none;'
                'background:radial-gradient(circle at 78% 18%,rgba(255,225,150,.5),transparent 34%);'
                'animation:ampwxsun 8s ease-in-out infinite;"></div>')
    if effect == "twilight":
        return ('<div style="position:absolute;inset:0;pointer-events:none;'
                'background:radial-gradient(circle at 79% 17%,rgba(246,231,200,.4),transparent 30%);'
                'animation:ampwxsun 7s ease-in-out infinite;"></div>')
    if effect == "storm":
        return ('<div style="position:absolute;inset:0;pointer-events:none;'
                'background:radial-gradient(ellipse at 62% 12%,rgba(255,255,255,.85),transparent 55%);'
                'animation:ampwxflash 6.5s linear infinite;"></div>')
    if effect == "blacktide":
        return ('<div style="position:absolute;inset:0;pointer-events:none;'
                'background:radial-gradient(ellipse at 50% 0%,rgba(210,45,95,.3),transparent 55%);'
                'animation:ampwxpulse 5s ease-in-out infinite;"></div>')
    return ""


@st.cache_data(show_spinner=False)
def _particle_html(effect: str, place: str) -> str:
    """The deterministic animated particle layer for an effect."""
    key = f"{effect}::{place}"
    r = __import__("random").Random("ampwx-" + key)
    uid = "ampwx" + str(_det_hash(key) % 100000)
    if effect == "rain":
        return _rain_svg(r)
    if effect == "storm":
        return _storm_svg(r)
    if effect == "snow":
        return _snow_svg(r)
    if effect == "twilight":
        return _twilight_svg(r)
    if effect == "cloud":
        return _svg(_cloud_svg(r, count=3, dark=False, uid=uid))
    if effect == "blacktide":
        return _blacktide_svg(r)
    return ""


def _overlay_html(effect, sky, place):
    """A full-bleed, layered, animated weather overlay for a scene."""
    emoji, label = EFFECT_LABEL.get(effect, EFFECT_LABEL["none"])
    tint = _TINT.get(effect, _TINT["none"])
    particles = _particle_html(effect, place)
    light = _light_layer(effect)
    label_txt = f"{emoji} {place} — {label}" + (f" <i>({sky})</i>" if sky else "")
    return (
        f"<style>{_BASE_KEYS}</style>"
        f"<div style=\"position:absolute;inset:0;pointer-events:none;overflow:hidden;\">"
        f"<div style=\"position:absolute;inset:0;background:{tint};\"></div>"
        f"{particles}"
        f"{light}"
        f"</div>"
        f"<div style=\"position:absolute;top:12px;left:14px;font-size:13px;"
        f"color:#f0e6c8;letter-spacing:.5px;text-shadow:0 1px 6px rgba(0,0,0,.8);"
        f"background:rgba(10,8,20,.45);padding:3px 12px;border-radius:999px;\">"
        f"{label_txt}</div>"
    )


def scene_html(image_path, place, effect, sky, height=300, rounded=True):
    """Full HTML for a location scene: art + weather overlay + place tag."""
    uri = _data_uri_jpeg(image_path)
    if not uri:
        return ""
    bg_css = f"background-image:url('{uri}');"
    radius = "border-radius:14px;" if rounded else ""
    return (
        f"<div style=\"position:relative;height:{height}px;{radius}overflow:hidden;"
        f"border:1px solid rgba(232,213,163,.16);\">"
        f"<div style=\"position:absolute;inset:0;{bg_css}background-size:cover;"
        f"background-position:center;\"></div>"
        f"{_overlay_html(effect, sky, place)}"
        "</div>"
    )


def overlay_for(location, place=None):
    """Public weather overlay HTML for a place — for embedding inside custom
    scenes (e.g. the Galgame view's component). Includes its keyframes."""
    effect, sky = effect_for(location)
    label_place = place or location or "Amphoreus"
    return _overlay_html(effect, sky, label_place)


def render_scene(location, image_path=None, title=None, height=300):
    """Render a weather-reactive scene for a place into the page."""
    effect, sky = effect_for(location)
    if image_path is None:
        slug = location_slug(location)
        p = GALGAME_DIR / f"{slug}.jpg" if slug else None
        image_path = p if p and p.exists() else (DEFAULT_BG if DEFAULT_BG.exists() else None)
    if not image_path:
        return
    place = title or location or "Amphoreus"
    html = scene_html(image_path, place, effect, sky, height=height)
    if html:
        st.markdown(html, unsafe_allow_html=True)
