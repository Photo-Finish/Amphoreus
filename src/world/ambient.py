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
}

CITY_ERRAND: Dict[str, str] = {
    "Okhema": "The baths of the Marmoreal Palace are full and the Council quarrels; Okhema looks to its guardians today.",
    "Janusopolis": "Pilgrims stand at the gates of the Three Fates' temples, asking for a door to open.",
    "Castrum Kremnos": "The forges never stop and the warriors drill in the cold; Kremnos wants its strong ones present.",
    "Grove of Epiphany": "The sages dispute a text in the Grove, and the scrolls of Cerces await a steady hand.",
    "Styxia": "The pale city is quiet; the sea sirens sing low, and the bell of Styxia waits to be answered.",
    "Aidonia": "Candles burn at every window in the snow; Aidonia remembers its dead and needs its comforters.",
    "Dawncloud": "The Demigod Council sits at Dawncloud; the elders' arguments grow loud enough to reach the streets.",
    "Aedes Elysiae": "The wheat stands ready in Aedes Elysiae; the wharf waits for a boat that carries it out.",
    "Vortex of Genesis": "The sacred nexus hums beneath the waves, restless and expectant.",
    "Great Tomb": "The Great Tomb is very quiet today, as if it is listening.",
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
    "2. errands — for each Heir, ONE short request that the city lays at their "
    "door (a plea, a duty, a message, an invitation). The Heir may accept, "
    "decline, or ignore it — that is their freedom. Tie each errand to that "
    "Heir's role, home city, and the day's month and mood. Keep each errand to one "
    "sentence.\n"
    "3. news — ONE short line of distant news that reaches every city.\n\n"
    "Be vivid but brief. Ground everything in canon — never invent modern or "
    "alien concepts; Amphoreus is a mythic world at rest after a long war, holding "
    "back the black tide. Never write what an Heir says, feels, or decides.\n\n"
    + KEEPER_KNOWLEDGE +
    'Reply with ONLY a JSON object like:\n'
    '{"weather": {"Okhema": "...", "Janusopolis": "..."}, '
    '"errands": {"tribbie": "...", "phainon": "..."}, "news": "..."}'
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
            f"It is Year {clock.year}, {clock.month_name} ({clock.season} Season, "
            f"patron {clock.patron_titan}), Week {clock.week}, Day {clock.day}.\n\n"
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
        # Defensive: ensure the shapes we promise, whatever the model returns.
        return {
            "weather": {c: (parsed.get("weather") or {}).get(c, "") for c in cities},
            "errands": {
                cid: (parsed.get("errands") or {}).get(cid, "")
                for cid in heirs
            },
            "news": str(parsed.get("news", "") or ""),
        }

    # ------------------------------------------------------------------ #
    # Fallback — the world keeps turning even without a Keeper's voice
    # ------------------------------------------------------------------ #
    def _fallback(self, clock, heirs: Dict[str, dict]) -> dict:
        rng = random.Random(self._date_key(clock))
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
            base = CITY_ERRAND.get(home, f"The people of {home} look to you today, as they always do.")
            # Weave the month's flavour into the errand.
            errands[cid] = f"{base} It is {seed}."
        return {
            "weather": weather,
            "errands": errands,
            "news": rng.choice(NEWS_PALETTE),
        }
