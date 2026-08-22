"""Stage-2 resident memory — named street people remember the visitor.

Persists under ``world.vivid['resident_memory']``. Does not rewrite Copilot
NPCS; wraps living-roster greet/talk with recognition flavor only.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _slug(text: str) -> str:
    out = []
    for ch in (text or "").lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_'" and out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-") or "x"


def npc_key(npc: Optional[dict] = None, *, npc_id: str = "",
            name: str = "", city: str = "") -> str:
    """Stable id: prefer ``npc['id']``, else ``slug(city)-slug(name)``."""
    if npc and npc.get("id"):
        return str(npc["id"])
    if npc_id:
        return str(npc_id)
    if npc:
        name = name or (npc.get("name") or "")
        city = city or (npc.get("city") or "")
    return f"{_slug(city)}-{_slug(name)}"


def memory_bucket(world) -> dict:
    """``world.vivid['resident_memory']`` = {npc_id: {name, city, meets, ...}}."""
    from .vivid_stage2 import vivid_bucket

    v = vivid_bucket(world)
    b = v.get("resident_memory")
    if not isinstance(b, dict):
        b = {}
        v["resident_memory"] = b
    return b


def _day_label(world) -> str:
    try:
        from .lived_mechanisms import date_key
        return date_key(world)
    except Exception:
        pass
    try:
        return world.clock.format_short()
    except Exception:
        return ""


_FIRST_RETURN = (
    "{name} looks twice — the traveler again.",
    "{name} nods in recognition. You have passed this way before.",
    "{name} softens a fraction. Ah — we have spoken.",
)
_WARMER = (
    "{name} lights a little. Back again, then.",
    "{name} smiles as if the street had expected you. Welcome back.",
    "{name} raises a hand, easy now. The familiar traveler returns.",
)


def recognition_line(world, npc: dict) -> Optional[str]:
    """If meets>=1, short recognition flavor (deterministic from meets).

    meets==1: first-return acknowledgment; meets>=2: warmer 'back again'.
    """
    if not isinstance(npc, dict):
        return None
    key = npc_key(npc)
    bucket = memory_bucket(world)
    rec = bucket.get(key)
    if not isinstance(rec, dict):
        # Fall back: match by name+city if key drifted
        name = (npc.get("name") or "").strip()
        city = (npc.get("city") or "").strip()
        for row in bucket.values():
            if not isinstance(row, dict):
                continue
            if row.get("name") == name and row.get("city") == city:
                rec = row
                break
    if not isinstance(rec, dict):
        return None
    meets = int(rec.get("meets") or 0)
    if meets < 1:
        return None
    name = (npc.get("name") or rec.get("name") or "A resident").strip()
    if meets == 1:
        pool = _FIRST_RETURN
    else:
        pool = _WARMER
    idx = meets % len(pool)
    return pool[idx].format(name=name)


def remember_meeting(world, npc_id: str, *, name: str, city: str,
                     line: str = "") -> dict:
    """Increment meets; store last_line / last_day from the clock."""
    bucket = memory_bucket(world)
    key = str(npc_id or npc_key(name=name, city=city))
    prev = bucket.get(key) if isinstance(bucket.get(key), dict) else {}
    meets = int(prev.get("meets") or 0) + 1
    entry = {
        "name": name,
        "city": city,
        "meets": meets,
        "last_line": (line or prev.get("last_line") or ""),
        "last_day": _day_label(world),
    }
    bucket[key] = entry
    return entry


def greet_with_memory(world, city: str, limit: int = 4) -> list:
    """Wrap resident_npcs.greet_here; attach ``recognition`` when known."""
    from . import resident_npcs as rn

    rows = rn.greet_here(world, city, limit=limit)
    out: List[dict] = []
    for row in rows:
        item = dict(row)
        recog = recognition_line(world, item)
        if recog:
            item["recognition"] = recog
        out.append(item)
    return out


def talk_with_memory(world, city: str, npc_name: str) -> dict:
    """talk_to_npc, then remember; prepend recognition if returning visitor."""
    from . import resident_npcs as rn

    prior = None
    # Peek recognition before this meeting (returning visitor).
    for n in rn.living_roster():
        if n.get("name") == npc_name and n.get("city") == city:
            prior = recognition_line(world, n)
            break

    res = rn.talk_to_npc(world, city, npc_name)
    if not res.get("ok"):
        return res

    match = res.get("npc") or {}
    key = npc_key(match if isinstance(match, dict) else None,
                  name=npc_name, city=city)
    name = (match.get("name") if isinstance(match, dict) else None) or npc_name
    line = res.get("line") or ""
    remember_meeting(world, key, name=name, city=city, line=line)

    if prior:
        line = f"{prior} {line}".strip()
        res = dict(res)
        res["line"] = line
        res["recognition"] = prior
    return res
