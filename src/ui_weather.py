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
        im.save(buf, format="JPEG", quality=88 if max_width >= 1600 else 82)
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


def _overlay_html(effect, sky, place, *, show_place_tag=True):
    """A full-bleed, layered, animated weather overlay for a scene."""
    emoji, label = EFFECT_LABEL.get(effect, EFFECT_LABEL["none"])
    tint = _TINT.get(effect, _TINT["none"])
    particles = _particle_html(effect, place)
    light = _light_layer(effect)
    tag = ""
    if show_place_tag:
        label_txt = f"{emoji} {place} — {label}" + (f" <i>({sky})</i>" if sky else "")
        tag = (
            f"<div style=\"position:absolute;top:12px;left:14px;font-size:13px;"
            f"color:#f0e6c8;letter-spacing:.5px;text-shadow:0 1px 6px rgba(0,0,0,.8);"
            f"background:rgba(10,8,20,.45);padding:3px 12px;border-radius:999px;\">"
            f"{label_txt}</div>"
        )
    return (
        f"<style>{_BASE_KEYS}</style>"
        f"<div style=\"position:absolute;inset:0;pointer-events:none;overflow:hidden;\">"
        f"<div style=\"position:absolute;inset:0;background:{tint};\"></div>"
        f"{particles}"
        f"{light}"
        f"</div>"
        f"{tag}"
    )


def image_data_uri(image_path, max_width=1920):
    """Public JPEG data-URI for embedding in pictorial / full-bleed stages."""
    return _data_uri_jpeg(image_path, max_width=max_width)


# High-key skies/wheat need dark ink; sampled left-reading zone of local JPEGs.
_INK_SLUGS = frozenset({"styxia", "aedes-elysiae"})
# Mid-key marble/mist: keep sanctuary gold, thicker glass.
_THICK_GOLD_SLUGS = frozenset({
    "okhema", "kremnos", "memortis-shore", "beyond-time",
    "grove", "eye-of-twilight",
})


def backdrop_slug(image_path) -> str:
    """``bg-okhema.jpg`` → ``okhema``."""
    stem = Path(image_path).stem.lower() if image_path else ""
    return stem[3:] if stem.startswith("bg-") else stem


def ground_css_position(image_path) -> str:
    """Pin the backdrop onto pavement / path, not the sky."""
    p = Path(image_path) if image_path else None
    if p and p.parent.name == "ground":
        # Already cropped to the floor — further 62% shift zooms into pavement.
        return "center center"
    slug = backdrop_slug(image_path)
    return {
        "okhema": "18% 88%",
        "okhema-evernight": "18% 86%",
        "aedes-elysiae": "center 68%",
        "dawncloud": "center 78%",
        "kremnos": "center 84%",
        "kremnos-ruins": "center 82%",
        "grove": "center 88%",
        "murmuring-woods": "42% 48%",
        "styxia": "22% 84%",
        "dragonbone-city": "20% 82%",
        "janusopolis": "center 88%",
        "abyss-of-fate": "center 86%",
        "memortis-shore": "18% 78%",
    }.get(slug, "center 78%")


def read_palette(image_path) -> dict:
    """Body/heading/glass/scrim for words over this backdrop."""
    slug = backdrop_slug(image_path)
    if slug in _INK_SLUGS:
        return {
            "body": "#1a140c",
            "heading": "#3d2a12",
            "sub": "#5c4030",
            "meta": "#4a3828",
            "beat": "#2a1c12",
            "glass": "rgba(248, 242, 228, 0.78)",
            "border": "rgba(61, 42, 18, 0.28)",
            "scrim": (
                "linear-gradient(105deg,"
                "rgba(248,242,228,.58) 0%,"
                "rgba(248,242,228,.22) 34%,"
                "rgba(248,242,228,.05) 100%)"
            ),
            "shadow": "0 1px 0 rgba(248,242,228,.6)",
            "chat_bg": "rgba(248, 242, 228, 0.86)",
        }
    thick = slug in _THICK_GOLD_SLUGS
    a0, a1 = ("0.58", "0.28") if thick else ("0.52", "0.20")
    glass = "rgba(10, 8, 20, 0.88)" if thick else "rgba(10, 8, 20, 0.78)"
    return {
        "body": "#f0e6c8",
        "heading": "#e8d5a3",
        "sub": "#b8a97f",
        "meta": "#c9b896",
        "beat": "#e8dcc0",
        "glass": glass,
        "border": "rgba(232, 213, 163, 0.22)",
        "scrim": (
            f"linear-gradient(105deg,"
            f"rgba(8, 6, 16, {a0}) 0%,"
            f"rgba(8, 6, 16, {a1}) 34%,"
            f"rgba(8, 6, 16, 0.08) 100%)"
        ),
        "shadow": (
            "0 0 1px rgba(0,0,0,.95),"
            "0 1px 2px rgba(0,0,0,.88),"
            "0 2px 8px rgba(0,0,0,.72),"
            "0 0 14px rgba(0,0,0,.5)"
        ),
        "chat_bg": "rgba(10, 8, 20, 0.84)",
    }


def page_backdrop_css(image_path, max_width=1920) -> str:
    """Pictorial chrome: transparent Streamlit page, no land photo.

    The JPEG lives inside the land iframe (``render_pictorial_stage``) so
    Streamlit cannot mangle ``background-size`` and so a fixed photo-band
    cannot leave a dark body gap above it.  ``max_width`` is unused (kept
    for callers).
    """
    pal = read_palette(image_path)
    return f"""
<style>
html, body {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
}}
.stApp {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
}}
[data-testid="stAppViewContainer"],
section[data-testid="stMain"] {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
}}
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {{
  content: none !important;
  display: none !important;
  background: none !important;
  background-image: none !important;
}}
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stAppToolbar"] {{
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
}}
[data-testid="stHeader"] {{
  z-index: 60 !important;
  pointer-events: auto !important;
}}
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stAppToolbar"],
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stLogoSpacer"] {{
  z-index: 90 !important;
  pointer-events: auto !important;
}}
section[data-testid="stSidebar"] {{
  z-index: 90 !important;
  pointer-events: auto !important;
}}
/* Look picker + tabs: glass over the land while they are on screen. */
[data-testid="stTabs"],
[data-testid="stTab"],
[role="tablist"],
[role="tab"],
[data-baseweb="tab-list"],
[data-baseweb="tab"] {{
  position: relative !important;
  z-index: 80 !important;
  pointer-events: auto !important;
}}
[role="tablist"] {{
  isolation: isolate;
  background: rgba(10, 8, 20, 0.42) !important;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}}
[role="tab"] {{
  color: {pal["sub"]} !important;
  text-shadow: {pal["shadow"]};
}}
[role="tab"][aria-selected="true"] {{
  color: {pal["heading"]} !important;
  border-bottom-color: {pal["heading"]} !important;
}}
section[data-testid="stMain"] {{
  pointer-events: none;
}}
.block-container {{
  position: relative;
  z-index: 2;
  pointer-events: none;
}}
[data-testid="stMainBlockContainer"] {{
  background: transparent !important;
}}
.block-container [role="radiogroup"],
.block-container [data-testid="stRadio"],
.block-container [role="switch"],
.block-container [data-testid="stCheckbox"] {{
  background: {pal["glass"]} !important;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid {pal["border"]};
  border-radius: 10px;
  padding: 0.15rem 0.45rem;
}}
.block-container [data-testid="stWidgetLabel"] p,
.block-container [role="radiogroup"] label,
.block-container [role="switch"] label {{
  color: {pal["body"]} !important;
  text-shadow: {pal["shadow"]};
}}
/* Empty page area clicks the land; widgets stay usable. */
.block-container .stButton,
.block-container .stCheckbox,
.block-container .stSelectbox,
.block-container .stMultiSelect,
.block-container .stTextInput,
.block-container .stTextArea,
.block-container .stNumberInput,
.block-container .stRadio,
.block-container [role="radiogroup"],
.block-container [role="switch"],
.block-container [data-testid="stCheckbox"],
.block-container .stExpander,
.block-container .stAlert,
.block-container .stImage,
.block-container .stChatInput,
.block-container [data-testid="stChatMessage"],
.block-container [data-testid="stCaptionContainer"],
.block-container [data-testid="stTooltipHoverTarget"],
.block-container [data-testid="stTabs"],
.block-container [data-testid="stFileUploader"],
.block-container [data-testid="stAudioInput"],
.block-container .amp-read,
.block-container .stMarkdown:has(.amp-read) {{
  position: relative !important;
  z-index: 10 !important;
  pointer-events: auto !important;
}}
[data-testid="stBottomBlockContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stTabs"],
[data-baseweb="tab-list"],
[data-baseweb="tab"],
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavLink"],
section[data-testid="stSidebar"] {{
  pointer-events: auto !important;
}}
[data-testid="stBottomBlockContainer"] {{
  position: relative;
  z-index: 6;
  background: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border-top: 1px solid rgba(232, 213, 163, 0.16) !important;
  box-shadow: none !important;
}}
[data-amp-land-wrap="1"] {{
  position: fixed !important;
  inset: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: visible !important;
  z-index: 0 !important;
  border: none !important;
  background: transparent !important;
  pointer-events: none !important;
}}
iframe[data-amp-land="1"] {{
  position: fixed !important;
  inset: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  min-width: 100% !important;
  min-height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  border: none !important;
  z-index: 0 !important;
  background: transparent !important;
  pointer-events: auto !important;
}}
[data-testid="stTabPanel"][hidden] iframe[data-amp-land="1"],
[data-testid="stTabPanel"][hidden] [data-amp-land-wrap="1"] {{
  display: none !important;
  pointer-events: none !important;
}}
.amp-read {{
  background: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0.35rem 0 0.55rem 0;
  color: {pal["body"]};
  margin: 0.25rem 0 0.55rem 0;
}}
.amp-read strong,
.amp-read .sub,
.amp-read .meta,
.amp-read .beat {{
  text-shadow: {pal["shadow"]};
}}
.amp-read h1, .amp-read h2, .amp-read h3 {{
  color: {pal["heading"]}; margin-top: 0;
}}
.amp-read .sub {{ color: {pal["sub"]}; }}
.amp-read .meta {{ color: {pal["meta"]}; font-size: 0.9rem; letter-spacing: 0.03em; }}
.amp-read .beat {{
  font-family: Georgia, "Palatino Linotype", serif;
  font-size: 1.1rem; line-height: 1.55; font-style: italic;
  color: {pal["beat"]}; margin: 0.35rem 0 0 0;
}}
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] [data-testid="stHeading"] {{
  color: {pal["heading"]} !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] p,
[data-testid="stMain"] li,
[data-testid="stMain"] label,
[data-testid="stMain"] em,
[data-testid="stMain"] strong,
[data-testid="stMain"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
[data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] .stCaption {{
  color: {pal["body"]} !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [data-testid="stCaptionContainer"] p,
[data-testid="stMain"] [data-testid="stCaptionContainer"] span {{
  color: {pal["sub"]} !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] [data-testid="stAlert"] {{
  background: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: none !important;
  border-left: 2px solid rgba(232, 213, 163, 0.35) !important;
  border-radius: 0 !important;
  color: {pal["body"]} !important;
  padding-left: 0.55rem !important;
}}
[data-testid="stMain"] [data-testid="stAlert"] p,
[data-testid="stMain"] [data-testid="stAlert"] span,
[data-testid="stMain"] [data-testid="stAlert"] div {{
  color: {pal["body"]} !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] [data-testid="stExpander"] {{
  background: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: none !important;
  border-radius: 0 !important;
  border-bottom: 1px solid rgba(232, 213, 163, 0.12) !important;
  box-shadow: none !important;
  margin-bottom: 0 !important;
}}
[data-testid="stMain"] [data-testid="stExpander"] details,
[data-testid="stMain"] [data-testid="stExpander"] > div,
[data-testid="stMain"] [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}}
[data-testid="stMain"] [data-testid="stExpander"] summary {{
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0.28rem 0 !important;
}}
[data-testid="stMain"] [data-testid="stExpander"] summary,
[data-testid="stMain"] [data-testid="stExpander"] p,
[data-testid="stMain"] [data-testid="stExpander"] li {{
  color: {pal["body"]} !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] .stButton > button,
[data-testid="stMain"] [data-testid^="stBaseButton"] {{
  background: transparent !important;
  color: {pal["body"]} !important;
  border: none !important;
  border-bottom: 1px solid rgba(232, 213, 163, 0.32) !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] .stButton > button:hover,
[data-testid="stMain"] [data-testid^="stBaseButton"]:hover {{
  color: {pal["heading"]} !important;
  border-bottom-color: rgba(232, 213, 163, 0.7) !important;
  background: transparent !important;
}}
[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="select"] > div {{
  background: transparent !important;
  background-color: transparent !important;
  color: {pal["body"]} !important;
  border: none !important;
  border-bottom: 1px solid rgba(232, 213, 163, 0.32) !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] span {{
  background: transparent !important;
  color: {pal["body"]} !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stChatMessage"],
[data-testid="stChatMessageContent"],
[data-testid="stChatMessage"] > div {{
  background: transparent !important;
  color: {pal["body"]} !important;
  border: none !important;
  box-shadow: none !important;
}}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li {{
  color: {pal["body"]} !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] .amp-travelbar {{
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid rgba(232, 213, 163, 0.12) !important;
  border-radius: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] .amp-travelnote {{
  background: transparent !important;
  border: none !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] [data-testid="stFileUploader"],
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"],
[data-testid="stMain"] [data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stMain"] [data-testid="stFileUploader"] section,
[data-testid="stMain"] [data-testid="stFileUploader"] button {{
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  text-shadow: {pal["shadow"]};
}}
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {{
  border: none !important;
  border-bottom: 1px dashed rgba(232, 213, 163, 0.28) !important;
  border-radius: 0 !important;
}}
[data-testid="stMain"] [data-testid="stAudioInput"],
[data-testid="stMain"] [data-testid="stAudioInput"] > div,
[data-testid="stMain"] [data-testid="stAudioInputWaveSurfer"] {{
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  border: none !important;
  border-bottom: 1px solid rgba(232, 213, 163, 0.28) !important;
  border-radius: 0 !important;
}}
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stBottomBlockContainer"] [data-testid="stChatInput"] {{
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input,
[data-testid="stChatInputTextArea"] {{
  color: {pal["body"]} !important;
  background: transparent !important;
  caret-color: {pal["heading"]} !important;
  text-shadow: {pal["shadow"]};
  border: none !important;
  border-bottom: 1px solid rgba(232, 213, 163, 0.32) !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}}
[data-testid="stChatInput"] [data-testid="stChatInputSubmitButton"] {{
  color: {pal["heading"]} !important;
  background: transparent !important;
  box-shadow: none !important;
}}
[data-testid="stMain"] [data-testid="stSelectbox"],
[data-testid="stMain"] [data-testid="stFileUploader"],
[data-testid="stMain"] [data-testid="stAudioInput"],
[data-testid="stChatInput"],
[data-testid="stBottomBlockContainer"] {{
  --secondary-background-color: transparent !important;
  --st-secondary-background-color: transparent !important;
}}
[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] div {{
  background: transparent !important;
  background-color: transparent !important;
}}
[data-testid="stChatInput"] div {{
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
}}
[data-testid="stMain"] [data-testid="stAudioInput"] div {{
  background: transparent !important;
  background-color: transparent !important;
}}
[data-testid="stMain"] [data-testid="stFileUploaderDropzone"] div {{
  background: transparent !important;
  background-color: transparent !important;
}}
section[data-testid="stSidebar"] {{
  background: rgba(12, 10, 22, 0.92) !important;
}}
[data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"],
.stCaption, .stAlert {{
  text-shadow: {pal["shadow"]};
}}
html.amp-land-off,
html.amp-land-off body,
html.amp-land-off .stApp,
html.amp-land-off [data-testid="stAppViewContainer"] {{
  background: #0b0a14 !important;
  background-color: #0b0a14 !important;
}}
html.amp-land-off [data-testid="stAppViewContainer"]::before,
html.amp-land-off [data-testid="stAppViewContainer"]::after {{
  display: none !important;
}}
html.amp-land-off iframe[data-amp-land="1"],
html.amp-land-off [data-amp-land-wrap="1"] {{
  display: none !important;
  pointer-events: none !important;
}}
html.amp-land-off section[data-testid="stMain"],
html.amp-land-off [data-testid="stMainBlockContainer"],
html.amp-land-off .block-container {{
  background: transparent !important;
  pointer-events: auto !important;
}}
</style>
"""


def scene_html(image_path, place, effect, sky, height=300, rounded=True,
               max_width=1280, full_bleed=False, *,
               box_max=None, aspect=None, full_width=False):
    """Full HTML for a location scene: art + weather overlay + place tag.

    ``full_bleed=True`` drops the rounded card frame so the art can read as
    the stage plane (used under pictorial hotspots / Walk the Land).
    ``aspect`` (e.g. ``"16 / 9"``) sizes a centered card from width instead
    of a fixed pixel height, so a wide layout does not squash the picture.
    ``full_width=True`` spans the column at a fixed ``height`` (Classic
    inset: wide but not taller).
    """
    uri = _data_uri_jpeg(image_path, max_width=max_width)
    if not uri:
        return ""
    bg_css = f"background-image:url('{uri}');"
    if full_bleed:
        radius = "border-radius:0;"
        border = "border:none;"
    else:
        radius = "border-radius:14px;" if rounded else "border-radius:0;"
        border = "border:1px solid rgba(232,213,163,.16);"
    if full_width:
        box = (
            f"position:relative;width:100%;height:{int(height)}px;"
            f"max-width:none;margin:0;{radius}{border}overflow:hidden;"
        )
        pos = "center center"
    elif aspect:
        cap = f"max-width:{int(box_max)}px;" if box_max else ""
        box = (
            f"position:relative;width:100%;{cap}margin:0 auto;"
            f"aspect-ratio:{aspect};{radius}{border}overflow:hidden;"
        )
        pos = "center center"
    else:
        box = (
            f"position:relative;height:{height}px;{radius}{border}overflow:hidden;"
        )
        pos = ground_css_position(image_path)
    return (
        f"<div style=\"{box}\">"
        f"<div style=\"position:absolute;inset:0;{bg_css}background-size:cover;"
        f"background-position:{pos};background-repeat:no-repeat;\"></div>"
        f"{_overlay_html(effect, sky, place)}"
        "</div>"
    )


def overlay_for(location, place=None, *, show_place_tag=True):
    """Public weather overlay HTML for a place — for embedding inside custom
    scenes (e.g. the Galgame view's component). Includes its keyframes."""
    effect, sky = effect_for(location)
    label_place = place or location or "Amphoreus"
    return _overlay_html(effect, sky, label_place, show_place_tag=show_place_tag)


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
