# -*- coding: utf-8 -*-
"""Crop and isolate official Special Program Q-Heirs.

Sources: wiki announcement stills in assets/eternal_page/q_program/announcement/
and optional Bilibili research frames.

    python tools/cut_q_program.py

Does not touch assets/eternal_page/cute/ (PPG busts).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
QP = ROOT / "assets" / "eternal_page" / "q_program"
ANN = QP / "announcement"
CROPS = QP / "crops"
CUTOUTS = QP / "cutouts"
FRAMES = QP / "frames"
PREVIEWS = QP / "_preview"

# (source announcement, box left, top, right, bottom)
CROP_BOXES: dict[str, tuple[str, tuple[int, int, int, int]]] = {
    "tribbie_v31_swing.png": (
        "Version_3.1_Special_Program_Announcement.png",
        (0, 470, 440, 1080),
    ),
    "mydei_v31_sit.png": (
        "Version_3.1_Special_Program_Announcement.png",
        (260, 560, 760, 1080),
    ),
    "aglaea_v31_sit.png": (
        "Version_3.1_Special_Program_Announcement.png",
        (600, 540, 1100, 1080),
    ),
    "mini_companion_v31.png": (
        "Version_3.1_Special_Program_Announcement.png",
        (1140, 740, 1480, 1060),
    ),
    "castorice_v33_sit.png": (
        "Version_3.3_Special_Program_Announcement.png",
        (300, 540, 760, 1080),
    ),
    "hyacine_v33_sit.png": (
        "Version_3.3_Special_Program_Announcement.png",
        (600, 470, 1060, 1080),
    ),
    "cipher_v33_sit.png": (
        "Version_3.3_Special_Program_Announcement.png",
        (900, 480, 1360, 1080),
    ),
    "cyrene_v34_mem.png": (
        "Version_3.4_Special_Program_Announcement.png",
        (10, 210, 430, 655),
    ),
    "phainon_v34_bust.png": (
        "Version_3.4_Special_Program_Announcement.png",
        (80, 560, 580, 1040),
    ),
    "anaxa_v34_bust.png": (
        "Version_3.4_Special_Program_Announcement.png",
        (1440, 0, 1920, 520),
    ),
    "hysilens_v35_sit.png": (
        "Version_3.5_Special_Program_Announcement.png",
        (250, 300, 560, 675),
    ),
    "cerydra_v35_sit.png": (
        "Version_3.5_Special_Program_Announcement.png",
        (450, 310, 800, 675),
    ),
    "sunday_v36_sit.png": (
        "Version_3.6_Special_Program_Announcement.png",
        (260, 450, 740, 1000),
    ),
    "dan_heng_pt_v36_sit.png": (
        "Version_3.6_Special_Program_Announcement.png",
        (540, 460, 1020, 1000),
    ),
    "himeko_v36_sit.png": (
        "Version_3.6_Special_Program_Announcement.png",
        (840, 500, 1160, 1000),
    ),
    "cyrene_v37_tv.png": (
        "Version_3.7_Special_Program_Announcement.png",
        (1240, 330, 1540, 650),
    ),
    "cyrene_v38_sit.png": (
        "Version_3.8_Special_Program_Announcement.png",
        (500, 480, 840, 1000),
    ),
}

# Extra crops from Bilibili 360p frames (emotion variants).
FRAME_CROPS: dict[str, tuple[str, tuple[int, int, int, int]]] = {
    "hyacine_v33_bili_t22.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t22.jpg",
        (0, 0, 318, 360),
    ),
    "castorice_v33_bili_t22.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t22.jpg",
        (318, 0, 640, 360),
    ),
    "hyacine_v33_bili_t28.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t28.jpg",
        (0, 0, 318, 360),
    ),
    "castorice_v33_bili_t28.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t28.jpg",
        (318, 0, 640, 360),
    ),
    "hyacine_v33_bili_t36.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t36.jpg",
        (0, 0, 318, 360),
    ),
    "castorice_v33_bili_t36.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t36.jpg",
        (318, 0, 640, 360),
    ),
    "cipher_v33_bili_t42.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t42.jpg",
        (0, 0, 360, 360),
    ),
    "hyacine_v33_bili_t42.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t42.jpg",
        (360, 0, 640, 180),
    ),
    "castorice_v33_bili_t42.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t42.jpg",
        (360, 180, 640, 360),
    ),
    "castorice_v33_bili_t480.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t480.jpg",
        (40, 210, 200, 355),
    ),
    "hyacine_v33_bili_t480.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t480.jpg",
        (175, 205, 315, 355),
    ),
    "cipher_v33_bili_t480.png": (
        "bilibili_3.3_BV1MB5KzQEYL_t480.jpg",
        (300, 195, 455, 355),
    ),
    "witch_guest_v34_bili_t480.png": (
        "bilibili_3.4_BV1APNWziErE_t480.jpg",
        (0, 225, 145, 355),
    ),
    "anaxa_v34_bili_t480.png": (
        "bilibili_3.4_BV1APNWziErE_t480.jpg",
        (125, 235, 255, 355),
    ),
    "phainon_v34_bili_t480.png": (
        "bilibili_3.4_BV1APNWziErE_t480.jpg",
        (245, 225, 400, 355),
    ),
    "hysilens_v35_bili_t480.png": (
        "bilibili_3.5_BV1gHhAz9EpC_t480.jpg",
        (135, 220, 275, 355),
    ),
    "cerydra_v35_bili_t480.png": (
        "bilibili_3.5_BV1gHhAz9EpC_t480.jpg",
        (265, 215, 410, 355),
    ),
}


def _clamp_box(box: tuple[int, int, int, int], w: int, h: int) -> tuple[int, int, int, int]:
    l, t, r, b = box
    return max(0, l), max(0, t), min(w, r), min(h, b)


def recrop_announcement() -> list[Path]:
    CROPS.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    stale = CROPS / "cyrene_v34_bust.png"
    if stale.exists():
        stale.unlink()
    for name, (src_name, box) in CROP_BOXES.items():
        src = ANN / src_name
        im = Image.open(src).convert("RGB")
        box = _clamp_box(box, im.width, im.height)
        crop = im.crop(box)
        dest = CROPS / name
        crop.save(dest, "PNG")
        written.append(dest)
        print(f"crop {name} {crop.size} from {src_name} {box}")
    return written


def recrop_frames() -> list[Path]:
    written: list[Path] = []
    for name, (src_name, box) in FRAME_CROPS.items():
        src = FRAMES / src_name
        if not src.exists():
            print(f"skip frame crop {name}: missing {src_name}")
            continue
        im = Image.open(src).convert("RGB")
        box = _clamp_box(box, im.width, im.height)
        crop = im.crop(box)
        dest = CROPS / name
        crop.save(dest, "PNG")
        written.append(dest)
        print(f"crop {name} {crop.size} from {src_name} {box}")
    return written


def _corner_lab_dist(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    cs = max(12, min(h, w) // 14)
    corners = np.concatenate(
        [
            lab[:cs, :cs].reshape(-1, 3),
            lab[:cs, -cs:].reshape(-1, 3),
            lab[-cs:, :cs].reshape(-1, 3),
            lab[-cs:, -cs:].reshape(-1, 3),
        ],
        axis=0,
    )
    med = np.median(corners, axis=0)
    return np.linalg.norm(lab - med, axis=2)


def _color_fg(rgb: np.ndarray) -> np.ndarray:
    dist = _corner_lab_dist(rgb)
    peak = float(dist.max()) or 1.0
    d8 = np.clip(dist / peak * 255.0, 0, 255).astype(np.uint8)
    _, otsu = cv2.threshold(d8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # also keep a high-distance floor so pale characters survive mixed corners
    floor = max(16.0, float(np.percentile(dist, 55)))
    return ((otsu > 0) | (dist > floor)).astype(np.uint8)


def _canny_interior_fg(rgb: np.ndarray) -> np.ndarray:
    """Flood from corners on Canny dams; leftover is outlined interiors."""
    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 35, 110)
    # thicken strokes so small outline gaps do not leak
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    # reject hairline stage rules (very long, very thin)
    num, labels, stats, _ = cv2.connectedComponentsWithStats(edges, 8)
    clean = np.zeros_like(edges)
    for i in range(1, num):
        x, y, bw, bh, area = stats[i]
        if area < 12:
            continue
        thin = (min(bw, bh) <= 3) and (max(bw, bh) > min(h, w) * 0.45)
        if thin:
            continue
        clean[labels == i] = 255
    # floodFill from each corner through non-edge pixels
    flood = np.zeros((h, w), np.uint8)
    vis = np.zeros((h, w), dtype=bool)
    stack = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    while stack:
        y, x = stack.pop()
        if y < 0 or y >= h or x < 0 or x >= w or vis[y, x]:
            continue
        vis[y, x] = True
        if clean[y, x]:
            continue
        flood[y, x] = 1
        stack.extend(((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)))
    interior = (1 - flood).astype(np.uint8)
    interior = np.maximum(interior, (clean > 0).astype(np.uint8))
    return interior


def _largest_blobs(mask: np.ndarray, keep: int = 2) -> np.ndarray:
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if num <= 1:
        return mask
    areas = [(stats[i, cv2.CC_STAT_AREA], i) for i in range(1, num)]
    areas.sort(reverse=True)
    out = np.zeros_like(mask)
    h, w = mask.shape
    cx, cy = w / 2.0, h / 2.0
    picked = []
    for area, i in areas:
        if area < (h * w) * 0.006:
            continue
        ys, xs = np.where(labels == i)
        mx, my = xs.mean(), ys.mean()
        dist = abs(mx - cx) / w + abs(my - cy) / h
        picked.append((dist, -area, i))
    picked.sort()
    for _, __, i in picked[:keep]:
        out[labels == i] = 1
    if out.sum() == 0 and areas:
        out[labels == areas[0][1]] = 1
    return out


def _grabcut_from_mask(rgb: np.ndarray, fg: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    gc = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    border = max(4, min(h, w) // 30)
    gc[:border, :] = cv2.GC_BGD
    gc[-border:, :] = cv2.GC_BGD
    gc[:, :border] = cv2.GC_BGD
    gc[:, -border:] = cv2.GC_BGD
    fg_u8 = (fg > 0).astype(np.uint8)
    kernel = np.ones((5, 5), np.uint8)
    sure = cv2.erode(fg_u8, kernel)
    gc[fg_u8 > 0] = cv2.GC_PR_FGD
    gc[sure > 0] = cv2.GC_FGD
    # if the seed is empty, fall back to a padded rectangle
    if sure.sum() < 40:
        m = max(8, min(h, w) // 16)
        gc[m : h - m, m : w - m] = cv2.GC_PR_FGD
        mode = cv2.GC_INIT_WITH_RECT
        rect = (m, m, max(1, w - 2 * m), max(1, h - 2 * m))
        try:
            bgd = np.zeros((1, 65), np.float64)
            fgd = np.zeros((1, 65), np.float64)
            cv2.grabCut(bgr, gc, rect, bgd, fgd, 5, mode)
        except cv2.error:
            return fg_u8
    else:
        try:
            bgd = np.zeros((1, 65), np.float64)
            fgd = np.zeros((1, 65), np.float64)
            cv2.grabCut(bgr, gc, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
        except cv2.error:
            return fg_u8
    return np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)


def _fill_internal_holes(fg: np.ndarray) -> np.ndarray:
    h, w = fg.shape
    fg = fg.copy()
    num, labels, stats, _ = cv2.connectedComponentsWithStats((1 - fg).astype(np.uint8), 8)
    for i in range(1, num):
        x, y, bw, bh, area = stats[i]
        touches = x <= 1 or y <= 1 or x + bw >= w - 2 or y + bh >= h - 2
        if (not touches) and area < (h * w) * 0.30:
            fg[labels == i] = 1
    return fg


def isolate_rgb(rgb: np.ndarray) -> np.ndarray:
    """Return uint8 alpha (0-255) for a Q-character crop."""
    h, w = rgb.shape[:2]
    color = _color_fg(rgb)
    canny = _canny_interior_fg(rgb)
    # prefer pixels that look unlike the corners AND sit inside an outline
    fg = color & canny
    if fg.mean() < 0.04:
        fg = np.maximum(color, canny)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    fg = _largest_blobs(fg, keep=1)
    fg = _grabcut_from_mask(rgb, fg)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    fg = _fill_internal_holes(fg)
    fg = _largest_blobs(fg, keep=1)
    # drop leftover border strips
    dist_bg = cv2.distanceTransform((1 - fg).astype(np.uint8), cv2.DIST_L2, 3)
    alpha = np.zeros((h, w), np.float32)
    alpha[fg > 0] = 1.0
    edge = (dist_bg > 0) & (dist_bg < 1.6)
    alpha[edge] = np.clip(1.0 - dist_bg[edge] / 1.6, 0, 1)
    return (alpha * 255).astype(np.uint8)


def _magenta_preview(rgba: np.ndarray) -> np.ndarray:
    h, w = rgba.shape[:2]
    mag = np.empty((h, w, 3), np.uint8)
    mag[:, :] = (255, 0, 255)
    a = rgba[:, :, 3:4].astype(np.float32) / 255.0
    rgb = rgba[:, :, :3].astype(np.float32)
    out = rgb * a + mag.astype(np.float32) * (1.0 - a)
    return out.astype(np.uint8)


def cutout_path(src: Path, dest: Path, preview_dir: Path | None = None) -> dict:
    im = Image.open(src).convert("RGB")
    rgb = np.array(im)
    alpha = isolate_rgb(rgb)
    rgba = np.dstack([rgb, alpha])
    Image.fromarray(rgba, "RGBA").save(dest, "PNG")
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=True)
        prev = _magenta_preview(rgba)
        Image.fromarray(prev, "RGB").save(preview_dir / dest.name, "PNG")
    cov = float(alpha.mean()) / 255.0
    return {"file": dest.name, "coverage": round(cov, 3), "size": f"{im.width}x{im.height}"}


def cut_all(extra_globs: list[str] | None = None) -> list[dict]:
    CUTOUTS.mkdir(parents=True, exist_ok=True)
    paths = sorted(CROPS.glob("*.png"))
    if extra_globs:
        for g in extra_globs:
            paths.extend(sorted(Path(g).parent.glob(Path(g).name)))
    reports = []
    for p in paths:
        dest = CUTOUTS / p.name
        info = cutout_path(p, dest, PREVIEWS)
        reports.append(info)
        print(f"cutout {info['file']} coverage={info['coverage']} {info['size']}")
    return reports


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-recrop", action="store_true")
    ap.add_argument("--frames", action="store_true", help="also recrop Bilibili emotion frames")
    args = ap.parse_args()
    if not args.skip_recrop:
        recrop_announcement()
    recrop_frames()
    extra = []
    if args.frames:
        extra.append(str(FRAMES / "*.png"))
    cut_all(extra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
