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
# Alternate forms of Amphoreus — the Dawn era and the Nether
# --------------------------------------------------------------------------- #
# Many places exist in TWO canon forms (see databank/world/geography.md §1 —
# the in-game map's "Dawn-era / Evernight-era" toggle, and the explicit "past
# version of Castrum Kremnos" of the quests). The present world is the
# Evernight era (the darkened world of Year 4932); each two-form area also has
# a DAWN-era (past) form — the same place as it stood under the Dawn Device.
#
# The borderline between the eras is the VEIL OF EVENINGT (Oronyx, Titan of
# Time). Only the Oronyx-blessed may cross it: the Trailblazer (the time
# traveler Oronyx took an interest in) and Evernight (Oronyx's heir). A blessed
# traveler may carry companions across. Other unique Titan properties open
# other borders: Janus's gates (Janusopolis's Dawn form stands behind the Gates
# of Destiny — Janus's heir Tribbie may open them) and Thanatos's death-realm
# (the Nether beneath Styxia — only the Thanatos-blessed may descend).
TIME_FORMS: Dict[str, str] = {
    "Okhema": "Eternal Holy City",              # "Fallen Twilight City" → "Eternal Holy City"
    "Dawncloud": "Demigod Council",             # "Lightless Chapel" → "Demigod Council"
    "Janusopolis": "Sanctum of Prophecy",       # "Abyss of Fate" → "Sanctum of Prophecy"
    "Grove of Epiphany": "Radiant Scarwood",    # "Murmuring Woods" → "Radiant Scarwood"
    "Castrum Kremnos": "Bloodbathed Battlefront",  # "Strife Ruins" → "Bloodbathed Battlefront"
    "Styxia": "Warbling Shores",                # "Dragonbone City" → "Warbling Shores"
    "Eye of Twilight": "Fortress of Dome",      # "Cloudedge Bastion Ruins" → "Fortress of Dome"
    "Great Tomb": "Universal Matrix",           # "Nightmare's Echo" → "Universal Matrix"
    "Aedes Elysiae": "Aedes Elysiae, of old",   # the village before the flames (memory form)
}
PAST_FORMS: set = set(TIME_FORMS.values())
NETHER = "The Nether"   # the death-form of Styxia — Thanatos's sea of flowers

# Dawn-era echo nodes (drawn on the map as faint "time echoes").
PAST_POS: Dict[str, Tuple[float, float]] = {
    "Eternal Holy City": (350, 442),
    "Demigod Council": (346, 252),
    "Sanctum of Prophecy": (620, 428),
    "Radiant Scarwood": (172, 390),
    "Universal Matrix": (80, 470),
    "Bloodbathed Battlefront": (128, 620),
    "Warbling Shores": (572, 584),
    "Fortress of Dome": (460, 58),
    "Aedes Elysiae, of old": (800, 512),
}
NETHER_POS: Tuple[float, float] = (668, 676)

# Small thematic icons for the areas (drawn at each node with a fading glow
# margin, instead of a bare dot). Dawn-era echoes reuse their place's icon,
# drawn faded; the Nether has its own.
AREA_ICONS: Dict[str, str] = {
    "Okhema": "🏛", "Dawncloud": "☁", "Janusopolis": "⛩",
    "Grove of Epiphany": "🌳", "Great Tomb": "🪦", "Castrum Kremnos": "🏰",
    "Styxia": "🌊", "Aidonia": "❄", "Aedes Elysiae": "🌾",
    "Vortex of Genesis": "🌀", "Eye of Twilight": "👁",
    "Eternal Holy City": "🏛", "Demigod Council": "☁",
    "Sanctum of Prophecy": "⛩", "Radiant Scarwood": "🌳",
    "Universal Matrix": "🪦", "Bloodbathed Battlefront": "🏰",
    "Warbling Shores": "🌊", "Fortress of Dome": "👁",
    "Aedes Elysiae, of old": "🌾",
    "The Nether": "🦋",
}

# Everything the map can draw (present + Dawn echoes + the Nether).
ALL_POS: Dict[str, Tuple[float, float]] = {**LOCATION_POS, **PAST_POS, NETHER: NETHER_POS}

# The travellers who may cross each unique border.
ORONYX_BLESSED = {"trailblazer", "evernight"}   # the Veil of Evernight (time)
JANUS_BLESSED = {"tribbie"}                     # the Gates of Destiny (Janusopolis's Dawn form)
THANATOS_BLESSED = {"castorice", "trailblazer"}  # the Nether (the Trailblazer crossed with Castorice)

# The roads of the DAWN era mirror the present roads among the two-form areas.
_DAWN_EDGES = [
    ("Okhema", "Dawncloud"),
    ("Okhema", "Janusopolis"),
    ("Okhema", "Grove of Epiphany"),
    ("Okhema", "Castrum Kremnos"),
    ("Okhema", "Styxia"),
    ("Okhema", "Aedes Elysiae"),
    ("Okhema", "Great Tomb"),
    ("Janusopolis", "Aedes Elysiae"),
    ("Grove of Epiphany", "Great Tomb"),
    ("Grove of Epiphany", "Castrum Kremnos"),
]

def is_past_form(name: str) -> bool:
    return name in PAST_FORMS

def is_cross_era(name: str) -> bool:
    """A Dawn-era form or the Nether — reached only across a Titan's border."""
    return name in PAST_FORMS or name == NETHER

def present_of(past_name: str) -> Optional[str]:
    """The present (Evernight-era) twin of a Dawn-era form."""
    for present, past in TIME_FORMS.items():
        if past == past_name:
            return present
    return None

def time_twin(name: str) -> Optional[str]:
    """The other-era form of a location, if it has one."""
    if name in TIME_FORMS:
        return TIME_FORMS[name]
    return present_of(name)

def can_cross_to(cid: str, dest: str) -> bool:
    """Can this traveler stand in `dest` at all? (Veil / gates / the Nether.)"""
    if dest in PAST_FORMS:
        twin = present_of(dest)
        if cid in ORONYX_BLESSED:
            return True
        if twin == "Janusopolis" and cid in JANUS_BLESSED:
            return True
        return False
    if dest == NETHER:
        return cid in THANATOS_BLESSED
    return True

# The one-period Veil crossings (present ↔ Dawn form).
_VEIL_EDGES: set = {frozenset((p, past)) for p, past in TIME_FORMS.items()}
# The two-period descent into the Nether.
_NETHER_EDGE: frozenset = frozenset(("Styxia", NETHER))

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

def travel_days_for(a: str, b: str, cid: Optional[str]) -> int:
    """Whole-DAY travel time for a specific traveler, honouring the Titan
    borders (999 = the border does not open for them)."""
    if a == b:
        return 0
    p = travel_time_for(a, b, cid)
    if p == 0:
        return 0
    if p >= 999:
        return 999
    return max(1, math.ceil(p / 5))

# Build the adjacency graph — the present layer (ROUTES), the Dawn layer
# (a mirror among the two-form areas), the Veil crossings (present ↔ Dawn,
# 1 period), and the Nether descent (Styxia → The Nether, 2 periods).
_GRAPH: Dict[str, Dict[str, int]] = {}
for (a, b), cost in ROUTES.items():
    _GRAPH.setdefault(a, {})[b] = cost
    _GRAPH.setdefault(b, {})[a] = cost
for (a, b), cost in ROUTES.items():
    if a in TIME_FORMS and b in TIME_FORMS:
        _GRAPH.setdefault(TIME_FORMS[a], {})[TIME_FORMS[b]] = cost
        _GRAPH.setdefault(TIME_FORMS[b], {})[TIME_FORMS[a]] = cost
for present, past in TIME_FORMS.items():
    _GRAPH.setdefault(present, {})[past] = 1
    _GRAPH.setdefault(past, {})[present] = 1
_GRAPH.setdefault("Styxia", {})[NETHER] = 2
_GRAPH.setdefault(NETHER, {})["Styxia"] = 2

def _edge_allowed(a: str, b: str, cid: Optional[str]) -> bool:
    """Whether a specific traveler may use the edge a-b (None = display mode:
    everything is shown). Crossing INTO the Dawn era (or the Nether) needs the
    Titan's blessing; the way BACK is always open — an Heir carried across is
    never trapped in the past (the Veil lets the carried return home)."""
    if cid is None:
        return True
    edge = frozenset((a, b))
    if edge in _VEIL_EDGES:
        if b in PAST_FORMS and a not in PAST_FORMS:
            # present -> past: entering the Dawn era needs the blessing
            if cid in ORONYX_BLESSED:
                return True
            if edge == frozenset(("Janusopolis", "Sanctum of Prophecy")) \
                    and cid in JANUS_BLESSED:
                return True
            return False
        return True  # past -> present: the carried return home
    if edge == _NETHER_EDGE:
        if b == NETHER:
            # descending into the Nether needs Thanatos's blessing
            return cid in THANATOS_BLESSED
        return True  # ascending back to the living world is always open
    return True


# --------------------------------------------------------------------------- #
# Travel times
# --------------------------------------------------------------------------- #
def neighbors(location: str) -> List[str]:
    return list(_GRAPH.get(location, {}))


def travel_time(a: str, b: str) -> int:
    """Shortest travel time in periods between two locations (0 if the same).

    Display mode: every route, including the Veil crossings and the Nether
    descent, counts (see `travel_time_for` for a specific traveler's view).
    """
    return _dijkstra(a, b, None)

def travel_time_for(a: str, b: str, cid: Optional[str]) -> int:
    """Travel time as a specific traveler would experience it.

    The unique Titan borders are closed to most people: the Veil of Evernight
    (Oronyx) opens only to the Oronyx-blessed, the Gates of Destiny (Janus)
    only to Janus-blessed Tribbie, and the Nether (Thanatos) only to the
    Thanatos-blessed. An impassable journey returns 999.
    """
    return _dijkstra(a, b, cid)

def _dijkstra(a: str, b: str, cid: Optional[str]) -> int:
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
            if not _edge_allowed(cur, nxt, cid):
                continue
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
    guest_ids: Optional[set] = None,
    interactive: bool = False,
) -> str:
    """Render the Amphoreus map as an inline SVG.

    heir_locations : character_id -> location name (their current place)
    traveling      : character_id -> {"to": loc, "remaining": int} (on the road)
    heir_names     : character_id -> display name
    highlight      : optional location name to outline (e.g. the selected one)
    guest_ids      : character_ids of the Trailblazer's companions who are
                     PRESENT as visitors today (drawn with a dashed halo).
                     Guests who are beyond Amphoreus should simply be omitted
                     from heir_locations by the caller (see WorldState
                     .present_locations()).
    interactive    : when True, every place and Heir is wrapped in a
                     <g data-kind="place|heir" data-key="..."> group so the
                     host page can attach click info-popups (the caller embeds
                     the info; this only marks the elements).
    """
    heir_locations = heir_locations or {}
    traveling = traveling or {}
    heir_names = heir_names or {}
    guest_ids = guest_ids or set()
    interactive = bool(interactive)
    _d = ((lambda kind, key: f' data-kind="{kind}" data-key="{key}"')
          if interactive else (lambda kind, key: ""))

    # Distinct marker colours for the thirteen Heirs (gold-adjacent palette).
    palette = [
        "#e8d5a3", "#7fd4c1", "#c9a0dc", "#e58a8a", "#8ab6e5",
        "#d9c17a", "#9ad08f", "#e58ab8", "#7ac2e0", "#d0a86a",
        "#b3a6ff", "#e5b7a0", "#9ee0c8",
    ]

    parts: List[str] = []
    _svg_id = ' id="amp-map"' if interactive else ""
    parts.append(
        f'<svg{_svg_id} viewBox="0 0 1000 820" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;height:auto;background:radial-gradient(ellipse at 50% 40%, #141126 0%, #0b0a14 70%);'
        f'border:1px solid rgba(232,213,163,.18);border-radius:14px;">'
    )
    # fading-margin glows behind the area icons
    parts.append(
        '<defs>'
        '<radialGradient id="gGold" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#e8d5a3" stop-opacity=".42"/>'
        '<stop offset="62%" stop-color="#e8d5a3" stop-opacity=".13"/>'
        '<stop offset="100%" stop-color="#e8d5a3" stop-opacity="0"/>'
        '</radialGradient>'
        '<radialGradient id="gSilver" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#a9cdf0" stop-opacity=".34"/>'
        '<stop offset="62%" stop-color="#a9cdf0" stop-opacity=".10"/>'
        '<stop offset="100%" stop-color="#a9cdf0" stop-opacity="0"/>'
        '</radialGradient>'
        '<radialGradient id="gPurple" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#b3a6ff" stop-opacity=".38"/>'
        '<stop offset="62%" stop-color="#b3a6ff" stop-opacity=".10"/>'
        '<stop offset="100%" stop-color="#b3a6ff" stop-opacity="0"/>'
        '</radialGradient>'
        '</defs>'
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
        '<text x="640" y="300" text-anchor="middle" font-size="10.5" font-style="italic" '
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
        if loc in ALL_POS:
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
    # The place icon + glow sits at the node; the Heirs gather just below the
    # icon (FAN_DY), with their name rows floating above it (NAME_DY).
    FAN_DY = 16
    NAME_DY = -18
    city_xs: Dict[str, list] = {}
    heir_label_rows: Dict[str, list] = {}
    for loc, cids in by_city.items():
        cx, cy = ALL_POS[loc]
        n = len(cids)
        gap = 24 if n > 1 else 0
        xs = [cx - (n - 1) * gap / 2 + k * gap for k in range(n)] if n > 1 else [cx]
        city_xs[loc] = xs
        if n == 1:
            heir_label_rows[loc] = [(xs[0], cy + NAME_DY,
                                     heir_names.get(cids[0], cids[0]), color_of[cids[0]])]
        else:
            items = [(heir_names.get(c, c), xs[k], color_of[c]) for k, c in enumerate(cids)]
            heir_label_rows[loc] = [(x, cy + NAME_DY - r * 18, nm, col)
                                    for nm, x, col, r in _pack_labels(items)]

    # Every name region that must stay clear of route labels. Dawn-era names
    # float ABOVE their echo node (so the Veil tags between the twins stay
    # clear); present names sit below their city, below the gathered Heirs.
    reserved = []
    for name, (x, y) in ALL_POS.items():
        w = 6.4 * len(name)
        if name in PAST_FORMS:
            reserved.append((x - w / 2 - 4, x + w / 2 + 4, y - 30, y - 16))
        else:
            reserved.append((x - w / 2 - 4, x + w / 2 + 4, y + 26, y + 44))
    for rows in heir_label_rows.values():
        for x, y, nm, _col in rows:
            w = 6.0 * len(nm)
            reserved.append((x - w / 2 - 4, x + w / 2 + 4, y - 11, y + 2))
    # the River of Souls label must stay clear of route-cost labels too
    reserved.append((640 - 46 - 4, 640 + 46 + 4, 290, 304))

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

    # the Veil of Evernight — the one-period borderline between each place
    # and its Dawn-era (past) form. Only the Oronyx-blessed may cross it, and
    # they may carry companions. Drawn as a faint, wavy "rift of time".
    for present, past in TIME_FORMS.items():
        ax, ay = LOCATION_POS[present]
        bx, by = PAST_POS[past]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        parts.append(
            f'<path d="M {ax} {ay} Q {(ax + bx) / 2 + 7:.0f} {(ay + by) / 2 - 8:.0f} '
            f'{(ax + bx) / 2:.0f} {(ay + by) / 2:.0f} Q {(ax + bx) / 2 - 7:.0f} '
            f'{(ay + by) / 2 + 8:.0f} {bx} {by}" fill="none" '
            f'stroke="rgba(120,175,255,.30)" stroke-width="1.2" '
            f'stroke-dasharray="3 4" stroke-linecap="round"/>'
        )
        if not _label_collides(mx, my - 6, 46):
            parts.append(
                f'<text x="{mx:.0f}" y="{my - 6:.0f}" text-anchor="middle" '
                f'font-size="10" fill="rgba(150,195,255,.65)" '
                f'font-family="Arial">⏳ 1 p</text>'
            )
    # the descent into the Nether — Thanatos's death-realm beneath Styxia.
    ax, ay = LOCATION_POS["Styxia"]
    bx, by = NETHER_POS
    mx, my = (ax + bx) / 2, (ay + by) / 2
    parts.append(
        f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" '
        f'stroke="rgba(170,150,220,.35)" stroke-width="1.2" '
        f'stroke-dasharray="2 5" stroke-linecap="round"/>'
    )
    # pinned clear of Styxia's name label
    if not _label_collides(664, 634, 46):
        parts.append(
            f'<text x="664" y="634" text-anchor="middle" '
            f'font-size="10" fill="rgba(190,170,240,.7)" '
            f'font-family="Arial">† 2 p</text>'
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

    # locations — present cities (icons with fading glows), Dawn-era echoes,
    # and the Nether
    _RUINS = {"Eye of Twilight"}
    for name, (x, y) in ALL_POS.items():
        icon = AREA_ICONS.get(name, "✦")
        hl = (name == highlight)
        ruin = name in _RUINS
        parts.append(f'<g{_d("place", name)}>')
        if name == NETHER:
            # the death-form of Styxia — Thanatos's sea of flowers
            parts.append(f'<circle cx="{x}" cy="{y}" r="26" fill="url(#gPurple)"/>')
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="11" fill="#140f22" '
                f'stroke="rgba(190,170,240,.55)" stroke-width="1.4" stroke-dasharray="3 3"/>'
            )
            parts.append(
                f'<text x="{x}" y="{y + 6}" text-anchor="middle" font-size="16" '
                f'fill="#c9b8f0">{icon}</text>'
            )
            parts.append(
                f'<text x="{x}" y="{y + 38}" text-anchor="middle" font-size="11.5" '
                f'fill="#b3a6d8" font-family="Georgia, serif" font-style="italic">{name}</text>'
            )
        elif name in PAST_FORMS:
            # a Dawn-era echo — the same place as it stood under the Dawn Device
            parts.append(f'<circle cx="{x}" cy="{y}" r="20" fill="url(#gSilver)"/>')
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="9" fill="#0e1522" '
                f'stroke="rgba(160,200,255,.55)" stroke-width="1.2" stroke-dasharray="2 3"/>'
            )
            parts.append(
                f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="12.5" '
                f'fill="#a9cdf0" opacity=".85">{icon}</text>'
            )
            parts.append(
                f'<text x="{x}" y="{y - 22}" text-anchor="middle" font-size="11.5" '
                f'fill="#a9c9e8" font-family="Georgia, serif" font-style="italic">{name}</text>'
            )
        else:
            # a present city: a small thematic icon with a fading glow margin
            parts.append(f'<circle cx="{x}" cy="{y}" r="26" fill="url(#gGold)"/>')
            if ruin:
                parts.append(
                    f'<circle cx="{x}" cy="{y}" r="13" fill="none" '
                    f'stroke="rgba(150,160,185,.45)" stroke-width="1.2" stroke-dasharray="3 4"/>'
                )
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="11" fill="#0d0b18" '
                f'stroke="{"#f4e3b2" if hl else "rgba(232,213,163,.55)"}" '
                f'stroke-width="{2.2 if hl else 1.4}"/>'
            )
            parts.append(
                f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-size="15" '
                f'fill="#e8d5a3">{icon}</text>'
            )
            label = f"{name} (fallen)" if ruin else name
            labelfill = "#f4e3b2" if hl else ("rgba(150,160,185,.8)" if ruin else "#d8cfa8")
            parts.append(
                f'<text x="{x}" y="{y + 36}" text-anchor="middle" font-size="12.5" '
                f'fill="{labelfill}" font-family="Georgia, serif" '
                f'font-style="italic">{label}</text>'
            )
        parts.append("</g>")

    # the Heirs as small lights gathered just below each place icon; name tags
    # are drawn from the packed rows precomputed above (route labels avoid
    # them). A bright outer ring + dark outline keep each Heir visible over
    # the area icons and their fading glows.
    for loc, cids in by_city.items():
        cx, cy = ALL_POS[loc]
        xs = city_xs[loc]
        fan_y = cy + FAN_DY
        for k, cid in enumerate(cids):
            x = xs[k]
            col = color_of[cid]
            name = heir_names.get(cid, cid)
            initial = name[0].upper() if name else "?"
            parts.append(f'<g{_d("heir", cid)}>')
            parts.append(
                f'<circle cx="{x:.1f}" cy="{fan_y}" r="9.5" fill="none" '
                f'stroke="rgba(247,237,214,.4)" stroke-width="1"/>'
            )
            parts.append(
                f'<circle cx="{x:.1f}" cy="{fan_y}" r="6.5" fill="{col}" '
                f'stroke="#0b0a14" stroke-width="1.6"/>'
            )
            parts.append(
                f'<text x="{x:.1f}" y="{fan_y + 4.5}" text-anchor="middle" font-size="9" '
                f'fill="#0b0a14" font-weight="bold" font-family="Arial">{initial}</text>'
            )
            if cid in guest_ids:
                # a visitor from beyond Amphoreus (the Trailblazer's own) —
                # a dashed halo around their light, distinct from a resident.
                parts.append(
                    f'<circle cx="{x:.1f}" cy="{fan_y}" r="12.5" fill="none" '
                    f'stroke="{col}" stroke-width="1" stroke-dasharray="2 3" opacity=".85"/>'
                )
                parts.append(
                    f'<text x="{x:.1f}" y="{fan_y - 11}" text-anchor="middle" font-size="8.5" '
                    f'fill="{col}" font-family="Arial">✦</text>'
                )
            parts.append("</g>")
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
        # We show them mid-route toward 'to' (a Dawn-era form counts too)
        if to in ALL_POS:
            # find their departure: any location adjacent on the route
            tx, ty = ALL_POS[to]
            parts.append(f'<g{_d("heir", cid)}>')
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
            parts.append("</g>")

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
