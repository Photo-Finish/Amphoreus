# -*- coding: utf-8 -*-
"""A/B the art appreciation prompt — old invitation vs the taste procedure.

    python tools/aesthetic_ab.py                        # default picture, 4 Heirs
    python tools/aesthetic_ab.py --image assets/galgame/ground/bg-vortex-of-genesis.jpg
    python tools/aesthetic_ab.py --heirs mydei,anaxa,hyacine --model qwen2.5vl:7b

Both arms use the same Heir, the same system prompt and the same picture; only the
instruction differs. That isolates what this change actually claims: that a
procedure produces specific, opinionated readings where an invitation produces
warm generalities.

Writes a markdown report (default `docs/AESTHETIC-AB.md`) with both answers, the
banned-phrase count, whether a verdict was reached, whether the Heir named
anything they would change, and how far the Heirs' answers are from each other —
the last one is the number that matters: if every Heir says the same thing, the
taste model is not doing its job.

Needs Ollama with a vision model. Nothing leaves the machine.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.core import aesthetic  # noqa: E402

DEFAULT_IMAGE = ROOT / "assets" / "galgame" / "ground" / "bg-vortex-of-genesis.jpg"
DEFAULT_HEIRS = "mydei,anaxa,hyacine,castorice"
ASK = "What do you make of this?"

STOP = set("""a an the and or but if then than that this these those of in on at to from by for with
without into over under is are was were be been being it its it's you your yours i my me we our they
their he she his her not no so as do does did can could would should will shall may might must have
has had more most much very just also there here what which who whom when where why how""".split())


def tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z']+", text.lower())
    return {w for w in words if len(w) > 3 and w not in STOP}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(len(a | b), 1)


def verdict_of(text: str) -> str:
    low = text.lower()
    for v in aesthetic.VERDICTS:
        if v.replace("i do not", "i don't") in low or v in low:
            return v
    # tolerate a paraphrased commitment
    for near, label in (
        ("holds me", "it holds me"), ("pleases me", "it pleases me"),
        ("leaves me cold", "it leaves me cold"), ("offends me", "it offends me"),
        ("unsettles me", "it unsettles me"), ("don't know", "I do not know yet"),
    ):
        if near in low:
            return label
    return ""


def named_change(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in ("would change", "i'd change", "change nothing",
                                  "would not change", "nothing to change",
                                  "would take out", "would add"))


def banned_hits(text: str) -> list[str]:
    low = text.lower()
    return [b for b in aesthetic.BANNED if b in low]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="A/B the appreciation prompt.")
    ap.add_argument("--image", default=str(DEFAULT_IMAGE))
    ap.add_argument("--heirs", default=DEFAULT_HEIRS)
    ap.add_argument("--model", default=os.environ.get("VISION_MODEL", "qwen2.5vl:7b"))
    ap.add_argument("--out", default=str(ROOT / "docs" / "AESTHETIC-AB.md"))
    args = ap.parse_args(argv)

    image_path = Path(args.image)
    if not image_path.is_file():
        print(f"no such image: {image_path}")
        return 1
    raw = image_path.read_bytes()
    mime = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    data_uri = f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"

    from src.core.character_loader import CharacterLoader
    from src.core.llm_client import LLMClient

    loader = CharacterLoader()
    llm = LLMClient(model=args.model, vision_model=args.model)

    rows = []
    for cid in [c.strip() for c in args.heirs.split(",") if c.strip()]:
        system = loader.build_system_prompt(cid)
        os.environ["AMP_AESTHETIC_TASTE"] = "0"
        try:
            legacy = aesthetic.vision_brief(cid)
        finally:
            os.environ.pop("AMP_AESTHETIC_TASTE", None)
        modern = aesthetic.vision_brief(cid)

        out = {}
        for arm, brief in (("old", legacy), ("new", modern)):
            try:
                text = llm.chat_vision(
                    text=brief + ASK,
                    image_data_uri=data_uri,
                    messages=[{"role": "system", "content": system}],
                    temperature=0.6,
                )
            except Exception as exc:
                text = f"[error: {exc.__class__.__name__}: {exc}]"
            out[arm] = str(text or "").strip()
        rows.append({"cid": cid, **out})

    # ---- metrics
    def summarise(arm: str) -> dict:
        texts = [r[arm] for r in rows]
        verdicts = [verdict_of(t) for t in texts]
        pairs = [jaccard(tokens(texts[i]), tokens(texts[j]))
                 for i in range(len(texts)) for j in range(i + 1, len(texts))]
        return {
            "banned": sum(len(banned_hits(t)) for t in texts),
            "verdicts": sum(1 for v in verdicts if v),
            "distinct_verdicts": len({v for v in verdicts if v}),
            "changes": sum(1 for t in texts if named_change(t)),
            "overlap": (sum(pairs) / len(pairs)) if pairs else 0.0,
            "words": sum(len(t.split()) for t in texts) / max(len(texts), 1),
        }

    old_m, new_m = summarise("old"), summarise("new")

    lines = [
        "# Appreciation A/B — old invitation vs taste procedure",
        "",
        f"*Generated: {datetime.date.today().isoformat()} · model "
        f"`{args.model}` · picture `{image_path.name}`*",
        "",
        "Same Heir, same system prompt, same picture. Only the instruction differs.",
        "",
        "| Measure | old invitation | taste procedure |",
        "|---|---:|---:|",
        f"| banned stock phrases | {old_m['banned']} | {new_m['banned']} |",
        f"| answers that reached a verdict | {old_m['verdicts']}/{len(rows)} | {new_m['verdicts']}/{len(rows)} |",
        f"| distinct verdicts across the cast | {old_m['distinct_verdicts']} | {new_m['distinct_verdicts']} |",
        f"| answers naming a change | {old_m['changes']}/{len(rows)} | {new_m['changes']}/{len(rows)} |",
        f"| cross-Heir word overlap (lower = more distinct) | {old_m['overlap']:.2f} | {new_m['overlap']:.2f} |",
        f"| average length (words) | {old_m['words']:.0f} | {new_m['words']:.0f} |",
        "",
        "The last two matter most: overlap near 1.0 means the thirteen have one voice,"
        " which is the failure this change targets.",
        "",
    ]
    for row in rows:
        profile = aesthetic.profile(row["cid"]) or {}
        leans = ", ".join(p for _k, p, s in aesthetic.axis_readings(row["cid"])[:3])
        lines += [f"## {row['cid']}", "", f"*leans: {leans}*", ""]
        for arm, label in (("old", "Old invitation"), ("new", "Taste procedure")):
            text = row[arm] or "_(empty)_"
            lines += [f"**{label}** — verdict: {verdict_of(text) or '—'}, "
                      f"change named: {'yes' if named_change(text) else 'no'}, "
                      f"banned: {', '.join(banned_hits(text)) or 'none'}", "", text, ""]
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"  old: banned {old_m['banned']}, verdicts {old_m['verdicts']}/{len(rows)}, "
          f"overlap {old_m['overlap']:.2f}")
    print(f"  new: banned {new_m['banned']}, verdicts {new_m['verdicts']}/{len(rows)}, "
          f"overlap {new_m['overlap']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
