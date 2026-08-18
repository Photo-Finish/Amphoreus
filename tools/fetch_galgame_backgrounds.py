"""
fetch_galgame_backgrounds.py — download Amphoreus AREA background artwork from
the English HSR wiki (honkai-star-rail.fandom.com) to decorate the Galgame UI.

The Amphoreus page carries the in-game area art as `Area_*.png` files (e.g.
Area_"Eternal_Holy_City"_Okhema.png). Those files are cinematic establishing
shots (sky / titan / tree-face). The wiki has no separate street-level plaza
files (Marmoreal Market, Kephale Plaza, etc. are Space Anchor icons only).
This tool saves the establishing JPEGs in `assets/galgame/bg-<slug>.jpg`.
Visit / Walk then crop them onto pavement via `src/ui_ground.py`
(`assets/galgame/ground/`).

NETWORK RECIPE (same as fetch_wiki_amphoreus.py): fandom + the image CDN are
DNS-poisoned and firewalled; works via the iKuuu proxy (127.0.0.1:12000) with
the real Cloudflare IPs pinned, retrying (the proxy is flaky). The CDN needs a
`?cb=` cache-buster.

USAGE:
    python tools/fetch_galgame_backgrounds.py [--slug okhema,kremnos]
"""

import argparse
import io
import json
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "galgame"

import urllib3.util.connection as _uc  # noqa: E402
import requests  # noqa: E402

PROXY = "http://127.0.0.1:12000"
REAL = {
    "honkai-star-rail.fandom.com": "162.159.142.170",
    "static.wikia.nocookie.net": "162.159.142.170",
    "vignette.wikia.nocookie.net": "162.159.142.170",
}
_orig_create = _uc.create_connection


def _pin(address, *a, **kw):
    host, port = address
    if host in REAL:
        address = (REAL[host], port)
    return _orig_create(address, *a, **kw)


_uc.create_connection = _pin

SESSION = requests.Session()
SESSION.proxies = {"https": PROXY, "http": PROXY}
SESSION.headers["User-Agent"] = "Mozilla/5.0 (Amphoreus bg fetch)"


def _try_direct_session():
    """Fall back to a no-proxy session when the local proxy is down."""
    s = requests.Session()
    s.proxies = {"https": "", "http": ""}
    s.headers["User-Agent"] = "Mozilla/5.0 (Amphoreus bg fetch)"
    return s


def api(params, tries=6, timeout=45):
    global SESSION
    last = None
    for i in range(tries):
        try:
            r = SESSION.get("https://honkai-star-rail.fandom.com/api.php",
                            params=params, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = RuntimeError(f"HTTP {r.status_code}")
        except Exception as e:  # noqa: BLE001
            last = e
            if i == 1 and ("ProxyError" in type(e).__name__ or "10061" in str(e)):
                print("  (proxy down — trying direct)")
                SESSION = _try_direct_session()
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"API failed: {last}")


def get(url, tries=6, timeout=120):
    last = None
    for i in range(tries):
        try:
            r = SESSION.get(url, timeout=timeout)
            if r.status_code == 200 and len(r.content) > 5000:
                return r.content
            last = RuntimeError(f"HTTP {r.status_code} len={len(r.content) if 'content' in dir(r) else '?'}")
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"download failed: {last}")


# Curated backgrounds: slug -> substring of the Area_* filename on the wiki.
TARGETS = {
    "okhema": "Area_\"Eternal_Holy_City\"_Okhema",
    "okhema-evernight": "Area_\"Fallen_Twilight_City\"_Okhema",
    "janusopolis": "Area_\"Sanctum_of_Prophecy\"_Janusopolis",
    "abyss-of-fate": "Area_\"Abyss_of_Fate\"_Janusopolis",
    "grove": "Area_\"Radiant_Scarwood\"_Grove_of_Epiphany",
    "murmuring-woods": "Area_\"Murmuring_Woods\"_Grove_of_Epiphany",
    "kremnos": "Area_\"Bloodbathed_Battlefront\"_Castrum_Kremnos",
    "kremnos-ruins": "Area_\"Strife_Ruins\"_Castrum_Kremnos",
    "styxia": "Area_\"Warbling_Shores\"_Styxia",
    "dragonbone-city": "Area_\"Dragonbone_City\"_Styxia",
    "aedes-elysiae": "Area_Aedes_Elysiae",
    "dawncloud": "Area_\"Demigod_Council\"_Dawncloud",
    "lightless-chapel": "Area_\"Lightless_Chapel\"_Dawncloud",
    "eye-of-twilight": "Area_\"Fortress_of_Dome\"_Eye_of_Twilight",
    "cloudedge-bastion": "Area_\"Cloudedge_Bastion_Ruins\"_Eye_of_Twilight",
    "great-tomb": "Area_\"Universal_Matrix\"_Great_Tomb_of_the_Nameless_Titan",
    "nightmare-echo": "Area_\"Nightmare",
    "memortis-shore": "Area_\"Memortis_Shore\"_Ruins_of_Time",
    "vortex-of-genesis": "Area_Vortex_of_Genesis",
    "beyond-time": "Area_Beyond_Time_An_Eternal_Page",
}


def area_images():
    """All Area_* image titles from the Amphoreus + Aedes Elysiae pages.
    (formatversion=2 returns image titles WITHOUT the File: prefix.)"""
    imgs = []
    for page in ("Amphoreus", "Aedes Elysiae"):
        d = api({"action": "parse", "page": page, "prop": "images",
                 "format": "json", "formatversion": "2"})
        for i in d["parse"]["images"]:
            name = i[5:] if i.lower().startswith("file:") else i
            if name.lower().startswith("area") or name.lower().startswith("map_"):
                imgs.append(name)
    return imgs


def pick(imgs, needle):
    """Return the File: title whose name contains needle (case-insensitive)."""
    n = needle.lower()
    for i in imgs:
        if n in i.lower():
            return i
    return None


def thumb_url(filename, width=1920):
    if not filename.lower().startswith("file:"):
        filename = "File:" + filename
    d = api({"action": "query", "titles": filename, "prop": "imageinfo",
             "iiprop": "url", "iiurlwidth": int(width), "format": "json",
             "formatversion": "2"})
    for p in d["query"]["pages"]:
        info = p.get("imageinfo", [{}])[0]
        if info.get("thumburl"):
            return info["thumburl"]
        if info.get("url"):
            return info["url"]
    return None


def save_jpg(raw, dest, max_px=1920):
    from PIL import Image
    img = Image.open(io.BytesIO(raw))
    if img.width > max_px:
        h = int(img.height * max_px / img.width)
        img = img.resize((max_px, h), Image.LANCZOS)
    img = img.convert("RGB")
    img.save(dest, "JPEG", quality=92)
    return dest


def main():
    ap = argparse.ArgumentParser(description="Fetch Amphoreus area backgrounds for the Galgame UI.")
    ap.add_argument("--slug", default="", help="comma-separated subset of slugs")
    ap.add_argument("--force", action="store_true",
                    help="re-download even if the file already exists")
    ap.add_argument("--width", type=int, default=1920,
                    help="wiki thumbnail width / max JPEG edge (default 1920)")
    args = ap.parse_args()

    wanted = {s.strip() for s in args.slug.split(",") if s.strip()} if args.slug else None

    print("listing Area_* images from the wiki...")
    imgs = area_images()
    print(f"  {len(imgs)} area/map images")

    OUT.mkdir(parents=True, exist_ok=True)
    ok, fail = 0, []
    for slug, needle in TARGETS.items():
        if wanted and slug not in wanted:
            continue
        dest = OUT / f"bg-{slug}.jpg"
        if dest.exists() and not args.force:
            print(f"  = {slug} (exists)")
            continue
        fn = pick(imgs, needle)
        if not fn:
            print(f"  ✗ {slug}: no image matched '{needle}'")
            fail.append(slug)
            continue
        try:
            url = thumb_url(fn, width=args.width)
            if not url:
                print(f"  ✗ {slug}: no thumburl")
                fail.append(slug)
                continue
            sep = "&" if "?" in url else "?"
            raw = get(f"{url}{sep}cb=20260818230000")
            save_jpg(raw, dest, max_px=args.width)
            try:
                from src.ui_ground import write_ground_jpeg
                write_ground_jpeg(dest)
            except Exception as e:  # noqa: BLE001
                print(f"  (ground crop skipped: {e})")
            print(f"  ✓ {slug} -> {dest.name} ({len(raw)//1024} KB)")
            ok += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {slug}: {e}")
            fail.append(slug)
        time.sleep(0.5)

    print(f"\nDone: {ok} downloaded, {len(fail)} failed: {', '.join(fail) or 'none'}")


if __name__ == "__main__":
    main()
