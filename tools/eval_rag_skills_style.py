"""
eval_rag_skills_style.py — A/B speech-style similarity: RAG with vs without skills.

Fair conditions (same Heir, same scene, RAG on):
  A  non-skilled  — CharacterLoader system prompt + Chroma RAG excerpts
  B  skilled      — A + skills prompt block (baseline or refined)

Judges STYLE & INTONATION only (delivery), using tools/test_dialogue_style.judge_style.

USAGE
-----
  python tools/eval_rag_skills_style.py
  python tools/eval_rag_skills_style.py --heirs phainon,tribbie,mydei --limit 3
  python tools/eval_rag_skills_style.py --variant baseline   # thin original skill rules
  python tools/eval_rag_skills_style.py --variant refined    # voice-first skills inject
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.amp_skills import maybe_inject  # noqa: E402
from src.core.character_loader import CharacterLoader  # noqa: E402
from src.core.context_builder import ContextBuilder  # noqa: E402
from src.core.heir_folders import HEIR_FOLDERS  # noqa: E402
from src.core.llm_client import LLMClient  # noqa: E402
from src.knowledge.kb_builder import CHARACTER_ALIASES  # noqa: E402
from src.knowledge.vector_store import VectorStore  # noqa: E402
from tools.test_dialogue_resemblance import sample_canon_lines, strip_reasoning  # noqa: E402
from tools.test_dialogue_style import (  # noqa: E402
    _trim_to_short,
    build_cases,
    is_degenerate,
    judge_style,
)

REPORT = ROOT / "docs" / "RAG-SKILLS-STYLE-AB.md"


def _gen(llm, system: str, user: str, temp: float) -> str:
    r = llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temp,
        max_tokens=160,
    ).strip()
    r = strip_reasoning(r)
    r = _trim_to_short(r, max_words=28)
    if is_degenerate(r):
        return "..."
    return r


def _build_rag_system(loader, builder, heir_id: str, question: str, *, skills: bool, variant: str) -> str:
    system = loader.build_system_prompt(heir_id)
    if builder is not None:
        system = builder.retrieve_for_chat(
            heir_id, system, question, voice_bias=bool(skills)
        )
    if skills:
        system = maybe_inject(system, heir_id, force=True, variant=variant)
    return system


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--heirs", default="phainon,tribbie,mydei")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--model", default="qwen2.5:14b-instruct")
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--temp", type=float, default=0.2)
    ap.add_argument(
        "--variant",
        choices=("baseline", "refined"),
        default="baseline",
        help="skilled-side block: baseline = original thin skill rules; refined = voice-first",
    )
    ap.add_argument("--report", default=str(REPORT))
    args = ap.parse_args()

    heir_ids = [h.strip() for h in args.heirs.split(",") if h.strip()]
    llm = LLMClient(model=args.model)
    judge_llm = LLMClient(model=args.judge_model or args.model)
    known = llm.list_models()
    needed = {args.model, args.judge_model or args.model}
    missing = sorted(m for m in needed if m not in known)
    if missing:
        print(f"✗ MODEL(S) NOT FOUND: {missing}")
        print("  Fix: powershell -ExecutionPolicy Bypass -File tools\\start_ollama.ps1")
        return 1

    loader = CharacterLoader(str(ROOT / "src" / "characters"))
    builder = None
    chroma = ROOT / ".chroma_db"
    if chroma.is_dir():
        try:
            store = VectorStore(persist_dir=str(chroma), embedding="local")
            builder = ContextBuilder(store, k=5, threshold=0.7)
            print(f"  RAG: Chroma ready at {chroma}")
        except Exception as e:
            print(f"  ! RAG unavailable ({e}) — continuing without Chroma inject")
    else:
        print("  ! no .chroma_db — continuing without Chroma inject")

    print(
        f"A/B RAG skills style — model {args.model}, variant={args.variant}, "
        f"heirs={heir_ids}, limit={args.limit}\n"
    )

    rows = []
    sum_a_style = sum_b_style = 0.0
    sum_a_content = sum_b_content = 0.0
    n = 0
    wins_b = wins_a = ties = 0

    for heir_id in heir_ids:
        folder = ROOT / HEIR_FOLDERS.get(heir_id, heir_id)
        card_path = ROOT / "src" / "characters" / f"{heir_id}.json"
        if not (folder / "personal-memories.md").exists() or not card_path.exists():
            print(f"  ! {heir_id}: missing files")
            continue
        card = json.loads(card_path.read_text(encoding="utf-8"))
        name = card["meta"]["name"]
        stats = ((card.get("speech", {}) or {}).get("style_measured") or {}).get("stats", {})
        try:
            aliases = CHARACTER_ALIASES.get(heir_id, [heir_id])
            exemplars = sample_canon_lines(folder, aliases, 6, max_words=24)
        except Exception:
            exemplars = []

        cases = build_cases(heir_id, args.limit, full=False)
        print(f"—— {name} ({heir_id}) · {len(cases)} cases ——")
        for ctx, anchors, _target in cases:
            # Visitor-facing prompt grounded in the scene (RAG-mode feeling),
            # without the style-gate's HARD STYLE RULES so skills can differ.
            user = (
                f"{ctx}\n\n"
                f"Reply in character as {name}, speaking aloud. "
                f"One short spoken line — no narration."
            )
            sys_a = _build_rag_system(
                loader, builder, heir_id, user, skills=False, variant=args.variant
            )
            sys_b = _build_rag_system(
                loader, builder, heir_id, user, skills=True, variant=args.variant
            )
            try:
                reply_a = _gen(llm, sys_a, user, args.temp)
                reply_b = _gen(llm, sys_b, user, args.temp)
                score_a = judge_style(
                    judge_llm, name, ctx, anchors or exemplars, reply_a, stats=stats
                )
                score_b = judge_style(
                    judge_llm, name, ctx, anchors or exemplars, reply_b, stats=stats
                )
            except Exception as e:
                print(f"  ! case failed: {e}")
                continue

            sa = int(score_a.get("style", 0))
            sb = int(score_b.get("style", 0))
            ca = int(score_a.get("content", 0))
            cb = int(score_b.get("content", 0))
            n += 1
            sum_a_style += sa
            sum_b_style += sb
            sum_a_content += ca
            sum_b_content += cb
            if sb > sa + 3:
                wins_b += 1
                verdict = "B+"
            elif sa > sb + 3:
                wins_a += 1
                verdict = "A+"
            else:
                ties += 1
                verdict = "~"

            print(
                f"  [{verdict}] A style={sa} content={ca} | B style={sb} content={cb}\n"
                f"      A: {reply_a}\n"
                f"      B: {reply_b}"
            )
            rows.append(
                {
                    "heir": heir_id,
                    "name": name,
                    "verdict": verdict,
                    "a_style": sa,
                    "b_style": sb,
                    "a_content": ca,
                    "b_content": cb,
                    "a_reply": reply_a,
                    "b_reply": reply_b,
                    "a_reason": score_a.get("reason", ""),
                    "b_reason": score_b.get("reason", ""),
                }
            )

    if n == 0:
        print("No cases scored.")
        return 1

    avg_a_s = sum_a_style / n
    avg_b_s = sum_b_style / n
    avg_a_c = sum_a_content / n
    avg_b_c = sum_b_content / n
    delta = avg_b_s - avg_a_s

    # "Significantly better" = mean style +≥5 and more wins than losses
    if delta >= 5 and wins_b > wins_a:
        overall = "SKILLED_BETTER"
        summary = (
            f"Skilled ({args.variant}) is significantly better on speech-style "
            f"(Δ style {delta:+.1f}, B wins {wins_b} / A wins {wins_a} / ties {ties})."
        )
    elif delta <= -5 and wins_a > wins_b:
        overall = "NONSKILLED_BETTER"
        summary = (
            f"Non-skilled is better on speech-style "
            f"(Δ style {delta:+.1f}, B wins {wins_b} / A wins {wins_a} / ties {ties})."
        )
    else:
        overall = "NO_CLEAR_WIN"
        summary = (
            f"No clear style win for skilled ({args.variant}) "
            f"(Δ style {delta:+.1f}, B wins {wins_b} / A wins {wins_a} / ties {ties})."
        )

    print("\n=== RESULT ===")
    print(f"cases={n}  A avg style={avg_a_s:.1f} content={avg_a_c:.1f}")
    print(f"          B avg style={avg_b_s:.1f} content={avg_b_c:.1f}  Δstyle={delta:+.1f}")
    print(f"wins: A={wins_a} B={wins_b} ties={ties}")
    print(f"verdict: {overall}")
    print(summary)

    report_path = Path(args.report)
    lines = [
        "# RAG skills vs non-skills — speech-style A/B",
        "",
        f"*Model `{args.model}` · skilled variant `{args.variant}` · cases {n}*",
        "",
        f"**Verdict:** `{overall}`",
        "",
        summary,
        "",
        "| side | avg style | avg content | case wins |",
        "|---|---:|---:|---:|",
        f"| A non-skilled | {avg_a_s:.1f} | {avg_a_c:.1f} | {wins_a} |",
        f"| B skilled ({args.variant}) | {avg_b_s:.1f} | {avg_b_c:.1f} | {wins_b} |",
        f"| ties | | | {ties} |",
        "",
        "## Cases",
        "",
    ]
    for r in rows:
        lines.append(
            f"### {r['name']} [{r['verdict']}] — A {r['a_style']}/{r['a_content']} vs "
            f"B {r['b_style']}/{r['b_content']}"
        )
        lines.append(f"- A: {r['a_reply']}")
        lines.append(f"- B: {r['b_reply']}")
        lines.append("")

    lines.extend(
        [
            "## How to toggle skills in RAG mode",
            "",
            "- Control Panel → **Skills aid (optional)**",
            "- Env: `AMP_SKILLS=1` (on) / `AMP_SKILLS=0` (off)",
            "- File: `world_runtime/amp_skills.json` → `{\"enabled\": true}`",
            "- Default: **OFF**",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {report_path}")

    # Machine-readable sidecar for agents
    sidecar = report_path.with_suffix(".json")
    sidecar.write_text(
        json.dumps(
            {
                "verdict": overall,
                "variant": args.variant,
                "n": n,
                "avg_a_style": avg_a_s,
                "avg_b_style": avg_b_s,
                "delta_style": delta,
                "wins_a": wins_a,
                "wins_b": wins_b,
                "ties": ties,
                "summary": summary,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
