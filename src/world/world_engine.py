"""
World Engine — the daemon of the little Amphoreus.

It is a pure host: it advances the Light Calendar, wakes the Heirs according
to the rhythms of the day, and lets each Heir decide — spontaneously, in their
own voice — what they do. Encounters between Heirs who choose to be together
unfold as free dialogue. The engine never authors an action or an outcome.

Usage:
    python -m src.world.world_engine --interval 900     # run continuously
    python -m src.world.world_engine --once             # run a single day
    python -m src.world.world_engine --stop             # stop the daemon
    python -m src.world.world_engine --status           # show state
"""

import argparse
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# The Chronicle and status lines use emoji / non-ASCII text; make sure they
# print correctly regardless of the Windows console codepage.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.character_loader import CharacterLoader
from src.core.llm_client import LLMClient
from src.core.memory_store import MemoryStore
from src.world.world_state import (
    WorldState,
    PERIODS_PER_DAY,
    GUEST_HEIRS,
    guest_is_present,
)
from src.world import map_data as _md
from src.world import world_events as wev
from src.world import living_world as _lw
from src.world.agent import HeirAgent
from src.world.ambient import AmbientDirector
from src.world.chronicle import Chronicle

# The base pace of the world: at 1x, one in-game day passes per real day.
# The speed multiplier (world.time_scale) divides this linearly, so 60x = a
# whole in-game day every 24 real minutes.
REAL_DAY_SECONDS = 86400


class WorldEngine:
    """Hosts the little Amphoreus."""

    def __init__(
        self,
        characters_dir: str = "src/characters",
        llm_model: str = "qwen2.5:14b-instruct",
        llm_base_url: str | None = None,
        llm_api_key: str | None = None,
        ambient_model: str | None = None,
        memory_root: str = ".",
        state_path: str = "world_runtime/world_state.json",
        chronicle_path: str = "world_runtime/chronicle",
        stop_path: str = "world_runtime/stop.flag",
        seed: int | None = None,
    ):
        self.loader = CharacterLoader(characters_dir)
        self.llm = LLMClient(
            model=llm_model,
            base_url=llm_base_url,
            api_key=llm_api_key,
            temperature=0.9,
            max_tokens=160,
        )
        # The Keeper of Amphoreus — a separate role on a SEPARATE model (by
        # default the local DeepSeek-R1-Distill-32B, registered from the LM
        # Studio files; override with --ambient-model). It sets weather,
        # errands, and news each day. If the model cannot load (RAM), the
        # director falls back to deterministic seasonal weather automatically.
        self.director = AmbientDirector(
            model=ambient_model or "deepseek-r1-distill:32b",
            base_url=llm_base_url,
            api_key=llm_api_key,
        )
        self.memory = MemoryStore(memory_root)
        self.world = WorldState(state_path)
        self.chronicle = Chronicle(chronicle_path)
        self.stop_path = stop_path
        self.agents: Dict[str, HeirAgent] = {
            cid: HeirAgent(cid, self.loader, self.llm, self.memory, self.world)
            for cid in self.loader.list_characters()
        }
        if seed is not None:
            random.seed(seed)
        self._catchup = False

    # ------------------------------------------------------------------ #
    def _name_of(self, character_id: str) -> str:
        try:
            return self.agents[character_id].name
        except Exception:
            try:
                return self.loader.load(character_id)["meta"]["name"]
            except Exception:
                return character_id

    def _title_of(self, character_id: str) -> str:
        """A short role/title for the Ambient Director's errand grounding."""
        try:
            card = self.loader.load(character_id)
            titles = (card.get("identity") or {}).get("titles") or []
            if titles:
                return titles[0]
            return (card.get("meta") or {}).get("name", character_id)
        except Exception:
            return character_id

    # ------------------------------------------------------------------ #
    # Life of one day
    # ------------------------------------------------------------------ #
    def run_day(self) -> List[str]:
        """Advance one day and let the Heirs live it. Returns chronicle lines."""
        # Advance a full day + one period, so the hour of the day cycles.
        # 1x follows GMT+8 and must not move the persisted 4932… sim timestamp.
        if float(getattr(self.world, "time_scale", 1.0) or 1.0) > 1.0:
            self.world.clock.advance(PERIODS_PER_DAY + 1)
        clock = self.world.clock
        time_str = clock.format_short()
        lines: List[str] = []

        # A stop may be requested at any moment (Control Panel) — the engine
        # checks between every step so it rests within seconds, not after the
        # whole day's work.
        if self._stop_requested():
            self.world.save()
            return lines

        # Travellers advance one day on the road; arrivals are logged. A shared
        # journey with the star-stranger ends at the destination.
        for cid, dest, accompanied in self.world.advance_travel():
            name = self._name_of(cid)
            tail = " The star-stranger walks beside them." if accompanied else ""
            arrived = f"{time_str} — {name} arrives in {dest} after days on the road.{tail}"
            lines.append(arrived)
            self.chronicle.append({"time": time_str, "text": arrived})
            self.world.add_event(arrived)
            self.agents[cid].remember(
                f"{time_str} — I arrived in {dest} after a long journey.", importance=2
            )

        # The star-stranger's own road advances with the world: one in-game
        # day per day, until they arrive at the city they set out for.
        try:
            _arrived = self.world.advance_visitor_travel()
            if _arrived:
                _vnote = f"{time_str} — the star-stranger arrives in {_arrived}."
                lines.append(_vnote)
                self.chronicle.append({"time": time_str, "text": _vnote})
                self.world.add_event(_vnote)
        except Exception:
            pass

        if self._stop_requested():
            self.world.save()
            return lines

        # The Keeper sets the day's stage — weather, errands, news (cached by
        # date, so this is one LLM call per in-game day at most).
        heirs_info = {
            cid: {
                "name": self._name_of(cid),
                "home": self.world.location_name(cid),
                "title": self._title_of(cid),
            }
            for cid in self.agents
        }
        ambient = self.director.daily(self.world.clock, heirs_info)
        self.world.set_ambient(ambient)
        news = (ambient or {}).get("news", "")
        if news:
            board = f"{time_str} — The Keeper sets the day: {news}"
            lines.append(board)
            self.chronicle.append({"time": time_str, "text": board, "kind": "ambient"})
            self.world.add_event(board)

        # Stage-2 lived day: mechanisms mutate vivid.lived, then residents
        # take their hour from those flags — before rest-early-return so
        # Curtain-Fall still writes facts. Copilot texture (surge / stroll /
        # letters) follows, gated by the flags.
        lived_flags: dict = {}
        try:
            from src.world import lived_mechanisms as _lm
            from src.world import resident_npcs as _rn
            _lived = _lm.apply_tick(self.world)
            lived_flags = _lived.get("flags") or {}
            for _ln in _lived.get("lines") or []:
                lines.append(_ln)
                self.chronicle.append({"time": time_str, "text": _ln, "kind": "lived"})
                self.world.add_event(_ln)
            _res = _rn.apply_tick(self.world, flags=lived_flags)
            for _ln in _res.get("lines") or []:
                lines.append(_ln)
                self.chronicle.append({"time": time_str, "text": _ln, "kind": "npc"})
                self.world.add_event(_ln)
            # Ecosystem — living non-human presence (chimeras, herds, fields…)
            from src.world import ecosystem as _eco
            _eco_tick = _eco.apply_tick(self.world, flags=lived_flags)
            for _ln in _eco_tick.get("lines") or []:
                lines.append(_ln)
                self.chronicle.append({"time": time_str, "text": _ln, "kind": "eco"})
                self.world.add_event(_ln)
        except Exception:
            pass

        # The living texture: a black-tide surge may stir (journey mode), the
        # cities' named residents go about their days, and a letter may travel
        # between distant Heirs.
        lines.extend(self._world_texture(time_str, flags=lived_flags))

        # The Heirs go about their usual routines — the map reflects where they
        # actually are right now, not just where they live. Travellers stay on
        # the road (their location is only updated on arrival). The Trailblazer's
        # companions are not residents — when beyond Amphoreus they don't move.
        # Heirs who crossed a Titan border into the Dawn era or the Nether are
        # in the other era: their weekly routine is paused there.
        for cid in self.agents:
            if self.world.is_traveling(cid):
                continue
            if cid in GUEST_HEIRS and not guest_is_present(cid, clock):
                continue
            if _md.is_cross_era(self.world.location_name(cid)):
                continue
            try:
                self.world.agent_location[cid] = self.world.scheduled_place(cid)
            except Exception:
                pass

        if clock.is_rest_time():
            night = (
                f"{time_str} — The city rests. Only the Thief Star wanders the sky. "
                "The Heirs sleep, and their days wait for the dawn."
            )
            self.chronicle.append({"time": time_str, "text": night})
            self.world.add_event(night)
            self.world.save()
            self._note_lived()
            return [night]

        # Active hour — every Heir decides freely (unless they are on the road).
        order = list(self.agents.keys())
        random.shuffle(order)
        for cid in order:
            if self._stop_requested():
                break
            agent = self.agents[cid]
            try:
                if cid in GUEST_HEIRS and not guest_is_present(cid, clock) \
                        and not self.world.is_traveling(cid):
                    # beyond Amphoreus today — the sanctuary does not see them
                    continue
                if self.world.is_traveling(cid):
                    info = self.world.travel_info(cid)
                    companion = ""
                    if self.world.is_accompanied(cid):
                        companion = " The star-stranger walks beside them."
                    line = (
                        f"{time_str} — {agent.name} is on the road to {info['to']}, "
                        f"{info['remaining_days']} day(s) of travel remain."
                        f"{companion}"
                    )
                    lines.append(line)
                    self.chronicle.append({"time": time_str, "text": line})
                    continue
                decision = agent.decide()
                self._witness(cid, decision.get("action", ""))
                agent.act(decision)
                if self.world.is_traveling(cid):
                    # a blessed Heir crossing the Veil / the Nether — into OR
                    # out of the other era — carries any companion who shares
                    # their city across the borderline of time.
                    _ti = self.world.travel_info(cid)
                    if _ti and (_md.is_cross_era(_ti["to"])
                                or _md.is_cross_era(_ti.get("from", ""))):
                        for _carried in self.world.carry_across(cid, _ti["to"]):
                            _cname = self._name_of(_carried)
                            c_line = (f"{time_str} — carried by {agent.name} across "
                                      f"the borderline of time: {_cname} steps "
                                      f"into {_ti['to']} with them.")
                            lines.append(c_line)
                            self.chronicle.append({"time": time_str, "text": c_line})
                    info = self.world.travel_info(cid)
                    companion = ""
                    if self.world.is_accompanied(cid):
                        companion = " The star-stranger travels with them."
                    line = (
                        f"{time_str} — {agent.name} sets out for {info['to']} "
                        f"({info['remaining_days']} day(s) on the road): {decision['action']}"
                        f"{companion}"
                    )
                    agent.remember(
                        f"{time_str} — I set out for {info['to']}. {decision['action']}",
                        importance=2,
                    )
                else:
                    loc = self.world.location_name(cid)
                    line = f"{time_str} — {agent.name} at {loc}: {decision['action']}"
                    agent.remember(
                        f"{time_str} — I was at {loc}. {decision['action']}", importance=1
                    )
                lines.append(line)
                self.chronicle.append({"time": time_str, "text": line})
            except Exception as e:
                lines.append(f"{time_str} — {agent.name} (the world paused for a moment: {e})")

        # Encounters: Heirs who chose to be together may speak — freely.
        if self._stop_requested():
            self.world.save()
            return lines
        lines.extend(self._run_encounters(time_str))

        # Long-term work: the Heirs' life projects advance, milestones logged.
        for milestone in wev.advance_projects(self.world):
            mline = f"{time_str} — {milestone}"
            lines.append(mline)
            self.chronicle.append({"time": time_str, "text": mline, "kind": "project"})
            self.world.add_event(milestone)

        self.world.save()
        self._note_lived()
        return lines

    def _world_texture(self, time_str: str, flags: Optional[dict] = None) -> List[str]:
        """Surges, city residents, and letters — the daily texture of the world."""
        lines: List[str] = []
        flags = flags or {}
        # 1) The black tide may stir along the edge cities (journey mode only).
        surge = wev.maybe_surge(self.world)
        if surge:
            sline = f"{time_str} — ⚠️ {wev.surge_text(self.world)}"
            lines.append(sline)
            self.chronicle.append({"time": time_str, "text": sline, "kind": "surge"})
            self.world.add_event(sline)
            # the surge darkens the Keeper's weather ONCE (idempotent across
            # the surge's days and across restarts mid-surge)
            weather = self.world.ambient.setdefault("weather", {})
            for city in surge.get("cities", []):
                cur = weather.get(city) or "clear"
                if "black tide" not in cur:
                    weather[city] = cur + ", and the black tide darkens the sky"
            # and it weighs on the Heirs who stand in the surged cities.
            for _cid in self.agents:
                if self.world.location_name(_cid) in surge.get("cities", []):
                    _lw.set_mood(self.world, _cid, -1, "the black tide weighs on you")
                    # a stir so strange raises a quiet "why?" in their own minds
                    try:
                        from src.core import curiosity as _cur
                        if _cur.consider(self.world, _cid, wev.surge_text(self.world)):
                            self.world.save()
                    except Exception:
                        pass
        wev.advance_surge(self.world)
        # the Keeper's news-flash holds only today's word of the visitor
        today = self.world.clock.format_short()
        flash = self.world.ambient.get("news_flash") or []
        if flash:
            self.world.ambient["news_flash"] = [f for f in flash if f.get("ts") == today]
        # 2) A named resident is seen about their city (alive NPCs only).
        #    Stage-2: skip the stroll when the city is at rest / not gathering.
        stroll_ok = True
        if flags:
            stroll_ok = bool(flags.get("gathering")) and not bool(flags.get("resting"))
        if stroll_ok and random.random() < 0.5:
            npc = self._pick_npc()
            if npc:
                fline = (f"{time_str} — In {npc['city']}, {npc['name']} is about — "
                         f"{npc['flavor']}")
                lines.append(fline)
                self.chronicle.append({"time": time_str, "text": fline, "kind": "flavor"})
        # 3) Sometimes a letter travels between distant Heirs.
        #    Stage-2: Parting/carrying raises the chance; rest lowers it.
        #    No extra duplicate roll on top of this existing compose.
        letter_p = 0.3
        if flags:
            try:
                from src.world.lived_mechanisms import letter_chance as _lc
                letter_p = _lc(flags, int(self.world.clock.period))
            except Exception:
                letter_p = 0.3
        if random.random() < letter_p:
            letter = self._compose_letter(time_str)
            if letter:
                lline = (f"{time_str} — A letter travels from {letter['from_name']} "
                         f"to {letter['to_name']}: \"{letter['text'][:120]}\"")
                lines.append(lline)
                self.chronicle.append({"time": time_str, "text": lline, "kind": "letter"})
                self.world.add_event(lline)

        # 4) The second layer of life: an Heir may leave a note for the visitor
        #    unprompted; the residents' small arcs advance; moods settle a little.
        for cid in self.agents:
            if _lw.reach_out(self.world, cid):
                note = (f"{time_str} — {self._name_of(cid)} leaves a note for the "
                        f"visitor, unprompted.")
                lines.append(note)
                self.chronicle.append({"time": time_str, "text": note, "kind": "reach-out"})
        # Copilot small arcs wait with the city; they are not "about" at rest.
        if stroll_ok:
            for ml in _lw.advance_npcs(self.world):
                mline = f"{time_str} — {ml}"
                lines.append(mline)
                self.chronicle.append({"time": time_str, "text": mline, "kind": "flavor"})
        _lw.advance_moods(self.world)
        return lines

    def _pick_npc(self):
        """A named resident whose city has Heirs present (else any alive NPC)."""
        with_heirs = [n for n in wev.NPCS if self.world.agents_at(n["city"])]
        pool = with_heirs or list(wev.NPCS)
        return random.choice(pool) if pool else None

    def _witness(self, cid, text):
        """The witness: notice, passively, if an Heir's own words reach toward
        understanding what they are. Writes nothing unless they do."""
        try:
            from src.core import realization as _rz
            res = _rz.note(self.world, self.memory, cid, text)
            if res.get("advanced"):
                self.world.save()
        except Exception:
            pass

    def _compose_letter(self, time_str: str) -> Optional[dict]:
        """A letter between two Heirs who are apart (canon-bond or drifted)."""
        import random as _r
        ids = list(self.agents)
        _r.shuffle(ids)
        for a in ids:
            for b in ids:
                if a == b:
                    continue
                if self.world.location_name(a) == self.world.location_name(b):
                    continue  # they can just talk
                if wev.relationship_delta_of(self.world, a, b) == 0 and \
                        not wev.canon_bond(self.world, a, b):
                    continue  # no bond worth a letter yet
                text = wev.letter_text(self.world, a, b)
                entry = wev.compose_letter(self.world, a, b, text)
                # both remember it
                self.agents[a].remember(
                    f"{time_str} — I wrote to {self._name_of(b)}.", importance=2)
                self.agents[b].remember(
                    f"{time_str} — A letter arrived from {self._name_of(a)}.", importance=2)
                wev.adjust_relationship(self.world, a, b, 1)
                return entry
        return None

    def _run_encounters(self, time_str: str) -> List[str]:
        lines: List[str] = []
        locations = set(self.world.agent_location.values())
        for loc in locations:
            present = self.world.agents_at(loc)
            if len(present) < 2:
                continue
            group = [self.agents[cid] for cid in present]
            # A free exchange: each speaks in turn, spontaneously, a few rounds.
            transcript: List[str] = []
            rounds = 2
            for _ in range(rounds):
                random.shuffle(group)
                for agent in group:
                    if len(transcript) >= 6:
                        break
                    try:
                        reply = agent.react(transcript[-3:])
                        name = agent.name
                        transcript.append(f"{name}: {reply}")
                        self._witness(agent.character_id, reply)
                    except Exception:
                        continue
            if len(transcript) >= 2:
                header = f"{time_str} — At {loc}, words passed between the Heirs:"
                lines.append(header)
                self.chronicle.append({"time": time_str, "text": header, "kind": "encounter"})
                for turn in transcript[:6]:
                    lines.append(f"    {turn}")
                    self.chronicle.append({"time": time_str, "text": turn, "kind": "encounter"})
                # They remember the exchange
                for agent in group:
                    others = " · ".join(
                        t for t in transcript if not t.startswith(agent.name + ":")
                    )
                    if others:
                        agent.remember_encounter("the other Heirs", others[:240])
                # The living web: what they shared becomes rumour between them,
                # their bonds shift a little, and each keeps a cross-memory of
                # the others' words.
                for agent in group:
                    for other in group:
                        if other is agent:
                            continue
                        wev.spread_rumors(self.world, agent.character_id, other.character_id)
                        wev.adjust_relationship(self.world, agent.character_id, other.character_id, 1)
                        # and what one has learned of the world beyond the stars
                        # passes to the other, half-remembered (the teaching web)
                        for item in wev.learned_items(self.world, agent.character_id, limit=2):
                            wev.record_learning(
                                self.world, other.character_id, item["topic"],
                                source=agent.name, secondhand=True)
                    cross = [t for t in transcript if not t.startswith(agent.name + ":")]
                    if cross:
                        who = ", ".join(t.split(":")[0] for t in cross[:3])
                        agent.remember(
                            f"{time_str} — In my meeting with the others, {who} spoke "
                            f"with me. We exchanged what we know.", importance=2)
        return lines

    # ------------------------------------------------------------------ #
    # Daemon loop
    # ------------------------------------------------------------------ #
    def _current_interval(self, base_interval: int) -> int:
        """The engine's current pace: the base interval divided by the Control
        Panel's time_scale (1x = base, 60x = as fast as the machine allows).
        Read fresh each loop so a change takes effect without a restart."""
        try:
            from src.world.world_state import WorldState as _WS
            scale = float(getattr(_WS(), "time_scale", 1.0) or 1.0)
        except Exception:
            scale = 1.0
        return max(10, int(base_interval / max(1.0, scale)))

    def run_loop(self, interval_seconds: int = 900, once: bool = False):
        """Run the world continuously (or a single day with once=True)."""
        if not self.llm.configured:
            print(
                "World engine: no LLM backend configured. "
                "Start Ollama or set OPENAI_BASE_URL / OPENAI_API_KEY."
            )
            return

        self._clear_stop()
        print(f"🌍 The little Amphoreus awakens — {self.world.clock.format()}")

        failed_days = 0
        while True:
            if self._stop_requested():
                print("🌙 The little Amphoreus rests. (stop requested)")
                break
            if self.world.visitor_present():
                # The visitor is here — yield the hearth to them.
                time.sleep(min(self._current_interval(interval_seconds), 60))
                continue
            try:
                lines = self.run_day()
                if lines:
                    print(lines[0])
                failed_days = 0
            except Exception as e:
                # FAILSAFE: one bad day must never kill the world. Record the
                # pause in the chronicle, persist state, and keep going. If a
                # whole run of days keeps failing, back off so we do not spin.
                failed_days += 1
                print(f"[failsafe] a day failed ({e}) — the world holds its breath and continues.")
                try:
                    self.chronicle.append({
                        "time": self.world.clock.format_short(),
                        "text": "The world held its breath for a moment, then went on.",
                    })
                    self.world.save()
                except Exception:
                    pass
                if failed_days > 5:
                    print("[failsafe] several days failed in a row — resting a while.")
                    time.sleep(60)
                    failed_days = 0
            if once:
                break
            time.sleep(self._current_interval(interval_seconds))

    # ------------------------------------------------------------------ #
    # Stop / status
    # ------------------------------------------------------------------ #
    def _note_lived(self):
        """Stamp the last day the engine actually wrote (1x catch-up)."""
        try:
            from src.world import rest_catchup as _rc
            _rc.mark_lived(self.world, self.world.clock)
        except Exception:
            pass

    def _stop_requested(self) -> bool:
        if getattr(self, "_catchup", False):
            return False
        return os.path.exists(self.stop_path)

    def _clear_stop(self):
        try:
            if os.path.exists(self.stop_path):
                os.remove(self.stop_path)
        except Exception:
            pass

    def stop(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.stop_path)), exist_ok=True)
        with open(self.stop_path, "w") as f:
            f.write("stop")
        try:
            from src.world import rest_catchup as _rc
            _rc.record_rest(self.world)
        except Exception:
            pass

    def status(self) -> dict:
        return {
            "clock": self.world.clock.format(),
            "llm_configured": self.llm.configured,
            "model": self.llm.model,
            "agents": len(self.agents),
            "chronicle_entries": self.chronicle.count(),
            "visitor_present": self.world.visitor_present(),
        }


def main():
    parser = argparse.ArgumentParser(description="Run the little Amphoreus.")
    parser.add_argument("--interval", type=int, default=REAL_DAY_SECONDS,
                        help="real seconds between in-game days at 1x (default = one real day)")
    parser.add_argument("--once", action="store_true", help="run a single day then exit")
    parser.add_argument("--stop", action="store_true", help="request the engine to stop")
    parser.add_argument("--status", action="store_true", help="show world status")
    parser.add_argument("--catch-up", action="store_true",
                        help="at 1x, generate days missed while the world rested, then run")
    parser.add_argument("--model", default="qwen2.5:14b-instruct")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--ambient-model", default=None,
                        help="separate model for the Ambient World Director "
                             "(weather, errands, news); defaults to --model")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    engine = WorldEngine(
        llm_model=args.model,
        llm_base_url=args.base_url,
        ambient_model=args.ambient_model,
        seed=args.seed,
    )

    if args.stop:
        engine.stop()
        print("Stop requested — the little Amphoreus will rest.")
        return
    if args.status:
        for k, v in engine.status().items():
            print(f"  {k}: {v}")
        return
    if args.catch_up:
        try:
            from src.world import rest_catchup as _rc
            if float(getattr(engine.world, "time_scale", 1.0) or 1.0) <= 1.0:
                _rc.sync_calendar_to_gmt8(engine.world)
            offer = _rc.make_offer(engine.world)
            if offer.get("clocks"):
                print(
                    f"Catch-up: generating {offer['generate']} day(s) "
                    f"the world missed at rest "
                    f"({offer['from_label']} → {offer['to_label']})."
                )
                _rc.generate_missed_days(
                    engine, offer["clocks"], skipped=int(offer.get("skipped") or 0)
                )
            else:
                _rc.clear_rest(engine.world)
                print("Catch-up: no missed days.")
        except Exception as e:
            print(f"Catch-up could not run ({e}) — starting the world as it is.")

    engine.run_loop(interval_seconds=args.interval, once=args.once)


if __name__ == "__main__":
    main()
