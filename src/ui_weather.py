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


def classify(sky) -> str:
    """Map a sky description to a visual effect key."""
    s = (sky or "").lower()
    if "black tide" in s or "darkens the sky" in s:
        return "blacktide"
    if any(k in s for k in ("storm", "thunder", "lightning", "tempest")):
        return "storm"
    if any(k in s for k in ("rain", "drizzle", "downpour")):
        return "rain"
    if any(k in s for k in ("snow", "frost", "hail")):
        return "snow"
    if any(k in s for k in ("twilight", "dusk", "night", "eclipse", "dim")):
        return "twilight"
    if any(k in s for k in ("cloud", "overcast", "mist", "fog", "haze")):
        return "cloud"
    if any(k in s for k in ("clear", "sun", "warm", "bright", "calm")):
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


_OVERLAY_CSS = {
    # a soft warm glow
    "clear": "linear-gradient(180deg,rgba(255,214,130,.10),rgba(255,180,80,.04) 45%,rgba(10,8,20,.35))",
    # dim, greyed
    "cloud": "linear-gradient(180deg,rgba(150,160,180,.22),rgba(80,90,110,.18) 50%,rgba(10,8,20,.45))",
    # rain: bluish veil + animated streaks
    "rain": ("linear-gradient(180deg,rgba(90,120,180,.20),rgba(60,80,140,.16) 50%,rgba(8,10,24,.5)),"
             "repeating-linear-gradient(103deg,transparent 0 6px,rgba(200,220,255,.10) 6px 7px)"),
    # storm: darker + flashes
    "storm": ("linear-gradient(180deg,rgba(30,40,80,.40),rgba(15,20,50,.45) 55%,rgba(5,6,16,.6)),"
              "repeating-linear-gradient(103deg,transparent 0 5px,rgba(220,235,255,.12) 5px 6px)"),
    # snow: light veil + soft dots
    "snow": ("linear-gradient(180deg,rgba(220,230,245,.16),rgba(190,205,230,.12) 50%,rgba(12,14,28,.42)),"
             "radial-gradient(rgba(255,255,255,.25) 0.5px,transparent 1.5px)"),
    # dusky violet
    "twilight": "linear-gradient(180deg,rgba(120,70,150,.18),rgba(60,30,90,.28) 55%,rgba(6,6,18,.55))",
    # black tide: deep bruise of red-violet, pulsing
    "blacktide": ("linear-gradient(180deg,rgba(90,10,60,.34),rgba(40,4,40,.5) 55%,rgba(5,2,12,.68)),"
                  "radial-gradient(ellipse at 50% 0%,rgba(200,40,90,.18),transparent 60%)"),
    "none": "linear-gradient(180deg,rgba(10,8,20,0),rgba(10,8,20,.35))",
}


def _overlay_html(effect, sky, place):
    """A full-bleed overlay div for a scene (animated for rain/storm/snow)."""
    emoji, label = EFFECT_LABEL.get(effect, EFFECT_LABEL["none"])
    css = _OVERLAY_CSS.get(effect, _OVERLAY_CSS["none"])
    animate = ""
    if effect in ("rain", "storm"):
        animate = " animation:ampwx-fall 0.9s linear infinite;"
    elif effect == "snow":
        animate = " animation:ampwx-fall 3.2s linear infinite;"
    label_txt = f"{emoji} {place} — {label}" + (f" <i>({sky})</i>" if sky else "")
    return (
        f"<div style=\"position:absolute;inset:0;pointer-events:none;"
        f"background:{css};{animate}\"></div>"
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
        "<style>"
        "@keyframes ampwx-fall { from { background-position: 0 0, 0 0; } "
        "to { background-position: -120px 260px, 0 0; } }"
        "</style>"
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
    return (
        "<style>"
        "@keyframes ampwx-fall { from { background-position: 0 0, 0 0; } "
        "to { background-position: -120px 260px, 0 0; } }"
        "</style>"
        + _overlay_html(effect, sky, label_place)
    )


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
