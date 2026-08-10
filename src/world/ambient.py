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
SEASON_WEATHER: Dict[str, List[str]] = {
    "Fate": [
        "clear and cool, with doorways of light opening in the morning air",
        "veiled and grey, as if Oronyx's curtain hangs over the sky",
        "bright and still, with the weight of doors about to open",
    ],
    "Pillar": [
        "warm and rooted; the earth smells of turned soil",
        "soft rain over the fields, as if Georios' hands were at work",
        "golden and heavy with harvest light",
    ],
    "Creation": [
        "golden and quiet, full of memory and ripe grain",
        "a mild breeze carrying the scent of Mnestia's looms",
        "crisp and clear — the kind of day stories are told in",
    ],
    "Calamity": [
        "sharp and restless; the wind has an edge to it",
        "grey and heavy, with a hush before what comes",
        "overcast, the light thinned by long shadows",
    ],
}

NEWS_PALETTE: List[str] = [
    "A caravan from the Grove brings word of strange lights over the ruins.",
    "The markets of Okhema hum with talk of a festival to be held in Dawncloud.",
    "Fisherfolk off Aidonia swear the tide turned silver for a single hour.",
    "A door in Janusopolis refused to open for three travelers, then opened by itself.",
    "The forges of Castrum Kremnos ring day and night — the city is re-arming, softly.",
    "Pilgrims whisper that the Great Tomb grew quiet, as if listening.",
    "The wind through Aedes Elysiae carried a song no one remembered singing.",
]

DIRECTOR_SYSTEM = (
    "You are the Keeper of Amphoreus — the calm intelligence that sets the stage "
    "of the world, not the actors on it.\n\n"
    "You do NOT control the Chrysos Heirs. They are free people; you only arrange "
    "the world around them. Each day you provide:\n"
    "1. weather — the day's sky over each city (short, vivid, season- and "
    "Titan-flavored; Amphoreus has no rain as we know it — it has light, veils, "
    "ash, silence, silver tides).\n"
    "2. errands — for each Heir, ONE short request that the city lays at their "
    "door (a plea, a duty, a message, an invitation). The Heir may accept, "
    "decline, or ignore it — that is their freedom. Tie each errand to that "
    "Heir's role, home city, and the day's mood. Keep each errand to one sentence.\n"
    "3. news — ONE short line of distant news that reaches every city.\n\n"
    "Be vivid but brief. Ground everything in Amphoreus canon: the Titans "
    "(Kephale, Janus, Oronyx, Mnestia, Nikador, Thanatos, ...), the cities "
    "(Okhema, Janusopolis, Castrum Kremnos, Grove of Epiphany, Styxia, Aidonia, "
    "Dawncloud, Aedes Elysiae, Vortex of Genesis, Great Tomb), and the peace "
    "after the long war. Never write what an Heir says, feels, or decides.\n"
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
        palette = SEASON_WEATHER.get(clock.season, SEASON_WEATHER["Creation"])
        cities = sorted({info.get("home", "Okhema") for info in heirs.values()})
        weather = {}
        for i, city in enumerate(cities):
            weather[city] = palette[(rng.randrange(len(palette)) + i) % len(palette)]
        errands = {
            cid: f"The people of {info.get('home', 'Okhema')} look to you today, "
                 f"as they always do."
            for cid, info in heirs.items()
        }
        return {
            "weather": weather,
            "errands": errands,
            "news": rng.choice(NEWS_PALETTE),
        }
