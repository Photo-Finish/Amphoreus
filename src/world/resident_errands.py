"""Recurring named residents with Amphoreus-native errands.

Deterministic seeds from city+role hash. Errands advance once per Light Calendar
date under ``world.vivid["resident_errands"]``. No invented festivals — may
mention Month of Reaping / Month of Cultivation only when the calendar month
matches those names.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

_SEED_RESIDENTS: List[dict] = [
    {"name": "Lysara", "role": "cloth-runner", "city": "Okhema"},
    {"name": "Helion", "role": "grain-carter", "city": "Okhema"},
    {"name": "Myris", "role": "letter-bearer", "city": "Okhema"},
    {"name": "Caelon", "role": "bath-porter", "city": "Okhema"},
    {"name": "Thera", "role": "mill-hand", "city": "Aedes Elysiae"},
    {"name": "Oreia", "role": "gate-scribe", "city": "Janusopolis"},
    {"name": "Vesper", "role": "grove-courier", "city": "Grove of Epiphany"},
    {"name": "Neris", "role": "harbor-hand", "city": "Styxia"},
    {"name": "Ktesos", "role": "forge-runner", "city": "Castrum Kremnos"},
    {"name": "Daphne", "role": "shrine-aide", "city": "Aidonia"},
    {"name": "Phaedra", "role": "water-carrier", "city": "Dawncloud"},
    {"name": "Leonis", "role": "market-runner", "city": "Okhema"},
]

_ERRANDS = [
    "cloth to the baths",
    "grain to the mill",
    "a letter to the gate",
    "oil to the shrine lamps",
    "water up from the lower cistern",
    "thread for the loom-hall",
    "a sealed note to the council clerk",
    "fresh bread to the teaching hall",
    "herbs to the healer's house",
    "stone dust swept from the gate threshold",
]


def _stable(text: str) -> int:
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)


def _month_name(world) -> str:
    try:
        return str(world.clock.month_name or "")
    except Exception:
        return ""


def _date_key(world) -> str:
    try:
        from .lived_mechanisms import date_key
        return date_key(world)
    except Exception:
        pass
    try:
        c = world.clock
        return f"{getattr(c, 'year', 0)}-{getattr(c, 'month', 0)}-{getattr(c, 'day', 0)}"
    except Exception:
        return ""


def errands_bucket(world) -> dict:
    try:
        from . import society_life as sl
        v = sl.vivid_ext(world)
    except Exception:
        from .vivid_stage2 import vivid_bucket
        v = vivid_bucket(world)
    b = v.get("resident_errands")
    if not isinstance(b, dict):
        b = {}
        v["resident_errands"] = b
    return b


def seed_residents(world=None) -> List[dict]:
    out = []
    month = _month_name(world) if world is not None else ""
    for raw in _SEED_RESIDENTS:
        city, role, name = raw["city"], raw["role"], raw["name"]
        h = _stable(f"{city}|{role}|{name}")
        rid = f"errand-{h:08x}"
        errand = _ERRANDS[h % len(_ERRANDS)]
        if "Reaping" in month and h % 3 == 0:
            errand = "grain to the mill (Month of Reaping)"
        elif "Cultivation" in month and h % 3 == 0:
            errand = "seed-sacks toward the field edge (Month of Cultivation)"
        out.append({
            "id": rid,
            "name": name,
            "role": role,
            "city": city,
            "errand": errand,
            "seed": h,
        })
    return out


def residents_for_city(world, city: str) -> List[dict]:
    return [r for r in seed_residents(world) if r.get("city") == (city or "")]


def _npc_seed(npc: dict) -> int:
    if not isinstance(npc, dict):
        return 0
    raw = npc.get("seed")
    if raw is not None:
        try:
            return int(raw)
        except Exception:
            pass
    city = (npc.get("city") or "").strip()
    role = (npc.get("role") or "").strip()
    name = (npc.get("name") or "").strip()
    key = f"{city}|{role}|{name}"
    if not key.strip("|"):
        key = str(npc.get("id") or "")
    return _stable(key)


def compute_errand(world, npc: dict, today: str | None = None) -> str:
    """Today's errand for any resident dict (seed or street roster)."""
    if not isinstance(npc, dict):
        return ""
    if today is None:
        today = _date_key(world)
    h = _npc_seed(npc)
    rid = str(npc.get("id") or npc.get("name") or "")
    day_h = _stable(f"{today}|{rid}")
    errand = _ERRANDS[(h + day_h) % len(_ERRANDS)]
    month = _month_name(world)
    if "Reaping" in month and day_h % 4 == 0:
        errand = "grain to the mill (Month of Reaping)"
    elif "Cultivation" in month and day_h % 4 == 0:
        errand = "seed-sacks toward the field edge (Month of Cultivation)"
    return errand


def advance_errands(world) -> dict:
    bucket = errands_bucket(world)
    today = _date_key(world)
    if bucket.get("_last_date") == today and bucket.get("by_id"):
        return {
            "advanced": False,
            "date": today,
            "count": len(bucket.get("by_id") or {}),
        }

    by_id: Dict[str, Any] = {}
    for npc in seed_residents(world):
        errand = compute_errand(world, npc, today=today)
        by_id[npc["id"]] = {
            "name": npc["name"],
            "city": npc["city"],
            "role": npc["role"],
            "errand": errand,
            "date": today,
        }
    bucket["_last_date"] = today
    bucket["by_id"] = by_id
    return {"advanced": True, "date": today, "count": len(by_id)}


def current_errand(world, npc: dict) -> str:
    if not isinstance(npc, dict):
        return ""
    today = _date_key(world)
    bucket = errands_bucket(world)
    by_id = bucket.get("by_id") or {}
    rid = npc.get("id") or ""
    if rid and rid in by_id:
        row = by_id[rid]
        if row.get("date") == today:
            return str(row.get("errand") or "")
    name = (npc.get("name") or "").strip()
    city = (npc.get("city") or "").strip()
    for row in by_id.values():
        if row.get("date") == today and row.get("name") == name and row.get("city") == city:
            return str(row.get("errand") or "")
    computed = compute_errand(world, npc, today=today)
    if computed:
        return computed
    return str(npc.get("errand") or "")


def errand_line(world, npc: dict) -> str:
    errand = current_errand(world, npc)
    name = (npc.get("name") if isinstance(npc, dict) else None) or "A resident"
    if not errand:
        return f"{name} is about ordinary street work."
    return f"{name} is on an errand: {errand}."


def apply_on_tick(world) -> dict:
    return advance_errands(world)
