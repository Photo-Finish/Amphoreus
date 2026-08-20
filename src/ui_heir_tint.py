"""Heir overlay text tints — Stage 2.

Visit pictorial chrome keeps the land-gold *shadow halo* and shifts
body/heading/caption colours toward each Heir's established accent
(databank appearance, character cards, existing UI hexes). Walk the Land
passes no heir_id and stays gold.
"""
from __future__ import annotations

import colorsys

# Canonical accent (before lifting for overlay). Prefer existing
# sanctuary/map hexes when they already match the Heir; otherwise the
# databank appearance colour, still in that same gold-adjacent family.
#
# Map palette (src/world/map_data.py) is assigned by *current location
# order*, not by identity — hexes are reused here keyed by Heir.
HEIR_ACCENT: dict[str, str] = {
    # Gold-Weaver: golden hair, threads, gown — land heading gold.
    "aglaea": "#e8d5a3",
    # Light green hair, teal jacket / 8-pointed star (databank).
    "anaxa": "#7fd4c1",
    # Lavender hair, white/purple dress; Tribbie's "tiny purple Cas".
    "castorice": "#c9a0dc",
    # Blue flame-like hair — Hyperborean royalty (card + databank).
    "cerydra": "#8ab6e5",
    # Bright cyan eyes, blue-lined bodysuit (databank).
    "cipher": "#7ac2e0",
    # Childhood light / golden hour (preferences); map peach.
    "cyrene": "#e5b7a0",
    # Teal eyes, black-to-teal hair; preferences.json aesthetics "teal".
    "dan-heng-permansor-terrae": "#9ee0c8",
    # Remembrance / moon / Memory Zone — map lilac.
    "evernight": "#b3a6ff",
    # Healer of Light, Sky, "radiant rainbow" — map pink.
    "hyacine": "#e58ab8",
    # Indigo / lilac eyes, sea (databank); map periwinkle icon fill.
    "hysilens": "#c9b8f0",
    # Dark maroon/red robe, strawberry-blond with red ends (databank).
    "mydei": "#e58a8a",
    # White hair + bright cyan eyes; map silver-sky stop #a9cdf0.
    "phainon": "#a9cdf0",
    # Red fluffy hair (databank) — coral, distinct from Mydei's maroon rose.
    "tribbie": "#e09060",
}

# Land-gold overlay (src/ui_weather.py) — Aglaea keeps this exactly.
_GOLD_TEXT = {
    "body": "#f0e6c8",
    "heading": "#e8d5a3",
    "sub": "#b8a97f",
    "meta": "#c9b896",
    "beat": "#e8dcc0",
}
_GOLD_ACCENT = "#e8d5a3"


def _parse_hex(value: str) -> tuple[float, float, float]:
    h = (value or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) < 6:
        return (232.0, 213.0, 163.0)
    return (float(int(h[0:2], 16)), float(int(h[2:4], 16)), float(int(h[4:6], 16)))


def _to_hex(rgb: tuple[float, float, float]) -> str:
    r, g, b = (max(0, min(255, int(round(c)))) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def _luma(rgb: tuple[float, float, float]) -> float:
    r, g, b = (c / 255.0 for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _hls(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = (c / 255.0 for c in rgb)
    return colorsys.rgb_to_hls(r, g, b)


def _from_hls(h: float, l: float, s: float) -> tuple[float, float, float]:
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return (r * 255.0, g * 255.0, b * 255.0)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _lift(rgb: tuple[float, float, float], lightness: float, sat_keep: float) -> str:
    """Same hue, overlay-readable lightness, chroma kept (not washed to cream)."""
    h, _l, s = _hls(rgb)
    sat = _clamp(s * sat_keep, 0.16, 0.55)
    return _to_hex(_from_hls(h, lightness, sat))


def _ink(rgb: tuple[float, float, float], lightness: float, sat_keep: float) -> str:
    h, _l, s = _hls(rgb)
    sat = _clamp(s * sat_keep, 0.18, 0.48)
    return _to_hex(_from_hls(h, lightness, sat))


def accent_for(heir_id: str | None) -> str | None:
    """Canonical accent hex, or None when there is no selected Heir."""
    if not heir_id:
        return None
    return HEIR_ACCENT.get(str(heir_id).strip().lower())


def overlay_text_colors(accent_hex: str, *, ink: bool = False) -> dict[str, str]:
    """Readable body/heading/sub/meta/beat from a canonical accent."""
    hex_n = (accent_hex or "").strip().lower()
    if hex_n == _GOLD_ACCENT and not ink:
        return dict(_GOLD_TEXT)
    rgb = _parse_hex(accent_hex)
    if ink:
        return {
            "body": _ink(rgb, 0.10, 0.70),
            "heading": _ink(rgb, 0.20, 0.78),
            "sub": _ink(rgb, 0.32, 0.62),
            "meta": _ink(rgb, 0.26, 0.68),
            "beat": _ink(rgb, 0.14, 0.72),
        }
    return {
        "body": _lift(rgb, 0.88, 0.42),
        "heading": _lift(rgb, 0.80, 0.58),
        "sub": _lift(rgb, 0.64, 0.50),
        "meta": _lift(rgb, 0.70, 0.48),
        "beat": _lift(rgb, 0.84, 0.46),
    }


def apply_heir_text_tint(pal: dict, heir_id: str | None) -> dict:
    """Replace overlay *text* colours. Shadow, glass, scrim stay as-is."""
    accent = accent_for(heir_id)
    if not accent or not pal:
        return pal
    ink = _luma(_parse_hex(str(pal.get("body") or "#f0e6c8"))) < 0.4
    tinted = dict(pal)
    tinted.update(overlay_text_colors(accent, ink=ink))
    return tinted
