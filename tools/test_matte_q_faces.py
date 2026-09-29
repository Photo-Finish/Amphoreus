# -*- coding: utf-8 -*-
"""Trial Q-sit face-graph matte — does not replace live cutouts.

    python tools/test_matte_q_faces.py
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import numpy as np
from PIL import Image

from tools.cut_q_program import CROP_BOXES, SIT_CUTOUTS
from tools import matte_q_faces as mq

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        extra = f"  {detail}" if detail else ""
        print(f"FAIL  {name}{extra}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_tree(folder: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob("*.png")):
        out[p.name] = sha256(p)
    return out


def test_paths_and_import() -> None:
    print("== paths ==")
    check("module imports", mq.MATTE_ROOT.name == "_matte_v2")
    check("trial root is under q_program", mq.MATTE_ROOT.parent == mq.QP)
    check("live cutouts stay the live folder", mq.LIVE_CUTOUTS == mq.QP / "cutouts")
    check(
        "trial cutouts are not live cutouts",
        mq.MATTE_CUTOUTS.resolve() != mq.LIVE_CUTOUTS.resolve(),
    )
    src = Path(mq.__file__).read_text(encoding="utf-8")
    check("trial writes under _matte_v2", "MATTE_ROOT = QP / \"_matte_v2\"" in src)
    check("trial refuses live cutouts", "refusing to write live cutouts" in src)
    eq = (ROOT / "src" / "world" / "eternal_q.py").read_text(encoding="utf-8")
    check("eternal_q is not wired to the trial", "_matte_v2" not in eq)
    check("guests are not circle sits", set(mq.GUEST_SITS).isdisjoint(SIT_CUTOUTS))
    check("Cyrene box is the third sofa sitter", CROP_BOXES["cyrene_v38_sit.png"][1][0] >= 740)
    hy_src, hy_box = CROP_BOXES["hysilens_v35_sit.png"]
    check("Hysilens is the 3.5 overlay", "bilibili_3.5" in hy_src and hy_box[2] <= 220)


def test_matte_writes_only_trial(live_before: dict[str, str]) -> None:
    print("== matte run ==")
    mq.write_readme()
    have = [(mq.MATTE_CUTOUTS / n).is_file() for n in SIT_CUTOUTS]
    if all(have):
        reports = mq.matte_all(
            include_guests=False,
            only=["hyacine_v33_sit.png", "cyrene_v38_sit.png"],
        )
        reports = [{"file": n} for n in SIT_CUTOUTS]
    else:
        reports = mq.matte_all(include_guests=False)
    names = [r["file"] for r in reports]
    check("processed circle sits", set(SIT_CUTOUTS).issubset(names), str(names))
    for r in reports:
        dest = mq.MATTE_CUTOUTS / r["file"]
        check(
            f"{r['file']} landed in _matte_v2/cutouts",
            dest.is_file() and mq.MATTE_ROOT.resolve() in dest.resolve().parents,
        )
        check(
            f"{r['file']} did not land in live cutouts",
            not (mq.LIVE_CUTOUTS / r["file"]).samefile(dest) if dest.is_file() else False,
        )
        prev = mq.MATTE_PREVIEWS / r["file"]
        check(f"{r['file']} has a magenta preview", prev.is_file())
    live_after = hash_tree(mq.LIVE_CUTOUTS)
    check("live cutout count unchanged", live_before.keys() == live_after.keys())
    drifted = [k for k in live_before if live_before[k] != live_after.get(k)]
    check("live cutout bytes unchanged", drifted == [], str(drifted[:8]))
    # Refuse helper actually blocks live paths.
    try:
        mq._refuse_outside_trial(mq.LIVE_CUTOUTS / "hyacine_v33_sit.png")
        blocked = False
    except RuntimeError:
        blocked = True
    check("refuse helper blocks live cutouts", blocked)
    readme = mq.MATTE_ROOT / "README.md"
    check("trial README exists", readme.is_file() and "Not wired" in readme.read_text(encoding="utf-8"))
    check("guests were not treated as circle bodies", "robin_v38_sit.png" not in names)


def _rgba(name: str) -> np.ndarray:
    return np.array(Image.open(mq.MATTE_CUTOUTS / name).convert("RGBA"))


def test_hyacine_ica() -> None:
    print("== Hyacine / Ica ==")
    rgba = _rgba("hyacine_v33_sit.png")
    h, w = rgba.shape[:2]
    a = rgba[:, :, 3]
    check("Hyacine trial exists", a.size > 0 and h > 200 and w > 100, f"{w}x{h}")
    # Lap region: Ica sits on her thighs (center-left, mid-lower).
    y0, y1 = int(h * 0.50), int(h * 0.76)
    x0, x1 = int(w * 0.22), int(w * 0.62)
    lap = rgba[y0:y1, x0:x1]
    opaque = int((lap[:, :, 3] > 128).sum())
    rgb = lap[:, :, :3].astype(np.int16)
    pale = rgb.min(axis=2) > 130
    pale_opaque = int(((lap[:, :, 3] > 128) & pale).sum())
    check("Ica lap has opaque pixels", opaque >= 180, f"opaque={opaque} pale={pale_opaque}")
    check("Ica pale pixels remain in the lap", pale_opaque >= 40, f"pale_opaque={pale_opaque}")
    torso = rgba[int(h * 0.22) : int(h * 0.48), int(w * 0.25) : int(w * 0.75), 3]
    check("Hyacine torso/head kept", int((torso > 128).sum()) >= 400, str(int((torso > 128).sum())))
    # Stage/sofa around her should not fill the crop.
    cov = float(a.mean()) / 255.0
    check("Hyacine coverage is not the whole crop", 0.12 <= cov <= 0.78, f"cov={cov:.3f}")


def test_cyrene_sofa() -> None:
    print("== Cyrene sofa ==")
    rgba = _rgba("cyrene_v38_sit.png")
    h, w = rgba.shape[:2]
    a = rgba[:, :, 3]
    r, g, b = rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 2]
    # Cream hair / face — upper center should stay.
    head = a[int(h * 0.12) : int(h * 0.42), int(w * 0.22) : int(w * 0.80)]
    check("Cyrene head/hair kept", int((head > 128).sum()) >= 250, str(int((head > 128).sum())))
    # Pink sofa (high R, weaker G) should be mostly gone.
    sofa_pink = (r > 145) & (b > 110) & (g < 125) & (r > g + 35)
    pink_n = int(sofa_pink.sum())
    pink_kept = int((sofa_pink & (a > 128)).sum())
    leftover = (pink_kept / pink_n) if pink_n >= 30 else 0.0
    check(
        "Cyrene sofa pink mostly gone",
        leftover <= 0.35,
        f"kept {pink_kept}/{pink_n} ({leftover:.2f})",
    )
    # Bottom-left used to be sofa/floor (hair is higher).
    corner = a[int(h * 0.86) :, : max(4, int(w * 0.22))]
    check("Cyrene left sofa strip mostly empty", float(corner.mean()) < 80, f"mean={corner.mean():.1f}")
    cov = float(a.mean()) / 255.0
    check("Cyrene character still present", 0.12 <= cov <= 0.72, f"cov={cov:.3f}")


def test_circle_sits_opaque() -> None:
    print("== circle sits ==")
    for name in SIT_CUTOUTS:
        path = mq.MATTE_CUTOUTS / name
        check(f"{name} trial PNG exists", path.is_file())
        if not path.is_file():
            continue
        im = Image.open(path)
        check(f"{name} is RGBA", im.mode == "RGBA", im.mode)
        arr = np.array(im)
        cov = float(arr[:, :, 3].mean()) / 255.0
        check(f"{name} has a character body", cov >= 0.08, f"cov={cov:.3f}")
        h, w = arr.shape[:2]
        torso = arr[int(h * 0.28) : int(h * 0.62), int(w * 0.28) : int(w * 0.72), 3]
        check(f"{name} torso probe", int((torso > 40).sum()) >= 20, str(int((torso > 40).sum())))
        check(
            f"{name} not in live path as the trial dest",
            path.resolve().parts[-3:] == ("_matte_v2", "cutouts", name)
            or path.resolve().parent == mq.MATTE_CUTOUTS.resolve(),
        )


def main() -> int:
    live_before = hash_tree(mq.LIVE_CUTOUTS)
    test_paths_and_import()
    test_matte_writes_only_trial(live_before)
    test_hyacine_ica()
    test_cyrene_sofa()
    test_circle_sits_opaque()
    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    for name in FAILED:
        print(f"  - {name}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
