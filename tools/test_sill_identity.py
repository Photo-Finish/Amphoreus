# -*- coding: utf-8 -*-
"""Does every sprite on the sill belong to the Heir it is filed under?

    python tools/test_sill_identity.py
    python tools/test_sill_identity.py --verbose

Filenames lie here — that is how a Trailblazer still ended up filed as "Anaxa", and
why Cyrene and Evernight were wearing other characters' art on 2026-11-01. So each
sprite is compared against that Heir's own **avatar** (the official head icon used in
chat) on the one thing that survives chibi stylisation: hair colour.

The check is deliberately blunt and catches the two failure modes seen in practice:

  * a different character — hair hue far from the avatar's (Cyrene filed as a
    silver-haired figure while her avatar is pink);
  * damaged or ghostly art — too little coverage or too little saturation to be a
    figure at all (Evernight's washed-out witch).

Exit code 1 on any mismatch.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world import eternal_page as ep  # noqa: E402
from src.world import eternal_sill as es  # noqa: E402

try:
    from PIL import Image
except Exception:  # pragma: no cover
    print("Pillow missing; identity cannot be checked")
    raise SystemExit(2)

HUE_TOLERANCE = 45.0      # degrees, circular
HIST_MIN = 0.20           # histogram intersection with the avatar's hair colours
MIN_SATURATION = 0.12     # below this the "hair" is grey/white: hue is meaningless
MIN_COVERAGE = 0.02       # opaque fraction of the canvas


def hair_signature(path: Path) -> dict:
    """Mean hue of the saturated pixels in the upper part of the image."""
    img = Image.open(path).convert("RGBA")
    img.thumbnail((200, 200))
    w, h = img.size
    px = img.load()
    hues: list[float] = []
    hist = [0] * 12
    opaque = 0
    total = w * h
    for y in range(h):
        if y > h * 0.62:          # hair and face live in the upper part
            break
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 120:
                continue
            opaque += 1
            mx, mn = max(r, g, b), min(r, g, b)
            sat = 0.0 if mx == 0 else (mx - mn) / mx
            if sat < 0.18 or mx < 50:
                continue
            h_deg = _hue(r, g, b)
            hues.append(h_deg)
            hist[int(h_deg / 30) % 12] += 1
    coverage = opaque / float(total)
    mean_hue = sum(hues) / len(hues) if hues else -1.0
    # a rough "is it colourful at all" measure over opaque pixels
    sat_energy = len(hues) / float(opaque or 1)
    total_hist = sum(hist) or 1
    return {"hue": mean_hue, "coverage": coverage, "sat_energy": sat_energy,
            "samples": len(hues), "hist": [v / total_hist for v in hist]}


def _hue(r: int, g: int, b: int) -> float:
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    if d == 0:
        return 0.0
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return (h * 60) % 360


def hue_gap(a: float, b: float) -> float:
    if a < 0 or b < 0:
        return 999.0
    d = abs(a - b) % 360
    return min(d, 360 - d)


def compare(sprite: Path, avatar: Path) -> tuple[bool, str]:
    s = hair_signature(sprite)
    a = hair_signature(avatar)
    if s["coverage"] < MIN_COVERAGE:
        return False, f"almost nothing drawn (coverage {s['coverage']:.1%})"
    if s["sat_energy"] < 0.08:
        return False, f"ghostly: only {s['sat_energy']:.0%} of it is coloured"
    # both grey/silver: hue distance means nothing, colourlessness must agree
    sprite_grey = s["samples"] < 30
    avatar_grey = a["samples"] < 30
    if sprite_grey and avatar_grey:
        return True, "both silver/grey"
    if sprite_grey != avatar_grey:
        return False, ("sprite is colourless where the avatar is not"
                       if sprite_grey else "avatar is colourless where the sprite is not")
    gap = hue_gap(s["hue"], a["hue"])
    inter = sum(min(x, y) for x, y in zip(s["hist"], a["hist"]))
    if gap > HUE_TOLERANCE:
        return False, (f"hair hue {s['hue']:.0f}° vs avatar {a['hue']:.0f}° "
                       f"(gap {gap:.0f}° > {HUE_TOLERANCE:.0f}°)")
    # Mean hue alone is blind to a different character drawn in the same family of
    # colour: the old Evernight art sat only 42° away yet shared almost none of the
    # avatar's colour distribution, so the shape of the histogram is checked too.
    if inter < HIST_MIN:
        return False, (f"colour distribution unlike the avatar"
                       f" (intersection {inter:.2f} < {HIST_MIN:.2f})")
    return True, (f"hair hue {s['hue']:.0f}° ~ avatar {a['hue']:.0f}°, "
                  f"distribution {inter:.2f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    bad = []
    checked = 0
    for cid in ep.all_ids():
        sprite = es.matte_path(cid)
        avatar = ROOT / "assets" / "avatars" / f"{cid}.png"
        if sprite is None or not avatar.is_file():
            print(f"SKIP {cid:30s} (missing sprite or avatar)")
            continue
        ok, why = compare(sprite, avatar)
        checked += 1
        print(f"{'ok  ' if ok else 'FAIL'} {cid:30s} {why}")
        if not ok:
            bad.append(cid)
    print()
    print(f"checked {checked}, mismatched {len(bad)}"
          + (": " + ", ".join(bad) if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
