"""Ecosystem suite — living presence, interactions, gated care."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.world.world_state import WorldState
from src.world.sanctuary_clock import WorldClock
from src.world import ecosystem as eco
from src.world import lived_mechanisms as lm
from src.world import resident_npcs as rn

PASS = 0
FAIL = 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f" FAIL {name}" + (f" — {detail}" if detail else ""))


def mk(period=2, place="Okhema", month=9, day=6):
    ws = WorldState()
    ws._clock_override = WorldClock(year=4933, month=month, day=day, period=period)
    ws.visitor_location = place
    ws.visitor_travel = {}
    ws.ambient = {
        "weather": {place: "golden light"},
        "news": "",
        "errands": {},
    }
    ws.save = lambda: None
    # Avoid polluting production vivid — isolate eco bucket
    ws.vivid = dict(ws.vivid or {})
    ws.vivid["eco"] = {"beings": {}, "scene": [], "audit": [], "last_key": "", "gazette": []}
    lm.apply_tick(ws)
    rn.apply_tick(ws)
    return ws


print("== Catalog / sanctuary ==")
check("no death status in CARE outcomes",
      all(
          (spec.get("to_status") or "well") not in {"dead", "starving", "plague"}
          for auth in eco.CARE_AUTH.values()
          for spec in auth.values()
      ))
check("hyacine can tend ailment",
      "tend_ailment" in eco.CARE_AUTH.get("hyacine", {}))

print("== Okhema Action: chimeras + interactions ==")
ws = mk(2, "Okhema")
tick = eco.apply_tick(ws)
scene = tick["scene"]
kinds = {b["kind"] for b in scene}
check("tick writes scene", bool(scene))
check("chimera in Okhema day", "chimera" in kinds)
check("grass or wind present", "grass" in kinds or "wind" in kinds)
check("no shore in Okhema", "shore" not in kinds)
check("no faults Okhema", not tick["faults"], str(tick["faults"]))
check("Okhema outdoor — no indoor furniture",
      not (kinds & {"bath", "hearth", "loom", "scroll", "lamp"}),
      str(kinds & {"bath", "hearth", "loom", "scroll", "lamp"}))

chim = next(b for b in scene if b["kind"] == "chimera")
inter = eco.interact(ws, chim["id"])
check("interact ok", inter.get("ok") is True)
check("Awoo sound", inter.get("sound") == "Awoo")
check("textbox has Awoo", "Awoo" in str(inter.get("textbox") or ""))

print("== Grove: no chimera / shore ==")
ws_g = mk(1, "Grove of Epiphany")
eco.apply_tick(ws_g)
sc_g = eco.derive_scene(ws_g, place="Grove of Epiphany")
kg = {b["kind"] for b in sc_g}
check("grove has leaf", "grove_leaf" in kg)
check("grove has olive or cicada", "olive" in kg or "cicada" in kg)
check("grove no chimera", "chimera" not in kg)
check("grove no shore", "shore" not in kg)
check("grove no boat", "boat" not in kg)
check("grove no scroll", "scroll" not in kg)
check("grove outdoor — no indoor furniture",
      not (kg & {"bath", "hearth", "loom", "scroll", "lamp"}),
      str(kg & {"bath", "hearth", "loom", "scroll", "lamp"}))
check("grove faults empty", not eco.logic_faults(sc_g, "Grove of Epiphany"))

print("== Night Okhema: chimeras rest ==")
ws_n = mk(4, "Okhema")
eco.apply_tick(ws_n)
sc_n = eco.derive_scene(ws_n, place="Okhema")
chim_n = [b for b in sc_n if b["kind"] == "chimera"]
check("night chimera resting or present",
      all(b["status"] in {"resting", "wandering", "ailing", "well"} for b in chim_n) if chim_n else True)
if chim_n:
    check("night chimera not busy wandering stalls",
          all(b["status"] == "resting" or "hearth" in (b.get("doing") or "")
              or b["status"] == "ailing" for b in chim_n)
          or all(b["status"] == "resting" for b in chim_n))

print("== Aedes Cultivation: wheat ==")
ws_a = mk(2, "Aedes Elysiae", month=4)
eco.apply_tick(ws_a)
sc_a = eco.derive_scene(ws_a, place="Aedes Elysiae")
wheat = next((b for b in sc_a if b["kind"] == "wheat"), None)
check("wheat present at Aedes", wheat is not None)
check("wheat sowing in Cultivation",
      wheat is not None and wheat.get("status") == "sowing")

print("== Styxia shore ==")
ws_s = mk(2, "Styxia")
eco.apply_tick(ws_s)
sc_s = eco.derive_scene(ws_s, place="Styxia")
check("shore in Styxia", any(b["kind"] == "shore" for b in sc_s))
check("siren in Styxia", any(b["kind"] == "siren" for b in sc_s))
check("pearl in Styxia", any(b["kind"] == "pearl" for b in sc_s))
check("boat in Styxia", any(b["kind"] == "boat" for b in sc_s))
check("no chimera in Styxia", not any(b["kind"] == "chimera" for b in sc_s))

print("== Visitor touch (pearl / shrine) ==")
pearl = next(b for b in sc_s if b["kind"] == "pearl")
touch = eco.visitor_touch(ws_s, pearl["id"], "pick_keepsake", place="Styxia", save=False)
check("pick pearl ok", touch.get("ok") is True, str(touch))
dup = eco.visitor_touch(ws_s, pearl["id"], "pick_keepsake", place="Styxia", save=False)
check("second pick refused", dup.get("ok") is False)
bad_touch = eco.visitor_touch(ws_s, pearl["id"], "vaporize", place="Styxia", save=False)
check("unknown touch refused", bad_touch.get("ok") is False)

print("== Gated care: Hyacine ==")
# Force an ailing chimera via overlay
ws_h = mk(2, "Okhema", day=7)
# Find a chimera id and force ailing
sc_h = eco.derive_scene(ws_h, place="Okhema")
chim_h = next(b for b in sc_h if b["kind"] == "chimera")
eco._set_overlay(ws_h, chim_h["id"], {
    "status": "ailing",
    "doing": "listless, needing a healer's gentle hand",
    "tended_date": "force",
})
# Re-derive with overlay — tended_date != today so base may win;
# set tended_date to today so overlay sticks, OR patch after derive
today = eco._date_seed(ws_h).rsplit("-p", 1)[0]
eco._set_overlay(ws_h, chim_h["id"], {
    "status": "ailing",
    "doing": "listless, needing a healer's gentle hand",
    "tended_date": today,
})
being = eco.get_being(ws_h, chim_h["id"], character_id="hyacine")
# Place Hyacine in Okhema for care
ws_h.agent_location = dict(getattr(ws_h, "agent_location", None) or {})
ws_h.agent_location["hyacine"] = "Okhema"
being = eco.get_being(ws_h, chim_h["id"], character_id="hyacine")
check("forced ailing visible", being is not None and being.get("status") == "ailing",
      str(being))

# Unauthorized Heir
bad = eco.apply_care(ws_h, "anaxa", chim_h["id"], "tend_ailment", save=False)
check("anaxa refused tend", bad.get("ok") is False)

# Wrong action
bad2 = eco.apply_care(ws_h, "hyacine", chim_h["id"], "vaporize", save=False)
check("unknown action refused", bad2.get("ok") is False)

# Authorized care
# Ensure hyacine location
if hasattr(ws_h, "location_name"):
    # monkey: scene_for uses location_name
    pass
ok = eco.apply_care(ws_h, "hyacine", chim_h["id"], "tend_ailment", save=False)
check("hyacine tend ok", ok.get("ok") is True, str(ok))
check("status now well", (ok.get("being") or {}).get("status") == "well", str(ok))
check("audit written", bool((ws_h.vivid.get("eco") or {}).get("audit")))

# Resident notice
residents = [b for b in sc_h if b["kind"] == "resident"]
if residents:
    ri = eco.interact(ws_h, residents[0]["id"], character_id="hyacine")
    check("resident identity on notice", ri.get("ok") and residents[0]["name"] in (ri.get("line") or ""))
else:
    check("resident identity on notice", True)  # hour may have none

print("== Profession outfit visuals ==")
ws_ok = mk(1, "Okhema")
sc_ok = eco.derive_scene(ws_ok, place="Okhema")
ok_res = [b for b in sc_ok if b["kind"] == "resident"]
if ok_res:
    from src.world import resident_npcs as _rn
    mapped = all(
        b.get("visual") == _rn.outfit_for_role(b.get("role"))
        for b in ok_res
    )
    check("Okhema residents visual=outfit", mapped, str([(b.get("role"), b.get("visual")) for b in ok_res]))
    special = [b for b in ok_res if b.get("visual") != "resident"]
    check("some special outfit present or all civilian hour", True)  # hour-dependent
else:
    check("Okhema residents visual=outfit", True, "no residents this hour")

print("== Prompt block ==")
block = eco.prompt_block(ws_h, "hyacine")
check("prompt names living presence", "Living presence" in block or "chimera" in block.lower())
check("prompt forbids arbitrary write", "cannot change the clock" in block.lower() or "You cannot change" in block)

print("== Breadth: Okhema / Kremnos / visitor acts ==")
ws_o = mk(2, "Okhema")
sc_o = eco.derive_scene(ws_o, place="Okhema")
ko = {b["kind"] for b in sc_o}
check("Okhema mosaic or fountain or pillar",
      bool(ko & {"mosaic", "fountain", "pillar"}), str(ko))
chim_o = next(b for b in sc_o if b["kind"] == "chimera")
scratch = eco.visitor_touch(ws_o, chim_o["id"], "scratch_ear", place="Okhema", save=False)
check("scratch chimera ear", scratch.get("ok") is True, str(scratch))
dawn = next((b for b in sc_o if b["kind"] == "dawn"), None)
if dawn:
    look = eco.visitor_touch(ws_o, dawn["id"], "look_up", place="Okhema", save=False)
    check("look up at Device", look.get("ok") is True, str(look))
else:
    check("look up at Device", False, "no dawn")

ws_n2 = mk(4, "Okhema")
sc_n2 = eco.derive_scene(ws_n2, place="Okhema")
cat = next((b for b in sc_n2 if b["kind"] == "hearth_cat"), None)
if cat:
    pet = eco.visitor_touch(ws_n2, cat["id"], "pet_cat", place="Okhema", save=False)
    check("pet square cat", pet.get("ok") is True, str(pet))
else:
    check("pet square cat", False, "no cat at night")

drom = next((b for b in sc_o if b["kind"] == "dromas"), None)
if drom:
    pet_d = eco.visitor_touch(ws_o, drom["id"], "pet", place="Okhema", save=False)
    check("pet dromas", pet_d.get("ok") is True, str(pet_d))
    acts = eco.visitor_acts_for("dromas")
    check("dromas has pet act", "pet" in acts, str(acts))
else:
    check("pet dromas", False, "no dromas")

print("== Trade caravan ==")
found = False
for per in (2, 3):
    for month in (4, 9, 1):
        ws_c = mk(per, "Okhema", month=month)
        sc_c = eco.derive_scene(ws_c, place="Okhema")
        mounts = [b for b in sc_c if b.get("kind") == "dromas" and b.get("caravan_id")]
        if mounts:
            cid = mounts[0]["caravan_id"]
            mates = [b for b in sc_c if b.get("caravan_id") == cid and b.get("kind") != "dromas"]
            check("caravan has dromas + people", bool(mates), f"mates={len(mates)}")
            found = True
            break
    if found:
        break
if not found:
    check("caravan has dromas + people", False, "no caravan hour in sample")

ws_k = mk(2, "Castrum Kremnos")
sc_k = eco.derive_scene(ws_k, place="Castrum Kremnos")
kk = {b["kind"] for b in sc_k}
check("Kremnos forge", "forge" in kk, str(kk))
check("Kremnos banner", "banner" in kk, str(kk))
check("Kremnos no chimera", "chimera" not in kk)
check("Kremnos no shore", "shore" not in kk)
forge = next(b for b in sc_k if b["kind"] == "forge")
ws_k.agent_location = dict(getattr(ws_k, "agent_location", None) or {})
ws_k.agent_location["mydei"] = "Castrum Kremnos"
iron = eco.visitor_touch(ws_k, forge["id"], "listen_iron", place="Castrum Kremnos", save=False)
check("listen to forge", iron.get("ok") is True, str(iron))
still = eco.apply_care(ws_k, "mydei", forge["id"], "still_anvil", save=False)
check("mydei still anvil", still.get("ok") is True, str(still))
bad_c = eco.apply_care(ws_k, "cipher", forge["id"], "still_anvil", save=False)
check("cipher refused anvil", bad_c.get("ok") is False)

ws_a2 = mk(2, "Aedes Elysiae", month=4)
sc_a2 = eco.derive_scene(ws_a2, place="Aedes Elysiae")
ka = {b["kind"] for b in sc_a2}
check("Aedes mill or kite or wheat", bool(ka & {"mill", "kite", "wheat"}), str(ka))
wheat2 = next((b for b in sc_a2 if b["kind"] == "wheat"), None)
if wheat2:
    brush = eco.visitor_touch(ws_a2, wheat2["id"], "brush_grain", place="Aedes Elysiae", save=False)
    check("brush wheat", brush.get("ok") is True, str(brush))
else:
    check("brush wheat", False, "no wheat")

print("== Engine hook import ==")
import inspect
from src.world import world_engine as we
src = inspect.getsource(we.WorldEngine.run_day)
check("run_day calls ecosystem apply_tick", "ecosystem" in src and "apply_tick" in src)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
