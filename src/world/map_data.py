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
    # Positions follow the canon geography (see databank/world/geography.md):
    # Aidonia lies in the NORTHERN snow wasteland; the Eye of Twilight is a
    # FALLEN SKY castrum above Okhema (its sky bridge to Dawncloud is lost);
    # the River of Souls runs from Styxia up into the northern snows.
    "Okhema": (400, 480),
    "Dawncloud": (400, 290),          # the council seat, in the clouds above Okhema
    "Janusopolis": (565, 470),        # the twin city, a short road east
    "Grove of Epiphany": (225, 430),  # the scholars' grove, west of Okhema
    "Great Tomb": (130, 525),         # the deep ruin, a short descent from the Grove
    "Castrum Kremnos": (175, 660),    # the mobile fortress on the long war road
    "Styxia": (620, 625),             # on the River of Souls
    "Aidonia": (660, 205),            # the northern snow wasteland
    "Aedes Elysiae": (845, 555),      # the coastal village beyond the Veil of Evernight
    "Vortex of Genesis": (360, 740),  # hidden by the waves; reached by sea
    "Eye of Twilight": (400, 95),     # the fallen sky castrum, above Dawncloud
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

    # the River of Souls — the great river that runs past Styxia up into the
    # northern snow wasteland, where the living realm gives way to the nether.
    parts.append(
        '<path d="M 620 625 C 595 540, 598 425, 622 325 C 633 280, 648 240, 660 205" '
        'fill="none" stroke="rgba(120,175,255,.20)" stroke-width="15" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
    )
    parts.append(
        '<path d="M 620 625 C 595 540, 598 425, 622 325 C 633 280, 648 240, 660 205" '
        'fill="none" stroke="rgba(170,210,255,.30)" stroke-width="5" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
    )
    parts.append(
        '<text x="600" y="555" text-anchor="middle" font-size="10.5" font-style="italic" '
        'fill="rgba(150,195,255,.6)" font-family="Georgia, serif">River of Souls</text>'
    )
    # clouds about the sky seat (Dawncloud) and the fallen sky castrum
    for cx, cy, rx, ry in [
        (400, 272, 62, 12), (445, 296, 42, 10), (358, 258, 46, 11),
        (400, 78, 52, 11), (438, 104, 36, 9), (362, 112, 40, 9),
    ]:
        parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
            f'fill="rgba(205,218,238,.05)"/>'
        )

    # ---- Precompute the Heir layout (fan positions + packed name rows) so
    # the route-cost labels below can avoid sitting on any name. ----
    from collections import defaultdict, OrderedDict
    order = list(heir_locations.keys())
    color_of = {cid: palette[i % len(palette)] for i, cid in enumerate(order)}
    by_city = OrderedDict()
    for cid in heir_locations:
        loc = heir_locations[cid]
        if loc in LOCATION_POS:
            by_city.setdefault(loc, []).append(cid)

    def _pack_labels(items):
        """Greedily place (name, x, color) labels into horizontal rows above
        the fan so no two labels overlap within a row (rows are skipped as
        needed). Estimated widths keep long names from touching."""
        rows = []   # rows[r] = right edge of the last label placed in row r
        packed = []
        for nm, x, col in items:
            w = 5.8 * len(nm)  # rough pixel width at font-size 10.5 Arial
            placed = False
            for r in range(len(rows)):
                if not rows[r] or x - w / 2 > rows[r][-1] + 5:
                    rows[r].append(x + w / 2)
                    packed.append((nm, x, col, r))
                    placed = True
                    break
            if not placed:
                rows.append([x + w / 2])
                packed.append((nm, x, col, len(rows) - 1))
        return packed

    # Fan x positions and final name-label rows per city (drawn later).
    city_xs: Dict[str, list] = {}
    heir_label_rows: Dict[str, list] = {}
    for loc, cids in by_city.items():
        cx, cy = LOCATION_POS[loc]
        n = len(cids)
        gap = 24 if n > 1 else 0
        xs = [cx - (n - 1) * gap / 2 + k * gap for k in range(n)] if n > 1 else [cx]
        city_xs[loc] = xs
        if n == 1:
            heir_label_rows[loc] = [(xs[0], cy - 12,
                                     heir_names.get(cids[0], cids[0]), color_of[cids[0]])]
        else:
            items = [(heir_names.get(c, c), xs[k], color_of[c]) for k, c in enumerate(cids)]
            heir_label_rows[loc] = [(x, cy - 15 - r * 18, nm, col)
                                    for nm, x, col, r in _pack_labels(items)]

    # Every name region that must stay clear of route labels.
    reserved = []
    for name, (x, y) in LOCATION_POS.items():
        w = 6.4 * len(name)
        reserved.append((x - w / 2 - 4, x + w / 2 + 4, y + 14, y + 32))
    for rows in heir_label_rows.values():
        for x, y, nm, _col in rows:
            w = 6.0 * len(nm)
            reserved.append((x - w / 2 - 4, x + w / 2 + 4, y - 11, y + 2))
    # the River of Souls label must stay clear of route-cost labels too
    reserved.append((600 - 46 - 4, 600 + 46 + 4, 544, 558))

    def _label_collides(x: float, y: float, w: float) -> bool:
        """True if a centered label at (x, y) of width w would overlap a name."""
        x0, x1 = x - w / 2 - 5, x + w / 2 + 5
        y0, y1 = y - 11, y + 2
        for rx0, rx1, ry0, ry1 in reserved:
            if x0 < rx1 and x1 > rx0 and y0 < ry1 and y1 > ry0:
                return True
        return False

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
        if cost > 0 and not _label_collides(mx, my - 6, 7.0 * len(str(cost)) + 8):
            parts.append(
                f'<text x="{mx:.0f}" y="{my - 6:.0f}" text-anchor="middle" '
                f'font-size="12" fill="rgba(232,213,163,.55)" '
                f'font-family="Georgia, serif">{cost} p</text>'
            )

    # the former sky bridge between the council seat and the sky castrum
    # (both ways lost in "Dawn, Shine at the World's End") — now only a faint
    # ghost of the old connection.
    dx, dy = LOCATION_POS["Dawncloud"]
    ex, ey = LOCATION_POS["Eye of Twilight"]
    parts.append(
        f'<line x1="{dx}" y1="{dy}" x2="{ex}" y2="{ey}" '
        f'stroke="rgba(232,213,163,.16)" stroke-width="1.4" stroke-dasharray="2 7"/>'
    )
    parts.append(
        f'<text x="{dx + 16}" y="{(dy + ey) // 2}" text-anchor="start" font-size="9" '
        f'font-style="italic" fill="rgba(232,213,163,.5)" '
        f'font-family="Arial">former sky bridge (lost)</text>'
    )

    # locations
    _RUINS = {"Eye of Twilight"}
    for name, (x, y) in LOCATION_POS.items():
        hl = (name == highlight)
        ruin = name in _RUINS
        if ruin:
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="14" fill="none" '
                f'stroke="rgba(150,160,185,.45)" stroke-width="1.2" stroke-dasharray="3 4"/>'
            )
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="9" fill="#0d0b18" '
            f'stroke="{"#f4e3b2" if hl else "rgba(232,213,163,.75)"}" '
            f'stroke-width="{2.6 if hl else 1.6}"/>'
        )
        label = f"{name} (fallen)" if ruin else name
        labelfill = "#f4e3b2" if hl else ("rgba(150,160,185,.8)" if ruin else "#d8cfa8")
        parts.append(
            f'<text x="{x}" y="{y + 24}" text-anchor="middle" font-size="12.5" '
            f'fill="{labelfill}" font-family="Georgia, serif" '
            f'font-style="italic">{label}</text>'
        )

    # the Heirs as small lights at their current places; name tags are drawn
    # from the packed rows precomputed above (route labels avoid them).
    for loc, cids in by_city.items():
        cx, cy = LOCATION_POS[loc]
        xs = city_xs[loc]
        for k, cid in enumerate(cids):
            x = xs[k]
            col = color_of[cid]
            name = heir_names.get(cid, cid)
            initial = name[0].upper() if name else "?"
            parts.append(
                f'<circle cx="{x:.1f}" cy="{cy}" r="12" fill="{col}" opacity=".16"/>'
            )
            parts.append(
                f'<circle cx="{x:.1f}" cy="{cy}" r="6" fill="{col}" stroke="#0b0a14" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{x:.1f}" y="{cy + 4.5}" text-anchor="middle" font-size="9" '
                f'fill="#0b0a14" font-weight="bold" font-family="Arial">{initial}</text>'
            )
        for x, y, nm, col in heir_label_rows[loc]:
            parts.append(
                f'<text x="{x:.1f}" y="{y}" text-anchor="middle" font-size="10.5" '
                f'fill="{col}" font-family="Arial" '
                f'font-style="italic">{nm}</text>'
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
                f'<text x="{tx}" y="{ty + 40}" text-anchor="middle" font-size="10" '
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
