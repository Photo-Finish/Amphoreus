"""
map_data.py — the geography of the little Amphoreus.

A weighted graph of the world: nodes are the places the Heirs live in, edges are
travel routes with a cost measured in Light-Calendar *periods* (there are five
periods per day). The world engine consults `travel_time()` so that no Heir can
simply teleport across the world — a journey to another city takes hours or days,
and during those periods the traveler is on the road, seeing nobody.

The UI renders the same graph as a hand-drawn-looking SVG map via
`render_map_svg()`.
"""

import heapq
import math
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Locations on the map (name -> position in the 1000x820 SVG coordinate space)
# --------------------------------------------------------------------------- #
LOCATION_POS: Dict[str, Tuple[float, float]] = {
    "Okhema": (400, 470),
    "Dawncloud": (400, 330),
    "Janusopolis": (545, 505),
    "Grove of Epiphany": (250, 400),
    "Great Tomb": (175, 320),
    "Castrum Kremnos": (140, 545),
    "Styxia": (620, 620),
    "Aidonia": (700, 720),
    "Aedes Elysiae": (830, 315),
    "Vortex of Genesis": (300, 680),
    "Eye of Twilight": (120, 205),
}

# --------------------------------------------------------------------------- #
# Travel routes (undirected), time in Light-Calendar PERIODS.
#   5 periods = one full day.
#   0 = within the same city (e.g. Dawncloud is the council seat inside Okhema)
#   1-4 = a journey of hours to most of a day
#   5+  = a journey of one or more days (crossing city-states is costly)
# --------------------------------------------------------------------------- #
ROUTES: Dict[Tuple[str, str], int] = {
    ("Okhema", "Dawncloud"): 0,                 # the Demigod Council sits within Okhema
    ("Okhema", "Janusopolis"): 1,               # the twin city, a short road
    ("Okhema", "Grove of Epiphany"): 2,         # the Sage Road, half a day
    ("Okhema", "Castrum Kremnos"): 8,           # the long war road to the mobile fortress
    ("Okhema", "Styxia"): 9,                    # the River of Souls road
    ("Okhema", "Aedes Elysiae"): 12,            # the remote village beyond the veil
    ("Okhema", "Great Tomb"): 10,               # down through the deep ruin
    ("Okhema", "Vortex of Genesis"): 14,        # the hidden sacred nexus
    ("Okhema", "Eye of Twilight"): 12,          # toward the fallen sky castrum
    ("Janusopolis", "Aedes Elysiae"): 9,        # the coastal road to the wharf
    ("Grove of Epiphany", "Great Tomb"): 2,     # the deep path into the ruin
    ("Grove of Epiphany", "Castrum Kremnos"): 6,
    ("Styxia", "Aidonia"): 3,                   # the snow road
    ("Styxia", "Vortex of Genesis"): 6,         # the sea crossing to the hidden nexus
    ("Castrum Kremnos", "Vortex of Genesis"): 8,
    ("Aidonia", "Vortex of Genesis"): 8,
}


def travel_days(a: str, b: str) -> int:
    """Travel time in whole DAYS (engine ticks), rounding up to whole days.

    0 if the two places are the same city; otherwise at least 1 day.
    """
    if a == b:
        return 0
    p = travel_time(a, b)
    if p == 0:
        return 0
    return max(1, math.ceil(p / 5))

# Build the adjacency graph.
_GRAPH: Dict[str, Dict[str, int]] = {}
for (a, b), cost in ROUTES.items():
    _GRAPH.setdefault(a, {})[b] = cost
    _GRAPH.setdefault(b, {})[a] = cost


# --------------------------------------------------------------------------- #
# Travel times
# --------------------------------------------------------------------------- #
def neighbors(location: str) -> List[str]:
    return list(_GRAPH.get(location, {}))


def travel_time(a: str, b: str) -> int:
    """Shortest travel time in periods between two locations (0 if the same)."""
    if a == b:
        return 0
    if a not in _GRAPH or b not in _GRAPH:
        return 999
    dist: Dict[str, int] = {a: 0}
    pq = [(0, a)]
    while pq:
        d, cur = heapq.heappop(pq)
        if cur == b:
            return d
        if d > dist.get(cur, math.inf):
            continue
        for nxt, cost in _GRAPH[cur].items():
            nd = d + cost
            if nd < dist.get(nxt, math.inf):
                dist[nxt] = nd
                heapq.heappush(pq, (nd, nxt))
    return 999


def travel_path(a: str, b: str) -> List[str]:
    """The list of locations along the shortest route a -> b."""
    if a == b:
        return [a]
    if a not in _GRAPH or b not in _GRAPH:
        return [a, b]
    prev: Dict[str, str] = {}
    dist: Dict[str, int] = {a: 0}
    pq = [(0, a)]
    while pq:
        d, cur = heapq.heappop(pq)
        if cur == b:
            break
        if d > dist.get(cur, math.inf):
            continue
        for nxt, cost in _GRAPH[cur].items():
            nd = d + cost
            if nd < dist.get(nxt, math.inf):
                dist[nxt] = nd
                prev[nxt] = cur
                heapq.heappush(pq, (nd, nxt))
    path = [b]
    while path[-1] != a:
        path.append(prev.get(path[-1], a))
    return list(reversed(path))


def travel_description(a: str, b: str) -> str:
    """A human sentence describing the journey from a to b."""
    if a == b:
        return f"You are already in {a}."
    t = travel_time(a, b)
    path = travel_path(a, b)
    route = " → ".join(path)
    if t == 0:
        return f"{a} and {b} are the same city — a short walk within the walls."
    if t <= 2:
        words = "a few hours"
    elif t <= 4:
        words = "most of a day"
    else:
        words = f"several days (about {t} periods)"
    return f"The journey from {a} to {b} takes {words} ({t} periods). Route: {route}."


# --------------------------------------------------------------------------- #
# SVG rendering — a night map of Amphoreus, with the Heirs as small lights
# --------------------------------------------------------------------------- #
def _style_route(a: str, b: str) -> str:
    return f"stroke=\"rgba(232,213,163,.28)\" stroke-width=\"1.6\"" \
           f" stroke-dasharray=\"6 5\" fill=\"none\""


def render_map_svg(
    heir_locations: Optional[Dict[str, str]] = None,
    traveling: Optional[Dict[str, Dict]] = None,
    heir_names: Optional[Dict[str, str]] = None,
    highlight: Optional[str] = None,
) -> str:
    """Render the Amphoreus map as an inline SVG.

    heir_locations : character_id -> location name (their current place)
    traveling      : character_id -> {"to": loc, "remaining": int} (on the road)
    heir_names     : character_id -> display name
    highlight      : optional location name to outline (e.g. the selected one)
    """
    heir_locations = heir_locations or {}
    traveling = traveling or {}
    heir_names = heir_names or {}

    # Distinct marker colours for the thirteen Heirs (gold-adjacent palette).
    palette = [
        "#e8d5a3", "#7fd4c1", "#c9a0dc", "#e58a8a", "#8ab6e5",
        "#d9c17a", "#9ad08f", "#e58ab8", "#7ac2e0", "#d0a86a",
        "#b3a6ff", "#e5b7a0", "#9ee0c8",
    ]

    parts: List[str] = []
    parts.append(
        f'<svg viewBox="0 0 1000 820" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;background:radial-gradient(ellipse at 50% 40%, #141126 0%, #0b0a14 70%);'
        f'border:1px solid rgba(232,213,163,.18);border-radius:14px;">'
    )
    # faint stars
    import random
    rng = random.Random(7)
    for _ in range(90):
        x, y = rng.uniform(10, 990), rng.uniform(10, 810)
        r = rng.uniform(0.5, 1.6)
        op = rng.uniform(0.15, 0.6)
        parts.append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#e8d5a3" opacity="{op:.2f}"/>'
        )

    # routes
    drawn = set()
    for (a, b), cost in ROUTES.items():
        key = tuple(sorted([a, b]))
        if key in drawn:
            continue
        drawn.add(key)
        ax, ay = LOCATION_POS[a]
        bx, by = LOCATION_POS[b]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        parts.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" {_style_route(a, b)}/>')
        if cost > 0:
            parts.append(
                f'<text x="{mx:.0f}" y="{my - 6:.0f}" text-anchor="middle" '
                f'font-size="12" fill="rgba(232,213,163,.55)" '
                f'font-family="Georgia, serif">{cost} p</text>'
            )

    # locations
    for name, (x, y) in LOCATION_POS.items():
        hl = (name == highlight)
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="9" fill="#0d0b18" '
            f'stroke="{"#f4e3b2" if hl else "rgba(232,213,163,.75)"}" '
            f'stroke-width="{2.6 if hl else 1.6}"/>'
        )
        parts.append(
            f'<text x="{x}" y="{y + 24}" text-anchor="middle" font-size="12.5" '
            f'fill="{"#f4e3b2" if hl else "#d8cfa8"}" font-family="Georgia, serif" '
            f'font-style="italic">{name}</text>'
        )

    # the Heirs as small lights at their current places
    for i, cid in enumerate(heir_locations):
        loc = heir_locations[cid]
        if loc not in LOCATION_POS:
            continue
        x, y = LOCATION_POS[loc]
        col = palette[i % len(palette)]
        name = heir_names.get(cid, cid)
        initial = name[0].upper() if name else "?"
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="12" fill="{col}" opacity=".16"/>'
        )
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="6" fill="{col}" stroke="#0b0a14" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{x}" y="{y + 4.5}" text-anchor="middle" font-size="9" '
            f'fill="#0b0a14" font-weight="bold" font-family="Arial">{initial}</text>'
        )

    # travelers shown on the road: a small dot between origin and destination
    for cid, info in traveling.items():
        to = info.get("to")
        name = heir_names.get(cid, cid)
        initial = name[0].upper() if name else "?"
        col = palette[list(heir_locations.keys()).index(cid) % len(palette)] \
            if cid in heir_locations else "#e8d5a3"
        # find the traveler's current position = destination if known, else origin
        # We show them mid-route toward 'to'
        if to in LOCATION_POS:
            # find their departure: any location adjacent on the route
            tx, ty = LOCATION_POS[to]
            parts.append(
                f'<circle cx="{tx}" cy="{ty}" r="14" fill="{col}" opacity=".10"/>'
            )
            parts.append(
                f'<path d="M {tx - 14} {ty - 14} L {tx + 14} {ty + 14} M {tx + 14} {ty - 14} L {tx - 14} {ty + 14}" '
                f'stroke="{col}" stroke-width="1.4"/>'
            )
            parts.append(
                f'<text x="{tx}" y="{ty + 22}" text-anchor="middle" font-size="10" '
                f'fill="{col}" font-family="Arial" font-style="italic">{initial} → {to}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# The Heirs' homes (kept in one place so map + schedules + state agree)
# --------------------------------------------------------------------------- #
# Canon-based home city of each Heir (mirrors world_state.HOME_LOCATIONS).
HEIR_HOMES: Dict[str, str] = {
    "tribbie": "Janusopolis",
    "cerydra": "Okhema",
    "evernight": "Okhema",
    "dan-heng-permansor-terrae": "Okhema",
    "hysilens": "Okhema",
    "hyacine": "Grove of Epiphany",
    "phainon": "Aedes Elysiae",
    "anaxa": "Grove of Epiphany",
    "aglaea": "Okhema",
    "mydei": "Castrum Kremnos",
    "castorice": "Aidonia",
    "cipher": "Okhema",
    "cyrene": "Aedes Elysiae",
}
