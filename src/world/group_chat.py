"""Stage 2 — group chat as social co-presence (not a lab).

When two or more Heirs stand in the same place, the operator may invite a
gathering. Invitations are answered in each Heir's own voice. The session is
a UI gathering: it lives in the Visit conversation and ends when Visit is left.

Uses existing world location APIs (`location_name`, `agents_at`, `travel_info`,
`companions_here`). Does not invent a second map. Does not author Heir speech
when a voice is available — fallback lines are only for offline tests / a
silent backend.
"""

from __future__ import annotations

import re
from typing import Callable, Dict, Iterable, List, Optional

from src.world import vivid_stage2 as v2

STATE_KEY = "amp_group"
VISIT_TAB = "Visit an Heir"

# Tokens the invite prompt asks the model to append (stripped before display).
_VERDICT = re.compile(r"\b(ACCEPT|DECLINE)\b", re.IGNORECASE)
_OFFLINE = re.compile(
    r"LLM backend is not configured|No backend configured",
    re.IGNORECASE,
)
_QUIET = re.compile(r"^\s*\[quiet\]\s*$", re.IGNORECASE)

NameFn = Callable[[str], str]
SpeakFn = Callable[[str, str], str]


def blank_session() -> dict:
    return {
        "active": False,
        "host": "",
        "place": "",
        "invited": [],
        "accepted": [],
        "declined": [],
        "members": [],
        "messages": [],
        "kind": "individual",
    }


def as_session(store) -> dict:
    """`store` is the group dict, or a mapping that holds it under STATE_KEY."""
    if store is None:
        return blank_session()
    if isinstance(store, dict) and "members" in store and "active" in store:
        if "messages" not in store:
            store["messages"] = []
        return store
    sess = store.setdefault(STATE_KEY, blank_session())
    if not isinstance(sess, dict):
        sess = blank_session()
        store[STATE_KEY] = sess
    return sess


def session_active(store) -> bool:
    sess = as_session(store)
    return bool(sess.get("active") and len(sess.get("members") or []) >= 2)


def session_end(store) -> dict:
    """Clear the gathering. Returns the session as it stood."""
    sess = as_session(store)
    old = dict(sess)
    sess.clear()
    sess.update(blank_session())
    return old


def session_start(store, *, host: str, place: str, invited: List[str],
                  accepted: List[str], declined: List[str]) -> dict:
    members = []
    for cid in [host, *accepted]:
        if cid and cid not in members:
            members.append(cid)
    sess = as_session(store)
    sess.update({
        "active": len(members) >= 2 and len(accepted) >= 1,
        "host": host,
        "place": place or "",
        "invited": list(invited),
        "accepted": list(accepted),
        "declined": list(declined),
        "members": members if len(members) >= 2 and accepted else [],
        "messages": [],
        "kind": "active" if (len(members) >= 2 and accepted) else "individual",
    })
    return sess


def append_message(store, *, role: str, content: str,
                   speaker: str = "") -> dict:
    sess = as_session(store)
    msg = {"role": role, "content": content}
    if speaker:
        msg["speaker"] = speaker
    sess.setdefault("messages", []).append(msg)
    return msg


def is_present_for_group(world, character_id: str) -> bool:
    """Physically here: not on the road, and not a guest currently beyond."""
    if not character_id:
        return False
    if world.travel_info(character_id):
        return False
    try:
        from src.world.world_state import guest_is_present
        if not guest_is_present(character_id, world.clock):
            return False
    except Exception:
        pass
    return True


def copresent_heirs(world, host_id: str) -> List[str]:
    """Heirs at the selected Heir's place, including the host.

    On Visit the operator's place is the selected Heir's location — the same
    map as `_loc_now` / `WorldState.location_name` / `agents_at`.
    """
    if not host_id or not is_present_for_group(world, host_id):
        return []
    loc = world.location_name(host_id)
    here = []
    for cid in world.agents_at(loc):
        if cid not in here and is_present_for_group(world, cid):
            here.append(cid)
    if host_id not in here:
        here.insert(0, host_id)
    return here


def companions_for_group(world, host_id: str) -> List[str]:
    """Other co-present Heirs who may be invited (excludes the host)."""
    return [c for c in copresent_heirs(world, host_id) if c != host_id]


def group_possible(world, host_id: str) -> bool:
    """True when at least two Heirs share the selected Heir's place."""
    return len(copresent_heirs(world, host_id)) >= 2


def operator_may_invite(is_visitor: bool) -> bool:
    """Guests stay read-only: they may see a gathering is possible, not invite."""
    return not bool(is_visitor)


def still_together(world, store) -> bool:
    """Whether the active gathering still has two members at the place."""
    sess = as_session(store)
    if not sess.get("active"):
        return False
    place = sess.get("place") or ""
    members = list(sess.get("members") or [])
    if not place or len(members) < 2:
        return False
    here = set(world.agents_at(place))
    living = [m for m in members if m in here and is_present_for_group(world, m)]
    return len(living) >= 2


def consider_invite(world, host_id: str, invitee_id: str,
                    name_of: Optional[NameFn] = None) -> dict:
    """Whether an invitee can join. Duty may force a decline (canon)."""

    def _nm(cid):
        if name_of:
            try:
                return name_of(cid)
            except Exception:
                pass
        try:
            return world.name_of(cid)
        except Exception:
            return cid

    place = world.location_name(host_id)
    base = {
        "host": host_id,
        "invitee": invitee_id,
        "place": place,
        "eligible": False,
        "forced_decline": False,
        "reason": "",
        "accepted": False,
    }
    if not invitee_id or invitee_id == host_id:
        base["reason"] = "already with you"
        return base
    if world.travel_info(host_id) or world.travel_info(invitee_id):
        base["reason"] = f"{_nm(invitee_id)} is on the road — not here to join."
        base["forced_decline"] = True
        return base
    if invitee_id not in companions_for_group(world, host_id):
        base["reason"] = f"{_nm(invitee_id)} is not at {place}."
        base["forced_decline"] = True
        return base
    refuse = v2._tide_duty_refusal(world, invitee_id, _nm)
    if refuse:
        base["reason"] = refuse
        base["forced_decline"] = True
        return base
    base["eligible"] = True
    base["reason"] = "may join"
    return base


def parse_invite_verdict(text: str) -> Optional[bool]:
    """True=accept, False=decline, None=unspecified."""
    if not text:
        return None
    marks = _VERDICT.findall(text)
    if marks:
        return marks[-1].upper() == "ACCEPT"
    low = text.lower()
    decline_bits = (
        "i cannot", "i can't", "i must not", "i will not join",
        "i won't join", "not now", "duty holds", "i decline",
        "leave me out", "i stay aside",
    )
    accept_bits = (
        "i'll join", "i will join", "count me in", "i'll sit",
        "i will sit", "i accept", "i'm here", "i am here",
        "let us speak", "let's speak",
    )
    if any(b in low for b in decline_bits):
        return False
    if any(b in low for b in accept_bits):
        return True
    return None


def strip_verdict_token(text: str) -> str:
    text = _VERDICT.sub("", text or "")
    text = re.sub(r"[\(\[]\s*[,\.;:]*\s*[\)\]]", "", text)
    return re.sub(r"\s+", " ", text).strip(" -,;:")


def looks_offline(text: str) -> bool:
    return bool(_OFFLINE.search(text or ""))


def fallback_invite_line(character_id: str, accepted: bool,
                         place: str, host_name: str) -> str:
    """Offline / test stand-in — still a line in the world, not a modal."""
    place = place or "this place"
    host_name = host_name or "them"
    accept = _FALLBACK_ACCEPT.get(character_id)
    decline = _FALLBACK_DECLINE.get(character_id)
    if accepted and accept:
        return accept.format(place=place, host=host_name)
    if (not accepted) and decline:
        return decline.format(place=place, host=host_name)
    name = character_id
    if accepted:
        return f"Very well — I will sit with you here in {place}."
    return f"Not this hour. I remain aside, here in {place}."


def fallback_group_line(
    character_id: str,
    user_message: str,
    others: Iterable[str],
    *,
    avoid: Optional[Iterable[str]] = None,
    turn_index: int = 0,
) -> str:
    """Offline / silent-backend stand-in — varies so rounds do not parrot."""
    others = [o for o in others if o]
    company = ", ".join(others) if others else "those gathered"
    said = (user_message or "").strip()
    snippet = said[:72] if said else "that"
    avoid_set = {_compact_line(x) for x in (avoid or []) if x}
    pool = list(_FALLBACK_GROUP_POOL.get(character_id) or [])
    generic = [
        "I hear you. ({company} are here with us.)",
        "Go on — we are listening, here together.",
        "Say it again another way if you must; I am still with you.",
        "That lands differently in this company. Speak on.",
    ]
    candidates = pool + generic
    # Rotate starting index by turn so consecutive offline rounds differ.
    start = (turn_index + sum(ord(ch) for ch in character_id)) % max(1, len(candidates))
    ordered = candidates[start:] + candidates[:start]
    for tmpl in ordered:
        try:
            line = tmpl.format(
                company=company,
                said=snippet,
                place="this place",
            )
        except Exception:
            line = tmpl
        if _compact_line(line) not in avoid_set:
            return line
    # Last resort: fold a unique scrap of the visitor's words in.
    tag = snippet[:40] or character_id
    return f"About “{tag}” — I hear you, with {company}."


def invite_prompt(host_name: str, place: str, company: List[str]) -> str:
    names = ", ".join(company) if company else host_name
    return (
        f"The star-stranger, standing here in {place} with {host_name}, "
        f"asks you to join a conversation — a gathering, not a trial. "
        f"Also invited or already here: {names}. "
        "Answer in one or two spoken sentences, in your own voice. "
        "This is company in the world, not an experiment. "
        "End with ACCEPT if you will sit with them, or DECLINE if you will not."
    )


def _compact_line(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def lines_too_similar(a: str, b: str) -> bool:
    """True when two spoken lines are the same beat reused."""
    ca, cb = _compact_line(a), _compact_line(b)
    if not ca or not cb:
        return False
    if ca == cb:
        return True
    if ca in cb or cb in ca:
        shorter = min(len(ca), len(cb))
        if shorter >= 24:
            return True
    wa, wb = set(ca.split()), set(cb.split())
    if len(wa) >= 4 and len(wb) >= 4:
        overlap = len(wa & wb) / float(max(len(wa), len(wb)))
        if overlap >= 0.72:
            return True
    return False


def group_prompt_block(
    character_id: str,
    members: List[str],
    place: str,
    name_of: NameFn,
    recent: Optional[List[dict]] = None,
    *,
    own_prior: Optional[List[str]] = None,
) -> str:
    names = [name_of(c) for c in members if c != character_id]
    company = ", ".join(names) if names else "the others"
    bits = [
        "# A gathering — you are not alone with the visitor",
        f"You stand together in {place} with {company} and the star-stranger.",
        "This is social co-presence: a conversation in the world, not a test.",
        "Speak only your own words. Never narrate another Heir's thoughts, "
        "never put words in their mouth, never make the gathering a chorus.",
        "Answer this turn freshly — do not reuse a line you already spoke "
        "in this gathering, and do not echo another Heir's beat.",
        "If you have nothing of your own to add this turn, reply with [quiet].",
        "Keep to the knowledge of Amphoreus; do not reach past the wall.",
    ]
    if own_prior:
        bits.append("Lines you already spoke here (do not repeat):")
        for line in own_prior[-4:]:
            clipped = (line or "").strip().replace("\n", " ")
            if clipped:
                bits.append(f"- {clipped[:200]}")
    if recent:
        bits.append("Recent words in this gathering:")
        for m in recent[-8:]:
            who = m.get("speaker") or (
                "the star-stranger" if m.get("role") == "user" else "someone"
            )
            if m.get("speaker") == character_id:
                who = "you"
            line = (m.get("content") or "").strip().replace("\n", " ")
            if line:
                bits.append(f"- {who}: {line[:240]}")
    return "\n".join(bits)


def who_speaks(
    members: List[str],
    host_id: str,
    user_message: str,
    name_of: NameFn,
    *,
    turn_index: int = 0,
) -> List[str]:
    """Natural multi-voice cast for one user turn.

    Small gatherings tend to speak together; larger ones rotate a subset so
    the scene stays alive without a parrot chorus. Named Heirs always speak.
    """
    members = [m for m in members if m]
    if not members:
        return []
    n = len(members)
    text = (user_message or "").lower()
    addressed: List[str] = []
    for cid in members:
        try:
            nm = (name_of(cid) or "").lower()
        except Exception:
            nm = cid.lower()
        if nm and len(nm) >= 3 and nm in text:
            addressed.append(cid)

    # How many voices this turn — scale with the gathering, vary by turn.
    if n <= 2:
        k = n
    elif n == 3:
        k = 3 if (turn_index % 3) != 2 else 2
    elif n == 4:
        k = 4 if (turn_index % 4) == 0 else 3
    else:
        # 5+: usually 3–4; occasional full company.
        k = min(n, 3 + (turn_index % 2))
        if turn_index % 5 == 0:
            k = n

    order: List[str] = []
    for cid in addressed:
        if cid not in order:
            order.append(cid)

    rest = [m for m in members if m not in order]
    # Prefer the host early when nobody was named, then rotate by turn.
    if host_id in rest and not addressed:
        rest = [host_id] + [m for m in rest if m != host_id]
    if rest:
        rot = turn_index % len(rest)
        rest = rest[rot:] + rest[:rot]
        # Message-stable shuffle among the rotated rest so similar prompts
        # still vary who joins after the first seat.
        seed = (
            sum(ord(ch) for ch in (user_message or "x"))
            + len(user_message or "")
            + turn_index * 17
        )
        if len(rest) > 1:
            pivot = seed % len(rest)
            rest = rest[pivot:] + rest[:pivot]

    for cid in rest:
        if len(order) >= k:
            break
        order.append(cid)

    # Named Heirs always keep a seat even if k was small.
    for cid in addressed:
        if cid not in order:
            order.append(cid)
    return order


def should_end_for_tab(tab_name: str) -> bool:
    """True when the selected main tab is no longer Visit an Heir."""
    name = re.sub(r"\s+", " ", (tab_name or "")).strip()
    if not name:
        return False
    return name != VISIT_TAB


def should_end_for_query(amp_tab: str) -> bool:
    val = str(amp_tab or "").strip().lower()
    if not val:
        return False
    return val not in {"visit", "heir", "1", "true"}


def send_invitations(
    world,
    host_id: str,
    invitee_ids: Iterable[str],
    *,
    name_of: Optional[NameFn] = None,
    speak: Optional[SpeakFn] = None,
    store=None,
) -> dict:
    """Ask each invitee; start a gathering if at least one other accepts.

    `speak(character_id, prompt) -> str` is the Heir voice. If omitted, uses
    offline fallback lines (tests / silent backend).
    """

    def _nm(cid):
        if name_of:
            try:
                return name_of(cid)
            except Exception:
                pass
        try:
            return world.name_of(cid)
        except Exception:
            return cid

    place = world.location_name(host_id)
    host_name = _nm(host_id)
    invitees = [c for c in invitee_ids if c and c != host_id]
    company = [host_name] + [_nm(c) for c in invitees]
    replies = []
    accepted: List[str] = []
    declined: List[str] = []

    for cid in invitees:
        considered = consider_invite(world, host_id, cid, name_of=_nm)
        if considered.get("forced_decline") or not considered.get("eligible"):
            line = considered.get("reason") or fallback_invite_line(
                cid, False, place, host_name)
            # Prefer a spoken fallback when the reason is a world-duty sentence
            # already in-world (tide). Keep that sentence — it is their answer.
            declined.append(cid)
            replies.append({
                "speaker": cid,
                "accepted": False,
                "content": line,
                "forced": True,
            })
            continue

        prompt = invite_prompt(host_name, place, company)
        spoken = ""
        if speak:
            try:
                spoken = (speak(cid, prompt) or "").strip()
            except Exception:
                spoken = ""
        verdict = parse_invite_verdict(spoken) if spoken else None
        if not spoken or looks_offline(spoken):
            spoken = fallback_invite_line(cid, True, place, host_name)
            verdict = True
        if verdict is None:
            # Co-present and eligible: joining is the natural default.
            verdict = True
        line = strip_verdict_token(spoken) or fallback_invite_line(
            cid, verdict, place, host_name)
        if verdict:
            accepted.append(cid)
        else:
            declined.append(cid)
        replies.append({
            "speaker": cid,
            "accepted": bool(verdict),
            "content": line,
            "forced": False,
        })

    started = len(accepted) >= 1
    world_line = ""
    if started:
        names = ", ".join(_nm(c) for c in accepted)
        world_line = (
            f"In {place}, {names} sit with {host_name} and the star-stranger. "
            "The gathering is company, not a trial."
        )
    else:
        world_line = (
            f"The invitation hangs in the air of {place}, and no one else "
            f"steps in. The hour remains with {host_name}."
        )

    sess = None
    if store is not None:
        if started:
            sess = session_start(
                store, host=host_id, place=place,
                invited=invitees, accepted=accepted, declined=declined,
            )
            append_message(store, role="assistant", content=world_line)
            for r in replies:
                append_message(
                    store, role="assistant",
                    content=r["content"], speaker=r["speaker"],
                )
        else:
            session_end(store)
            sess = as_session(store)

    return {
        "ok": True,
        "started": started,
        "place": place,
        "host": host_id,
        "invited": invitees,
        "accepted": accepted,
        "declined": declined,
        "replies": replies,
        "world_line": world_line,
        "session": sess,
    }


def enrich_system(manager, character_id: str) -> str:
    """Same sanctuary injectors as 1:1 chat — voice fidelity, knowledge wall."""
    system_prompt = manager.loader.build_system_prompt(character_id)
    for fn_name in (
        "_inject_memory_context",
        "_inject_world_context",
        "_inject_social_context",
        "_inject_living_context",
        "_inject_vivid_context",
        "_inject_curiosity_context",
        "_inject_horizons_context",
        "_inject_length_freedom",
    ):
        fn = getattr(manager, fn_name, None)
        if not fn:
            continue
        try:
            system_prompt = fn(character_id, system_prompt)
        except Exception:
            pass
    try:
        from src.core.visitor_mode import visitor_framing_block
        system_prompt += visitor_framing_block()
    except Exception:
        pass
    try:
        pref = manager.preferences.to_prompt_block(character_id)
        if pref:
            system_prompt = f"{system_prompt}\n\n{pref}"
    except Exception:
        pass
    return system_prompt


def heir_speak(manager, character_id: str, user_message: str,
               extra_system: str = "",
               *,
               gathering_so_far: str = "") -> str:
    """A short in-character line that does not write the 1:1 session."""
    from src.core.speech_sanitize import spoken_words

    system_prompt = enrich_system(manager, character_id)
    if extra_system:
        system_prompt = f"{system_prompt}\n\n{extra_system}"
    manager._oplora_character_id = character_id
    # Keep gathering history in the user turn (not as fake assistant turns)
    # so the model does not treat other Heirs' lines as its own speech.
    if gathering_so_far:
        user_content = (
            f"{gathering_so_far.strip()}\n\n"
            f"Now answer in your own voice only:\n{user_message}"
        )
    else:
        user_content = user_message
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    try:
        manager._sanitize_history_for_llm(messages)
    except Exception:
        pass
    try:
        raw = manager._call_llm(messages, stream=False)
    except Exception as exc:
        return f"[{character_id} cannot answer this hour: {exc}]"
    if isinstance(raw, str):
        return spoken_words(raw)
    return spoken_words(str(raw or ""))


def generate_group_turn(
    manager,
    store,
    user_message: str,
    *,
    world=None,
    name_of: Optional[NameFn] = None,
    speak: Optional[SpeakFn] = None,
) -> List[dict]:
    """Sequential Heir lines for one user turn. Skips quiet / parrot fills."""
    sess = as_session(store)
    members = list(sess.get("members") or [])
    host_id = sess.get("host") or (members[0] if members else "")
    place = sess.get("place") or ""
    all_msgs = list(sess.get("messages") or [])

    def _nm(cid):
        if name_of:
            try:
                return name_of(cid)
            except Exception:
                pass
        try:
            return manager.get_character_info(cid)["name"]
        except Exception:
            return cid

    # Current user line is already appended by the UI — do not feed it twice.
    prior = list(all_msgs)
    if (
        prior
        and prior[-1].get("role") == "user"
        and (prior[-1].get("content") or "").strip() == (user_message or "").strip()
    ):
        prior = prior[:-1]
    user_turns = [m for m in all_msgs if m.get("role") == "user"]
    turn_index = max(0, len(user_turns) - 1)

    speakers = who_speaks(
        members, host_id, user_message, _nm, turn_index=turn_index,
    )
    out: List[dict] = []
    said_so_far: List[str] = []
    used_by: Dict[str, List[str]] = {}
    for m in prior:
        sp = m.get("speaker") or ""
        if sp and m.get("role") == "assistant":
            used_by.setdefault(sp, []).append(m.get("content") or "")

    for cid in speakers:
        own_prior = list(used_by.get(cid) or [])
        extra = group_prompt_block(
            cid, members, place, _nm,
            recent=prior + out,
            own_prior=own_prior,
        )
        if said_so_far:
            extra += (
                "\nAnother gathered Heir already answered this turn. "
                "Add only what is yours — a brief beat, a disagreement, "
                "or [quiet]. Do not restate their line."
            )
        prompt = (
            f"The star-stranger says, here in {place}: {user_message}"
        )
        gathering_so_far = ""
        if prior or out:
            lines = []
            for m in (prior + out)[-10:]:
                who = m.get("speaker") or (
                    "the star-stranger" if m.get("role") == "user" else "someone"
                )
                if m.get("speaker") == cid:
                    who = "you"
                try:
                    if m.get("speaker") and m.get("speaker") != cid:
                        who = _nm(m["speaker"])
                except Exception:
                    pass
                line = (m.get("content") or "").strip().replace("\n", " ")
                if line:
                    lines.append(f"- {who}: {line[:220]}")
            if lines:
                gathering_so_far = (
                    "Gathering so far (do not repeat your own lines):\n"
                    + "\n".join(lines)
                )
        text = ""
        if speak:
            try:
                text = (speak(cid, prompt) or "").strip()
            except Exception:
                text = ""
        elif manager is not None:
            text = (
                heir_speak(
                    manager, cid, prompt,
                    extra_system=extra,
                    gathering_so_far=gathering_so_far,
                ) or ""
            ).strip()
        if not text or looks_offline(text) or _QUIET.match(text):
            if _QUIET.match(text or ""):
                continue
            others = [_nm(m) for m in members if m != cid]
            avoid = own_prior + [
                m.get("content") or "" for m in out
            ]
            text = fallback_group_line(
                cid, user_message, others,
                avoid=avoid, turn_index=turn_index,
            )
        # Drop a parrot of this turn or of this Heir's earlier words.
        compact = _compact_line(text)
        if said_so_far and any(lines_too_similar(text, prev) for prev in said_so_far):
            continue
        if any(lines_too_similar(text, prev) for prev in own_prior):
            others = [_nm(m) for m in members if m != cid]
            alt = fallback_group_line(
                cid, user_message, others,
                avoid=own_prior + said_so_far + [text],
                turn_index=turn_index + 1,
            )
            if any(lines_too_similar(alt, prev) for prev in own_prior + said_so_far):
                continue
            text = alt
            compact = _compact_line(text)
        msg = append_message(store, role="assistant", content=text, speaker=cid)
        out.append(msg)
        said_so_far.append(compact)
        used_by.setdefault(cid, []).append(text)
        try:
            if manager is not None:
                snippet = re.sub(r"\s+", " ", text).strip()[:120]
                manager.memory.add_memory(
                    cid,
                    mtype="social",
                    content=(
                        f"In a gathering in {place} with "
                        f"{', '.join(_nm(m) for m in members if m != cid)}, "
                        f"you told the star-stranger: {snippet}"
                    ),
                    importance=1,
                )
        except Exception:
            pass
        try:
            if manager is not None:
                manager._witness_realization(cid, text)
        except Exception:
            pass
    return out


# --------------------------------------------------------------------------- #
# Offline stand-in speech (tests / silent backend) — not used when the Heir
# voice answers. Kept short and in-world. Multiple lines per Heir so consecutive
# offline turns do not parrot the same beat.
# --------------------------------------------------------------------------- #
_FALLBACK_ACCEPT: Dict[str, str] = {
    "phainon": "Hah. If you're gathering here in {place}, I'm not sitting it out.",
    "aglaea": "Very well. The threads already know you are here — I will sit with you.",
    "mydei": "Fine. I am here. Speak, then.",
    "castorice": "If I am wanted in {place}… I will stay a little.",
    "cipher": "Oho. A huddle? Sure — I'll linger, if the talk's worth my ears.",
    "anaxa": "A conversation. Very well. I can spare the hour.",
    "hyacine": "Of course. Sit — I'll stay with you in {place}.",
    "tribbie": "We can sit! We like it when friends gather in {place}.",
    "cerydra": "You summon a council of two? Very well. I will hear it.",
    "hysilens": "I will stand with you. The hour is yours.",
    "cyrene": "♪ Then let us keep this hour together, here in {place}.",
    "evernight": "♭ If the gathering is kind… I will sit.",
    "dan-heng-permansor-terrae": "I can stay. Speak as you need.",
}

_FALLBACK_DECLINE: Dict[str, str] = {
    "phainon": "Not this hour. Walk with me another time.",
    "aglaea": "The weave pulls me elsewhere. Go on without me.",
    "mydei": "No. The watch is mine. Leave me to it.",
    "castorice": "I… I should not join. Forgive me.",
    "cipher": "Tempting — but I've got my own errand. Catch me later.",
    "anaxa": "I decline. My work does not pause for a huddle.",
    "hyacine": "I wish I could — someone else needs me first.",
    "tribbie": "We have to run! Another time, promise.",
    "cerydra": "I have no hour to spare. Dismissed.",
    "hysilens": "Duty first. I cannot sit with you now.",
    "cyrene": "♪ The song pulls me away. Keep the hour without me.",
    "evernight": "♭ Not tonight. Let the gathering go on.",
    "dan-heng-permansor-terrae": "I will stand aside. Continue without me.",
}

_FALLBACK_GROUP_POOL: Dict[str, List[str]] = {
    "phainon": [
        "I'm listening. Say it plainly — we're all here.",
        "Hah. That lands. Speak on — I won't look away.",
        "With this company? Fine. Say what you came to say.",
        "I heard “{said}”. Go on — I'm still with you.",
    ],
    "aglaea": [
        "The gold of this hour is company. Speak; I am attending.",
        "The weave holds. I hear you — continue.",
        "Company steadies the thread. Say it again if you must; I am here.",
        "About “{said}” — the gold listens with you.",
    ],
    "mydei": [
        "Go on. I have ears.",
        "Speak. I am not leaving.",
        "Short words. I am listening.",
        "“{said}” — say the rest.",
    ],
    "castorice": [
        "I am here. You may speak.",
        "I… I hear you. Go on, if you wish.",
        "Still with you. Softly — I am listening.",
        "About that… I stay.",
    ],
    "cipher": [
        "Well? Don't leave a girl hanging — out with it.",
        "Heh. That's a thing to say in this company.",
        "I'm listening. Make it worth my ears.",
        "Oho — “{said}”? Keep talking.",
    ],
    "anaxa": [
        "Proceed. I will judge the claim, not the volume.",
        "A claim, then. State it cleanly.",
        "I remain. Continue the argument.",
        "Regarding “{said}” — elaborate.",
    ],
    "hyacine": [
        "We're with you. Tell us what's on your mind.",
        "I'm here. Take your time.",
        "Breathe — we're listening.",
        "About “{said}” — go on, I'm with you.",
    ],
    "tribbie": [
        "We hear you! Tell us, tell us.",
        "We like this! Say more!",
        "We're listening — together!",
        "“{said}”! Tell us the rest!",
    ],
    "cerydra": [
        "Speak. A ruler listens when the hour asks it.",
        "I will hear it. Continue.",
        "Council is seated. State your case.",
        "On “{said}” — proceed.",
    ],
    "hysilens": [
        "I hear you. Say what you came to say.",
        "I stand with you. Go on.",
        "The hour is still. Speak.",
        "“{said}” — I am listening.",
    ],
    "cyrene": [
        "♪ The hour leans in. We are listening.",
        "♪ Keep the melody — I hear you.",
        "♪ Another verse, if you will.",
        "♪ On “{said}” — the song waits.",
    ],
    "evernight": [
        "♭ I am still here. Go on.",
        "♭ Softly — I hear you.",
        "♭ The night holds. Speak.",
        "♭ “{said}”… continue, if you wish.",
    ],
    "dan-heng-permansor-terrae": [
        "Go on. I am listening.",
        "I remain. Speak as you need.",
        "Understood. Continue.",
        "About “{said}” — go on.",
    ],
}
