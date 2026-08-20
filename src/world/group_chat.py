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


def fallback_group_line(character_id: str, user_message: str,
                        others: Iterable[str]) -> str:
    others = [o for o in others if o]
    company = ", ".join(others) if others else "those gathered"
    base = _FALLBACK_GROUP.get(character_id)
    if base:
        return base.format(company=company, said=(user_message or "").strip()[:80])
    return f"I hear you. ({company} are here with us.)"


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


def group_prompt_block(character_id: str, members: List[str], place: str,
                       name_of: NameFn, recent: Optional[List[dict]] = None) -> str:
    names = [name_of(c) for c in members if c != character_id]
    company = ", ".join(names) if names else "the others"
    bits = [
        "# A gathering — you are not alone with the visitor",
        f"You stand together in {place} with {company} and the star-stranger.",
        "This is social co-presence: a conversation in the world, not a test.",
        "Speak only your own words. Never narrate another Heir's thoughts, "
        "never put words in their mouth, never make the gathering a chorus.",
        "If you have nothing of your own to add this turn, reply with [quiet].",
        "Keep to the knowledge of Amphoreus; do not reach past the wall.",
    ]
    if recent:
        bits.append("Recent words in this gathering:")
        for m in recent[-8:]:
            who = m.get("speaker") or (
                "the star-stranger" if m.get("role") == "user" else "someone"
            )
            line = (m.get("content") or "").strip().replace("\n", " ")
            if line:
                bits.append(f"- {who}: {line[:240]}")
    return "\n".join(bits)


def who_speaks(members: List[str], host_id: str, user_message: str,
               name_of: NameFn) -> List[str]:
    """One or two voices — never a parrot circle.

    Addressed Heirs speak first. Otherwise the host speaks, and at most one
    other may add a beat (stable from the message, not random).
    """
    members = [m for m in members if m]
    if not members:
        return []
    text = (user_message or "").lower()
    addressed = []
    for cid in members:
        try:
            nm = (name_of(cid) or "").lower()
        except Exception:
            nm = cid.lower()
        if nm and len(nm) >= 3 and nm in text:
            addressed.append(cid)
    if addressed:
        out = []
        for cid in addressed:
            if cid not in out:
                out.append(cid)
        return out[:2]

    order = []
    if host_id in members:
        order.append(host_id)
    others = [c for c in members if c != host_id]
    if not others:
        return order
    if len(members) == 2:
        order.append(others[0])
        return list(dict.fromkeys(order))
    seed = sum(ord(ch) for ch in (user_message or "x")) + len(user_message or "")
    # Four in five turns, a second Heir adds a line; otherwise the host alone.
    if seed % 5 != 0:
        order.append(others[seed % len(others)])
    return list(dict.fromkeys(order))[:2]


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
               extra_system: str = "") -> str:
    """A short in-character line that does not write the 1:1 session."""
    from src.core.speech_sanitize import spoken_words

    system_prompt = enrich_system(manager, character_id)
    if extra_system:
        system_prompt = f"{system_prompt}\n\n{extra_system}"
    manager._oplora_character_id = character_id
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
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

    speakers = who_speaks(members, host_id, user_message, _nm)
    recent = list(sess.get("messages") or [])
    out: List[dict] = []
    said_so_far: List[str] = []

    for cid in speakers:
        extra = group_prompt_block(
            cid, members, place, _nm, recent=recent + out,
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
        text = ""
        if speak:
            try:
                text = (speak(cid, prompt) or "").strip()
            except Exception:
                text = ""
        elif manager is not None:
            text = (heir_speak(manager, cid, prompt, extra_system=extra) or "").strip()
        if not text or looks_offline(text) or _QUIET.match(text):
            if not text or looks_offline(text):
                others = [_nm(m) for m in members if m != cid]
                text = fallback_group_line(cid, user_message, others)
            else:
                continue
        # Drop a parrot of the previous line.
        compact = re.sub(r"\s+", " ", text).strip().lower()
        if said_so_far and compact == said_so_far[-1]:
            continue
        msg = append_message(store, role="assistant", content=text, speaker=cid)
        out.append(msg)
        said_so_far.append(compact)
        try:
            if manager is not None:
                manager.memory.add_memory(
                    cid,
                    mtype="social",
                    content=(
                        f"You spoke with the star-stranger in {place} "
                        f"together with {', '.join(_nm(m) for m in members if m != cid)}."
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
# voice answers. Kept short and in-world.
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

_FALLBACK_GROUP: Dict[str, str] = {
    "phainon": "I'm listening. Say it plainly — we're all here.",
    "aglaea": "The gold of this hour is company. Speak; I am attending.",
    "mydei": "Go on. I have ears.",
    "castorice": "I am here. You may speak.",
    "cipher": "Well? Don't leave a girl hanging — out with it.",
    "anaxa": "Proceed. I will judge the claim, not the volume.",
    "hyacine": "We're with you. Tell us what's on your mind.",
    "tribbie": "We hear you! Tell us, tell us.",
    "cerydra": "Speak. A ruler listens when the hour asks it.",
    "hysilens": "I hear you. Say what you came to say.",
    "cyrene": "♪ The hour leans in. We are listening.",
    "evernight": "♭ I am still here. Go on.",
    "dan-heng-permansor-terrae": "Go on. I am listening.",
}
