"""Build per-place civic env sprites under assets/life_sprites/.

Copies Okhema-polished fixtures as ``*_okhema`` stems, then recolors /
procedurally paints place-family variants (Aedes rustic, Janus ritual,
Kremnos martial, Styxia pearl, Grove scholar, Aidonia muted).

Does not touch ``assets/life_sprites/_hsr_src/``.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "life_sprites"
SIZE = 256


def _blank() -> Image.Image:
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def _save(im: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    im.save(path, "PNG")
    print(f"  wrote {path.name}")


def _copy_as(src_name: str, dest_name: str) -> None:
    src = OUT / src_name
    if not src.is_file():
        print(f"  skip copy {src_name} -> {dest_name} (missing)")
        return
    im = Image.open(src).convert("RGBA")
    _save(im, dest_name)


def _map_pixels(im: Image.Image, fn) -> Image.Image:
    src = im.convert("RGBA")
    px = src.load()
    w, h = src.size
    out = src.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            op[x, y] = fn(r, g, b, a)
    return out


def _is_gold(r, g, b) -> bool:
    return r > 140 and g > 100 and b < 160 and (r - b) > 35 and r >= g


def _is_cream(r, g, b) -> bool:
    return r > 170 and g > 150 and b > 120 and abs(r - g) < 40 and (r + g + b) > 480


def recolor_aedes(im: Image.Image) -> Image.Image:
    """Plain wood / modest stone — strip polished gold."""

    def fn(r, g, b, a):
        if _is_gold(r, g, b):
            return (118, 86, 54, a)
        if _is_cream(r, g, b):
            return (156, 138, 112, a)
        # mild desat toward warm grey-brown
        avg = (r + g + b) // 3
        r = int(r * 0.55 + avg * 0.35 + 20)
        g = int(g * 0.55 + avg * 0.30 + 12)
        b = int(b * 0.45 + avg * 0.25 + 8)
        return (min(255, r), min(255, g), min(255, b), a)

    out = _map_pixels(im, fn)
    return ImageEnhance.Contrast(out).enhance(0.92)


def recolor_janus(im: Image.Image) -> Image.Image:
    """Quieter ritual cloth — soft violet / pale linen, less gold glare."""

    def fn(r, g, b, a):
        if _is_gold(r, g, b):
            return (168, 148, 118, a)
        if _is_cream(r, g, b):
            return (210, 200, 214, a)
        # cool the midtones slightly toward ritual cloth
        r2 = int(r * 0.92 + 12)
        g2 = int(g * 0.90 + 8)
        b2 = int(b * 0.98 + 18)
        return (min(255, r2), min(255, g2), min(255, b2), a)

    return _map_pixels(im, fn)


def recolor_kremnos(im: Image.Image) -> Image.Image:
    """Martial iron — gold to cold metal, cream to slate."""

    def fn(r, g, b, a):
        if _is_gold(r, g, b):
            return (92, 96, 104, a)
        if _is_cream(r, g, b):
            return (110, 108, 112, a)
        # keep reds (ember / blood cloth), mute warm stone
        if r > g + 25 and r > b + 20 and r > 90:
            return (min(255, int(r * 0.95)), int(g * 0.7), int(b * 0.65), a)
        avg = (r + g + b) // 3
        return (
            int(avg * 0.85 + 10),
            int(avg * 0.82 + 8),
            int(avg * 0.88 + 12),
            a,
        )

    out = _map_pixels(im, fn)
    return ImageEnhance.Brightness(out).enhance(0.92)


def recolor_styxia(im: Image.Image) -> Image.Image:
    """Pearly / pale shore — soft blue-white shift."""

    def fn(r, g, b, a):
        if _is_gold(r, g, b):
            return (186, 198, 208, a)
        r2 = int(r * 0.78 + 40)
        g2 = int(g * 0.82 + 48)
        b2 = int(b * 0.88 + 62)
        return (min(255, r2), min(255, g2), min(255, b2), a)

    out = _map_pixels(im, fn)
    return ImageEnhance.Color(out).enhance(0.85)


def recolor_grove(im: Image.Image) -> Image.Image:
    """Scholar leaf / olive stone."""

    def fn(r, g, b, a):
        if _is_gold(r, g, b):
            return (140, 150, 78, a)
        r2 = int(r * 0.75 + 18)
        g2 = int(g * 0.88 + 28)
        b2 = int(b * 0.70 + 12)
        return (min(255, r2), min(255, g2), min(255, b2), a)

    return _map_pixels(im, fn)


def recolor_aidonia(im: Image.Image) -> Image.Image:
    """Snow / death city — muted stone and ribbon cold."""

    def fn(r, g, b, a):
        avg = (r + g + b) // 3
        r2 = int(avg * 0.92 + 18)
        g2 = int(avg * 0.94 + 22)
        b2 = int(avg * 1.02 + 28)
        return (min(255, r2), min(255, g2), min(255, min(255, b2)), a)

    out = _map_pixels(im, fn)
    return ImageEnhance.Color(out).enhance(0.45)


def _poly(draw, pts, fill, outline=None, width=1):
    draw.polygon(pts, fill=fill, outline=outline)
    if outline and width > 1:
        draw.line(pts + [pts[0]], fill=outline, width=width)


def paint_stall(
    *,
    awning,
    post,
    body,
    shelf,
    goods,
    trim=None,
    rustic: bool = False,
    name: str,
) -> None:
    """Isometric-ish market stall on transparent 256 canvas."""
    im = _blank()
    d = ImageDraw.Draw(im)
    # ground shadow
    d.ellipse((58, 198, 198, 238), fill=(0, 0, 0, 55))
    # posts
    post_w = 7 if rustic else 8
    for x0 in (70, 178):
        d.rectangle((x0, 96, x0 + post_w, 210), fill=post)
    # counter / body
    _poly(
        d,
        [(78, 140), (178, 140), (190, 210), (66, 210)],
        fill=body,
        outline=trim or post,
        width=2,
    )
    # shelf lip
    d.rectangle((82, 148, 174, 158), fill=shelf)
    # goods on shelf
    gx = 92
    for color in goods:
        if rustic:
            d.ellipse((gx, 128, gx + 18, 148), fill=color)
        else:
            d.rounded_rectangle((gx, 124, gx + 20, 148), radius=4, fill=color)
        gx += 26
    # awning (triangle / peaked)
    if rustic:
        _poly(
            d,
            [(60, 108), (128, 62), (196, 108)],
            fill=awning,
            outline=post,
            width=2,
        )
        # plain underside strip
        d.rectangle((72, 108, 184, 118), fill=tuple(max(0, c - 25) for c in awning[:3]) + (255,))
    else:
        _poly(
            d,
            [(52, 112), (128, 48), (204, 112)],
            fill=awning,
            outline=trim or (40, 30, 24, 255),
            width=2,
        )
        # scalloped edge
        for i in range(6):
            x = 64 + i * 22
            d.pieslice((x, 100, x + 22, 128), 0, 180, fill=awning)
        if trim:
            d.line([(56, 110), (128, 52), (200, 110)], fill=trim, width=3)
    # soft shade
    im = im.filter(ImageFilter.SMOOTH)
    _save(im, name)


def paint_ribbon(*, cloth, knot, name: str) -> None:
    im = _blank()
    d = ImageDraw.Draw(im)
    # twin hanging loops
    for cx, sign in ((100, -1), (156, 1)):
        pts = []
        for t in range(0, 21):
            u = t / 20
            x = cx + sign * (8 + 18 * math.sin(u * math.pi))
            y = 40 + u * 160
            pts.append((x, y))
        d.line(pts, fill=cloth, width=10)
    d.ellipse((112, 108, 144, 140), fill=knot)
    d.ellipse((120, 116, 136, 132), fill=tuple(min(255, c + 30) for c in knot[:3]) + (255,))
    _save(im, name)


def paint_pillar(*, stone, capital, name: str) -> None:
    im = _blank()
    d = ImageDraw.Draw(im)
    d.ellipse((70, 200, 186, 236), fill=(0, 0, 0, 50))
    d.rectangle((98, 48, 158, 210), fill=stone)
    # fluting hint
    for x in (110, 128, 146):
        d.line([(x, 56), (x, 200)], fill=tuple(max(0, c - 18) for c in stone[:3]) + (90,), width=2)
    d.rectangle((82, 40, 174, 58), fill=capital)
    d.rectangle((86, 200, 170, 218), fill=capital)
    _save(im, name)


def paint_mosaic(*, tiles, name: str) -> None:
    im = _blank()
    d = ImageDraw.Draw(im)
    # diamond floor panel
    cx, cy = 128, 140
    size = 72
    for i, col in enumerate(tiles):
        ox = (i % 2) * 36 - 18
        oy = (i // 2) * 28 - 14
        _poly(
            d,
            [
                (cx + ox, cy + oy - size // 3),
                (cx + ox + size // 2, cy + oy),
                (cx + ox, cy + oy + size // 3),
                (cx + ox - size // 2, cy + oy),
            ],
            fill=col,
            outline=(30, 24, 18, 180),
            width=1,
        )
    _save(im, name)


def build_stalls() -> None:
    paint_stall(
        awning=(201, 74, 74, 255),
        post=(106, 90, 72, 255),
        body=(216, 200, 168, 255),
        shelf=(184, 150, 90, 255),
        goods=((120, 48, 120, 255), (60, 140, 80, 255), (220, 160, 60, 255), (200, 80, 80, 255)),
        trim=(232, 200, 106, 255),
        name="stall_okhema.png",
    )
    # also generic stall.png for KIND_VISUAL fallback "stall"
    paint_stall(
        awning=(201, 74, 74, 255),
        post=(106, 90, 72, 255),
        body=(216, 200, 168, 255),
        shelf=(184, 150, 90, 255),
        goods=((120, 48, 120, 255), (60, 140, 80, 255), (220, 160, 60, 255)),
        trim=(232, 200, 106, 255),
        name="stall.png",
    )
    paint_stall(
        awning=(168, 140, 100, 255),
        post=(96, 72, 48, 255),
        body=(150, 122, 88, 255),
        shelf=(120, 92, 64, 255),
        goods=((140, 100, 60, 255), (100, 120, 70, 255)),
        rustic=True,
        name="stall_aedes.png",
    )
    paint_stall(
        awning=(180, 168, 196, 255),
        post=(120, 110, 128, 255),
        body=(198, 188, 200, 255),
        shelf=(160, 148, 170, 255),
        goods=((200, 190, 210, 255), (150, 130, 170, 255), (220, 210, 200, 255)),
        trim=(168, 148, 118, 255),
        name="stall_janus.png",
    )
    paint_stall(
        awning=(120, 40, 40, 255),
        post=(70, 72, 78, 255),
        body=(96, 94, 98, 255),
        shelf=(78, 80, 86, 255),
        goods=((90, 90, 96, 255), (140, 50, 40, 255), (110, 110, 118, 255)),
        trim=(120, 124, 132, 255),
        name="stall_kremnos.png",
    )
    paint_stall(
        awning=(210, 224, 230, 255),
        post=(150, 160, 168, 255),
        body=(220, 228, 232, 255),
        shelf=(180, 198, 208, 255),
        goods=((230, 240, 245, 255), (160, 190, 200, 255), (200, 180, 190, 255)),
        trim=(186, 198, 208, 255),
        name="stall_styxia.png",
    )


def build_from_existing() -> None:
    # Canonical polished fixtures → okhema family
    for base in ("well", "fountain", "shrine", "laundry", "mill"):
        _copy_as(f"{base}.png", f"{base}_okhema.png")

    # Gate art is Janus-faced — keep as janus; derive okhema from shrine/gate gold
    if (OUT / "gate.png").is_file():
        _copy_as("gate.png", "gate_janus.png")
        gate = Image.open(OUT / "gate.png").convert("RGBA")
        # Okhema gate: warmer gold push (less violet cloth feel)
        def ok_gate(r, g, b, a):
            if _is_gold(r, g, b):
                return (min(255, int(r * 1.05)), min(255, int(g * 0.98)), int(b * 0.85), a)
            return (r, g, b, a)

        _save(_map_pixels(gate, ok_gate), "gate_okhema.png")

    # Forge / banner already martial
    _copy_as("forge.png", "forge_kremnos.png")
    _copy_as("banner.png", "banner_kremnos.png")
    # Milder civic banner for okhema if ever needed — gold cloth, not blood
    if (OUT / "banner.png").is_file():
        ban = Image.open(OUT / "banner.png").convert("RGBA")

        def ok_ban(r, g, b, a):
            if r > 100 and g < 90 and b < 90:
                return (200, 170, 90, a)
            return (r, g, b, a)

        _save(_map_pixels(ban, ok_ban), "banner_okhema.png")

    boat = OUT / "boat.png"
    if boat.is_file():
        bim = Image.open(boat).convert("RGBA")
        _save(bim, "boat_styxia.png")
        _save(recolor_aedes(bim), "boat_aedes.png")

    well = OUT / "well.png"
    if well.is_file():
        w = Image.open(well).convert("RGBA")
        _save(recolor_aedes(w), "well_aedes.png")
        _save(recolor_janus(w), "well_janus.png")
        _save(recolor_kremnos(w), "well_kremnos.png")
        _save(recolor_styxia(w), "well_styxia.png")
        _save(recolor_aidonia(w), "well_aidonia.png")

    fountain = OUT / "fountain.png"
    if fountain.is_file():
        f = Image.open(fountain).convert("RGBA")
        _save(recolor_grove(f), "fountain_grove.png")
        _save(recolor_styxia(f), "fountain_styxia.png")

    shrine = OUT / "shrine.png"
    if shrine.is_file():
        s = Image.open(shrine).convert("RGBA")
        _save(recolor_janus(s), "shrine_janus.png")
        _save(recolor_aedes(s), "shrine_aedes.png")

    laundry = OUT / "laundry.png"
    if laundry.is_file():
        la = Image.open(laundry).convert("RGBA")
        _save(recolor_aedes(la), "laundry_aedes.png")
        _save(recolor_styxia(la), "laundry_styxia.png")


def build_extras() -> None:
    paint_ribbon(
        cloth=(200, 120, 160, 255),
        knot=(232, 180, 200, 255),
        name="ribbon_janus.png",
    )
    paint_ribbon(
        cloth=(160, 170, 185, 255),
        knot=(190, 198, 210, 255),
        name="ribbon_aidonia.png",
    )
    paint_pillar(
        stone=(201, 184, 150, 255),
        capital=(232, 213, 163, 255),
        name="pillar_okhema.png",
    )
    paint_pillar(
        stone=(140, 150, 100, 255),
        capital=(170, 175, 120, 255),
        name="pillar_grove.png",
    )
    paint_pillar(
        stone=(150, 155, 165, 255),
        capital=(180, 186, 196, 255),
        name="pillar_aidonia.png",
    )
    # also generic pillar.png
    paint_pillar(
        stone=(201, 184, 150, 255),
        capital=(232, 213, 163, 255),
        name="pillar.png",
    )
    paint_mosaic(
        tiles=(
            (106, 138, 170, 255),
            (201, 168, 106, 255),
            (201, 74, 74, 255),
            (74, 122, 72, 255),
        ),
        name="mosaic_okhema.png",
    )
    paint_mosaic(
        tiles=(
            (106, 138, 170, 255),
            (201, 168, 106, 255),
            (201, 74, 74, 255),
            (74, 122, 72, 255),
        ),
        name="mosaic.png",
    )


def main() -> None:
    print("Building place-family env sprites…")
    build_stalls()
    build_from_existing()
    build_extras()
    print("Done.")


if __name__ == "__main__":
    main()
