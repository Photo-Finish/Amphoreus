# -*- coding: utf-8 -*-
"""Download official cute PPG stickers (all emotion poses) for An Eternal Page.

Uses the Wikia CDN (hashed paths). WebP responses are converted to PNG.

    python tools/fetch_eternal_page_art.py
"""
from __future__ import annotations

import hashlib
import io
import shutil
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "eternal_page" / "cute"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
WIKI = "houkai-star-rail"

# Known Pom-Pom Gallery packs per Heir. Variants are probed 01–08.
PPG_PACKS: dict[str, list[str]] = {
    "aglaea": ["Sticker_PPG_20_Aglaea_{nn}.png"],
    "anaxa": ["Sticker_PPG_22_Anaxa_{nn}.png"],
    "castorice": [
        "Sticker_PPG_22_Castorice_{nn}.png",
        "Sticker_PPG_21_Castorice_{nn}.png",
    ],
    "cerydra": ["Sticker_PPG_23_Cerydra_{nn}.png"],
    "cipher": ["Sticker_PPG_22_Cipher_{nn}.png"],
    "cyrene": ["Sticker_PPG_24_Cyrene_{nn}.png"],
    "dan-heng-permansor-terrae": [
        "Sticker_PPG_24_Dan_Heng_•_Permansor_Terrae_{nn}.png",
        "Sticker_PPG_24_Dan_Heng_Permansor_Terrae_{nn}.png",
    ],
    "evernight": ["Sticker_PPG_24_Evernight_{nn}.png"],
    "hyacine": ["Sticker_PPG_22_Hyacine_{nn}.png"],
    "hysilens": ["Sticker_PPG_23_Hysilens_{nn}.png"],
    "mydei": ["Sticker_PPG_21_Mydei_{nn}.png"],
    "phainon": ["Sticker_PPG_21_Phainon_{nn}.png"],
    "tribbie": ["Sticker_PPG_21_Tribbie_{nn}.png"],
}

# Official files that do not share the main pack's 01–N numbering.
# Trianne/Trinnon are extra PPG 21 stickers (not Tribbie_03/_04).
# Castorice PPG 21 is a fifth pose beside PPG 22 01–04.
PPG_EXTRAS: dict[str, dict[str, str]] = {
    "tribbie": {
        "03": "Sticker_PPG_21_Trianne_01.png",
        "04": "Sticker_PPG_21_Trinnon_01.png",
    },
    "castorice": {
        "05": "Sticker_PPG_21_Castorice_01.png",
    },
    # Pack 23 is a second Phainon set; do not number it 01–04 or it
    # overwrites PPG 21's weary/sleepy 01.
    "phainon": {
        "02": "Sticker_PPG_23_Phainon_01.png",
        "03": "Sticker_PPG_23_Phainon_02.png",
        "04": "Sticker_PPG_23_Phainon_03.png",
        "05": "Sticker_PPG_23_Phainon_04.png",
    },
}


def _ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def cdn_url(filename: str) -> str:
    name = filename.replace(" ", "_")
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    quoted = urllib.parse.quote(name, safe="._-~•")
    return (
        f"https://static.wikia.nocookie.net/{WIKI}/images/"
        f"{digest[0]}/{digest[:2]}/{quoted}/revision/latest"
    )


def fetch(url: str, timeout: int = 12) -> bytes | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "image/png,image/webp,image/*,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, context=_ctx(), timeout=timeout) as resp:
            data = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
        if len(data) < 4000:
            return None
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return data
        if data[:4] == b"RIFF" or data[:4] == b"\xff\xd8\xff" or "image" in ctype:
            return data
    except Exception:
        return None
    return None


def to_png(data: bytes) -> bytes | None:
    try:
        im = Image.open(io.BytesIO(data))
        im = im.convert("RGBA")
        if im.width < 64 or im.height < 64:
            return None
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception:
        return None


def _have(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 8000:
        return False
    try:
        Image.open(path).verify()
        return True
    except Exception:
        return False


def save_variant(cid: str, nn: str, templates: list[str]) -> bool:
    folder = OUT / cid
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{nn}.png"
    if _have(dest):
        print(f"  have {cid}/{nn}.png")
        return True
    for tmpl in templates:
        name = tmpl.format(nn=nn)
        raw = fetch(cdn_url(name))
        if not raw:
            continue
        png = to_png(raw)
        if not png:
            continue
        dest.write_bytes(png)
        print(f"  ok  {cid}/{nn}.png  {len(png)}  <- {name}")
        return True
    return False


def save_named(cid: str, nn: str, filename: str) -> bool:
    folder = OUT / cid
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{nn}.png"
    if _have(dest):
        print(f"  have {cid}/{nn}.png")
        return True
    raw = fetch(cdn_url(filename))
    if not raw:
        return False
    png = to_png(raw)
    if not png:
        return False
    dest.write_bytes(png)
    print(f"  ok  {cid}/{nn}.png  {len(png)}  <- {filename}")
    return True


def sync_default(cid: str) -> None:
    """Keep `{cid}.png` as the calm/default pose (variant 01)."""
    variant = OUT / cid / "01.png"
    default = OUT / f"{cid}.png"
    if _have(default) and not _have(variant):
        variant.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(default, variant)
        print(f"  copy {default.name} -> {cid}/01.png")
    elif _have(variant) and not _have(default):
        shutil.copy2(variant, default)
        print(f"  copy {cid}/01.png -> {default.name}")
    elif _have(variant) and _have(default):
        if variant.stat().st_size != default.stat().st_size:
            shutil.copy2(variant, default)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    missing = []
    for cid, templates in PPG_PACKS.items():
        print(f"-- {cid} --")
        sync_default(cid)
        got_any = False
        consecutive_miss = 0
        for i in range(1, 9):
            nn = f"{i:02d}"
            if save_variant(cid, nn, templates):
                got_any = True
                consecutive_miss = 0
            else:
                consecutive_miss += 1
                if i >= 2 and consecutive_miss >= 2:
                    break
        for nn, filename in PPG_EXTRAS.get(cid, {}).items():
            if save_named(cid, nn, filename):
                got_any = True
        sync_default(cid)
        if not got_any and not _have(OUT / f"{cid}.png"):
            missing.append(cid)
    print("missing:", ", ".join(missing) or "(none)")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
