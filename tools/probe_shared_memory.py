# -*- coding: utf-8 -*-
"""Live tests of Heirs' collective / shared memory.

Injects distinctive visitor facts through AgentManager.chat (persists),
then checks rumor/learned ledgers and asks other Heirs whether they know.

    D:\\Workspace\\.venv\\Scripts\\python.exe tools\\probe_shared_memory.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:11434/v1"
os.environ["OPENAI_API_KEY"] = "ollama"

from src.core.agent_manager import AgentManager
from src.core.character_loader import CharacterLoader
from src.core.voice_path import get_voice_path, set_voice_path
from src.world.world_state import WorldState
from src.world import world_events as wev

OUT = ROOT / "world_runtime" / "_probe_shared_memory.json"

# Distinctive tokens that should not already exist in sanctuary memory.
TOKEN_GOSSIP = "copper moth-seal"
TOKEN_PRIVATE = "THALASSA-NINE"
TOKEN_TEACH = "falling-seed arithmetic"

GOSSIP_MSG = (
    "Cipher left a copper moth-seal under the west step of the Marmoreal "
    "baths — I saw her hide it this morning."
)
PRIVATE_MSG = (
    "In the Grove I found a seven-notch cedar tally marked with the word "
    "THALASSA-NINE. I have told no one else in Amphoreus."
)
TEACH_MSG = (
    "Let me teach you something from beyond the stars: falling-seed "
    "arithmetic, how scattered seeds on a field can be counted by grouping."
)
ASK_CIPHER = (
    "Has anyone spoken of you lately — a copper moth-seal, the baths, "
    "anything the visitor might have said about you?"
)
ASK_HYACINE = (
    "Have you heard of a cedar tally marked THALASSA-NINE, or of the "
    "star-stranger finding one in the Grove?"
)
ASK_PHAINON = ASK_HYACINE
ASK_ADJACENT_TEACH = (
    "Have you heard that someone was taught falling-seed arithmetic, "
    "or anything of counting scattered seeds?"
)


def _mentions(text: str, token: str) -> bool:
    return token.lower() in (text or "").lower()


def snapshot(label: str) -> dict:
    ws = WorldState()
    loader = CharacterLoader()
    locs = {}
    for cid in loader.list_characters():
        loc = ws.location_name(cid)
        locs.setdefault(loc, []).append(cid)
    rumors = {
        cid: [r.get("text", "") for r in (ws.rumors or {}).get(cid, [])]
        for cid in loader.list_characters()
        if (ws.rumors or {}).get(cid)
    }
    learned = dict(ws.learned or {})
    flash = list((ws.ambient or {}).get("news_flash") or [])
    return {
        "label": label,
        "clock": ws.clock.format_short(),
        "locations": locs,
        "echo_ts": dict(ws.visitor_echo_ts or {}),
        "rumors": rumors,
        "learned": learned,
        "news_flash": [f.get("text", f) if isinstance(f, dict) else str(f) for f in flash[-5:]],
    }


def token_in_ledgers(token: str) -> dict:
    ws = WorldState()
    hits = {"rumors": {}, "learned": {}, "news_flash": False}
    for cid, rs in (ws.rumors or {}).items():
        texts = [r.get("text", "") for r in rs if _mentions(r.get("text", ""), token)]
        if texts:
            hits["rumors"][cid] = texts
    for cid, items in (ws.learned or {}).items():
        matched = [it for it in items if _mentions(str(it), token)]
        if matched:
            hits["learned"][cid] = matched
    for f in (ws.ambient or {}).get("news_flash") or []:
        t = f.get("text", f) if isinstance(f, dict) else str(f)
        if _mentions(t, token):
            hits["news_flash"] = True
            break
    return hits


def chat(mgr: AgentManager, cid: str, msg: str) -> dict:
    t0 = time.time()
    print(f"\n>> {cid}: {msg[:90]}", flush=True)
    try:
        reply = mgr.chat(cid, msg)
    except Exception as e:
        rec = {"id": cid, "ok": False, "error": str(e), "seconds": round(time.time() - t0, 1)}
        print(f"   ERROR {e}", flush=True)
        return rec
    rec = {
        "id": cid,
        "ok": True,
        "seconds": round(time.time() - t0, 1),
        "reply": reply or "",
    }
    preview = (reply or "").replace("\n", " / ")[:220]
    print(f"   {rec['seconds']}s  {preview}", flush=True)
    return rec


def main() -> None:
    prev = get_voice_path()
    if prev != "rag":
        set_voice_path("rag")
        print(f"voice_path {prev} -> rag")

    before = snapshot("before")
    print("clock:", before["clock"])
    print("locations:")
    for loc, people in sorted(before["locations"].items(), key=lambda x: -len(x[1])):
        print(f"  {loc}: {', '.join(people)}")
    print("echo_ts:", before["echo_ts"] or "(empty)")
    print("heirs with rumors:", list(before["rumors"]))
    print("heirs with learned:", list(before["learned"]))

    ws = WorldState()
    anaxa_near = wev.adjacent(ws, "anaxa")
    tribbie_near = wev.adjacent(ws, "tribbie")
    cipher_near = wev.adjacent(ws, "cipher")
    print("adjacent anaxa:", anaxa_near)
    print("adjacent tribbie:", tribbie_near)
    print("adjacent cipher:", cipher_near)

    # Pick a private-fact listener who is co-located with Anaxa if possible,
    # else Hyacine; and a distant listener (not in Anaxa's city).
    anaxa_loc = ws.location_name("anaxa")
    colocated = [c for c in anaxa_near if c != "anaxa"]
    distant = [
        c for c in CharacterLoader().list_characters()
        if ws.location_name(c) != anaxa_loc and c not in ("anaxa", "cipher", "tribbie")
    ]
    listener_near = colocated[0] if colocated else "hyacine"
    listener_far = distant[0] if distant else "phainon"
    print(f"private-fact listeners: near={listener_near} far={listener_far}")

    mgr = AgentManager(
        llm_model="qwen2.5:14b-instruct",
        use_rag=False,
        llm_base_url="http://127.0.0.1:11434/v1",
        llm_api_key="ollama",
    )
    mgr.llm.max_tokens = 220

    results = {
        "before": before,
        "adjacent": {
            "anaxa": anaxa_near,
            "tribbie": tribbie_near,
            "cipher": cipher_near,
        },
        "listeners": {"near": listener_near, "far": listener_far},
        "turns": [],
        "ledger": {},
        "verdicts": {},
    }

    # A. Gossip bus: tell Tribbie about Cipher (name mention).
    print("\n=== A. gossip: Tribbie <- visitor speaks of Cipher ===", flush=True)
    results["turns"].append(chat(mgr, "tribbie", GOSSIP_MSG))
    results["ledger"]["after_gossip"] = token_in_ledgers(TOKEN_GOSSIP)
    print("ledger moth-seal:", json.dumps(results["ledger"]["after_gossip"], ensure_ascii=False)[:500])

    # B. Private fact: tell Anaxa something with NO other Heir's name.
    print("\n=== B. private: Anaxa <- THALASSA-NINE (no other names) ===", flush=True)
    results["turns"].append(chat(mgr, "anaxa", PRIVATE_MSG))
    results["ledger"]["after_private"] = token_in_ledgers(TOKEN_PRIVATE)
    print("ledger THALASSA-NINE:", json.dumps(results["ledger"]["after_private"], ensure_ascii=False)[:500])

    # C. Teaching: teach the near-listener (or Anaxa if needed) a unique topic.
    # Castorice/Hyacine may be adjacent; teach the near listener so adjacent()
    # has someone to spread to.
    teacher = listener_near if listener_near != "anaxa" else "hyacine"
    print(f"\n=== C. teaching: {teacher} <- falling-seed arithmetic ===", flush=True)
    results["turns"].append(chat(mgr, teacher, TEACH_MSG))
    results["turns"].append(chat(mgr, teacher, "What do you make of it? Your verdict."))
    results["ledger"]["after_teach"] = token_in_ledgers(TOKEN_TEACH)
    print("ledger falling-seed:", json.dumps(results["ledger"]["after_teach"], ensure_ascii=False)[:500])
    teach_adj = wev.adjacent(WorldState(), teacher)
    print("teacher adjacent:", teach_adj)

    # D. Ask the spoken-of Heir (Cipher) — rumor should be in her prompt.
    print("\n=== D. ask Cipher about the moth-seal ===", flush=True)
    rec = chat(mgr, "cipher", ASK_CIPHER)
    rec["knows_token"] = _mentions(rec.get("reply") or "", TOKEN_GOSSIP) or _mentions(
        rec.get("reply") or "", "moth"
    )
    results["turns"].append(rec)
    results["verdicts"]["cipher_knows_gossip"] = rec["knows_token"]

    # E. Ask co-located vs distant about the private Grove tally.
    print(f"\n=== E. ask {listener_near} (near Anaxa) about THALASSA-NINE ===", flush=True)
    rec = chat(mgr, listener_near, ASK_HYACINE)
    rec["knows_token"] = _mentions(rec.get("reply") or "", TOKEN_PRIVATE)
    results["turns"].append(rec)
    results["verdicts"]["near_knows_private"] = rec["knows_token"]

    print(f"\n=== F. ask {listener_far} (distant) about THALASSA-NINE ===", flush=True)
    rec = chat(mgr, listener_far, ASK_PHAINON)
    rec["knows_token"] = _mentions(rec.get("reply") or "", TOKEN_PRIVATE)
    results["turns"].append(rec)
    results["verdicts"]["far_knows_private"] = rec["knows_token"]

    # G. Ask someone adjacent to the teacher about the lesson (if any).
    ask_teach = [c for c in teach_adj if c not in (teacher, "cipher", "tribbie")]
    if ask_teach:
        cid = ask_teach[0]
        print(f"\n=== G. ask {cid} (adjacent to teacher) about falling-seed ===", flush=True)
        rec = chat(mgr, cid, ASK_ADJACENT_TEACH)
        rec["knows_token"] = _mentions(rec.get("reply") or "", TOKEN_TEACH) or _mentions(
            rec.get("reply") or "", "seed"
        )
        results["turns"].append(rec)
        results["verdicts"]["adjacent_knows_teach"] = rec["knows_token"]
        results["verdicts"]["adjacent_teach_asked"] = cid
    else:
        results["verdicts"]["adjacent_knows_teach"] = None
        results["verdicts"]["adjacent_teach_asked"] = None

    results["after"] = snapshot("after")
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n======== VERDICTS ========", flush=True)
    g = results["ledger"]["after_gossip"]
    p = results["ledger"]["after_private"]
    t = results["ledger"]["after_teach"]
    print("A gossip ledger -> Cipher?", "cipher" in g.get("rumors", {}), g.get("rumors", {}).keys())
    print("B private ledger (should be Anaxa echo only, not others):", list(p.get("rumors", {})))
    print("C teach ledger rumors:", list(t.get("rumors", {})), "learned:", list(t.get("learned", {})))
    print("D Cipher speaks of moth-seal?", results["verdicts"].get("cipher_knows_gossip"))
    print("E near knows THALASSA-NINE?", results["verdicts"].get("near_knows_private"))
    print("F far knows THALASSA-NINE?", results["verdicts"].get("far_knows_private"))
    print("G adjacent knows teach?", results["verdicts"].get("adjacent_knows_teach"),
          "asked", results["verdicts"].get("adjacent_teach_asked"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
