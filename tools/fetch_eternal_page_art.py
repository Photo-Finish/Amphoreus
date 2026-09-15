# -*- coding: utf-8 -*-
"""Download official cute PPG stickers for An Eternal Page.

Uses the Wikia CDN (hashed paths). Fandom HTML/API often times out;
static.wikia.nocookie.net does not. WebP responses are converted to PNG.

    python tools/fetch_eternal_page_art.py
"""
from __future__ import annotations

import hashlib
import io
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

STICKERS: dict[str, list[str]] = {
    "aglaea": ["Sticker_PPG_20_Aglaea_01.png"],
    "anaxa": ["Sticker_PPG_22_Anaxa_01.png"],
    "castorice": ["Sticker_PPG_22_Castorice_01.png", "Sticker_PPG_21_Castorice_01.png"],
    "cerydra": [f"Sticker_PPG_{n}_Cerydra_01.png" for n in range(20, 27)],
    "cipher": ["Sticker_PPG_22_Cipher_01.png"],
    "cyrene": [f"Sticker_PPG_{n}_Cyrene_01.png" for n in range(20, 27)],
    "dan-heng-permansor-terrae": [
        "Sticker_PPG_24_Dan_Heng_•_Permansor_Terrae_01.png",
        "Sticker_PPG_24_Dan_Heng_Permansor_Terrae_01.png",
        "Sticker_PPG_25_Dan_Heng_•_Permansor_Terrae_01.png",
        "Sticker_PPG_23_Dan_Heng_•_Permansor_Terrae_01.png",
        "Sticker_PPG_18_Dan_Heng_01.png",
        "Sticker_PPG_02_Dan_Heng_01.png",
    ],
    "evernight": [
        *[f"Sticker_PPG_{n}_Evernight_01.png" for n in range(20, 27)],
        "Sticker_PPG_16_March_7th_01.png",
    ],
    "hyacine": ["Sticker_PPG_22_Hyacine_01.png"],
    "hysilens": [f"Sticker_PPG_{n}_Hysilens_01.png" for n in range(20, 27)],
    "mydei": ["Sticker_PPG_21_Mydei_01.png"],
    "phainon": ["Sticker_PPG_21_Phainon_01.png"],
    "tribbie": ["Sticker_PPG_21_Tribbie_01.png"],
}

SPLASH = {
    "aglaea": "Character_Aglaea_Splash_Art.png",
    "anaxa": "Character_Anaxa_Splash_Art.png",
    "castorice": "Character_Castorice_Splash_Art.png",
    "cerydra": "Character_Cerydra_Splash_Art.png",
    "cipher": "Character_Cipher_Splash_Art.png",
    "cyrene": "Character_Cyrene_Splash_Art.png",
    "dan-heng-permansor-terrae": "Character_Dan_Heng_•_Permansor_Terrae_Splash_Art.png",
    "evernight": "Character_Evernight_Splash_Art.png",
    "hyacine": "Character_Hyacine_Splash_Art.png",
    "hysilens": "Character_Hysilens_Splash_Art.png",
    "mydei": "Character_Mydei_Splash_Art.png",
    "phainon": "Character_Phainon_Splash_Art.png",
    "tribbie": "Character_Tribbie_Splash_Art.png",
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
            print(f"  skip small {len(data)} {url[-60:]}")
            return None
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return data
        if data[:4] == b"RIFF" or data[:4] == b"\xff\xd8\xff" or "image" in ctype:
            return data
        print(f"  skip not image {ctype} {url[-60:]}")
    except Exception as exc:
        print(f"  miss {type(exc).__name__} {url[-70:]}")
    return None


def to_png(data: bytes) -> bytes | None:
    try:
        im = Image.open(io.BytesIO(data))
        im = im.convert("RGBA")
        if im.width < 64 or im.height < 64:
            return None
        # Stickers are already chibi; splash art is tall — keep as-is.
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as exc:
        print(f"  decode fail: {exc}")
        return None


def save_cid(cid: str, names: list[str]) -> bool:
    dest = OUT / f"{cid}.png"
    if dest.is_file() and dest.stat().st_size > 8000:
        try:
            Image.open(dest).verify()
            print(f"  have {dest.name} ({dest.stat().st_size})")
            return True
        except Exception:
            pass
    for name in names:
        url = cdn_url(name)
        raw = fetch(url)
        if not raw:
            continue
        png = to_png(raw)
        if not png:
            continue
        dest.write_bytes(png)
        print(f"  ok  {dest.name}  {len(png)}  <- {name}")
        return True
    return False


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    missing = []
    for cid, names in STICKERS.items():
        print(f"-- {cid} --")
        extra = [SPLASH.get(cid)] if SPLASH.get(cid) else []
        if not save_cid(cid, names + extra):
            missing.append(cid)
    print("missing:", ", ".join(missing) or "(none)")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
