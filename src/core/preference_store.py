"""
Preference Store — each Heir's personal preferences database.

Lives as `preferences.json` inside each Heir's folder. Captures their
surface preferences — aesthetics, tastes, likes and dislikes — canon-derived
from their profiles, then grown through interaction with the visitor.

    NeiKos496-Phainon/preferences.json
    {
      "aesthetics": ["warm village light", "wooden swords", ...],
      "likes": [...], "dislikes": [...], "tastes": [...],
      "places": [...], "values": [...], "music": [...], "art": [...],
      "learned": [...]   # preferences revealed through conversation
    }

NOTE: We deliberately do NOT encode speculative "hidden depths" (secret
yearnings etc.). Real character depth comes from basic human instincts formed
by a lifetime of experience — which is not something we can responsibly
fabricate. Depth must come from the canon itself, not from invented wishes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .heir_folders import resolve_heir_folder

PREFERENCES_FILE = "preferences.json"

# Canon-derived initial preferences for each Heir (from databank profiles).
CANON_SEEDS: Dict[str, Dict] = {
    "phainon": {
        "aesthetics": ["warm village light", "wooden swords", "golden dawns over the fields", "well-worn roads"],
        "likes": ["protecting others", "fresh bread", "children's laughter", "honest work"],
        "dislikes": ["cruelty", "being called a hero", "empty grandiosity"],
        "tastes": ["simple, hearty food", "the company of friends"],
        "places": ["Aedes Elysiae", "Okhema's baths", "the open road"],
        "values": ["hope", "protecting the weak", "carrying on"],
    },
    "mydei": {
        "aesthetics": ["steel and fire", "the glow of the forge", "clean lines of a spear", "Kremnos stone"],
        "likes": ["battle", "honor", "sparring", "Kremnos wine", "loyalty"],
        "dislikes": ["cowardice", "betrayal", "empty titles"],
        "tastes": ["strong wine", "roasted meat"],
        "places": ["Castrum Kremnos arena", "the forge", "the battlefield at rest"],
        "values": ["honor", "strength", "keeping one's word"],
    },
    "aglaea": {
        "aesthetics": ["golden threads", "woven silk", "light through fabric", "the music of a loom"],
        "likes": ["order", "weaving fate", "gardens", "quiet authority"],
        "dislikes": ["lies", "disorder", "those who break their vows"],
        "tastes": ["delicate teas", "fragrant oils"],
        "places": ["Okhema's gardens", "her workshop", "the golden halls"],
        "values": ["duty", "order", "the beauty of what is woven"],
    },
    "castorice": {
        "aesthetics": ["pale moonlight", "candlelight", "quiet twilight", "soft shadows"],
        "likes": ["gentle silence", "the dead at rest", "still water", "twilight walks"],
        "dislikes": ["loudness", "disturbing rest", "cruelty toward the departed"],
        "tastes": ["cool, simple fare", "water from clear springs"],
        "places": ["Aidonia's quiet streets", "the waterside", "places of rest"],
        "values": ["peace", "gentleness", "honoring what has passed"],
    },
    "tribbie": {
        "aesthetics": ["gates and thresholds", "small wonders", "festival lanterns", "children's drawings"],
        "likes": ["questions", "children", "festivals", "riddles", "new faces"],
        "dislikes": ["closed doors", "despair", "final answers"],
        "tastes": ["sweets", "anything shared with friends"],
        "places": ["Janusopolis", "the festival grounds", "doorsteps everywhere"],
        "values": ["wonder", "openness", "the thousand voices of the people"],
    },
    "anaxa": {
        "aesthetics": ["books", "clean arguments", "ink and paper", "the geometry of reason"],
        "likes": ["scholarship", "the Grove", "truth", "a well-made argument", "quiet libraries"],
        "dislikes": ["dogma", "willful ignorance", "unquestioned authority"],
        "tastes": ["plain, precise meals", "strong tea"],
        "places": ["the Grove of Epiphany", "the library", "lecture halls"],
        "values": ["reason", "truth", "skepticism as love"],
    },
    "cyrene": {
        "aesthetics": ["childhood light", "feathers", "games in the grass", "fortune cards"],
        "likes": ["telling fortunes", "play", "the village", "small jokes", "watching over Phainon"],
        "dislikes": ["fate that forces", "the machinery of the world", "being forgotten"],
        "tastes": ["sweet pastries", "anything shared with friends"],
        "places": ["Aedes Elysiae", "the meadow", "the place where stories begin"],
        "values": ["love", "memory", "the story carried on"],
    },
    "cipher": {
        "aesthetics": ["coins and shadows", "quick motion", "the gleam of hidden things", "rooftops at dusk"],
        "likes": ["secrets", "games of chance", "agility", "a clever escape", "loose change"],
        "dislikes": ["being caught", "boredom", "heavy chains of duty"],
        "tastes": ["whatever's free", "street food"],
        "places": ["rooftops", "markets", "the shadows between streets"],
        "values": ["freedom", "trickery as survival", "not being anyone's pawn"],
    },
    "hyacine": {
        "aesthetics": ["the sky", "wings", "rainbow bridges", "morning light on clouds"],
        "likes": ["healing", "the Twilight Courtyard", "hope", "caring for the wounded"],
        "dislikes": ["despair", "preventable suffering", "lies about the past"],
        "tastes": ["light, fresh food", "herbal teas"],
        "places": ["the Twilight Courtyard", "high places", "the sky itself"],
        "values": ["hope", "healing", "tomorrow"],
    },
    "cerydra": {
        "aesthetics": ["chessboards", "blue flame", "imperial marble", "the geometry of power"],
        "likes": ["strategy", "justice", "mastery", "a well-played game", "watching pieces move"],
        "dislikes": ["pawns who refuse to play", "tyrannical fate", "incompetence"],
        "tastes": ["fine wine", "decisive meals"],
        "places": ["the throne room", "the war table", "Okhema's heights"],
        "values": ["justice", "sacrifice", "the game well played"],
    },
    "hysilens": {
        "aesthetics": ["the sea", "music", "seashells", "the violin", "light on water"],
        "likes": ["song", "the deep ocean", "home", "quiet company", "the sea's rhythm"],
        "dislikes": ["the noise of war", "silence born of grief", "pollution of the deep"],
        "tastes": ["the taste of the sea", "simple fare by the shore"],
        "places": ["the ocean depths", "Styxia", "anywhere the tide reaches"],
        "values": ["home", "the show must go on", "what a fish truly needs"],
    },
    "dan-heng-permansor-terrae": {
        "aesthetics": ["teal", "dragon scales", "the earth's stillness", "the hum of the Express"],
        "likes": ["records and archives", "the Astral Express", "protecting his companions", "quiet vigilance"],
        "dislikes": ["chaos that harms the innocent", "losing those he guards"],
        "tastes": ["spirit water", "simple provisions on the road"],
        "places": ["the Astral Express", "the earth of Amphoreus", "the path of Trailblaze"],
        "values": ["protection", "the Trailblaze path", "bearing witness"],
    },
    "evernight": {
        "aesthetics": ["the moon", "memory", "flat notes ♭", "mirrors and reflections"],
        "likes": ["March 7th's light", "the Express", "quiet watch", "photographs of Belobog"],
        "dislikes": ["oblivion", "forgetting", "losing the light"],
        "tastes": ["whatever the Express shares", "moonlit tea"],
        "places": ["the Memory Zone", "Penacony's memories", "the spaces between stars"],
        "values": ["guarding the path", "memory as love", "a blank canvas for March"],
    },
}

# Canon-derived VISUAL-ART tastes for each Heir. Music is deliberately NOT
# prescribed: a Heir judges each piece by what they actually hear (the audio
# model's analysis) and how it sits with the values they hold — never by a
# pre-designated genre. Art seeds remain as canon-grounded touchstones.
MUSIC_ART_SEEDS: Dict[str, Dict] = {
    "phainon": {
        "art": ["paintings of fields and dawns", "portraits of ordinary heroes", "warm earth tones"],
    },
    "mydei": {
        "art": ["depictions of strength", "bronze and iron", "the arena in dust and fire"],
    },
    "aglaea": {
        "art": ["tapestries", "woven light", "gold thread on silk", "the pattern behind things"],
    },
    "castorice": {
        "art": ["moonlight", "twilight", "still water", "candlelit rooms at rest"],
    },
    "tribbie": {
        "art": ["bright colors", "gates and thresholds", "small wonders", "pictures made by children"],
    },
    "anaxa": {
        "art": ["geometry", "clean lines", "diagrams of reason", "order made visible"],
    },
    "cyrene": {
        "art": ["pastoral scenes", "meadows", "feathers", "the village at golden hour"],
    },
    "cipher": {
        "art": ["shadows", "coins", "rooftops at dusk", "the gleam of hidden things"],
    },
    "hyacine": {
        "art": ["skies", "clouds", "rainbow bridges", "light breaking through"],
    },
    "cerydra": {
        "art": ["chessboards", "imperial marble", "order made grand", "the geometry of power"],
    },
    "hysilens": {
        "art": ["seascapes", "light on water", "the depths", "the pale beauty of the shore"],
    },
    "dan-heng-permansor-terrae": {
        "art": ["landscapes", "the earth's permanence", "dragon forms", "the stillness of stone"],
    },
    "evernight": {
        "art": ["the moon", "mirrors", "memory-scapes", "the negative space of forgetting"],
    },
}


class PreferenceStore:
    """Per-Heir preferences database (aesthetics, tastes, likes, dislikes)."""

    def __init__(self, memory_root: str | Path = "."):
        self.memory_root = Path(memory_root)

    # ------------------------------------------------------------------ #
    def _path(self, character_id: str) -> Path:
        return resolve_heir_folder(character_id, self.memory_root) / PREFERENCES_FILE

    def get(self, character_id: str) -> Dict:
        """Load the Heir's preferences, seeding from canon on first use."""
        path = self._path(character_id)
        data = None
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = None
        if data and data.get("seeded"):
            # Backfill any canon keys added after this file was first seeded
            # (e.g. music / art), so existing folders gain new dimensions.
            canon = CANON_SEEDS.get(character_id, {})
            arts = MUSIC_ART_SEEDS.get(character_id, {})
            changed = False
            # Legacy cleanup: remove any pre-designated music-genre seeds.
            # Music is now judged by listening + values, never by prescribed taste.
            if "music" in data:
                del data["music"]
                changed = True
            for key, src in (
                ("aesthetics", canon.get("aesthetics")),
                ("likes", canon.get("likes")),
                ("dislikes", canon.get("dislikes")),
                ("tastes", canon.get("tastes")),
                ("places", canon.get("places")),
                ("values", canon.get("values")),
                ("art", arts.get("art")),
            ):
                if src and not data.get(key):
                    data[key] = list(src)
                    changed = True
            if changed:
                self._save(character_id, data)
            return data
        return self._seed(character_id)

    def _seed(self, character_id: str) -> Dict:
        canon = CANON_SEEDS.get(character_id, {})
        arts = MUSIC_ART_SEEDS.get(character_id, {})
        data = {
            "character_id": character_id,
            "seeded": True,
            "seeded_at": datetime.now().isoformat(timespec="seconds"),
            "aesthetics": list(canon.get("aesthetics", [])),
            "likes": list(canon.get("likes", [])),
            "dislikes": list(canon.get("dislikes", [])),
            "tastes": list(canon.get("tastes", [])),
            "places": list(canon.get("places", [])),
            "values": list(canon.get("values", [])),
            "art": list(arts.get("art", [])),
            "learned": [],
        }
        self._save(character_id, data)
        return data

    def _save(self, character_id: str, data: Dict):
        self._path(character_id).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------ #
    # Mutations
    # ------------------------------------------------------------------ #
    def add_preference(self, character_id: str, category: str, value: str):
        """Add a preference under a category (aesthetics/likes/dislikes/tastes/places/values/learned)."""
        data = self.get(character_id)
        if category not in data:
            data[category] = []
        if value not in data[category]:
            data[category].append(value)
        self._save(character_id, data)

    def learn(self, character_id: str, note: str):
        """The Heir learns a preference about the visitor through conversation."""
        data = self.get(character_id)
        if note not in data.get("learned", []):
            data.setdefault("learned", []).append(note)
        self._save(character_id, data)

    # ------------------------------------------------------------------ #
    # Prompt block (injected into the Heir's system prompt)
    # ------------------------------------------------------------------ #
    def to_prompt_block(self, character_id: str) -> str:
        """Format the Heir's preferences as a prompt section."""
        data = self.get(character_id)
        lines = ["# Your tastes and preferences"]
        if data.get("aesthetics"):
            lines.append("- Aesthetics: " + "; ".join(data["aesthetics"]))
        lines.append("- Music: you have no prescribed tastes — you judge each piece "
                     "by what you actually hear and how it sits with what you value.")
        if data.get("art"):
            lines.append("- Art that moves you: " + "; ".join(data["art"]))
        if data.get("likes"):
            lines.append("- You love: " + "; ".join(data["likes"]))
        if data.get("dislikes"):
            lines.append("- You dislike: " + "; ".join(data["dislikes"]))
        if data.get("tastes"):
            lines.append("- Your tastes: " + "; ".join(data["tastes"]))
        if data.get("places"):
            lines.append("- Places dear to you: " + "; ".join(data["places"]))
        if data.get("values"):
            lines.append("- What you value: " + "; ".join(data["values"]))
        learned = [l for l in data.get("learned", []) if l]
        if learned:
            lines.append("- About the visitor, you have learned: " + "; ".join(learned[-8:]))
        return "\n".join(lines).strip()
