# -*- coding: utf-8 -*-
"""Second-pass sill matte — no LLM, no GPU, no browser.

    python tools/test_eternal_sill.py

Guards the promises the art pass makes: the first-pass `cutouts/` are untouched,
every sill body has no straight crop edge left, the page really draws the matte,
and a missing matte folder falls back to the first pass instead of breaking.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world import eternal_sill  # noqa: E402
from src.world.eternal_page import CIRCLE, all_ids  # noqa: E402
from src.world.eternal_q import CUTOUTS, Q_SIT  # noqa: E402

PASSED, FAILED = [], []
POLICIES = {"saliency", "cut"}


def hair_hue(im) -> tuple[float, float]:
    """(hue in degrees, saturation) of the crown of the figure — where hair is."""
    import colorsys

    import numpy as np

    a = np.asarray(im.convert("RGBA"))
    alpha = a[..., 3]
    ys, _ = np.where(alpha > 160)
    cut = ys.min() + (ys.max() - ys.min()) * 0.32
    sel = (alpha > 160) & (np.arange(a.shape[0])[:, None] <= cut)
    rgb = a[..., :3][sel].astype("float32").mean(axis=0) / 255.0
    h, _l, s = colorsys.rgb_to_hls(*rgb)
    return h * 360.0, s


def check(name: str, cond: object, extra: str = "") -> None:
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}{('  ' + extra) if extra else ''}")


def main() -> int:
    from PIL import Image

    print("== The module stays a world-layer helper ==")
    src = (ROOT / "src" / "world" / "eternal_sill.py").read_text(encoding="utf-8")
    check("no Streamlit import", "streamlit" not in src)
    check("no network import", not any(
        t in src for t in ("urllib", "requests", "http.client", "socket")))

    print("== The first pass is untouched (provenance) ==")
    provenance = {}
    prov_path = eternal_sill.MATTE_DIR / "sources.json"
    check("provenance record exists", prov_path.is_file())
    if prov_path.is_file():
        provenance = json.loads(prov_path.read_text(encoding="utf-8")).get("sources", {})
    check("every circle cutout is recorded", set(provenance) >= {Q_SIT[c][0] for c in CIRCLE})
    mismatched = []
    for name, row in provenance.items():
        # Override sources are recorded relative to q_program/; first-pass
        # cutouts live in cutouts/.
        path = (CUTOUTS.parent / name) if "/" in name else (CUTOUTS / name)
        if not path.is_file():
            mismatched.append(f"{name}: missing")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row.get("sha256"):
            mismatched.append(f"{name}: changed")
    check("none of the first-pass cutouts changed since the matte was derived",
          not mismatched, ", ".join(mismatched))
    check("the first pass still holds its whole catalog", len(list(CUTOUTS.glob("*.png"))) >= 13,
          f"{len(list(CUTOUTS.glob('*.png')))} files")

    print("== Every companion has a cleaned body ==")
    ids = all_ids()
    check("thirteen companions", len(ids) == 13, str(len(ids)))
    check("every companion has a matte", set(eternal_sill.ids()) == set(ids),
          str(sorted(set(ids) - set(eternal_sill.ids()))))
    manifest = eternal_sill.manifest()
    missing_policy = [c for c in ids if (manifest.get(c) or {}).get("policy") not in POLICIES]
    check("each body records its policy", not missing_policy, ", ".join(missing_policy))

    print("== No straight crop edge survives ==")
    bad_edge, tiny, not_rgba = [], [], []
    for cid in ids:
        path = eternal_sill.matte_path(cid)
        if path is None:
            bad_edge.append(f"{cid}: none")
            continue
        im = Image.open(path)
        if im.mode != "RGBA":
            not_rgba.append(cid)
        if path.stat().st_size < eternal_sill.MIN_BYTES:
            tiny.append(cid)
        alpha = im.convert("RGBA").getchannel("A")
        border = Image.new("L", alpha.size, 0)
        border.paste(alpha.crop((0, 0, alpha.size[0], 1)), (0, 0))
        border.paste(alpha.crop((0, alpha.size[1] - 1, alpha.size[0], alpha.size[1])),
                     (0, alpha.size[1] - 1))
        border.paste(alpha.crop((0, 0, 1, alpha.size[1])), (0, 0))
        border.paste(alpha.crop((alpha.size[0] - 1, 0, alpha.size[0], alpha.size[1])),
                     (alpha.size[0] - 1, 0))
        edges = [
            max(alpha.crop((0, 0, alpha.size[0], 1)).getdata()),
            max(alpha.crop((0, alpha.size[1] - 1, alpha.size[0], alpha.size[1])).getdata()),
            max(alpha.crop((0, 0, 1, alpha.size[1])).getdata()),
            max(alpha.crop((alpha.size[0] - 1, 0, alpha.size[0], alpha.size[1])).getdata()),
        ]
        if max(edges) > 8:
            bad_edge.append(f"{cid}: edge alpha {max(edges)}")
        w, h = im.size
        if min(w, h) < 80:
            tiny.append(f"{cid}: {w}x{h}")
    check("every border pixel is see-through", not bad_edge, ", ".join(bad_edge))
    check("every body is RGBA", not not_rgba, ", ".join(not_rgba))
    check("no body is suspiciously small", not tiny, ", ".join(tiny))

    print("== Identity: the corrected sources stay corrected ==")
    anaxa = eternal_sill.matte_path("anaxa")
    check("anaxa draws the announcement bust, not the stage crop",
          anaxa is not None and anaxa.name == eternal_sill.ALIAS["anaxa"],
          anaxa.name if anaxa else "none")
    row = manifest.get("anaxa") or {}
    check("anaxa's override is recorded in the manifest",
          "misidentified" in str(row.get("note", "")), str(row.get("note", "")))
    hue, sat = hair_hue(Image.open(anaxa))
    # Canon: light green hair, black gold-patterned eyepatch
    # (`databank/chrysos-heirs/anaxa.md`). The rejected crop was grey + gold eyes.
    check(f"anaxa's hair reads mint green (hue {hue:.0f}, sat {sat:.2f})",
          115 <= hue <= 180 and sat >= 0.12)
    check("the mislabelled first-pass crop is kept on record",
          (CUTOUTS / "anaxa_v34_sit.png").is_file())
    phainon = eternal_sill.matte_path("phainon")
    check("phainon draws the sharper announcement bust",
          phainon is not None and phainon.name == eternal_sill.ALIAS["phainon"],
          phainon.name if phainon else "none")

    print("== The page draws the matte, and falls back cleanly ==")
    from src.ui_eternal_page import stage_art_uris
    art = stage_art_uris({})
    check("stage art covers the circle", set(art) == set(ids))
    no_edge, sourced = [], []
    for cid in ids:
        body = art[cid]["body"]
        raw = base64.b64decode(body.split(",", 1)[1])
        drawn = Image.open(io.BytesIO(raw)).convert("RGBA")
        alpha = drawn.getchannel("A")
        w, h = drawn.size
        edges = max(
            max(alpha.crop((0, 0, w, 1)).getdata()),
            max(alpha.crop((0, h - 1, w, h)).getdata()),
            max(alpha.crop((0, 0, 1, h)).getdata()),
            max(alpha.crop((w - 1, 0, w, h)).getdata()),
        )
        # The first pass always ends in an opaque crop edge; the matte never does.
        if edges <= 8:
            no_edge.append(cid)
        src_im = Image.open(eternal_sill.matte_path(cid))
        if abs(w / h - src_im.size[0] / src_im.size[1]) < 0.02:
            sourced.append(cid)
    check("the stage draws matte bodies (no opaque crop edge)",
          len(no_edge) == len(ids), f"{len(no_edge)}/{len(ids)}")
    check("the drawn proportions match the matte files",
          len(sourced) == len(ids), f"{len(sourced)}/{len(ids)}")

    check("an unknown id has no body", eternal_sill.body_png("not-an-heir") is None)
    check("an unknown id falls back to nothing", eternal_sill.matte_path("mem") is None)
    saved = eternal_sill.MATTE_DIR
    try:
        eternal_sill.MATTE_DIR = ROOT / "world_runtime" / "_no_such_matte"
        eternal_sill.matte_path.cache_clear() if hasattr(
            eternal_sill.matte_path, "cache_clear") else None
        eternal_sill.body_png.cache_clear()
        check("a missing matte folder disables the pass",
              not eternal_sill.has_body("cyrene") and eternal_sill.body_png("cyrene") is None)
    finally:
        eternal_sill.MATTE_DIR = saved
        eternal_sill.body_png.cache_clear()

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
