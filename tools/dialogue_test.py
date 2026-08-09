"""
dialogue_test.py — run small multi-Heir dialogue scenarios and show what each
Heir newly remembers about them.

Three scenarios are simulated (round-robin free exchange, in character, with
the canon relationship web as hints):
  1. Aglaea & Anaxa
  2. Anaxa & Hyacine & Phainon & Castorice
  3. Hysilens & Cerydra

After each dialogue every participant keeps a world memory in their
memories.jsonl (the same mechanism the world engine uses for encounters).
The script prints the transcript and the NEW memory entries per Heir.

USAGE:
    python tools/dialogue_test.py [--heirs aglaea,anaxa] [--turns N] [--scenario 1|2|3]
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.core.character_loader import CharacterLoader  # noqa: E402
from src.core.llm_client import LLMClient  # noqa: E402
from src.core.memory_store import MemoryStore  # noqa: E402
from src.core.relationships import get_relationships  # noqa: E402

SCENARIOS = [
    {
        "name": "Scenario 1 — Aglaea & Anaxa",
        "heirs": ["aglaea", "anaxa"],
        "turns": 3,
        "opening": "In Okhema's golden halls, the weaver of fates meets the scholar of the Grove.",
    },
    {
        "name": "Scenario 2 — Anaxa & Hyacine & Phainon & Castorice",
        "heirs": ["anaxa", "hyacine", "phainon", "castorice"],
        "turns": 2,
        "opening": "At the Grove of Epiphany, the teacher gathers with his students after the long war.",
    },
    {
        "name": "Scenario 3 — Hysilens & Cerydra",
        "heirs": ["hysilens", "cerydra"],
        "turns": 3,
        "opening": "In the throne room of Okhema, the Imperator summons her Dux Gladiorum.",
    },
]


def relationship_hints(loader, heir_id: str, present: list) -> str:
    """Canon roles of the other Heirs present, from the relationships registry."""
    rels = {r["name"].lower(): r for r in get_relationships(heir_id)}
    hints = []
    for cid in present:
        if cid == heir_id:
            continue
        name = loader.load(cid)["meta"]["name"]
        rel = rels.get(name.lower())
        if rel:
            hints.append(f"- {name} is here — {rel['role']} to you.")
    return "\n".join(hints)


def speak(loader, llm, heir_id: str, present: list, transcript: list) -> str:
    """One Heir's free in-character reply to the transcript so far."""
    name = loader.load(heir_id)["meta"]["name"]
    system = (
        loader.build_system_prompt(heir_id)
        + "\n\nYou are speaking with fellow Heirs, freely and in your own voice."
    )
    hints = relationship_hints(loader, heir_id, present)
    user = (
        (("Those present and your relation to them:\n" + hints + "\n") if hints else "")
        + "What is being said around you:\n"
        + "\n".join(transcript)
        + "\n\nWhat do you say or do in reply? Reply briefly, in character (1–3 sentences)."
    )
    reply = llm.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.85,
        max_tokens=140,
    ).strip()
    # the model sometimes restates its own name — strip that so we format it once
    reply = re.sub(rf"^\s*(?:\*\*)?{re.escape(name)}(?:\*\*)?\s*:\s*", "", reply).strip()
    reply = re.sub(r"^\s*\*\*+\s*", "", reply).strip()   # stray leading bold markers
    reply = re.sub(r"\s*\*\*+\s*$", "", reply).strip()   # stray trailing bold markers
    return f"**{name}:** {reply}"


def run_scenario(loader, llm, memory, scenario: dict):
    heirs = scenario["heirs"]
    names = {h: loader.load(h)["meta"]["name"] for h in heirs}
    others_of = {h: ", ".join(names[o] for o in heirs if o != h) for h in heirs}
    before = {h: memory.memory_count(h) for h in heirs}

    transcript = []
    if scenario.get("opening"):
        transcript.append(f"*(scene) {scenario['opening']}*")

    print(f"\n{'=' * 72}\n{scenario['name']}\n{'=' * 72}")
    for turn in range(scenario["turns"]):
        for heir in heirs:
            line = speak(loader, llm, heir, heirs, transcript)
            transcript.append(line)
            print(line)

    # each participant keeps a world memory of the exchange (as the world engine does),
    # anchored on their OWN part of the dialogue so each memory differs per Heir.
    lines = [ln for ln in transcript if not ln.startswith("*(scene)")]
    for heir in heirs:
        tag = f"**{names[heir]}:**"
        start = next((i for i, ln in enumerate(lines) if ln.startswith(tag)), 0)
        excerpt = " ".join(lines[start:]).replace("**", "").replace("\n", " ").strip()
        if len(excerpt) > 240:
            excerpt = excerpt[:240] + "…"
        memory.add_memory(
            heir,
            mtype="world",
            content=f"Exchanged words with {others_of[heir]}: {excerpt}",
            importance=2,
        )

    print(f"\n--- NEW MEMORIES (memories.jsonl) ---")
    for heir in heirs:
        new = memory.get_memories(heir, limit=memory.memory_count(heir) - before[heir])
        print(f"  {names[heir]} ({heir}): +{len(new)} memory/ies")
        for m in new:
            print(f"      [{m['mtype']}, imp {m['importance']}] {m['content'][:220]}")


def main():
    ap = argparse.ArgumentParser(description="Run multi-Heir dialogue scenarios.")
    ap.add_argument("--scenario", type=int, default=0, help="1, 2 or 3 (0 = all three)")
    ap.add_argument("--heirs", default="", help="override: comma-separated ids")
    ap.add_argument("--turns", type=int, default=0, help="override turns (0 = scenario default)")
    ap.add_argument("--model", default="qwen2.5:14b-instruct", help="LLM model")
    args = ap.parse_args()

    # server check
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as r:
            json.loads(r.read().decode("utf-8", "replace"))
    except Exception as err:
        print(f"Ollama not reachable: {err}\nStart it with: powershell -File tools/start_ollama.ps1")
        return 1

    loader = CharacterLoader(str(ROOT / "src" / "characters"))
    llm = LLMClient(model=args.model)
    memory = MemoryStore(ROOT)

    scenarios = SCENARIOS if args.scenario == 0 else [SCENARIOS[args.scenario - 1]]
    if args.heirs:
        custom = [h.strip() for h in args.heirs.split(",") if h.strip()]
        scenarios = [{"name": f"Custom — {', '.join(custom)}", "heirs": custom,
                      "turns": args.turns or 2, "opening": "Fellow Heirs meet in Amphoreus."}]
    if args.turns:
        for s in scenarios:
            s["turns"] = args.turns

    for scenario in scenarios:
        run_scenario(loader, llm, memory, scenario)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
