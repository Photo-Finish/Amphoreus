"""Test the living-world systems — rumors, echo, teaching spread + stickiness,
relationships, letters (canon-bonded + templates), projects, surges, engine
texture, news-flash lifecycle, echo cooldown, rumor nesting cap.

Pure logic + a simulated multi-day engine loop; no GPU, no LLM calls.
"""
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
wev.spread_rumors(ws, "anaxa", "phainon")
heard = wev.rumors_for(ws, "phainon", limit=3)
assert heard and "Anaxa told me" in heard[0], heard
print("rumors + spread OK:", heard[0][:60])

# --- rumor nesting cap (max 2 hops survive) + fidelity death at hop 3 ---
w2 = WorldState(state_path=str(tmp / "s2.json"))
wev.add_rumor(w2, "tribbie", "a comet crossed the sky over Janusopolis")
wev.spread_rumors(w2, "tribbie", "aglaea")
wev.spread_rumors(w2, "aglaea", "cipher")
wev.spread_rumors(w2, "cipher", "mydei")
nested = w2.rumors["cipher"][0]["text"]
assert nested.count("told me:") == 2, nested  # two hops, no more wrapping
assert len(nested) <= 160, len(nested)
assert not w2.rumors.get("mydei"), "3rd hop dies by fidelity (0.7^3 < 0.35)"
print("rumor nesting cap OK:", nested.count("told me:"), "hops, 3rd hop dies")

# --- visitor echo + cooldown ---
r = wev.visitor_echo(ws, "mydei", "asked about the Kremnos forges")
assert ws.rumors.get("mydei") and r
assert ws.ambient.get("news_flash"), "Keeper flash should be set"
flash0 = len(ws.ambient["news_flash"])
r2 = wev.visitor_echo(ws, "mydei", "asked again, a second time, about forges and oaths")
assert r2 == "", "second echo same day must be silenced"
assert len(ws.ambient["news_flash"]) == flash0, "no duplicate flash"
print("visitor echo + cooldown OK")

# --- teaching spread to adjacent + stickiness ---
os.environ["SANCTUARY_MODE"] = "journey"
ws.set_location("castorice", "Styxia"); ws.set_location("hyacine", "Styxia")
assert set(wev.adjacent(ws, "castorice")) == {"hyacine"}
wev.teaching_rumor(ws, "castorice", "the mathematics of change")
adj = wev.rumors_for(ws, "hyacine", limit=3)
assert adj and "Castorice told me" in adj[0], adj
# first-hand knowledge persists on the taught Heir
casi = wev.learned_for(ws, "castorice")
assert any("taught" in x and "star-stranger" in x for x in casi), casi
# secondhand persists on the adjacent Heir, marked as such
hyac = wev.learned_for(ws, "hyacine")
assert any("told of" in x and "secondhand" in x and "Castorice" in x for x in hyac), hyac
# secondhand is upgraded to first-hand when the visitor teaches it directly
wev.record_learning(ws, "hyacine", "the mathematics of change", source="the star-stranger")
hyac2 = wev.learned_for(ws, "hyacine")
assert any("taught" in x and "star-stranger" in x for x in hyac2), hyac2
# the ledger persists across save/reload
ws.save()
ws2 = WorldState(state_path=str(tmp / "state.json"))
assert wev.learned_for(ws2, "castorice") == casi, "learned must persist"
print("teaching spread + stickiness + persistence OK")

# --- relationships + canon bond ---
wev.adjust_relationship(ws, "mydei", "phainon", 2)
wev.adjust_relationship(ws, "mydei", "phainon", -1)
assert wev.relationship_delta_of(ws, "mydei", "phainon") == 1
blk = wev.relationships_block(ws)
assert blk and "grown closer" in blk
assert wev.canon_bond(ws, "mydei", "phainon"), "mydei~phainon canon-bonded"
assert not wev.canon_bond(ws, "hysilens", "cyrene"), "hysilens~cyrene NOT bonded"
print("relationships + canon_bond OK")

# --- letters (direct + templates) ---
e = wev.compose_letter(ws, "mydei", "tribbie", "I think of your questions.")
assert ws.letters and e["to"] == "tribbie"
lt1 = wev.letter_text(ws, "mydei", "phainon")
lt2 = wev.letter_text(ws, "mydei", "tribbie")
assert lt1 and "Mydei" in lt1 and lt1 != lt2, (lt1, lt2)
print("letters + varied templates OK")

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
os.environ["SANCTUARY_MODE"] = "aftermath"
assert wev.maybe_surge(ws, chance=1.0) is None
os.environ["SANCTUARY_MODE"] = "journey"
print("surge (journey) + aftermath gating OK")

# --- engine: multi-day loop (no LLM) ---
from src.world.world_engine import WorldEngine
eng = WorldEngine(state_path=str(tmp / "engine_state.json"),
                  memory_root=str(tmp / "memory"),
                  chronicle_path=str(tmp / "chronicle"))

# (a) surge darkens the sky ONCE, idempotent across days + restart
eng.world.surge = {"active": True, "remaining": 3, "cities": ["Styxia"]}
eng.world.ambient.setdefault("weather", {})["Styxia"] = "grey and cold"
eng._world_texture("Day A")
eng._world_texture("Day B")
sky = eng.world.ambient["weather"]["Styxia"]
assert sky.count("black tide") == 1, sky
print("surge darken-once OK:", sky)

# (b) news_flash keeps only today's word
today = eng.world.clock.format_short()
eng.world.ambient["news_flash"] = [
    {"text": "yesterday's gossip", "ts": "an older day"},
    {"text": "today's word", "ts": today},
]
eng._world_texture("Day C")
flashes = eng.world.ambient.get("news_flash") or []
assert all(f.get("ts") == today for f in flashes), flashes
print("news_flash daily lifecycle OK")

# (c) a letter travels along a CANON bond even with no drift (mydei~phainon
#     are apart by home; the fresh world has no relationship deltas)
eng.world.relationship_delta = {}
letter = eng._compose_letter("Day D")
assert letter is not None, "canon-bonded distant pair should write"
print("canon-bond letter OK:", letter["from_name"], "->", letter["to_name"])

# (d) texture never crashes and returns lines
random.seed(11)
lines = eng._world_texture("Day E")
assert isinstance(lines, list)
print("engine texture OK — lines:", len(lines))

# --- companion lifecycle: the shared journey ends at the destination ---
w3 = WorldState(state_path=str(tmp / "s3.json"))
w3.set_location("phainon", "Okhema")
w3.begin_travel("phainon", "Aedes Elysiae")
assert w3.is_traveling("phainon")
w3.companions["phainon"] = True
assert w3.is_accompanied("phainon")
while w3.is_traveling("phainon"):
    w3.advance_travel()
assert not w3.is_traveling("phainon")
assert not w3.is_accompanied("phainon"), "companion must clear on arrival"
# an instant move (same city) is not a journey — no companion is set
w3.set_location("phainon", "Okhema")
w3.begin_travel("phainon", "Okhema")
assert not w3.is_traveling("phainon")
print("companion lifecycle OK (cleared on arrival; instant move = no journey)")

# --- gazette data helpers build without error ---
from src.ui_gazette import _load as _gaz_load
_gws, _gch, _gwev = _gaz_load()
assert _gwev is not None and _gch is not None
print("gazette data load OK")

# --- weather classifier: word-aware (a harvest sky is NOT rain) ---
from src.ui_weather import classify as _wx_classify
_WX_CASES = [
    ("golden and quiet, full of memory and ripe grain", "clear"),
    ("a cold drizzle over the harbour", "rain"),
    ("it is raining softly", "rain"),
    ("dark clouds and a rising wind", "cloud"),
    ("heavy cloud cover, grey", "cloud"),
    ("snow is falling on the rooftops", "snow"),
    ("thunder rolling, lightning over the walls", "storm"),
    ("dusk settles, the sky turning violet", "twilight"),
    ("the black tide stirs along the shore", "blacktide"),
    ("warm and bright, a clear sky", "clear"),
    ("still air, the mist curling", "cloud"),
    ("a mild breeze carrying the scent of the looms", "none"),
]
_bad = [(s, e, _wx_classify(s)) for s, e in _WX_CASES if _wx_classify(s) != e]
assert not _bad, _bad
print("weather classifier OK —", len(_WX_CASES), "sky descriptions classified")

print("\nALL VIVID-WORLD TESTS PASSED (incl. refinements)")
