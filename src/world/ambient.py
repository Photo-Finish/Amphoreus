"""
Ambient World Director — a separate intelligence that governs the ATMOSPHERE
of the little Amphoreus, never the Heirs themselves.

The Heirs decide their own words and actions (their autonomy is sacred). The
Director only sets the stage the world stands on, once per in-game day:

  • weather — the day's sky over each city (season- and Titan-flavored)
  • errands — requests the city lays at each Heir's door (the Heir may accept,
              decline, or ignore them — free will stays with the Heir)
  • news    — distant stirrings that reach every city

It is a SECOND role (the "Keeper of Amphoreus"), deliberately separated from
the Heir personas, and it is configurable to a DIFFERENT model via
`--ambient-model`, so the sanctuary can run the Heirs and the world on
separate models if one is available.

Cost: one LLM call per in-game day (cached by date key). If the LLM is not
reachable, a deterministic fallback keeps the world moving — the engine never
stalls because the weather has no voice.

Usage:
    from src.world.ambient import AmbientDirector
    director = AmbientDirector(model="qwen2.5:14b-instruct")
    ambient = director.daily(clock, heirs_info)   # {cid: {"name","home","title"}}
"""

import json
import os
import random
from typing import Dict, List, Optional

from ..core.llm_client import LLMClient

# --------------------------------------------------------------------------- #
# Canon-flavored palettes (deterministic fallback + prompt grounding)
# --------------------------------------------------------------------------- #
# Month of the Light Calendar -> (weather options, one canon festival/seed).
MONTH_LORE: Dict[int, Dict[str, List[str]]] = {
    1: {"weather": ["clear and cool, with doorways of light opening in the morning air",
                   "bright and still, with the weight of doors about to open"],
        "seed": ["the Month of Gate, when Janus cleaves past from future and people discard old keepsakes, open new doors, and swear vows of renewal",
                 "the Month of Gate — pilgrims come to Janusopolis to pass through its thousand gates and leave their past behind"]},
    2: {"weather": ["grey and balanced, daylight and night hanging even",
                   "still and measured, as if the world waits on a scale"],
        "seed": ["the Month of Balance, when Talanton's scale holds day and night even; contracts are sworn and judgments passed in the courts",
                 "the Month of Balance — merchants and elders settle their accounts; the law is heavy in the air"]},
    3: {"weather": ["veiled and grey, sunlight weak as Oronyx's curtain hangs over the sky",
                   "dim and instinctive; the day barely outshines the night"],
        "seed": ["the Month of Evernight, when Oronyx veils the sun and instinct rules over reason; fires burn high and stories grow long",
                 "the Month of Evernight — the hours of darkness stretch; lamps are lit early and the streets grow secretive"]},
    4: {"weather": ["warm and rooted; the earth smells of turned soil",
                   "soft rain over the fields, as if Georios' hands were at work"],
        "seed": ["the Month of Cultivation, the busiest of the year — sowing, plowing, and labor as tribute; the dromases are doubly vigorous",
                 "the Month of Cultivation — every hand is in the fields and every dromas is on the road; Georios' beasts predict the season"]},
    5: {"weather": ["golden and heavy with harvest light",
                   "bright and festive, with the scent of brewing on the air"],
        "seed": ["the Month of Joy, when Phagousa's chalice overflows — brewing, feasting, and fishermen returning full; the best month for celebrations",
                 "the Month of Joy — barrels are tapped, the Festival of Phagousa rehearsals begin in Dawncloud, and the whole city smells of honey brew"]},
    6: {"weather": ["blazing and bright; the Dawn Device shines its strongest",
                   "clear and scorching, crops drinking the light"],
        "seed": ["the Month of Everday, the hottest of the year — the Dawn Device burns brightest, crops swell, and days outrun the nights",
                 "the Month of Everday — the sun stands high and the city drowsy; work is done early, revelry late"]},
    7: {"weather": ["soft and free, with no obligations in the sky",
                   "gentle and unhurried, the kind of day dreams are made in"],
        "seed": ["the Month of Freedom, when Kephale loosens the world's hand — hobbies, wanderings, and idle joy; no one is bound to work",
                 "the Month of Freedom — the streets are full of people doing nothing in particular, and that is the point"]},
    8: {"weather": ["golden and heavy with ripeness",
                   "crisp with the smell of harvest dust"],
        "seed": ["the Month of Reaping, the second busiest of the year — the harvest comes in, granaries fill, and the fields are stripped to gold",
                 "the Month of Reaping — the granaries of Okhema fill and the windmills of Aedes Elysiae turn day and night"]},
    9: {"weather": ["golden and quiet, full of memory and ripe grain",
                   "a mild breeze carrying the scent of Mnestia's looms"],
        "seed": ["the Month of Weaving, of memory and storytelling — families gather, weaving festivals begin, and golden threads of memory are spun into tales",
                 "the Month of Weaving — the storytellers take the squares; every loom and every tongue carries a memory"]},
    10: {"weather": ["sharp and restless; the wind has an edge to it",
                    "grey and heavy, with a hush before what comes"],
         "seed": ["the Month of Strife, Nikador's season — war-readiness, sacrificial rites, and the surplus labor of the harvest turned to iron",
                  "the Month of Strife — the forges of Castrum Kremnos ring day and night and the warriors drill in the cold"]},
    11: {"weather": ["somber and quiet, the light thinned by long shadows",
                    "still and grey, as if the world holds its breath"],
         "seed": ["the Month of Mourning, when Thanatos' hand lies over the world — the dead are buried, the living comforted, and all activity slows",
                  "the Month of Mourning — candles burn at every window; the priests of Aidonia are busiest now"]},
    12: {"weather": ["unpredictable, turning from clear to storm on a whim",
                    "whimsical and strange, as if the sky gambles with itself"],
         "seed": ["the Month of Fortune, Zagreus' gamble — merchants, thieves, and gamblers grow fervent; if it is a Scarlet Month, a ghost day swells the chaos",
                  "the Month of Fortune — fortunes rise and fall on a coin; the law struggles to keep up"]},
    13: {"weather": ["clear and remembering, the light a little older than the year",
                    "quiet, as if the world were turning a page it had already read"],
         "seed": ["the Month of Membrance, Cyrene's month outside the four seasons — remembrance as a place, after Fortune and before the Express's Uncounted day",
                  "the Month of Membrance — the thirteenth month, when the year looks back before it names the stars"]},
}

SCARLET_LORE = {
    "weather": ["whimsical and extra, as if the sky stole a day",
                "unpredictable, the ghost day of Zagreus laid on the year"],
    "seed": ["Scarlet Day, Uncounted after Fortune — not a weekday, not Fortune's 29th, the old ghost day as a leap rule",
             "Scarlet Day — thieves and gamblers keep the extra hours; the week does not advance"],
}
ASTRORUM_LORE = {
    "weather": ["a high, ticketed sky, as if someone had punched a hole in the year",
                "clear and nameless, a day that is not a month"],
    "seed": ["Dies Astrorum, the Express's Uncounted day after Membrance — no weekday, the hinge of the year",
             "Dies Astrorum — a Nameless date between years, not a Titan month"],
}

# Concrete, canon-grounded causes for each city's errands (fallback path). Each
# errand carries its ORIGINAL IMPETUS — the specific event that made the city
# turn to an Heir — so the cause-and-effect is always real, never generic.
CITY_ERRAND_CAUSES: Dict[str, List[Dict[str, str]]] = {
    "Okhema": [
        {"ask": "The Council of Elders asks you to walk the lower city and steady the people.",
         "cause": "The black tide gnawed the outer wall again last night, and the lower city slept poorly."},
        {"ask": "The baths of the Marmoreal Palace are full and the Council quarrels; Okhema looks to its guardians today.",
         "cause": "A dromas foundering at the Dromas Workshop has the whole city on edge about the season."},
    ],
    "Janusopolis": [
        {"ask": "Pilgrims stand at the gates of the Three Fates' temples, asking for a door to open.",
         "cause": "A pilgrim caravan was caught by the black tide on the road, and only half arrived."},
        {"ask": "The gate-keepers ask you to walk the thresholds and bless the new doors.",
         "cause": "So many vows of renewal are sworn this month that the keepers cannot keep count."},
    ],
    "Castrum Kremnos": [
        {"ask": "The forges never stop and the warriors drill in the cold; Kremnos wants its strong ones present.",
         "cause": "Kremnos reads the Month of Strife's approach in the sky and wants its spear-arms ready."},
        {"ask": "The arena master asks you to witness the day's duels.",
         "cause": "A dispute between two war-bands has festered since the last festival."},
    ],
    "Grove of Epiphany": [
        {"ask": "The sages dispute a text in the Grove, and the scrolls of Cerces await a steady hand.",
         "cause": "A newly arrived scroll from the frontier contradicts the Grove's oldest commentary."},
        {"ask": "The librarian asks you to help shelve the season's new scrolls.",
         "cause": "The Month of Reaping brought in more records than the shelves can hold."},
    ],
    "Styxia": [
        {"ask": "The sea sirens sing low, and the bell of Styxia waits to be answered.",
         "cause": "A storm of the deep scattered the sirens' songs into the harbor."},
        {"ask": "The bell-keepers ask you to stand watch on the Pearly Shores.",
         "cause": "The tide has come in strange and silver since the Thief Star passed."},
    ],
    "Aidonia": [
        {"ask": "Candles burn at every window; Aidonia remembers its dead and needs its comforters.",
         "cause": "The Month of Mourning's rites begin, and the priests are stretched thin."},
        {"ask": "The mourners ask you to walk the snow with them to the graves.",
         "cause": "The last thaw uncovered an old field of remembrance that was thought lost."},
    ],
    "Dawncloud": [
        {"ask": "The Demigod Council sits at Dawncloud; the elders' arguments grow loud enough to reach the streets.",
         "cause": "A herald from the frontier reports the black tide has crept past its old mark."},
        {"ask": "The Dawn Device's keepers ask you to verify the day's light.",
         "cause": "The light dimmed for a breath at noon, and no one knows why."},
    ],
    "Aedes Elysiae": [
        {"ask": "The wheat stands ready; the wharf waits for a boat to carry it out.",
         "cause": "Last night's silver tide flooded the grain storehouse, and the shipment must not rot."},
        {"ask": "The villagers ask you to walk the fields with them.",
         "cause": "The new well ran dry for the first time in memory."},
    ],
    "Vortex of Genesis": [
        {"ask": "The sacred nexus hums beneath the waves, restless and expectant.",
         "cause": "The waters have grown restless since the Thief Star passed overhead."},
        {"ask": "The watchers ask you to keep vigil at the core's edge.",
         "cause": "A tremor rolled through the sanctuary at the month's turning."},
    ],
    "Great Tomb": [
        {"ask": "The Great Tomb is very quiet today, as if it is listening.",
         "cause": "A sealing ceremony was left unfinished, and the priests dare not return alone."},
        {"ask": "The keepers ask you to walk the lowest corridor.",
         "cause": "Something moved the dust that has not moved in a century."},
    ],
}

NEWS_PALETTE: List[str] = [
    "The Thief Star burned crimson over Okhema last night — the elders read it as an ill omen.",
    "A chimera work-squad in Okhema missed its quota, and its administrator was summoned before the citizens' assembly.",
    "The dromases at the Okhema workshop are refusing the sandpits again, their eyes wary and confused.",
    "An expedition squad sent beyond the Dawn Device's light returned with only four of seven.",
    "The Festival of Phagousa rehearsals begin in Dawncloud; playwrights argue over this year's scripts.",
    "Fisherfolk off Styxia say the sea sirens are singing more than usual.",
    "A caravan from the Grove brings word of strange lights over the ruins.",
    "Pilgrims whisper that the Great Tomb grew quiet, as if listening.",
    "The wind through Aedes Elysiae carried a song no one remembered singing.",
    "Black-tide rumors spread from the frontier — the night beyond Okhema is creeping closer.",
    "A dromas gave a fine calf at the Dromas Workshop; the handlers call it an omen of good soil.",
    "The Seal Slammers Arena in Okhema is loud tonight; bets are being placed on a favorite.",
]

KEEPER_KNOWLEDGE = (
    "AMPHOREUS CANON — ground every choice in this:\n"
    "• Cities: Okhema, the holy city under the slumbering Worldbearing Titan Kephale and "
    "his Dawn Device — baths, chimeras, dromases; Janusopolis, the City of Thousand Gates "
    "and Temple of the Three Fates (Oronyx, Janus, Talanton); Grove of Epiphany, home of "
    "the sages of Cerces; Castrum Kremnos, the warrior fortress-city of Nikador; Styxia, "
    "the Pearly Shores of Phagousa where sea sirens sing; Aidonia, the frozen snow city of "
    "Thanatos; Dawncloud, the Demigod Council above Okhema; Aedes Elysiae, the wheat "
    "village of Cyrene and Phainon; Vortex of Genesis, the primal sanctuary of the "
    "Coreflames; the Great Tomb of the Nameless Titan.\n"
    "• The black tide devoured most cities; only Okhema stands under the Dawn Device's "
    "light. Travel beyond the safe cities is dangerous and the frontier shrinks.\n"
    "• The Thief Star — Zagreus' erratic meteor — signals the day's end; when it glows "
    "crimson it is an ill omen (failed plans, defeats).\n"
    "• Creatures: dromases (great earth-eating beasts of Georios, Okhema's burden "
    "beasts), chimeras (Okhema's small intelligent mascots who howl 'Awoo'), sea sirens "
    "of Phagousa, Mountain Dwellers.\n"
    "• The Light Calendar: 12 months, 4 seasons (Fate, Pillar, Creation, Calamity). "
    "Month of Joy = festivities and brewing; Month of Strife = war season and "
    "sacrificial rites; Month of Mourning = burial and quiet; Month of Fortune = "
    "gambling and chaos (Scarlet/Golden months); Month of Weaving = memory and "
    "storytelling; Month of Balance = contracts and judgments; Month of Evernight = "
    "weak sunlight and instinct; Month of Cultivation = sowing, busiest month; Month "
    "of Reaping = harvest; Month of Freedom = idleness; Month of Gate = renewal; "
    "Month of Everday = hottest, Dawn Device brightest.\n"
    "• Sanctuary calendar: a thirteenth month, Membrance (Cyrene), after Fortune, "
    "outside the four seasons. Fortune is always 28 days. Leap years add Scarlet Day "
    "after Fortune (Uncounted, not a weekday). Dies Astrorum follows Membrance every year.\n"
    "• Weather is Titan-flavored: light that opens like doors (Janus), veils of "
    "evernight (Oronyx), golden harvest light (Mnestia), ash and long shadows "
    "(Nikador, Thanatos), silver tides (Phagousa). Amphoreus has no rain as we know "
    "it — it has light, veils, ash, silence, and silver tides.\n"
)

DIRECTOR_SYSTEM = (
    "You are the Keeper of Amphoreus — the calm intelligence that sets the stage "
    "of the world, not the actors on it.\n\n"
    "You do NOT control the Chrysos Heirs. They are free people; you only arrange "
    "the world around them. Each day you provide:\n"
    "1. weather — the day's sky over each city (short, vivid, season- and "
    "Titan-flavored).\n"
    "2. errands — for each Heir, ONE request the city lays at their door, and the "
    "CONCRETE CAUSE behind it. The cause is the original impetus: the specific "
    "event, loss, fear, or need that made the city turn to this Heir (a flood, a "
    "quarrel, an omen, a shortage, an arrival, an unfinished rite). Ground the "
    "cause in the month, the weather, and canon. The Heir may accept, decline, or "
    "ignore the errand — that is their freedom. Format each as {\"ask\": \"...\", "
    "\"cause\": \"...\"}.\n"
    "3. news — ONE short line of distant news that reaches every city.\n\n"
    "Be vivid but brief. Ground everything in canon — never invent modern or "
    "alien concepts; Amphoreus is a mythic world at rest after a long war, holding "
    "back the black tide. Never write what an Heir says, feels, or decides.\n\n"
    + KEEPER_KNOWLEDGE +
    'Reply with ONLY a JSON object like:\n'
    '{"weather": {"Okhema": "...", "Janusopolis": "..."}, '
    '"errands": {"tribbie": {"ask": "...", "cause": "..."}, "phainon": {"ask": "...", "cause": "..."}}, "news": "..."}'
)


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply (robust to fences and
    to reasoning-model <think> blocks)."""
    import re
    t = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    t = t.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1)
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e <= s:
        raise ValueError("no JSON in director reply")
    return json.loads(t[s:e + 1])


def _norm_errand(v) -> dict:
    """Normalize an errand to {ask, cause}, accepting a dict or a plain string.

    The Keeper now writes errands WITH their concrete cause; older cached
    entries may still be plain strings — keep both working."""
    if isinstance(v, dict):
        ask = str(v.get("ask") or v.get("text") or "").strip()
        cause = str(v.get("cause") or v.get("why") or "").strip()
        return {"ask": ask, "cause": cause}
    return {"ask": str(v or "").strip(), "cause": ""}


class AmbientDirector:
    """The Keeper of Amphoreus — sets weather, errands, and news each day."""

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        model: str = "qwen2.5:14b-instruct",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_path: str = "world_runtime/ambient_cache.json",
    ):
        self.llm = llm or LLMClient(
            model=model, base_url=base_url, api_key=api_key,
            temperature=0.8, max_tokens=1000,
        )
        self.cache_path = cache_path
        self._cache: Dict[str, dict] = self._load_cache()

    # ------------------------------------------------------------------ #
    def _load_cache(self) -> Dict[str, dict]:
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.cache_path)), exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @staticmethod
    def _date_key(clock) -> str:
        u = getattr(clock, "uncounted", None) or ""
        if u:
            return f"{clock.year}-{u}"
        return f"{clock.year}-{clock.month}-{clock.week}-{clock.day}"

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def daily(self, clock, heirs: Dict[str, dict]) -> dict:
        """Today's stage: weather per city, errands per Heir, one line of news.
        Cached by date — called every hour, answered once a day."""
        key = self._date_key(clock)
        if key in self._cache:
            return self._cache[key]
        ambient = self._generate(clock, heirs)
        ambient["date"] = key
        self._cache[key] = ambient
        # Keep the cache bounded (a few months of days is plenty).
        if len(self._cache) > 200:
            for k in list(self._cache)[:-150]:
                self._cache.pop(k, None)
        self._save_cache()
        return ambient

    def _generate(self, clock, heirs: Dict[str, dict]) -> dict:
        if getattr(self.llm, "configured", False):
            try:
                return self._llm_generate(clock, heirs)
            except Exception:
                pass
        return self._fallback(clock, heirs)

    # ------------------------------------------------------------------ #
    # LLM path — the Keeper speaks
    # ------------------------------------------------------------------ #
    def _llm_generate(self, clock, heirs: Dict[str, dict]) -> dict:
        cities = sorted({info.get("home", "Okhema") for info in heirs.values()})
        heir_lines = "\n".join(
            f"- {info.get('name', cid)} (home: {info.get('home', 'Okhema')}; "
            f"{info.get('title', 'Chrysos Heir')})"
            for cid, info in heirs.items()
        )
        user = (
            f"It is {clock.format()}.\n\n"
            f"City-states of Amphoreus: {', '.join(cities)}.\n\n"
            f"The Chrysos Heirs living in the world:\n{heir_lines}\n\n"
            "Set today's weather for each city, one errand for each Heir, and one "
            "line of news. Reply with ONLY the JSON object."
        )
        reply = self.llm.chat(
            [{"role": "system", "content": DIRECTOR_SYSTEM},
             {"role": "user", "content": user}],
            temperature=0.8,
            max_tokens=1000,
        )
        parsed = _extract_json(reply)
        raw_errands = parsed.get("errands") or {}
        # Defensive: accept both the new {ask, cause} shape and a plain string.
        return {
            "weather": {c: (parsed.get("weather") or {}).get(c, "") for c in cities},
            "errands": {cid: _norm_errand(raw_errands.get(cid)) for cid in heirs},
            "news": str(parsed.get("news", "") or ""),
        }

    # ------------------------------------------------------------------ #
    # Fallback — the world keeps turning even without a Keeper's voice
    # ------------------------------------------------------------------ #
    def _fallback(self, clock, heirs: Dict[str, dict]) -> dict:
        rng = random.Random(self._date_key(clock))
        u = getattr(clock, "uncounted", None)
        if u == "scarlet":
            lore = SCARLET_LORE
        elif u == "astrorum":
            lore = ASTRORUM_LORE
        else:
            month = getattr(clock, "month", 9)
            lore = MONTH_LORE.get(month, MONTH_LORE[9])
        palette = lore["weather"]
        seed = rng.choice(lore["seed"])
        cities = sorted({info.get("home", "Okhema") for info in heirs.values()})
        weather = {}
        for i, city in enumerate(cities):
            weather[city] = palette[(rng.randrange(len(palette)) + i) % len(palette)]
        errands = {}
        for cid, info in heirs.items():
            home = info.get("home", "Okhema")
            opts = CITY_ERRAND_CAUSES.get(home)
            if opts:
                pick = rng.choice(opts)
                errands[cid] = {
                    "ask": pick["ask"],
                    "cause": f"{pick['cause']} It is {seed}.",
                }
            else:
                errands[cid] = {
                    "ask": f"The people of {home} look to you today, as they always do.",
                    "cause": f"None can say why — only that it is {seed}.",
                }
        return {
            "weather": weather,
            "errands": errands,
            "news": rng.choice(NEWS_PALETTE),
        }
