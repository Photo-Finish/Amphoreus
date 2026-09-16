# -*- coding: utf-8 -*-
"""Collect official Cyrene cycle-form art into assets/eternal_page/cyrene_forms/.

Sources: Pom-Pom Gallery / wiki CDN (same hasher as fetch_eternal_page_art.py)
and local copies of special-program announcement stills. Does not write to
q_program/crops, q_program/cutouts, or cute/.

    python tools/fetch_cyrene_forms.py
"""
from __future__ import annotations

import hashlib
import io
import shutil
import ssl
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "eternal_page" / "cyrene_forms"
ANN = ROOT / "assets" / "eternal_page" / "q_program" / "announcement"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
WIKI = "houkai-star-rail"
WIKI_FILE = "https://honkai-star-rail.fandom.com/wiki/File:{name}"

# dest relative to OUT -> wiki filename
CDN_FILES: list[tuple[str, str]] = [
    # Demiurge / playable Q + catalog
    ("demiurge/ppg24_01_heart.png", "Sticker_PPG_24_Cyrene_01.png"),
    ("demiurge/ppg24_02_look.png", "Sticker_PPG_24_Cyrene_02.png"),
    ("demiurge/ppg24_03_wink.png", "Sticker_PPG_24_Cyrene_03.png"),
    ("demiurge/ppg24_04_orb.png", "Sticker_PPG_24_Cyrene_04.png"),
    ("demiurge/icon.png", "Character_Cyrene_Icon.png"),
    ("demiurge/portrait.png", "Character_Cyrene_Portrait.png"),
    ("demiurge/splash_catalog.png", "Character_Cyrene_Splash_Art.png"),
    ("demiurge/introduction.png", "Character_Cyrene_Introduction.png"),
    ("demiurge/light_cone_icon.png", "Light_Cone_This_Love,_Forever.png"),
    ("demiurge/light_cone_artwork.png", "Light_Cone_This_Love,_Forever_Artwork.png"),
    ("demiurge/eidolon_1.png", "Character_Cyrene_Eidolon_1.png"),
    ("demiurge/eidolon_2.png", "Character_Cyrene_Eidolon_2.png"),
    ("demiurge/eidolon_3.png", "Character_Cyrene_Eidolon_3.png"),
    ("demiurge/eidolon_4.png", "Character_Cyrene_Eidolon_4.png"),
    ("demiurge/eidolon_5.png", "Character_Cyrene_Eidolon_5.png"),
    ("demiurge/eidolon_6.png", "Character_Cyrene_Eidolon_6.png"),
    # Childhood / tiny (PPG 05 is the navy-dress Q; NPC icon is story model)
    ("childhood/ppg24_05_wink.png", "Sticker_PPG_24_Cyrene_05.png"),
    ("childhood/npc_icon.png", "NPC_Cyrene_Icon.png"),
    # Mem
    ("mem/ppg21_01_heart.png", "Sticker_PPG_21_Mem_01.png"),
    ("mem/ppg21_02_allow_me.png", "Sticker_PPG_21_Mem_02.png"),
    ("mem/ppg21_03_hugs.png", "Sticker_PPG_21_Mem_03.png"),
    ("mem/ppg23_01_cry.png", "Sticker_PPG_23_Mem_01.png"),
    ("mem/ppg23_02_swim.png", "Sticker_PPG_23_Mem_02.png"),
    ("mem/ppg23_03_sleep.png", "Sticker_PPG_23_Mem_03.png"),
    ("mem/npc.png", "NPC_Mem.png"),
    ("mem/npc_icon.png", "NPC_Mem_Icon.png"),
    ("mem/npc_artwork.png", "NPC_Mem_Artwork.png"),
    ("mem/profile_picture.png", "Profile_Picture_Mem.png"),
]


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


def fetch(url: str, timeout: int = 20) -> tuple[bytes | None, int | None, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "image/png,image/webp,image/*,*/*"},
    )
    try:
        with urllib.request.urlopen(req, context=_ctx(), timeout=timeout) as resp:
            data = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
            return data, resp.status, ctype
    except urllib.error.HTTPError as e:
        return None, e.code, ""
    except Exception:
        return None, None, ""


def to_png(data: bytes) -> bytes | None:
    try:
        im = Image.open(io.BytesIO(data))
        im = im.convert("RGBA")
        if im.width < 32 or im.height < 32:
            return None
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception:
        return None


def save_png(dest: Path, data: bytes) -> bool:
    png = to_png(data)
    if not png:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(png)
    return True


def download_named(rel: str, filename: str) -> dict:
    dest = OUT / rel
    url = cdn_url(filename)
    raw, status, ctype = fetch(url)
    rec = {
        "file": rel.replace("\\", "/"),
        "wiki_file": filename,
        "url": url,
        "wiki_page": WIKI_FILE.format(name=filename),
        "http": status,
        "ok": False,
        "px": None,
    }
    if status != 200 or not raw or len(raw) < 2000:
        print(f"  miss {rel}  HTTP {status}  <- {filename}")
        return rec
    if not save_png(dest, raw):
        print(f"  bad  {rel}  <- {filename}")
        return rec
    im = Image.open(dest)
    rec["ok"] = True
    rec["px"] = f"{im.width}x{im.height}"
    rec["bytes"] = dest.stat().st_size
    print(f"  ok   {rel}  {rec['px']}  {rec['bytes']}  <- {filename}")
    return rec


def copy_announcements() -> list[str]:
    dest_dir = OUT / "_source_announcement"
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in [
        "Version_3.0_Special_Program_Announcement.png",
        "Version_3.4_Special_Program_Announcement.png",
        "Version_3.7_Special_Program_Announcement.png",
    ]:
        src = ANN / name
        if not src.is_file():
            print(f"  missing announcement {name}")
            continue
        dest = dest_dir / name
        shutil.copy2(src, dest)
        copied.append(name)
        print(f"  copy announcement {name}")
    return copied


def crop_box(src: Path, dest: Path, box: tuple[int, int, int, int]) -> dict:
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    l, t, r, b = box
    l, t = max(0, l), max(0, t)
    r, b = min(w, r), min(h, b)
    crop = im.crop((l, t, r, b))
    dest.parent.mkdir(parents=True, exist_ok=True)
    crop.save(dest, "PNG", optimize=True)
    rec = {
        "file": str(dest.relative_to(OUT)).replace("\\", "/"),
        "source": src.name,
        "box": [l, t, r, b],
        "px": f"{crop.width}x{crop.height}",
        "ok": True,
    }
    print(f"  crop {rec['file']}  {rec['px']}  from {src.name} {rec['box']}")
    return rec


def local_crops() -> list[dict]:
    """Crops keep Mem / childhood figures whole. Does not write q_program/."""
    out = []
    a34 = OUT / "_source_announcement" / "Version_3.4_Special_Program_Announcement.png"
    a37 = OUT / "_source_announcement" / "Version_3.7_Special_Program_Announcement.png"
    splash = OUT / "demiurge" / "splash_catalog.png"
    intro = OUT / "demiurge" / "introduction.png"
    if a34.is_file():
        # 3.4 only draws Mem as a bust-in-frame. Keep both wings + brooch.
        out.append(crop_box(a34, OUT / "mem" / "q_v34_portrait_whole.png", (25, 175, 400, 545)))
    if a37.is_file():
        out.append(crop_box(a37, OUT / "mem" / "q_v37_tv_scene.png", (1080, 160, 1720, 920)))
        # Sitting pixel Mem including tail and both wings.
        out.append(crop_box(a37, OUT / "mem" / "q_v37_pixel_mem_whole.png", (1268, 338, 1510, 612)))
    if splash.is_file():
        out.append(crop_box(splash, OUT / "childhood" / "splash_ghost_whole.png", (430, 880, 920, 1450)))
        out.append(crop_box(splash, OUT / "mem" / "splash_ghost_whole.png", (1160, 820, 1520, 1280)))
    if intro.is_file():
        out.append(crop_box(intro, OUT / "childhood" / "introduction_ghost_whole.png", (430, 300, 820, 820)))
        out.append(crop_box(intro, OUT / "mem" / "introduction_ghost_whole.png", (1080, 300, 1380, 720)))
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "demiurge").mkdir(exist_ok=True)
    (OUT / "childhood").mkdir(exist_ok=True)
    (OUT / "mem").mkdir(exist_ok=True)

    print("-- wiki CDN --")
    records = []
    for rel, filename in CDN_FILES:
        records.append(download_named(rel, filename))
        time.sleep(0.08)

    print("-- local announcement copies/crops --")
    copied = copy_announcements()
    crops = local_crops()

    ok_n = sum(1 for r in records if r["ok"])
    print(f"done cdn {ok_n}/{len(records)} crops {len(crops)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
