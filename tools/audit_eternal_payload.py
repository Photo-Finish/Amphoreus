# -*- coding: utf-8 -*-
"""Audit the Eternal Page art payload.

The stage inlines every companion (and the parchment) as a data URI inside one
iframe document, so this is the string Streamlit hands the browser on every
rerun. This tool measures it the same way `render_eternal_page` builds it and
reports what the WebP cache saves.

    python tools/audit_eternal_payload.py
    python tools/audit_eternal_payload.py --json

Read-only: it never writes to assets/, and the derived cache lives in the
gitignored `world_runtime/_art_cache/`. Compare a run with
`$env:AMP_ART_CACHE='off'` to see the plain PNG path.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.world import art_cache  # noqa: E402
from src.world import eternal_page as ep  # noqa: E402


def build_stage_art() -> tuple[dict, int, int]:
    """(uri map, source bytes, uri bytes) for the thirteen and the page.

    Built through the same `stage_art_uris` the page calls, so this audit cannot
    drift from what actually reaches the browser — including the second-pass
    matte, when `cutouts_matte/` exists.
    """
    from src.ui_eternal_page import stage_art_uris
    from src.world import eternal_sill
    from src.world.eternal_q import source_path

    art = stage_art_uris({})
    png_bytes = 0
    for cid in ep.all_ids():
        if cid not in art:
            continue
        cleaner = eternal_sill.matte_path(cid)
        source = cleaner if cleaner is not None else source_path(cid)
        if source is not None:
            png_bytes += source.stat().st_size
        face = ep.cute_art(cid, "calm")
        if face is not None:
            png_bytes += face.stat().st_size
    parchment = ep.parchment_path()
    parchment_uri = ""
    if parchment:
        from src.ui_eternal_page import _data_uri

        png_bytes += parchment.stat().st_size
        parchment_uri = _data_uri(parchment, max_px=art_cache.PARCHMENT_MAX_PX)
    uri_bytes = sum(len(v["body"]) + len(v["face"]) for v in art.values()) + len(parchment_uri)
    return art, png_bytes, uri_bytes


def measure() -> dict:
    art_cache.reset()
    t0 = time.perf_counter()
    build_stage_art()  # cold: encodes + writes the disk cache
    cold = time.perf_counter() - t0

    t0 = time.perf_counter()
    _art, png_bytes, uri_bytes = build_stage_art()  # warm: memory hits
    warm = time.perf_counter() - t0

    return {
        "cache": art_cache.stats(),
        "sprites": len(_art),
        "png_bytes": png_bytes,
        "uri_bytes": uri_bytes,
        "mdhtml_bytes": uri_bytes + len(_art) * 120,
        "cold_seconds": round(cold, 3),
        "warm_seconds": round(warm, 4),
        "cache_dir": str(art_cache.cache_dir()),
        "disk_files": len(list(art_cache.cache_dir().glob("*.webp")))
        if art_cache.cache_dir().is_dir() else 0,
    }


def main(argv: list[str]) -> int:
    rows = measure()
    if "--json" in argv:
        print(json.dumps(rows, indent=2))
        return 0

    cache = rows["cache"]
    print("Eternal Page art payload")
    print(f"  sprites            {rows['sprites']}")
    print(f"  cache              {'on' if cache['enabled'] else 'off'} "
          f"(quality {cache['quality']}, {rows['disk_files']} webp on disk)")
    print(f"  png masters        {rows['png_bytes'] / 1024:9.1f} KB")
    print(f"  inlined data URIs  {rows['uri_bytes'] / 1024:9.1f} KB  "
          f"({100 * rows['uri_bytes'] / max(rows['png_bytes'], 1):5.1f}% of PNG)")
    print(f"  stage markup       {rows['mdhtml_bytes'] / 1024:9.1f} KB  (URIs + img tags)")
    print(f"  cold build         {rows['cold_seconds']:9.3f} s  (encode + disk write)")
    print(f"  warm build         {rows['warm_seconds']:9.4f} s  (memory hits)")
    print(f"  cache dir          {rows['cache_dir']}")
    if cache["enabled"]:
        print(f"  saved              "
              f"{(rows['png_bytes'] - rows['uri_bytes']) / 1024:9.1f} KB per rerun")
    else:
        print("  note               AMP_ART_CACHE is off — plain PNG data URIs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
