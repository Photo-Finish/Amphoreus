"""Quick smoke test for map_data + schedules + world_state travel.

Verifies the geography, the weekly routines, and the commuting-time mechanics
(travel state) of the little Amphoreus.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.world import schedules as s
from src.world.world_state import WorldState

print("--- schedule sample ---")
for cid in ["aglaea", "phainon", "tribbie", "mydei", "cyrene", "hyacine"]:
    p, a = s.scheduled_entry(cid, 1, 0)
    print(f"{cid:12s} Day1 Entry: {a}  [{p}]")

print()
print("--- Phainon week (place grid) ---")
for d, row in enumerate(s.week_overview("phainon"), 1):
    print(f"Day{d}: " + " | ".join(f"{x[:12]:12s}" for x in row))

print()
print("--- travel mechanics: phainon at Aedes Elysiae -> Okhema ---")
ws = WorldState(os.path.join("world_runtime", "_test_state.json"))
ws.agent_location["phainon"] = "Aedes Elysiae"
print("phainon at:", ws.location_name("phainon"), "| traveling:", ws.is_traveling("phainon"))
ws.begin_travel("phainon", "Okhema")
print("after begin_travel -> traveling:", ws.is_traveling("phainon"), ws.travel_info("phainon"))
for i in range(4):
    arr = ws.advance_travel()
    print(f"  day+{i+1}: arrivals={arr} traveling={ws.is_traveling('phainon')} loc={ws.location_name('phainon')}")

print()
print("--- same-city travel is instant ---")
ws2 = WorldState(os.path.join("world_runtime", "_test_state.json"))
ws2.agent_location["aglaea"] = "Okhema"
ws2.begin_travel("aglaea", "Dawncloud")
print("aglaea Okhema->Dawncloud traveling:", ws2.is_traveling("aglaea"), "loc:", ws2.location_name("aglaea"))

print()
print("--- agents_at excludes travelers ---")
ws3 = WorldState(os.path.join("world_runtime", "_test_state.json"))
ws3.agent_location["phainon"] = "Aedes Elysiae"
ws3.agent_location["cyrene"] = "Aedes Elysiae"
ws3.begin_travel("phainon", "Okhema")
print("at Aedes Elysiae:", ws3.agents_at("Aedes Elysiae"), "(phainon traveling, should be excluded)")
print("travelers:", ws3.travelers())
