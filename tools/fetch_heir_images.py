"""
fetch_heir_images.py — download Chrysos Heir portraits + Amphoreus background
for the visual UI.

Source: wiki.biligame.com/sr (reachable Chinese HSR wiki, MediaWiki API).
For each Heir: search the English name -> character page -> `parse.images`
(fast, lists the images used) -> pick the official portrait (立绘 / <name>.png)
-> resolve the CDN URL via `imageinfo` -> download into assets/heirs/<id>.<ext>
(resized <=512px). Also fetches the Amphoreus background (翁法罗斯-bg.jpg) as
the themed banner.

USAGE:
    python tools/fetch_heir_images.py [--heirs phainon,aglaea] [--size 512]
"""

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402

API = "https://wiki.biligame.com/sr/api.php"
UA = {"User-Agent": "Mozilla/5.0 (Amphoreus image fetch)"}
ASSETS = ROOT / "assets" / "heirs"

NAME_FALLBACKS = {
    "evernight": ["March 7th", "三月七", "Evernight"],
    "dan-heng-permansor-terrae": ["Dan Heng", "丹恒"],
    "cyrene": ["Cyrene", "昔涟"],
    "hyacine": ["Hyacine", "风堇"],
    "hysilens": ["Hysilens", "海瑟音"],
    "cerydra": ["Cerydra", "刻律德菈"],
    "cipher": ["Cipher", "赛飞儿"],
    "anaxa": ["Anaxa", "那刻夏"],
    "castorice": ["Castorice", "遐蝶"],
    "aglaea": ["Aglaea", "阿格莱雅"],
    "mydei": ["Mydei", "万敌"],
    "phainon": ["Phainon", "白厄"],
    "tribbie": ["Tribbie", "缇宝"],
}


def api(params: dict, timeout: int = 40):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def search_page(name: str):
    data = api({"action": "query", "list": "search", "srsearch": name,
                "srlimit": 5, "format": "json", "formatversion": "2"})
    hits = data.get("query", {}).get("search", [])
    if not hits:
        return None
    for h in hits:
        if h["title"].lower() == name.lower() or h["title"].startswith(name):
            return h["title"]
    return hits[0]["title"]


def page_images(title: str):
    data = api({"action": "parse", "page": title, "prop": "images",
                "format": "json", "formatversion": "2"})
    return data.get("parse", {}).get("images", [])


def pick_portrait(title: str, images):
    base = title
    pref = [f"{base}立绘.png", f"{base}立绘.jpg", f"{base}立绘.webp",
            f"{base}.png", f"{base}.jpg", f"{base}.webp"]
    for p in pref:
        for img in images:
            if img.replace("File:", "") == p:
                return img.replace("File:", "")
    for img in images:
        n = img.replace("File:", "")
        if n.startswith(base) and n.endswith((".png", ".jpg", ".jpeg", ".webp")):
            return n
    return None


def image_url(filename: str, width: int):
    data = api({"action": "query", "titles": f"File:{filename}",
                "prop": "imageinfo", "iiprop": "url", "iiurlwidth": width,
                "format": "json", "formatversion": "2"})
    for p in data.get("query", {}).get("pages", []):
        ii = p.get("imageinfo") or []
        if ii and ii[0].get("thumburl"):
            return ii[0]["thumburl"]
        if ii and ii[0].get("url"):
            return ii[0]["url"]
    return None


def download(url: str, dest: Path, max_px: int = 512):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(raw))
        img.thumbnail((max_px, max_px))
        ext = ".png" if img.mode in ("RGBA", "P") else ".jpg"
        dest = dest.with_suffix(ext)
        img.convert("RGB" if ext == ".jpg" else img.mode).save(dest)
        return dest
    except Exception:
        dest.write_bytes(raw)
        return dest


def main():
    ap = argparse.ArgumentParser(description="Fetch Heir portraits + Amphoreus background.")
    ap.add_argument("--heirs", default="")
    ap.add_argument("--size", type=int, default=512)
    args = ap.parse_args()

    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()] or list(HEIR_FOLDERS)
    ASSETS.mkdir(parents=True, exist_ok=True)

    names = {}
    for h in heir_ids:
        try:
            card = json.loads((ROOT / "src" / "characters" / f"{h}.json").read_text(encoding="utf-8"))
            names[h] = card["meta"]["name"]
        except Exception:
            names[h] = h

    for heir_id in heir_ids:
        title = None
        for c in [names[heir_id]] + NAME_FALLBACKS.get(heir_id, []):
            try:
                title = search_page(c)
                if title:
                    break
            except Exception:
                continue
            time.sleep(0.2)
        if not title:
            print(f"  {heir_id:>26}: NO PAGE")
            continue
        try:
            images = page_images(title)
            portrait = pick_portrait(title, images)
            if not portrait:
                print(f"  {heir_id:>26}: no portrait in {title} ({len(images)} imgs)")
                continue
            url = image_url(portrait, args.size)
            if not url:
                print(f"  {heir_id:>26}: no URL for {portrait}")
                continue
            dest = download(url, ASSETS / heir_id, args.size)
            print(f"  {heir_id:>26}: '{portrait}' -> {dest.relative_to(ROOT)} ({dest.stat().st_size//1024} KB)")
        except Exception as err:
            print(f"  {heir_id:>26}: failed: {err}")
        time.sleep(0.2)

    # Amphoreus background banner (for the themed UI)
    try:
        title = search_page("翁法罗斯") or "翁法罗斯"
        images = page_images(title)
        bg = None
        for img in images:
            n = img.replace("File:", "")
            if "bg" in n.lower() and n.endswith((".jpg", ".jpeg", ".png")):
                bg = n
                break
        if bg:
            url = image_url(bg, 1920)
            dest = download(url, ROOT / "assets" / "amphoreus_bg", 1920)
            print(f"  banner: '{bg}' -> {dest.relative_to(ROOT)} ({dest.stat().st_size//1024} KB)")
        else:
            print("  banner: no Amphoreus bg found")
    except Exception as err:
        print(f"  banner failed: {err}")

    print("\nDone.")


if __name__ == "__main__":
    main()
