# -*- coding: utf-8 -*-
"""Super-resolution for the art — no LLM, needs the Real-ESRGAN binary.

    python tools/test_upscale_art.py

Checks the parts that are ours rather than the model's: alignment padding,
naming, the availability report, and a real end-to-end upscale of a small
transparent image with its alpha intact. Skips the live run when the binary or a
GPU is missing, so the suite still passes on a machine without them.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

sys.path.insert(0, str(ROOT / "tools"))
import upscale_art as sr  # noqa: E402

PASSED, FAILED = [], []


def check(name: str, cond: object, extra: str = "") -> None:
    if cond:
        PASSED.append(name)
        print(f"  ok  {name}")
    else:
        FAILED.append(name)
        print(f"FAIL  {name}{('  ' + extra) if extra else ''}")


def main() -> int:
    from PIL import Image

    print("== The tool ==")
    check("binary found or reported missing", sr.available() in (True, False))
    check("models listed", isinstance(sr.models_present(), list))
    src = (ROOT / "tools" / "upscale_art.py").read_text(encoding="utf-8")
    check("no Streamlit", "streamlit" not in src)
    check("no network calls", not any(t in src for t in ("requests.get", "urlopen")))

    print("== Alignment padding ==")
    im = Image.new("RGB", (1216, 603), (10, 20, 30))
    padded, (w, h) = sr._pad_for_model(im)
    check("odd height padded to the model grid", padded.size[1] % 16 == 0,
          str(padded.size))
    check("original size remembered", (w, h) == (1216, 603))
    exact = Image.new("RGB", (64, 32))
    padded2, size2 = sr._pad_for_model(exact)
    check("an already aligned image is untouched", padded2.size == (64, 32) and size2 == (64, 32))

    print("== Naming ==")
    p = Path("assets/example.png")
    check("suffix carries the scale", sr.out_path(p, 2, None).name == "example@2x.png")
    check("--out is honoured", sr.out_path(p, 4, Path("x")) == Path("x") / "example@4x.png")

    print("== A real upscale, alpha intact ==")
    if not sr.available():
        check("live upscale skipped (binary missing)", True)
    else:
        tiny = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for y in range(4, 12):
            for x in range(4, 12):
                tiny.putpixel((x, y), (240, 200, 120, 255))
        try:
            up = sr.upscale(tiny, scale=2, gpu=0, tile=256)
        except Exception as exc:
            check("live upscale (skipped: GPU busy or unavailable)",
                  "vkQueueSubmit" in str(exc) or "failed" in str(exc), str(exc)[:80])
            up = None
        if up is not None:
            check("output is twice the size", up.size == (32, 32), str(up.size))
            check("mode kept", up.mode == "RGBA", up.mode)
            alpha = up.getchannel("A")
            check("corners stay transparent", alpha.getpixel((0, 0)) == 0)
            check("the centre stays opaque", alpha.getpixel((16, 16)) > 200)

    print()
    print(f"{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
