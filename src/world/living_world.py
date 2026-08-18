"""living_world.py — the second layer of the little Amphoreus's life.

The first layer (world_events.py) gave the world rumors, letters, life
projects, canon-checked NPCs and black-tide surges. This module adds the
features the visitor asked for to make the world *vivid* and the Heirs more
*human* — all as pure data + logic, never authoring an Heir's action:

- **Black tide as a live threat** (A2) — an OPTIONAL toggle; when on, a surge
  slows travel into the edge cities and weighs on the Heirs who live there.
- **Market & gift economy** (A3) — each city's market offers region-flavored
  wares; a gift becomes a durable memory for the Heir who receives it.
- **Mailbox / bulletin board** (A4) — a persistent place where letters and
  notices (including Heirs reaching out to the visitor) accumulate.
- **Living named NPCs** (A5) — each canon-checked resident has a small arc
  that advances across the days.
- **Persistent mood** (B1) — an Heir's emotional weather, derived from the
  world and the visitor, decaying back toward calm.
- **Proactive reach-out** (B2) — sometimes an Heir thinks of the visitor and
  leaves a note on their own.
- **Slow-burn personal arcs** (B4) — the deeper story each Heir shares only as
  the bond deepens.
- **Value-based hurt & reconcile** (B5) — words that cross an Heir's values
  sting and are remembered; an honest apology can mend them.
- **Story-beat recall** (B6) — a shared moment the Heir may find themselves
  remembering, re-narrated in the present.
- **Gossip & relationship deltas** (B7) — telling one Heir about another
  travels through the social web and shifts the bond between them.
- **Sensory grounding** (B8) — the sky, the hour, and the Heir's own mood
  colour how the day feels where they stand.
"""

from typing import Dict, List, Optional

from .world_state import _day_index

# --------------------------------------------------------------------------- #
# Small stable helpers
# --------------------------------------------------------------------------- #
def _seed(text: str) -> int:
    s = 0
    for ch in text:
        s = (s * 31 + ord(ch)) & 0x7FFFFFFF
    return s


FRIENDSHIP_ORDER = ["stranger", "acquaintance", "friend", "close friend", "best friend"]


def _bond_rank(level: str) -> int:
    try:
        return FRIENDSHIP_ORDER.index((level or "stranger").lower())
    except ValueError:
        return 0


# --------------------------------------------------------------------------- #
# A2 — Black tide as a live threat (optional toggle)
# --------------------------------------------------------------------------- #
def black_tide_enabled(world) -> bool:
    """Whether the live black tide is currently switched on. Defaults to on;
    the visitor mode exposes it as an OPTIONAL toggle."""
    return bool(getattr(world, "black_tide_enabled", True))


def surge_consequence_line(world, character_id: str) -> str:
    """The weight a live surge puts on an Heir who stands in a surged city."""
    try:
        from . import world_events as _wev
    except Exception:
        return ""
    if not black_tide_enabled(world) or not _wev.surge_active(world):
        return ""
    if world.location_name(character_id) in world.surge.get("cities", []):
        return ("The black tide presses at the edge of this place; the sky is "
                "heavy with it, and you carry a quiet weariness.")
    return ""


def surge_travel_penalty(world, destination: str) -> int:
    """A live surge adds one extra day of travel into a surged edge city."""
    try:
        from . import world_events as _wev
    except Exception:
        return 0
    if not black_tide_enabled(world) or not _wev.surge_active(world):
        return 0
    return 1 if destination in world.surge.get("cities", []) else 0


def wind_down_surge(world):
    """Turning the live black tide OFF clears any active surge and the darkened
    skies it left in the Keeper's weather, so the world visibly returns to
    peace (not just a flag flip)."""
    world.surge = {"active": False, "remaining": 0, "cities": []}
    try:
        weather = world.ambient.setdefault("weather", {})
        for city in list(weather):
            sky = str(weather.get(city) or "")
            if "black tide" in sky:
                cleaned = sky.split(", and the black tide")[0].strip()
                weather[city] = cleaned or "clear"
        world.ambient["weather"] = weather
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# A3 — Market & gift economy
# --------------------------------------------------------------------------- #
MARKETS: Dict[str, List[dict]] = {
    "Okhema": [
        {"name": "a length of woven silk", "note": "golden thread from the holy city's looms"},
        {"name": "a jar of fragrant oil", "note": "pressed from Okhema's garden blooms"},
        {"name": "a small bronze mirror", "note": "polished to catch the Dawn Device's light"},
    ],
    "Janusopolis": [
        {"name": "a twin-keyed charm", "note": "for doors that open both ways"},
        {"name": "a festival lantern", "note": "painted with a child's question"},
        {"name": "a gate-stone", "note": "worn smooth by every threshold it has crossed"},
    ],
    "Castrum Kremnos": [
        {"name": "a whetstone from the forge", "note": "still warm from the fires"},
        {"name": "a clasp of Kremnos steel", "note": "simple, unbreakable"},
        {"name": "a flask of strong Kremnos wine", "note": "for the road, or the arena"},
    ],
    "Grove of Epiphany": [
        {"name": "a pressed sprig of the Grove", "note": "kept between the pages of a book"},
        {"name": "a bound sheaf of blank pages", "note": "for a scholar's next truth"},
        {"name": "a jar of Grove honey", "note": "gathered where reason grows wild"},
    ],
    "Styxia": [
        {"name": "a pale shore-pearl", "note": "the sea keeps giving them back"},
        {"name": "a mourning bell", "note": "small, and very still"},
        {"name": "a sprig of still-water reed", "note": "for the departed, or the living"},
    ],
    "Aidonia": [
        {"name": "a candle for the quiet", "note": "burns low and long"},
        {"name": "a garland of dried flowers", "note": "the dead are remembered with them"},
        {"name": "a smooth river-stone", "note": "from the water's edge at twilight"},
    ],
    "Aedes Elysiae": [
        {"name": "a bundle of wheat", "note": "from the village that survived"},
        {"name": "a wooden sword, small and worn", "note": "a child's, once"},
        {"name": "a wildflower crown", "note": "woven from the meadow"},
    ],
    "Dawncloud": [
        {"name": "a Sunborn brooch", "note": "bright, orderly, warm"},
        {"name": "a phial of clear light", "note": "it catches the dawn and keeps it"},
        {"name": "a length of white ribbon", "note": "for the ones who wait"},
    ],
}

_GENERIC_WARES = [
    {"name": "a small wrapped sweet", "note": "from the nearest stall"},
    {"name": "a twist of dried herbs", "note": "fragrant and honest"},
    {"name": "a polished pebble", "note": "kept warm in the pocket"},
]


def market_for(world, city: str) -> List[dict]:
    """The wares on offer in a city (region-flavored, generic elsewhere)."""
    return MARKETS.get(city, _GENERIC_WARES)


def give_gift(world, memory, character_id: str, gift_name: str) -> dict:
    """The visitor gives an Heir a gift. It becomes a durable memory and
    warms the Heir's mood. Returns a summary for the UI/chat."""
    clean = (gift_name or "").strip()
    if not clean:
        return {"given": False, "reason": "no gift chosen"}
    world_name = world.name_of(character_id)
    mood_reason = f"the visitor brought you a gift"
    set_mood(world, character_id, 1, mood_reason)
    try:
        memory.add_memory(
            character_id,
            mtype="gift",
            content=f"The visitor gave you {clean}.",
            importance=3,
        )
    except Exception:
        pass
    return {
        "given": True,
        "heir": world_name,
        "gift": clean,
        "mood": mood_of(world, character_id).get("name"),
    }


def gifts_given(memory, character_id: str, limit: int = 6) -> List[str]:
    try:
        return [m["content"] for m in
                memory.get_memories(character_id, mtype="gift", limit=limit)]
    except Exception:
        return []


# --------------------------------------------------------------------------- #
# A4 — Mailbox / bulletin board
# --------------------------------------------------------------------------- #
def post(world, to: str, from_name: str, text: str, kind: str = "letter") -> dict:
    """Leave a message in the mailbox (to 'visitor' or an Heir id)."""
    entry = {
        "to": to,
        "from": from_name,
        "text": text[:400],
        "kind": kind,
        "ts": world.clock.format_short(),
        "read": False,
    }
    box = getattr(world, "mailbox", None)
    if box is None:
        world.mailbox = []
        box = world.mailbox
    box.append(entry)
    del box[:-40]
    return entry


def mailbox_for(world, to: str) -> List[dict]:
    return [m for m in getattr(world, "mailbox", []) if m.get("to") == to]


def unread_count(world, to: str) -> int:
    return sum(1 for m in mailbox_for(world, to) if not m.get("read"))


def mark_all_read(world, to: str):
    for m in mailbox_for(world, to):
        m["read"] = True


# --------------------------------------------------------------------------- #
# A5 — Living named NPCs with small arcs
# --------------------------------------------------------------------------- #
NPC_ARCS: Dict[str, dict] = {
    "Bartholos": {
        "stages": [
            "Bartholos sets out a fresh stall of odd goods and watches the crowd with a merchant's patience.",
            "Bartholos is heard muttering that someone owes him a secret — and he means to collect it.",
            "Bartholos trades a fine secret for a string of coins, and smiles like a man who knows more than he sells.",
        ],
    },
    "Seliose": {
        "stages": [
            "Seliose dusts Hyacine's old notes and tidies the Grove's quiet corners.",
            "Seliose finds a page she thought lost, and reads it twice, softly.",
            "Seliose passes a small truth on to a younger scholar, the way it was once passed to her.",
        ],
    },
    "Noldus": {
        "stages": [
            "Noldus greets the travelers at the gates of Janusopolis, learning every name.",
            "Noldus mends a hinge on an old threshold and hums to himself while he works.",
            "Noldus is seen opening a gate no one else remembers how to open.",
        ],
    },
    "Researcher Eikura Shuu": {
        "stages": [
            "Researcher Eikura Shuu fills another notebook with tireless questions about the ruins.",
            "Eikura Shuu sketches a ruin's broken sigil and frowns at what it might have meant.",
            "Eikura Shuu closes a notebook with a satisfied nod — one question fewer, many more in its place.",
        ],
    },
    "Mem": {
        "stages": [
            "Mem drifts at the village's edge, holding memories the world has dropped.",
            "Mem gathers a few small, half-forgotten things and keeps them safe.",
            "Mem lets a memory go where it belongs, and seems a little lighter.",
        ],
    },
    "Theodosia": {
        "stages": [
            "Theodosia lays the departed to rest, speaking to them as she works.",
            "Theodosia sets a small stone for someone no one else remembers.",
            "Theodosia finishes her work and sits by the water, saying nothing at all.",
        ],
    },
}


def npc_stage(world, name: str) -> int:
    st = getattr(world, "npc_states", None) or {}
    return st.get(name, {}).get("stage", 0)


def npc_line(world, name: str) -> str:
    arc = NPC_ARCS.get(name)
    if not arc:
        return ""
    stages = arc["stages"]
    return stages[min(npc_stage(world, name), len(stages) - 1)]


def advance_npcs(world) -> List[str]:
    """Occasionally move one resident's small story forward. Returns lines for
    the Chronicle (a finished arc rests and starts again, renewed)."""
    import random
    if random.random() < 0.5:
        return []
    name = random.choice(list(NPC_ARCS.keys()))
    st = getattr(world, "npc_states", None)
    if st is None:
        world.npc_states = {}
        st = world.npc_states
    entry = st.setdefault(name, {"stage": 0})
    arc = NPC_ARCS[name]
    milestone = f"{name} — {arc['stages'][min(entry['stage'], len(arc['stages'])-1)]}"
    entry["stage"] += 1
    if entry["stage"] >= len(arc["stages"]):
        entry["stage"] = 0  # the small story begins again
    return [milestone]


# --------------------------------------------------------------------------- #
# B1 — Persistent mood
# --------------------------------------------------------------------------- #
MOOD_NAMES = {
    3: "radiant",
    2: "bright",
    1: "warm",
    0: "calm",
    -1: "weary",
    -2: "troubled",
    -3: "wounded",
}


def _clamp(v: int) -> int:
    return max(-3, min(3, v))


def set_mood(world, character_id: str, delta: int, reason: str = ""):
    m = getattr(world, "mood", None)
    if m is None:
        world.mood = {}
        m = world.mood
    cur = m.get(character_id, {"valence": 0, "reason": "", "ts": ""})
    valence = _clamp(cur.get("valence", 0) + delta)
    m[character_id] = {
        "valence": valence,
        "reason": reason[:200] or cur.get("reason", ""),
        "ts": world.clock.format_short(),
    }


def mood_of(world, character_id: str) -> dict:
    m = getattr(world, "mood", None) or {}
    e = m.get(character_id, {"valence": 0, "reason": "", "ts": ""})
    return {
        "valence": e.get("valence", 0),
        "name": MOOD_NAMES.get(_clamp(e.get("valence", 0)), "calm"),
        "reason": e.get("reason", ""),
        "ts": e.get("ts", ""),
    }


def advance_moods(world):
    """Daily decay: moods drift back toward calm unless something holds them."""
    m = getattr(world, "mood", None)
    if not m:
        return
    for cid, e in list(m.items()):
        v = e.get("valence", 0)
        if v == 0:
            continue
        v = v - 1 if v > 0 else v + 1
        if v == 0:
            m[cid] = {"valence": 0, "reason": "", "ts": e.get("ts", "")}
        else:
            m[cid]["valence"] = v


def mood_block(world, character_id: str) -> str:
    """A prompt block letting the Heir's mood colour — not command — their voice."""
    mo = mood_of(world, character_id)
    surge = surge_consequence_line(world, character_id)
    if mo["valence"] == 0 and not surge:
        return ""
    if surge and mo["valence"] == 0:
        return (
            "\n\n# How you feel today\n"
            f"{surge} You are yourself, only heavier for it."
        )
    reason = f" — {mo['reason']}" if mo["reason"] else ""
    lines = ["\n\n# How you feel today",
             f"You feel {mo['name']}{reason}."]
    if surge:
        lines.append(surge)
    lines.append("Let it colour, not command, how you speak; you are still yourself.")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# B2 — Proactive reach-out
# --------------------------------------------------------------------------- #
def should_reach_out(clock, character_id: str) -> bool:
    """A deterministic ~1-in-9-days chance that this Heir thinks of the
    visitor and leaves a note on their own (same answer in every process)."""
    return (_seed(character_id) + _day_index(clock)) % 9 == 0


_REACH_OUT_TEMPLATES = [
    "I thought of you today. If your road brings you to {city}, you would find me there.",
    "It is {hour} here, and I found myself wondering how your journey goes. Come by when you like.",
    "I kept something for you — come and see, when the road allows.",
    "The {season} season has its own quiet. I thought you might like to hear it.",
    "You have been on my mind. The door here is open to you.",
]


def reach_out_text(world, character_id: str) -> str:
    k = _seed(character_id) % len(_REACH_OUT_TEMPLATES)
    return _REACH_OUT_TEMPLATES[k].format(
        city=world.location_name(character_id),
        hour=world.clock.period_name.lower(),
        season=world.clock.season.lower(),
    )


def reach_out(world, character_id: str) -> Optional[dict]:
    """If today is the Heir's day to think of the visitor, leave a note in the
    mailbox (deduped per Heir per day)."""
    if not should_reach_out(world.clock, character_id):
        return None
    name = world.name_of(character_id)
    today = world.clock.format_short()
    for m in mailbox_for(world, "visitor"):
        if m.get("from") == name and m.get("ts") == today:
            return None  # already left a note today
    return post(world, "visitor", name, reach_out_text(world, character_id),
                kind="reach-out")


def materialize_reach_outs(world) -> List[str]:
    """Post today's deterministic reach-outs into the mailbox (deduped per Heir
    per day). Idempotent, so the UI can call it on any load and the mailbox
    stays alive even when the world engine is not running."""
    posted: List[str] = []
    for cid in list(world.present_locations()):
        try:
            if reach_out(world, cid):
                posted.append(cid)
        except Exception:
            continue
    return posted


def warm_on_visit(world, character_id: str):
    """A warm, substantive visit lifts the Heir's mood a little."""
    set_mood(world, character_id, 1, "a warm visit from the star-stranger")


# --------------------------------------------------------------------------- #
# B4 — Slow-burn personal arcs (bond-gated layers of each Heir's story)
# --------------------------------------------------------------------------- #
ARCS: Dict[str, dict] = {
    "aglaea": {
        "title": "The threads she will not weave",
        "stages": [
            "You carry the memory of a girl who was afraid of the dark and of ghosts, long before she learned to weave golden threads.",
            "You have seen what duty costs, and you choose it anyway — the city's threads before your own.",
            "You do not weave the fate you fear most. There are threads even the Golden Weaver leaves untouched.",
        ],
    },
    "anaxa": {
        "title": "A truth that outlives the myth",
        "stages": [
            "Your sister Diotima believed in you before anyone else did, and she died to the black tide.",
            "You love reason because it is the one thing that never asked you to believe without proof.",
            "You know the world was built on the ruins of an older one. You keep asking what the myth was for.",
        ],
    },
    "castorice": {
        "title": "The garden of the still",
        "stages": [
            "Your touch is death, and so you learned gentleness the way others learn speech.",
            "You tend the graves and mourning places of Aidonia because someone must remember the quiet ones.",
            "You made a promise to someone — with your own hands — and you mean to keep it.",
        ],
    },
    "cerydra": {
        "title": "The game well played",
        "stages": [
            "You were shaped to be a piece on a board, and you resolved instead to learn the whole game.",
            "You once asked your sharpest blade what she would do if you ordered her to turn it against you. You still think about her answer.",
            "You know the price of the moves you have made, and you pay it without flinching.",
        ],
    },
    "cipher": {
        "title": "The one last locked door",
        "stages": [
            "You were a pawn once, before the three hundred rogues taught you that family is a thing you choose.",
            "You keep moving so no one can chain you down — duty, fate, or anything heavier than loose change.",
            "There is one vault you have never opened. You are not sure you want to.",
        ],
    },
    "cyrene": {
        "title": "A story kept alive",
        "stages": [
            "You have watched the same story begin a thousand times, and you remember every one.",
            "You play and tell fortunes because the children must believe the world can still surprise them.",
            "You know how the script ends. You keep telling it anyway, because being remembered is a kind of living.",
        ],
    },
    "dan-heng-permansor-terrae": {
        "title": "The Archiver's record",
        "stages": [
            "You carry the Terravox — the Permansor — and with it the weight of recording worlds as they truly are.",
            "You protect your companions before yourself; bearing witness is its own duty.",
            "You are writing Amphoreus down so that it is not forgotten, exactly as it was and as it is now.",
        ],
    },
    "evernight": {
        "title": "The garden of recollection",
        "stages": [
            "You gather the memories the world almost forgot, because forgetting is the only death you cannot abide.",
            "You watched thirty million futile lives once, and you understood a story could be fuel for ruin.",
            "You keep watch for the ones you love — March, and the Trailblazer, and the light that must not go out.",
        ],
    },
    "hyacine": {
        "title": "The healer's path",
        "stages": [
            "You chose healing because you could not bear preventable suffering, not because it was gentle.",
            "You have held the truth about the past in your hands and still chose to speak of tomorrow.",
            "You would have given your life for the Trailblazer's — you keep that willingness close.",
        ],
    },
    "hysilens": {
        "title": "A song for the sea",
        "stages": [
            "Your city drowned, and you are still composing its requiem.",
            "You once snuffed out the flame you swam toward, and you have not finished asking yourself why.",
            "You left your violin, your chessboard and your lyre in Aglaea's workshop. A part of you stayed there too.",
        ],
    },
    "mydei": {
        "title": "The spear that guards",
        "stages": [
            "You slew your own father, and Kremnos calls that tradition. You have never pretended it was clean.",
            "You measure the world in honor and in strength, and you distrust every title you did not earn.",
            "You entrusted your people to a rival you came to respect — the deepest vow a warrior can make.",
        ],
    },
    "phainon": {
        "title": "A world at peace",
        "stages": [
            "You were told you had golden blood, and you believed it — until you learned what that meant.",
            "You never wanted to be called a hero. You wanted the village, the wheat, and the ones you love to be safe.",
            "You pass the torch on, because a Deliverer's work is not to rule but to make sure the peace holds.",
        ],
    },
    "tribbie": {
        "title": "A thousand questions",
        "stages": [
            "You carry a thousand voices and a thousand questions, because a closed door is the one thing you cannot bear.",
            "You dream of your mother, and of reuniting with her at the gates.",
            "You taught a frightened girl that even the dark could be walked through, one question at a time.",
        ],
    },
}


def arc_stage(friendship_level: str) -> int:
    """Which layer of the Heir's deeper story is open at this bond.
    -1 = not yet (below friend); 0..2 = the layers shared with trust."""
    rank = _bond_rank(friendship_level)
    if rank >= 4:   # best friend
        return 2
    if rank >= 3:   # close friend
        return 1
    if rank >= 2:   # friend
        return 0
    return -1


def arc_block(world, memory, character_id: str) -> str:
    """A prompt block revealing only the layers of the Heir's story that the
    bond has earned. Never forced — it is what they carry, not a script."""
    arc = ARCS.get(character_id)
    if not arc:
        return ""
    try:
        bond = memory.get_bond(character_id) or {}
    except Exception:
        bond = {}
    stage = arc_stage(bond.get("friendship_level", "stranger"))
    if stage < 0:
        return ""
    depth = ["what you have begun to share",
             "what you have come to share",
             "what, in the deepest trust, you may share"][stage]
    return (
        f"\n\n# What you carry (the deeper story you may share with the visitor)\n"
        f"“{arc['title']}” — {depth}: {arc['stages'][stage]}"
    )


# --------------------------------------------------------------------------- #
# B5 — Value-based hurt & reconcile
# --------------------------------------------------------------------------- #
# (value, [words the visitor might say that cross this value])
HEIR_VALUES: Dict[str, List[tuple]] = {
    "aglaea": [("order and the vows people keep", ["liar", "you lie", "deceit", "faithless"]),
               ("the beauty of what is woven", ["ugly", "worthless", "pointless"])],
    "anaxa": [("reason and truth", ["liar", "you lie", "stupid", "ignorant", "fool"]),
              ("skepticism as love", ["gullible", "you believe anything"])],
    "castorice": [("gentleness toward the departed", ["grave-robb", "defile", "disrespect the dead"]),
                  ("peace and quiet", ["shut up", "too loud", "stop talking"])],
    "cerydra": [("justice and the game well played", ["unfair", "cheat", "injustice", "tyrant"]),
                ("mastery and competence", ["incompetent", "useless", "fool"])],
    "cipher": [("freedom", ["pawn", "slave", "chain", "you belong to"]),
               ("her found family", ["rogue", "thief", "you steal", "criminal"])],
    "cyrene": [("love and being remembered", ["forgotten", "forget you", "nobody remembers"]),
               ("play and wonder", ["boring", "grow up"])],
    "dan-heng-permansor-terrae": [("protecting his companions", ["harm", "hurt them", "betray"]),
                                  ("bearing witness", ["erase", "forget what happened"])],
    "evernight": [("memory as love", ["forget", "oblivion", "erased"]),
                  ("guarding the light", ["darkness", "go out", "extinguish"])],
    "hyacine": [("hope and healing", ["hopeless", "give up", "no cure"]),
                ("tomorrow", ["no future", "all is lost"])],
    "hysilens": [("home and the sea", ["drown", "pollute", "the sea is nothing"]),
                 ("her music", ["noise", "your song is", "stop playing"])],
    "mydei": [("honor and keeping one's word", ["dishonor", "oathbreak", "coward"]),
              ("strength earned, not given", ["weak", "soft", "title"])],
    "phainon": [("protecting the weak", ["hurt them", "crush", "prey"]),
                ("honest work over heroism", ["hero", "golden boy", "fake hero"])],
    "tribbie": [("wonder and open doors", ["close every door", "no more questions", "shut it"]),
                ("the thousand voices of the people", ["silence them", "nobody cares", "the people are nothing"])],
}


def detect_violation(character_id: str, message: str) -> Optional[str]:
    """If the visitor's words cross one of this Heir's values, return the value
    (or None). Conservative on purpose — only clear crossings sting."""
    low = (message or "").lower()
    for value, keywords in HEIR_VALUES.get(character_id, []):
        for kw in keywords:
            if kw.lower() in low:
                return value
    return None


def hurt(world, memory, character_id: str, value: str, message: str):
    set_mood(world, character_id, -2, f"the visitor's words crossed something you hold dear")
    try:
        memory.add_memory(
            character_id,
            mtype="grievance",
            content=(f"The visitor's words stung you — they crossed your value "
                     f"of {value}: \"{message[:160]}\""),
            importance=3,
        )
    except Exception:
        pass


def open_grievance(memory, character_id: str) -> Optional[str]:
    try:
        items = memory.get_memories(character_id, mtype="grievance", limit=3)
    except Exception:
        return None
    if not items:
        return None
    # the newest entry is the current state — a reconciliation closes it.
    newest = items[-1]
    content = newest.get("content", "")
    if "forgiven" in content.lower():
        return None
    return content


def reconcile(world, memory, character_id: str) -> bool:
    g = open_grievance(memory, character_id)
    if not g:
        return False
    set_mood(world, character_id, 2, "the visitor made things right between you")
    try:
        memory.add_memory(
            character_id,
            mtype="grievance",
            content="The visitor apologized, and it is forgiven.",
            importance=2,
        )
    except Exception:
        pass
    return True


_APOLOGY_WORDS = ("i'm sorry", "i am sorry", "forgive me", "my apologies",
                  "i apologize", "i was wrong", "i shouldn't have")


def is_apology(message: str) -> bool:
    low = (message or "").lower()
    return any(w in low for w in _APOLOGY_WORDS)


def grievance_block(world, memory, character_id: str) -> str:
    """An unresolved hurt the Heir carries honestly (not theatrically)."""
    g = open_grievance(memory, character_id)
    if not g:
        return ""
    return (
        "\n\n# An unresolved hurt\n"
        f"{g} It still sits with you. You may carry it quietly, or let it "
        "colour your words — honestly, as you are."
    )


# --------------------------------------------------------------------------- #
# B6 — Story-beat recall
# --------------------------------------------------------------------------- #
_RECALL_INTROS = [
    "You find yourself remembering",
    "It comes back to you that",
    "A small thing reminds you",
    "You recall, not for the first time,",
    "It surfaces, quiet and sure:",
]


def recall(world, memory, character_id: str) -> Optional[str]:
    """A shared moment the Heir may spontaneously remember, re-phrased today."""
    try:
        pool = memory.get_memories(character_id, limit=40, min_importance=2)
    except Exception:
        return None
    meaningful = [m for m in pool
                  if m.get("mtype") in ("moment", "gift", "preference", "teaching")
                  and "grievance" not in m.get("content", "").lower()]
    if not meaningful:
        return None
    import random
    m = random.choice(meaningful)
    intro = _RECALL_INTROS[_day_index(world.clock) % len(_RECALL_INTROS)]
    return f"{intro} {m['content']}"


def recall_block(world, memory, character_id: str) -> str:
    r = recall(world, memory, character_id)
    if not r:
        return ""
    return (
        "\n\n# A memory that may surface\n"
        f"{r}\n"
        "(If it feels natural, let it touch what you say — you are not required to repeat it.)"
    )


# --------------------------------------------------------------------------- #
# B7 — Gossip & relationship deltas between Heirs
# --------------------------------------------------------------------------- #
def gossip(world, from_cid: str, to_cid: str, note: str):
    """The visitor told one Heir about another; it travels to the one spoken
    of, and the bond between the two Heirs shifts a little."""
    if from_cid == to_cid:
        return
    try:
        from . import world_events as _wev
        rumor = (f"{world.name_of(from_cid)} heard from the star-stranger about you — {note}")
        _wev.add_rumor(world, to_cid, rumor, source="the star-stranger")
        _wev.adjust_relationship(world, from_cid, to_cid, 1)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# B8 — Sensory grounding
# --------------------------------------------------------------------------- #
def sensory_block(world, character_id: str) -> str:
    """The sky, the hour, and the Heir's mood — how the day feels where they
    stand right now."""
    loc = world.location_name(character_id)
    weather = world.ambient_weather(loc) or world.sensory_text(loc).split(": ", 1)[-1][:140]
    mo = mood_of(world, character_id)
    parts = [f"- The air here: {weather}"]
    parts.append(f"- The hour: {world.clock.period_name}.")
    if mo["valence"] != 0:
        parts.append(f"- You carry yourself as one who is {mo['name']} today.")
    return "\n".join(parts)
