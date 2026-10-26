# -*- coding: utf-8 -*-
"""Audit duplicate art in `assets/` — read-only.

    python tools/audit_asset_duplicates.py
    python tools/audit_asset_duplicates.py --json

Reports byte-identical images (same content, different name or folder) and the
bytes a dedupe would reclaim. It never deletes or moves anything: the art tree
is the project's master copy, and removing a master is the operator's call.

The same art often arrives twice — once as a name-addressed sprite the page uses
(`cute/cyrene/02.png`) and once inside a research catalog
(`cyrene_forms/demiurge/ppg24_02_look.png`).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
SKIP_DIRS = {"__pycache__", ".git"}


def image_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if SKIP_DIRS & set(path.parts):
            continue
        files.append(path)
    return sorted(files)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def audit(root: Path) -> dict:
    files = image_files(root)
    by_hash: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        try:
            by_hash[digest(path)].append(path)
        except OSError:
            continue
    groups = []
    for sha, paths in by_hash.items():
        if len(paths) < 2:
            continue
        size = paths[0].stat().st_size
        groups.append(
            {
                "sha256": sha,
                "bytes": size,
                "files": [str(p.relative_to(root)) for p in sorted(paths)],
                "reclaimable": size * (len(paths) - 1),
            }
        )
    groups.sort(key=lambda g: -g["reclaimable"])
    total_bytes = sum(p.stat().st_size for p in files if p.exists())
    return {
        "root": str(root),
        "images": len(files),
        "bytes": total_bytes,
        "groups": groups,
        "reclaimable": sum(g["reclaimable"] for g in groups),
        "unique_bytes": total_bytes - sum(g["reclaimable"] for g in groups),
    }


def main(argv: list[str]) -> int:
    result = audit(ROOT / "assets")
    if "--json" in argv:
        print(json.dumps(result, indent=2))
        return 0

    print(f"asset tree         {result['images']} images, {result['bytes'] / 1048576:.2f} MB")
    print(f"duplicate groups   {len(result['groups'])}")
    print(f"reclaimable        {result['reclaimable'] / 1048576:.2f} MB "
          f"({100 * result['reclaimable'] / max(result['bytes'], 1):.1f}% of the tree)")
    print(f"unique content     {result['unique_bytes'] / 1048576:.2f} MB")
    if not result["groups"]:
        return 0
    print()
    print("largest groups (kept copy first, duplicates after):")
    for group in result["groups"][:12]:
        print(f"  {group['bytes'] / 1024:8.1f} KB x{len(group['files'])}"
              f"  reclaim {group['reclaimable'] / 1024:8.1f} KB")
        for name in group["files"]:
            print(f"        {name}")
    if len(result["groups"]) > 12:
        print(f"  … {len(result['groups']) - 12} more groups (use --json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
