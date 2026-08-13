"""Test the living-world systems (rumors, echo, teaching spread, relationships,
letters, projects, surges, engine texture) — pure logic, no GPU."""
import os, random, sys, tempfile
from pathlib import Path
sys.path.insert(0, r"D:\Workspace\Amphoreus")

from src.world.world_state import WorldState
from src.world import world_events as wev

tmp = Path(tempfile.mkdtemp(prefix="vivid-"))
ws = WorldState(state_path=str(tmp / "state.json"))

# --- rumors ---
wev.add_rumor(ws, "anaxa", "the star-stranger spoke of strange knowledge")
assert ws.rumors["anaxa"][0]["fidelity"] == 1.0
# spread anaxa -> phainon (they're in different cities; simulate adjacency)
wev.spread_rumors(ws, "anaxa", "phainon")
heard = wev.rumors_for(ws, "phainon", limit=3)
assert heard and "Anaxa told me" in heard[0], heard
print("rumors + spread OK:", heard[0][:60])

# --- visitor echo ---
r = wev.visitor_echo(ws, "mydei", "asked about the Kremnos forges")
assert ws.rumors.get("mydei") and r
assert ws.ambient.get("news_flash"), "Keeper flash should be set"
print("visitor echo OK")

# --- teaching spread to adjacent ---
os.environ["SANCTUARY_MODE"] = "journey"
# place castorice + hyacine together in Styxia
ws.set_location("castorice", "Styxia"); ws.set_location("hyacine", "Styxia")
assert set(wev.adjacent(ws, "castorice")) == {"hyacine"}
wev.teaching_rumor(ws, "castorice", "the mathematics of change")
adj = wev.rumors_for(ws, "hyacine", limit=3)
assert adj and "Castorice told me" in adj[0], adj
print("teaching spread to adjacent OK")

# --- relationships ---
wev.adjust_relationship(ws, "mydei", "phainon", 2)
wev.adjust_relationship(ws, "mydei", "phainon", -1)
assert wev.relationship_delta_of(ws, "mydei", "phainon") == 1
blk = wev.relationships_block(ws)
assert blk and "grown closer" in blk
print("relationships OK")

# --- letters ---
e = wev.compose_letter(ws, "mydei", "tribbie", "I think of your questions.")
assert ws.letters and e["to"] == "tribbie"
print("letters OK")

# --- projects ---
random.seed(7)
prog = wev.project_progress(ws, "anaxa")
miles = wev.advance_projects(ws)
assert wev.project_progress(ws, "anaxa") >= prog
assert isinstance(miles, list)
pinfo = wev.project_info(ws, "anaxa")
assert pinfo and "title" in pinfo
print("projects OK:", pinfo["title"])

# --- surges (journey) ---
random.seed(3)
s = wev.maybe_surge(ws, chance=1.0)
assert s and s["active"], s
assert wev.surge_active(ws) and wev.surge_text(ws)
wev.advance_surge(ws); wev.advance_surge(ws); wev.advance_surge(ws)
assert not wev.surge_active(ws)
print("surge (journey) OK")

# --- surges (aftermath = none) ---
os.environ["SANCTUARY_MODE"] = "aftermath"
assert wev.maybe_surge(ws, chance=1.0) is None
os.environ["SANCTUARY_MODE"] = "journey"
print("surge (aftermath gated) OK")

# --- engine texture (no LLM calls) ---
from src.world.world_engine import WorldEngine
eng = WorldEngine(state_path=str(tmp / "engine_state.json"),
                  memory_root=str(tmp / "memory"),
                  chronicle_path=str(tmp / "chronicle"))
random.seed(11)
lines = eng._world_texture("Year 4932 · Month of Weaving · Day 1 · Lucid Hour")
assert isinstance(lines, list)
print("engine texture OK — lines:", len(lines))
for l in lines[:4]:
    print("   ", l)

print("\nALL VIVID-WORLD TESTS PASSED")
