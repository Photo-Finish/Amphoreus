"""Quick style audit: Okhema Life sprites vs HSR-quality heuristics."""
from __future__ import annotations

import statistics
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "assets" / "life_sprites"

OKHEMA = [
    "chimera",
    "chimera_blue",
    "chimera_pink",
    "chimera_purple",
    "chimera_orange",
    "dromas",
    "dromas_calf",
    "hearth_cat",
    "resident",
    "resident_merchant",
    "fountain",
    "fountain_okhema",
    "shrine",
    "shrine_okhema",
    "well",
    "well_okhema",
    "market_stall",
    "stall_okhema",
    "mosaic",
    "mosaic_okhema",
    "pillar",
    "pillar_okhema",
    "gate",
    "gate_okhema",
    "laundry",
    "laundry_okhema",
    "forge",
    "loom",
    "scroll",
    "lamp",
]

# Reference tier: HSR-cut chimera still (184 cell, rich palette).
REF_STEMS = ("chimera", "market_stall", "dromas")


def analyze(stem: str) -> dict:
    p = ROOT / f"{stem}.png"
    if not p.is_file():
        return {"stem": stem, "missing": True}
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    px = im.load()
    opaque = [px[x, y][:3] for y in range(h) for x in range(w) if px[x, y][3] > 40]
    if not opaque:
        return {"stem": stem, "empty": True, "size": (w, h)}
    lum = [(r + g + b) / 3 for r, g, b in opaque]
    sat = [max(r, g, b) - min(r, g, b) for r, g, b in opaque]
    edges = 0
    for y in range(h - 1):
        for x in range(w - 1):
            if px[x, y][3] > 40 and px[x + 1, y][3] > 40:
                c1, c2 = px[x, y][:3], px[x + 1, y][:3]
                if sum(abs(c1[i] - c2[i]) for i in range(3)) > 48:
                    edges += 1
    fill = len(opaque) / (w * h)
    return {
        "stem": stem,
        "size": (w, h),
        "opaque_pct": round(fill * 100, 1),
        "colors": len(set(opaque)),
        "lum_std": round(statistics.pstdev(lum), 1),
        "sat_mean": round(statistics.mean(sat), 1),
        "edge_density": round(edges / (w * h) * 100, 2),
        "bytes": p.stat().st_size,
    }


def tier(r: dict) -> str:
    if r.get("missing"):
        return "MISSING"
    if r.get("empty"):
        return "EMPTY"
    w, h = r["size"]
    # Procedural flat art: low color count + low edge density on 256 canvas.
    if w >= 250 and r["colors"] < 120 and r["edge_density"] < 1.5:
        return "PROCEDURAL"
    if r["colors"] < 80 and r["sat_mean"] < 35:
        return "FLAT/PLACEHOLDER"
    if r["colors"] >= 400 and r["edge_density"] >= 2.0:
        return "HSR-RICH"
    if r["colors"] >= 200:
        return "PAINTED"
    return "MIXED"


def main() -> None:
    rows = [analyze(s) for s in OKHEMA]
    print("=== Okhema Life sprite audit ===")
    print(f"{'stem':22} {'size':>9} {'fill%':>6} {'colors':>6} {'lum':>5} {'sat':>5} {'edge':>5} {'kb':>4}  tier")
    for r in rows:
        if r.get("missing"):
            print(f"{r['stem']:22} {'MISSING':>9}")
            continue
        if r.get("empty"):
            print(f"{r['stem']:22} {str(r['size']):>9} EMPTY")
            continue
        w, h = r["size"]
        print(
            f"{r['stem']:22} {w:4}x{h:<4} {r['opaque_pct']:6.1f} {r['colors']:6d} "
            f"{r['lum_std']:5.1f} {r['sat_mean']:5.1f} {r['edge_density']:5.2f} "
            f"{r['bytes'] // 1024:4d}  {tier(r)}"
        )

    print("\n=== _hsr_src (non-bak) ===")
    src = ROOT / "_hsr_src"
    for p in sorted(src.rglob("*.png")):
        if "_bak" in p.parts:
            continue
        if p.parent.name in ("walk", "pet"):
            continue
        im = Image.open(p)
        print(f"  {p.relative_to(ROOT)}  {im.size[0]}x{im.size[1]}")


if __name__ == "__main__":
    main()
