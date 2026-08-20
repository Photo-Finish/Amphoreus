"""Build HSR-accurate chimera/dromas land sprites.

Front still PNGs for stationary display; side-profile *walk films* for roam.
Walk frames are distinct poses under assets/life_sprites/_hsr_src/walk/
(not bobbed copies of one still).

Dromas canon (HSR Okhema / 大地兽): cute soft earth-beast companion —
round blunt head, soft eyes, white petal ruff (not blade spikes), smooth
dusty periwinkle hide with almost no small squama, cream throat with only
a few large rounded plates, limb white shells. NOT a sharp photoreal
sauropod. Walk/pet sources under _hsr_src must match that soft silhouette;
packing also runs a residual tan→blue safeguard + cute smooth pass.

Rebuild:
  python tools/build_hsr_life_sprites.py              # chimera + dromas stills/walk
  python tools/build_hsr_life_sprites.py pet           # pet films (incl. dromas)
  python tools/build_hsr_life_sprites.py calf          # dromas_calf from adult
  python tools/build_hsr_life_sprites.py dromas        # dromas still+walk+pet+calf
"""
from __future__ import annotations

import colorsys
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "life_sprites" / "_hsr_src"
WALK = SRC / "walk"
PET = SRC / "pet"
OUT = ROOT / "assets" / "life_sprites"
CELL = 184

# HSR default Okhema coat — dusty periwinkle (degrees).
DROMAS_HIDE_HUE = 208.0

PROFILE_KINDS = ("chimera", "dromas")

STILL_SRC = {
    "chimera": SRC / "chimera_okhema.png",
    # Front still keyed from blue HSR-faithful source (not brown okhema drafts).
    "dromas": SRC / "dromas_front_still.png",
}


def _white_flood(im: Image.Image, white_min: int = 220, thresh: int = 28) -> Image.Image:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    vis = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def is_white(c) -> bool:
        return c[0] >= white_min and c[1] >= white_min and c[2] >= white_min

    def seed(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and not vis[y][x] and is_white(px[x, y]):
            vis[y][x] = True
            q.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)

    def near(a, b) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) <= thresh

    while q:
        x, y = q.popleft()
        c = px[x, y]
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (
                0 <= nx < w
                and 0 <= ny < h
                and not vis[ny][nx]
                and is_white(px[nx, ny])
                and near(c, px[nx, ny])
            ):
                vis[ny][nx] = True
                q.append((nx, ny))

    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        for x in range(w):
            md[x, y] = 0 if vis[y][x] else 255
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im.convert("RGBA"), mask=mask)
    return out


def _dark_flood(im: Image.Image, dark_max: int = 48, thresh: int = 36) -> Image.Image:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    vis = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def is_dark(c) -> bool:
        return c[0] <= dark_max and c[1] <= dark_max and c[2] <= dark_max

    def seed(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and not vis[y][x] and is_dark(px[x, y]):
            vis[y][x] = True
            q.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)

    def near(a, b) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) <= thresh

    while q:
        x, y = q.popleft()
        c = px[x, y]
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (
                0 <= nx < w
                and 0 <= ny < h
                and not vis[ny][nx]
                and is_dark(px[nx, ny])
                and near(c, px[nx, ny])
            ):
                vis[ny][nx] = True
                q.append((nx, ny))

    mask = Image.new("L", (w, h))
    md = mask.load()
    for y in range(h):
        for x in range(w):
            md[x, y] = 0 if vis[y][x] else 255
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im.convert("RGBA"), mask=mask)
    return out


def _drop_islands(im: Image.Image, keep_frac: float = 0.05) -> Image.Image:
    w, h = im.size
    px = im.load()
    vis = [[False] * w for _ in range(h)]
    blobs: list[list[tuple[int, int]]] = []
    for y in range(h):
        for x in range(w):
            if vis[y][x] or px[x, y][3] < 20:
                continue
            stack = [(x, y)]
            vis[y][x] = True
            blob: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                blob.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not vis[ny][nx] and px[nx, ny][3] >= 20:
                        vis[ny][nx] = True
                        stack.append((nx, ny))
            blobs.append(blob)
    if not blobs:
        return im
    keep = max(blobs, key=len)
    out = im.copy()
    opx = out.load()
    for blob in blobs:
        if blob is keep or len(blob) >= len(keep) * keep_frac:
            continue
        for x, y in blob:
            opx[x, y] = (0, 0, 0, 0)
    return out


def _trim(im: Image.Image, pad: int = 4) -> Image.Image:
    bbox = im.split()[-1].point(lambda p: 255 if p > 16 else 0).getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    return im.crop(
        (max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad))
    )


def _fit_cell(im: Image.Image, cell: int = CELL) -> Image.Image:
    im = _trim(im)
    canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    ratio = min((cell - 8) / im.width, (cell - 8) / im.height)
    nw, nh = max(1, int(im.width * ratio)), max(1, int(im.height * ratio))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas.paste(im, ((cell - nw) // 2, cell - nh - 2), im)
    return canvas


def _key(im: Image.Image) -> Image.Image:
    return _drop_islands(_white_flood(im))


def _recolor_dromas_hide(im: Image.Image, target_hue: float = DROMAS_HIDE_HUE) -> Image.Image:
    """Shift residual clay-tan hide to dusty periwinkle; keep plates & tack.

    Preserves cream/white throat plates + head ruff, brown leather, gold metal,
    orange cloth, purple tassels, and already-blue dorsal hide / eyes.
    """
    src = im.convert("RGBA")
    px = src.load()
    w, h = src.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 16:
                op[x, y] = (0, 0, 0, 0)
                continue
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            hh, ss, vv = colorsys.rgb_to_hsv(rf, gf, bf)
            hue = hh * 360.0
            # Cream / white plates & ruff (incl. soft beige shell patches).
            cream = vv > 0.58 and ss < 0.28 and (r + g + b) / 3 > 145 and r >= b - 8
            dark = vv < 0.16
            blueish = 165 <= hue <= 255 and ss > 0.06
            orange = (hue < 48 or hue > 348) and ss > 0.45 and vv > 0.38 and r > g + 12
            purple = 255 <= hue <= 335 and ss > 0.22
            gold = (
                32 <= hue <= 58
                and ss > 0.32
                and vv > 0.42
                and r > 135
                and g > 95
                and b < 130
            )
            leather = (
                8 <= hue <= 48
                and ss > 0.18
                and vv < 0.40
                and r > g >= b - 10
            )
            tan_hide = (
                not cream
                and not dark
                and not blueish
                and not orange
                and not purple
                and not gold
                and not leather
                and 5 <= hue <= 58
                and ss > 0.10
                and vv > 0.20
            )
            if tan_hide:
                new_s = min(0.40, max(0.16, ss * 0.70 + 0.10))
                new_v = min(0.92, vv * 0.98)
                nr, ng, nb = colorsys.hsv_to_rgb(target_hue / 360.0, new_s, new_v)
                op[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
            else:
                op[x, y] = (r, g, b, a)
    return out


def _cuteify_dromas(im: Image.Image) -> Image.Image:
    """Soften silhouette toward HSR cute 大地兽: smooth hide, rounder frills.

    Walk/pet art must not read as a sharp scaled sauropod. Soften blue-hide
    mottling, round cream frill tips, and slightly blur plate edges while
    keeping harness colors.
    """
    src = im.convert("RGBA")
    w, h = src.size
    px = src.load()
    # Masks: blue hide vs cream/white vs keep (tack).
    hide = Image.new("L", (w, h), 0)
    cream = Image.new("L", (w, h), 0)
    hp, cp = hide.load(), cream.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 16:
                continue
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            hh, ss, vv = colorsys.rgb_to_hsv(rf, gf, bf)
            hue = hh * 360.0
            is_cream = vv > 0.55 and ss < 0.30 and (r + g + b) / 3 > 140 and r >= b - 10
            is_blue = 165 <= hue <= 255 and ss > 0.05 and vv > 0.18 and not is_cream
            if is_blue:
                hp[x, y] = 255
            elif is_cream:
                cp[x, y] = 255
    # Smooth blue hide — kill small-scale mottling.
    smooth = src.filter(ImageFilter.MedianFilter(size=5)).filter(
        ImageFilter.GaussianBlur(radius=1.1)
    )
    out = src.copy()
    out.paste(smooth, mask=hide)
    # Soften / round cream frill and plate edges.
    cream_blur = out.filter(ImageFilter.GaussianBlur(radius=1.6))
    cream_m = cream.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    out.paste(cream_blur, mask=cream_m)
    # Light overall cel soften on opaque area.
    alpha = out.split()[-1]
    soft = out.filter(ImageFilter.SMOOTH_MORE)
    mixed = Image.blend(out.convert("RGBA"), soft.convert("RGBA"), 0.35)
    mixed.putalpha(alpha)
    return mixed


def _prepare_dromas(im: Image.Image) -> Image.Image:
    """HSR blue coat + light soft pass before keying (walk / pet / still)."""
    # Cute sources already carry round-head / smooth-hide silhouette; only a
    # light soften after the tan→blue safeguard so we do not mush good art.
    blue = _recolor_dromas_hide(im)
    return Image.blend(blue, _cuteify_dromas(blue), 0.45)


def _key_still(path: Path, *, dromas: bool = False) -> Image.Image:
    raw = Image.open(path)
    if dromas:
        raw = _prepare_dromas(raw)
    return _fit_cell(_key(raw))


def _key_walk_frame(path: Path, *, dromas: bool = False) -> Image.Image:
    """Key a generated walk pose; frames already face right for roam facing."""
    raw = Image.open(path)
    if dromas:
        raw = _prepare_dromas(raw)
    return _fit_cell(_key(raw))


def _film(frames: list[Image.Image], dest: Path) -> None:
    strip = Image.new("RGBA", (CELL * len(frames), CELL), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * CELL, 0), fr)
    strip.save(dest)
    print("wrote", dest.name, strip.size)


def _frame_diversity(frames: list[Image.Image]) -> list[float]:
    """Mean absolute RGB delta vs frame 0 (opaque pixels only)."""
    base = frames[0].convert("RGBA")
    bp = base.load()
    scores: list[float] = []
    for fr in frames[1:]:
        fp = fr.convert("RGBA").load()
        total = 0.0
        n = 0
        for y in range(CELL):
            for x in range(CELL):
                a0 = bp[x, y][3]
                a1 = fp[x, y][3]
                if a0 < 20 and a1 < 20:
                    continue
                n += 1
                total += sum(abs(bp[x, y][i] - fp[x, y][i]) for i in range(3)) / 3.0
        scores.append(total / max(1, n))
    return scores


def build_kind(name: str) -> None:
    still_path = STILL_SRC[name]
    if not still_path.is_file():
        raise FileNotFoundError(f"missing still source: {still_path}")

    is_dromas = name == "dromas"
    still = _key_still(still_path, dromas=is_dromas)
    still.save(OUT / f"{name}.png")
    print("wrote", f"{name}.png", still.size, "(front still)")

    frames: list[Image.Image] = []
    for i in range(1, 5):
        path = WALK / f"{name}_walk_f{i}.png"
        if not path.is_file():
            raise FileNotFoundError(f"missing walk frame: {path}")
        fr = _key_walk_frame(path, dromas=is_dromas)
        frames.append(fr)
        fr.save(OUT / f"{name}_f{i}.png")
        print("wrote", f"{name}_f{i}.png", fr.size)

    deltas = _frame_diversity(frames)
    print(f"  {name} frame diversity vs f1:", ", ".join(f"{d:.1f}" for d in deltas))
    if any(d < 4.0 for d in deltas):
        print(f"  WARNING: {name} walk frames look nearly identical (bob risk)")

    _film(frames, OUT / f"{name}_film.png")


def pack_pet_films(*, kinds: tuple[str, ...] | None = None) -> None:
    """Key generated pet poses into 4-frame reaction strips.

    Prefers assets/life_sprites/_hsr_src/pet/ (reproducible). Optional Cursor
    gen drop folder is only a fallback for first-time imports.
    """
    gen = Path(r"C:\Users\17501\.cursor\projects\d-Workspace-Amphoreus\assets")
    PET.mkdir(parents=True, exist_ok=True)
    jobs = (
        ("chimera", 184),
        ("dromas", 184),
        ("hearth_cat", 256),
    )
    for name, cell in jobs:
        if kinds is not None and name not in kinds:
            continue
        frames: list[Image.Image] = []
        for i in range(1, 5):
            src = PET / f"{name}_pet_f{i}.png"
            imported = False
            if not src.is_file():
                alt = gen / f"{name}_pet_f{i}.png"
                if not alt.is_file():
                    alt = gen / f"{name}_pet_f{i}_gen.png"
                if not alt.is_file():
                    raise FileNotFoundError(f"missing pet frame: {name} f{i}")
                src = alt
                imported = True
            raw = Image.open(src).convert("RGBA")
            if imported:
                # First-time import into canonical _hsr_src/pet.
                raw.save(PET / f"{name}_pet_f{i}.png")
            if name == "dromas":
                raw = _prepare_dromas(raw)
            keyed = (
                _drop_islands(_dark_flood(raw))
                if _needs_dark_key(raw)
                else _drop_islands(_white_flood(raw))
            )
            fr = _fit_cell(keyed, cell=cell)
            frames.append(fr)
            fr.save(OUT / f"{name}_pet_f{i}.png")
        strip = Image.new("RGBA", (cell * len(frames), cell), (0, 0, 0, 0))
        for i, fr in enumerate(frames):
            strip.paste(fr, (i * cell, 0), fr)
        dest = OUT / f"{name}_pet_film.png"
        strip.save(dest)
        print("wrote", dest.name, strip.size)


def _needs_dark_key(im: Image.Image) -> bool:
    """True when the canvas is mostly dark (pet gens on #1a1524)."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    dark = 0
    n = 0
    step = max(1, min(w, h) // 64)
    px = rgb.load()
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y]
            n += 1
            if r <= 48 and g <= 48 and b <= 48:
                dark += 1
    return n > 0 and (dark / n) >= 0.35


def pack_dromas_calf(scale: float = 0.52) -> None:
    """Baby dromas: scaled adult still / walk / pet films."""
    stems = (
        "dromas.png",
        *(f"dromas_f{i}.png" for i in range(1, 5)),
        "dromas_film.png",
        *(f"dromas_pet_f{i}.png" for i in range(1, 5)),
        "dromas_pet_film.png",
    )
    for name in stems:
        src = OUT / name
        if not src.is_file():
            print("skip missing", name)
            continue
        im = Image.open(src).convert("RGBA")
        w, h = im.size
        out = im.resize(
            (max(1, int(w * scale)), max(1, int(h * scale))),
            Image.Resampling.LANCZOS,
        )
        dest = OUT / name.replace("dromas", "dromas_calf", 1)
        out.save(dest)
        print("wrote", dest.name, out.size)


# ---------------------------------------------------------------------------
# Profession outfits — recolor/composite from civilian resident still + walk
# ---------------------------------------------------------------------------

# Recipes keyed by sprite stem (matches resident_npcs.ROLE_OUTFIT values).
# fabric: chiton + drape near-whites. gold: optional trim retint. sash/apron:
# simple overlays so professions read at land scale without new source art.
OUTFIT_RECIPES: dict[str, dict] = {
    "resident_guard": {
        "fabric": (132, 46, 52),
        "gold": (210, 168, 78),
        "sash": (36, 32, 40),
        "sash_y": 0.42,
    },
    "resident_merchant": {
        "fabric": (236, 224, 196),
        "cloak": (74, 96, 148),
        "gold": (220, 176, 72),
        "pouch": True,
    },
    "resident_scholar": {
        "fabric": (78, 84, 118),
        "gold": (196, 170, 96),
        "scroll": True,
    },
    "resident_smith": {
        "fabric": (86, 72, 62),
        "gold": (168, 132, 72),
        "apron": (42, 36, 32),
    },
    "resident_weaver": {
        "fabric": (198, 176, 204),
        "gold": (188, 148, 92),
        "sash": (148, 72, 108),
        "sash_y": 0.44,
    },
    "resident_shrine": {
        "fabric": (248, 244, 232),
        "gold": (228, 188, 72),
        "laurel": True,
    },
    "resident_healer": {
        "fabric": (196, 224, 204),
        "gold": (180, 160, 88),
        "sash": (86, 138, 112),
        "sash_y": 0.45,
    },
    "resident_harbor": {
        "fabric": (82, 112, 142),
        "gold": (176, 148, 84),
    },
    "resident_field": {
        "fabric": (152, 132, 84),
        "gold": (156, 128, 64),
        "apron": (112, 100, 64),
    },
    "resident_handler": {
        "fabric": (156, 128, 100),
        "gold": (188, 148, 72),
        "harness": True,
    },
    "resident_baker": {
        "fabric": (244, 236, 220),
        "gold": (196, 156, 84),
        "apron": (226, 218, 200),
    },
}


def _is_skin(r: int, g: int, b: int, sat: float, lum: float) -> bool:
    return (
        r > 110
        and g > 70
        and b > 45
        and r >= g >= b - 8
        and 85 < lum < 200
        and 0.12 < sat < 0.55
        and (r - b) > 25
    )


def _is_gold(r: int, g: int, b: int, sat: float, lum: float) -> bool:
    return r > 145 and g > 100 and b < 120 and sat > 0.20 and lum > 105


def _is_fabric(r: int, g: int, b: int, sat: float, lum: float) -> bool:
    if _is_skin(r, g, b, sat, lum) or _is_gold(r, g, b, sat, lum):
        return False
    # Near-white / cream drapery (incl. warm folds).
    if lum >= 155 and sat <= 0.28:
        return True
    # Lit cream with a little warm bias.
    if lum >= 140 and sat <= 0.35 and r >= g >= b - 6 and (r - b) < 70:
        return True
    return False


def _shade_rgb(rgb: tuple[int, int, int], lum: float) -> tuple[int, int, int]:
    shade = 0.48 + 0.52 * (lum / 255.0)
    return (
        int(min(255, rgb[0] * shade)),
        int(min(255, rgb[1] * shade)),
        int(min(255, rgb[2] * shade)),
    )


def _recolor_outfit(im: Image.Image, recipe: dict) -> Image.Image:
    """Recolor civilian near-white drapery; preserve skin / hair / sandals."""
    out = im.convert("RGBA").copy()
    px = out.load()
    w, h = out.size
    fabric = recipe.get("fabric")
    cloak = recipe.get("cloak")
    gold = recipe.get("gold")
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 40:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            sat = (mx - mn) / mx if mx else 0.0
            lum = (r + g + b) / 3.0
            if _is_gold(r, g, b, sat, lum):
                if gold:
                    px[x, y] = (*_shade_rgb(gold, lum), a)
                continue
            if not _is_fabric(r, g, b, sat, lum):
                continue
            # Cloak bias: left side of figure (drape over shoulder/arm).
            use_cloak = bool(cloak) and x < int(w * 0.48) and y < int(h * 0.72)
            target = cloak if use_cloak else fabric
            if not target:
                continue
            px[x, y] = (*_shade_rgb(target, lum), a)
    return out


def _overlay_band(
    im: Image.Image,
    rgb: tuple[int, int, int],
    *,
    y_frac: float,
    thickness: float = 0.045,
    x0_frac: float = 0.30,
    x1_frac: float = 0.72,
    alpha: int = 150,
) -> None:
    """Paint a soft sash/apron band across the torso (in-place)."""
    from PIL import ImageDraw, ImageFilter, ImageChops

    w, h = im.size
    y = int(h * y_frac)
    th = max(2, int(h * thickness))
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x0, x1 = int(w * x0_frac), int(w * x1_frac)
    draw.rounded_rectangle(
        [x0, y - th, x1, y + th],
        radius=max(2, th),
        fill=(*rgb, alpha),
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.2))
    base_a = im.split()[-1]
    band_a = overlay.split()[-1]
    overlay.putalpha(ImageChops.multiply(band_a, base_a))
    im.alpha_composite(overlay)


def _overlay_marks(im: Image.Image, recipe: dict) -> Image.Image:
    """Profession marks: sash, apron, pouch, scroll, laurel, harness."""
    from PIL import ImageDraw, ImageChops

    out = im.convert("RGBA").copy()
    w, h = out.size
    if recipe.get("sash"):
        _overlay_band(
            out,
            recipe["sash"],
            y_frac=float(recipe.get("sash_y", 0.45)),
            thickness=0.028,
            alpha=135,
        )
    if recipe.get("apron"):
        _overlay_band(
            out,
            recipe["apron"],
            y_frac=0.58,
            thickness=0.09,
            x0_frac=0.34,
            x1_frac=0.68,
            alpha=160,
        )
    draw_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(draw_layer)
    if recipe.get("pouch"):
        cx, cy = int(w * 0.58), int(h * 0.55)
        d.ellipse([cx - 7, cy - 9, cx + 7, cy + 9], fill=(92, 64, 40, 200))
        d.rectangle([cx - 2, cy - 12, cx + 2, cy - 6], fill=(160, 128, 64, 210))
    if recipe.get("scroll"):
        x0, y0 = int(w * 0.62), int(h * 0.48)
        d.rounded_rectangle(
            [x0, y0, x0 + 9, y0 + 26],
            radius=3,
            fill=(236, 224, 196, 210),
            outline=(168, 140, 88, 230),
        )
    if recipe.get("laurel"):
        cx, cy = int(w * 0.50), int(h * 0.14)
        d.arc([cx - 18, cy - 8, cx + 18, cy + 14], 200, 340, fill=(168, 188, 96, 210), width=3)
        d.arc([cx - 16, cy - 6, cx + 16, cy + 12], 200, 340, fill=(210, 176, 72, 200), width=2)
    if recipe.get("harness"):
        _overlay_band(
            out, (72, 56, 44), y_frac=0.36, thickness=0.022, x0_frac=0.32, x1_frac=0.70, alpha=170
        )
        _overlay_band(
            out, (72, 56, 44), y_frac=0.52, thickness=0.020, x0_frac=0.34, x1_frac=0.68, alpha=160
        )
    base_a = out.split()[-1]
    marks_a = draw_layer.split()[-1]
    draw_layer.putalpha(ImageChops.multiply(marks_a, base_a))
    out.alpha_composite(draw_layer)
    return out


def _load_resident_bases() -> tuple[Image.Image, list[Image.Image]]:
    still = Image.open(OUT / "resident.png").convert("RGBA")
    frames = [Image.open(OUT / f"resident_f{i}.png").convert("RGBA") for i in range(1, 5)]
    return still, frames


def build_profession_outfits() -> None:
    """Derive full still + walk film sets for each special profession outfit."""
    still, frames = _load_resident_bases()
    for stem, recipe in OUTFIT_RECIPES.items():
        new_still = _overlay_marks(_recolor_outfit(still, recipe), recipe)
        new_still.save(OUT / f"{stem}.png")
        print("wrote", f"{stem}.png", new_still.size)

        out_frames: list[Image.Image] = []
        for i, fr in enumerate(frames, start=1):
            nf = _overlay_marks(_recolor_outfit(fr, recipe), recipe)
            nf.save(OUT / f"{stem}_f{i}.png")
            out_frames.append(nf)
            print("wrote", f"{stem}_f{i}.png", nf.size)

        cell = out_frames[0].size[0]
        strip = Image.new("RGBA", (cell * len(out_frames), cell), (0, 0, 0, 0))
        for i, fr in enumerate(out_frames):
            strip.paste(fr, (i * cell, 0), fr)
        dest = OUT / f"{stem}_film.png"
        strip.save(dest)
        print("wrote", dest.name, strip.size)
    print("done — profession outfits:", ", ".join(OUTFIT_RECIPES))


# ---------------------------------------------------------------------------
# Chimera color variants (HSR pet colors: blue / pink / orange / purple)
# Stills from GrabCut of _hsr_src color shots; walk/pet films = recolor of base.
# ---------------------------------------------------------------------------

# stem → (source PNG, grabCut rect as fractions of W/H: x,y,w,h), target hue deg
CHIMERA_COLOR_VARIANTS: dict[str, dict] = {
    "chimera_blue": {
        "src": "chimera_blue.png",
        "rect": (0.36, 0.30, 0.28, 0.42),
        "hue": 185.0,
    },
    "chimera_pink": {
        "src": "chimera_pink.png",
        "rect": (0.42, 0.28, 0.22, 0.42),
        "hue": 330.0,
    },
    "chimera_orange": {
        "src": "chimera_orange.png",
        "rect": (0.34, 0.28, 0.32, 0.44),
        "hue": 22.0,
    },
    "chimera_purple": {
        "src": "chimera_purple.png",
        "rect": (0.36, 0.30, 0.28, 0.44),
        "hue": 285.0,
    },
}


def _grabcut_subject(path: Path, rect_frac: tuple[float, float, float, float]) -> Image.Image:
    import cv2
    import numpy as np

    bgr = cv2.imread(str(path))
    if bgr is None:
        raise FileNotFoundError(path)
    h, w = bgr.shape[:2]
    x, y, rw, rh = rect_frac
    rect = (int(w * x), int(h * y), int(w * rw), int(h * rh))
    mask = np.zeros(bgr.shape[:2], np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
    kernel = np.ones((3, 3), np.uint8)
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel)
    mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask2, 8)
    if n > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        best = 1 + int(np.argmax(areas))
        mask2 = (labels == best).astype("uint8") * 255
    rgba = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGBA)
    rgba[:, :, 3] = mask2
    return Image.fromarray(rgba)


def _clean_grab_subject(im: Image.Image) -> Image.Image:
    """Keep the main centered blob; drop furniture leftovers."""
    import cv2
    import numpy as np

    rgba = np.array(im.convert("RGBA"))
    alpha = rgba[:, :, 3]
    h, w = alpha.shape
    ys, xs = np.where(alpha > 16)
    if len(xs) == 0:
        return im
    cy, cx = float(ys.mean()), float(xs.mean())
    mask = (alpha > 16).astype(np.uint8)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
    best, best_score = 1, -1.0
    for i in range(1, n):
        area = float(stats[i, cv2.CC_STAT_AREA])
        ccx, ccy = float(cents[i][0]), float(cents[i][1])
        score = area - 0.3 * ((ccx - cx) ** 2 + (ccy - cy) ** 2) ** 0.5
        if score > best_score:
            best_score = score
            best = i
    keep = (labels == best).astype(np.uint8)
    ys, xs = np.where(keep > 0)
    if len(xs):
        pad = 8
        x0, x1 = max(0, int(xs.min()) - pad), min(w, int(xs.max()) + pad + 1)
        y0, y1 = max(0, int(ys.min()) - pad), min(h, int(ys.max()) + pad + 1)
        box = np.zeros_like(keep)
        box[y0:y1, x0:x1] = 1
        keep = keep * box
    rgba[:, :, 3] = keep * alpha
    # Drop warm furniture wood (tan benches) left behind pink GrabCut.
    r, g, b, a = rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2], rgba[:, :, 3]
    tan = (
        (a > 16)
        & (r > 120)
        & (g > 90)
        & (b < 110)
        & (r >= g - 10)
        & ((r.astype(int) - b) > 40)
        & (np.abs(r.astype(int) - g) < 45)
    )
    pinkish = (r > 140) & (b > 100) & (g < 160)
    horn = (a > 16) & (r > 150) & (g > 130) & (b > 90) & ((r.astype(int) - b) < 80)
    tan = tan & ~pinkish & ~horn
    rgba[tan, 3] = 0
    # Extra pass: warm wood leftovers in the top band (pink lounge furniture).
    r, g, b, a = rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2], rgba[:, :, 3]
    top = np.zeros(a.shape, dtype=bool)
    top[: max(1, h // 3), :] = True
    wood = (
        top
        & (a > 16)
        & (r > 100)
        & (g > 80)
        & (b < 130)
        & ((r.astype(int) - b) > 25)
        & (np.abs(r.astype(int) - g) < 55)
    )
    horn = (r > 160) & (g > 140) & (b > 100) & (r > g - 5)
    rgba[wood & ~horn, 3] = 0
    return Image.fromarray(rgba)


def _recolor_chimera_film(im: Image.Image, target_hue: float) -> Image.Image:
    """Shift purple/magenta fur toward *target_hue*; keep cream belly and darks."""
    import colorsys

    src = im.convert("RGBA")
    px = src.load()
    w, h = src.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 16:
                op[x, y] = (0, 0, 0, 0)
                continue
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            hh, ss, vv = colorsys.rgb_to_hsv(rf, gf, bf)
            hue_deg = hh * 360.0
            # Cream / beige belly & face — leave alone.
            cream = vv > 0.55 and ss < 0.28 and r >= g >= b - 12
            # Near-black lineart / eyes — leave alone.
            dark = vv < 0.18
            # Red/orange irises & blush — leave alone.
            warm_eye = (
                (hue_deg < 40 or hue_deg > 340)
                and ss > 0.35
                and vv > 0.35
                and r > g
            )
            # Purple / magenta / lilac fur (and dark purple mask).
            purpleish = (
                not cream
                and not dark
                and not warm_eye
                and ss > 0.12
                and 240 <= hue_deg <= 340
            )
            if purpleish:
                # Keep value; nudge saturation toward a readable pet color.
                new_s = min(0.85, max(ss, 0.35) * 1.05)
                nr, ng, nb = colorsys.hsv_to_rgb(target_hue / 360.0, new_s, vv)
                op[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
            else:
                op[x, y] = (r, g, b, a)
    return out


def build_chimera_variants() -> None:
    """Front stills from color photos + recolored walk/pet films."""
    base_film = OUT / "chimera_film.png"
    base_pet = OUT / "chimera_pet_film.png"
    if not base_film.is_file():
        raise FileNotFoundError(f"need base walk film first: {base_film}")

    for stem, meta in CHIMERA_COLOR_VARIANTS.items():
        src = SRC / meta["src"]
        if not src.is_file():
            print("skip missing source", src.name)
            continue
        subject = _grabcut_subject(src, meta["rect"])
        still = _fit_cell(_drop_islands(_clean_grab_subject(subject), keep_frac=0.08))
        still.save(OUT / f"{stem}.png")
        print("wrote", f"{stem}.png", still.size, "(color still)")

        hue = float(meta["hue"])
        # Walk film (4 cells wide).
        film = Image.open(base_film).convert("RGBA")
        fw, fh = film.size
        cell_w = fw // 4
        frames = []
        for i in range(4):
            fr = film.crop((i * cell_w, 0, (i + 1) * cell_w, fh))
            frames.append(_recolor_chimera_film(fr, hue))
            frames[-1].save(OUT / f"{stem}_f{i + 1}.png")
        _film(frames, OUT / f"{stem}_film.png")

        # Pet film — optional if base exists.
        if base_pet.is_file():
            pet = Image.open(base_pet).convert("RGBA")
            pw, ph = pet.size
            pcell = pw // 4
            pframes = []
            for i in range(4):
                fr = pet.crop((i * pcell, 0, (i + 1) * pcell, ph))
                pframes.append(_recolor_chimera_film(fr, hue))
                pframes[-1].save(OUT / f"{stem}_pet_f{i + 1}.png")
            strip = Image.new("RGBA", (pcell * 4, ph), (0, 0, 0, 0))
            for i, fr in enumerate(pframes):
                strip.paste(fr, (i * pcell, 0), fr)
            dest = OUT / f"{stem}_pet_film.png"
            strip.save(dest)
            print("wrote", dest.name, strip.size)

    print("done — chimera color variants:", ", ".join(CHIMERA_COLOR_VARIANTS))


def build_dromas_all() -> None:
    """Full adult + calf pipeline: still, walk film, pet film, calf scales."""
    if not WALK.is_dir():
        raise FileNotFoundError(f"missing walk frame dir: {WALK}")
    build_kind("dromas")
    pack_pet_films(kinds=("dromas",))
    pack_dromas_calf()
    print("done — dromas + dromas_calf stills / walk / pet films")


def main() -> None:
    if not WALK.is_dir():
        raise FileNotFoundError(f"missing walk frame dir: {WALK}")
    for kind in PROFILE_KINDS:
        build_kind(kind)
    print("done — front stills + distinct side walk films for", ", ".join(PROFILE_KINDS))


if __name__ == "__main__":
    import sys

    args = set(sys.argv[1:])
    if "dromas" in args or "dromas-all" in args or "dromas_all" in args:
        build_dromas_all()
    elif "pet" in args:
        pack_pet_films()
    elif "outfits" in args:
        build_profession_outfits()
    elif "calf" in args:
        pack_dromas_calf()
    elif "chimera-colors" in args or "chimera_colors" in args:
        build_chimera_variants()
    else:
        main()
