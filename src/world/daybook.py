"""Stage-2 daybook — literary view over tick facts (not the chronicle JSONL).

Deterministic prose for the Gazette. People live on; no inventory dump.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

_CHRONICLE_KINDS = frozenset({"encounter", "letter", "surge"})

_BANNED_FRAGMENTS = (
    "inventory", "json", "{", "}", "http://", "https://",
    "traceback", "stack", "filepath", ".py:",
)


def _clock_label(world) -> str:
    try:
        return world.clock.format()
    except Exception:
        pass
    try:
        return world.clock.format_short()
    except Exception:
        return "a day in Amphoreus"


def _sanitize(text: str, *, max_len: int = 180) -> str:
    t = " ".join(str(text or "").split())
    if not t:
        return ""
    low = t.lower()
    for frag in _BANNED_FRAGMENTS:
        if frag in low:
            return ""
    # Drop raw operational dumps
    if t.count("|") >= 4 or t.count(";") >= 5:
        return ""
    if len(t) > max_len:
        t = t[: max_len - 1].rstrip() + "…"
    return t


def _ambient_facts(world) -> List[str]:
    out: List[str] = []
    try:
        news = (world.ambient_news() or "").strip()
        if news:
            s = _sanitize(news)
            if s:
                out.append(s)
    except Exception:
        pass
    try:
        weather = (getattr(world, "ambient", None) or {}).get("weather") or {}
        if isinstance(weather, dict):
            # Stable order for determinism
            for city in sorted(weather.keys()):
                sky = _sanitize(str(weather.get(city) or ""), max_len=120)
                if sky:
                    out.append(f"Over {city}: {sky}")
                if len(out) >= 4:
                    break
    except Exception:
        pass
    return out


def _lived_facts(world, limit: int) -> List[str]:
    try:
        from . import lived_mechanisms as lm
        items = lm.gazette_world_items(world, fact_limit=limit)
        facts = []
        for f in items.get("facts") or []:
            s = _sanitize(str(f))
            if s:
                facts.append(s)
        return facts[:limit]
    except Exception:
        return []


def _eco_facts(world, limit: int = 3) -> List[str]:
    try:
        from . import ecosystem as eco
        bits = eco.gazette_items(world, limit=limit)
        out = []
        for b in bits or []:
            s = _sanitize(str(b))
            if s:
                out.append(s)
        return out
    except Exception:
        return []


def _chronicle_facts(rows: Optional[list], limit: int = 4) -> List[str]:
    if not rows:
        return []
    out: List[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        kind = (row.get("kind") or "").strip().lower()
        if kind not in _CHRONICLE_KINDS:
            continue
        text = _sanitize(row.get("text") or "")
        if not text:
            continue
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _weave_paragraphs(date_label: str, facts: List[str],
                      ambient: List[str], lived: List[str],
                      eco: List[str], chronicle: List[str]) -> List[str]:
    """2–4 short Amphoreus daybook paragraphs. Deterministic."""
    paragraphs: List[str] = []

    # Opening — sky / news
    open_bits = []
    news = ambient[0] if ambient else ""
    skies = [a for a in ambient[1:3]] if len(ambient) > 1 else []
    if skies:
        open_bits.append(skies[0])
    if news:
        open_bits.append(f"Word on the air: {news}")
    if open_bits:
        paragraphs.append(
            f"On {date_label}, the day unfolds as it always has. "
            + " ".join(open_bits)
        )
    else:
        paragraphs.append(
            f"On {date_label}, Amphoreus keeps its quiet course — "
            "roads, hearths, and the slow turn of the Light Calendar."
        )

    # Lived / eco — people and land continue
    body_bits = (lived[:3] + eco[:2])[:4]
    if body_bits:
        joined = " ".join(body_bits)
        paragraphs.append(
            "In the cities and along the roads, people live on. " + joined
        )
    else:
        paragraphs.append(
            "In the cities and along the roads, people live on — "
            "stalls open when the hour allows, lamps wait for night, "
            "and no ledger of goods invents the day."
        )

    # Chronicle — encounters / letters / surge, lightly
    if chronicle:
        paragraphs.append(
            "Among the Heirs' recorded hours: " + " ".join(chronicle[:3])
        )

    # Closing calm — only if we still have room and something to say
    if len(paragraphs) < 4:
        if facts:
            paragraphs.append(
                "The daybook keeps what the clock produced, not a storehouse: "
                + facts[0]
            )
        else:
            paragraphs.append(
                "The page of eternity turns without inventory — "
                "only the living hour, written lightly."
            )

    # Clamp 2–4
    if len(paragraphs) < 2:
        paragraphs.append(
            "The sanctuary holds; the visitor may walk among it."
        )
    return paragraphs[:4]


def compose_daybook(world, chronicle_rows: list | None = None,
                    *, limit_facts: int = 8) -> dict:
    """Return ``{title, date_label, paragraphs, facts}``.

    Pulls ambient news/weather, lived gazette, recent chronicle kinds
    encounter/letter/surge (sanitized), ecosystem notes when present.
    """
    date_label = _clock_label(world)
    ambient = _ambient_facts(world)
    lived = _lived_facts(world, max(3, limit_facts // 2))
    eco = _eco_facts(world, limit=3)
    chronicle = _chronicle_facts(chronicle_rows, limit=4)

    facts: List[str] = []
    seen = set()
    for chunk in (ambient, lived, eco, chronicle):
        for f in chunk:
            if f not in seen:
                seen.add(f)
                facts.append(f)
            if len(facts) >= limit_facts:
                break
        if len(facts) >= limit_facts:
            break

    paragraphs = _weave_paragraphs(
        date_label, facts, ambient, lived, eco, chronicle
    )
    return {
        "title": "Today in Amphoreus",
        "date_label": date_label,
        "paragraphs": paragraphs,
        "facts": facts[:limit_facts],
    }


def daybook_markdown(entry: dict) -> str:
    """Render a compose_daybook result as readable markdown."""
    if not isinstance(entry, dict):
        return ""
    title = entry.get("title") or "Today in Amphoreus"
    date_label = entry.get("date_label") or ""
    lines = [f"### {title}"]
    if date_label:
        lines.append(f"*{date_label}*")
    lines.append("")
    for p in entry.get("paragraphs") or []:
        p = str(p).strip()
        if p:
            lines.append(p)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
