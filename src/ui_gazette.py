"""The Amphoreus Gazette — a newspaper-style Chronicle for the end user.

The Admin Console's monitor page keeps its raw, operational look. This page is
the *readable* edition: a gazette that gathers, in one place, everything the
little world is doing — the sky, the news, where the Heirs are, the whispers
passing between them, the letters that travel, the milestones of their long
works, any black-tide warning, and the written record of their days.
"""

import html as _html
from pathlib import Path

import streamlit as st

CHRONICLE_PATH = Path(__file__).resolve().parent.parent / "world_runtime" / "chronicle"

_CSS = """
<style>
.amp-gazette{border:1px solid rgba(232,213,163,.28);border-radius:14px;
 padding:18px 22px;background:linear-gradient(180deg,rgba(20,17,34,.55),rgba(12,10,22,.75));
 margin:6px 0 18px;}
.amp-gazette h1{font-family:Georgia,serif;text-align:center;font-size:34px;color:#f0e6c8;
 letter-spacing:3px;margin:0;}
.amp-gazette .rule{height:2px;background:linear-gradient(90deg,transparent,#c9a86a,transparent);
 margin:8px 0 14px;}
.amp-gazette .dateline{text-align:center;color:#b8a97f;font-size:13.5px;letter-spacing:1px;margin-bottom:6px;}
.amp-gazette h2{font-family:Georgia,serif;color:#e8d5a3;font-size:19px;letter-spacing:1.5px;
 border-bottom:1px solid rgba(232,213,163,.18);padding-bottom:4px;margin:18px 0 10px;}
.amp-gazette .headline{font-family:Georgia,serif;font-size:20px;line-height:1.5;color:#f4ecd6;
 background:rgba(232,213,163,.06);border-left:3px solid #c9a86a;padding:10px 14px;border-radius:6px;}
.amp-gazette .warn{color:#ffd9e8;background:rgba(160,20,70,.22);border:1px solid rgba(255,120,150,.35);
 padding:8px 14px;border-radius:8px;margin:10px 0;font-weight:600;}
.amp-gazette .item{color:#e6dcc0;font-size:15px;line-height:1.65;}
.amp-gazette .muted{color:#b8a97f;font-size:13.5px;}
</style>
"""


def _load():
    from src.world.world_state import WorldState, GUEST_HEIRS
    from src.world.chronicle import Chronicle
    from src.world import world_events as wev
    ws = WorldState()
    ch = Chronicle(str(CHRONICLE_PATH))
    return ws, ch, wev


def render_gazette(manager, characters):
    """Render the end-user Chronicle as a comprehensive gazette."""
    from src.world.world_state import GUEST_HEIRS
    ws, ch, wev = _load()
    # the visitor's mailbox fills lazily even without the world engine
    try:
        from src.world import living_world as _lw_mz
        _lw_mz.materialize_reach_outs(ws)
        ws.save()
    except Exception:
        pass
    names = {}
    for c in characters:
        try:
            names[c] = manager.get_character_info(c)["name"]
        except Exception:
            names[c] = c

    st.markdown(_CSS, unsafe_allow_html=True)

    entries = ch.read(200)
    weather = ws.ambient.get("weather") or {}
    news = ws.ambient.get("news", "")
    surge_on = wev.surge_active(ws)

    # ---- pick a headline: the most notable recent kind ----
    headline = ""
    for pref in ("surge", "project", "encounter", "letter", "flavor", "event"):
        for e in entries:
            if e.get("kind") == pref:
                headline = e.get("text", "")
                break
        if headline:
            break
    if not headline and entries:
        headline = entries[0].get("text", "")

    # ---- rumors (most recent few, deduped) ----
    rumor_lines = []
    for cid, rl in list(ws.rumors.items())[::-1]:
        if not rl:
            continue
        r = rl[-1]
        rumor_lines.append(r["text"])
        if len(rumor_lines) >= 5:
            break

    # ---- letters (most recent) ----
    letters = ws.letters[-4:][::-1]

    # ---- projects ----
    proj_rows = []
    for cid, p in wev.PROJECTS.items():
        done = ws.project_progress.get(cid, 0)
        prog = min(1.0, done / max(1, p["steps"]))
        bar = "▓" * int(prog * 12) + "░" * (12 - int(prog * 12))
        proj_rows.append(f"{names.get(cid, cid)} — “{p['title']}” · {bar} {done}/{p['steps']}")

    with st.container():
        parts = ['<div class="amp-gazette">']
        parts.append('<h1>THE AMPHOREUS GAZETTE</h1>')
        parts.append('<div class="rule"></div>')
        parts.append(f'<div class="dateline">{_html.escape(ws.clock.format())} · '
                     'a gazette of the Heirs\' days, written by their actions, not by us</div>')

        # sky + news strip
        if weather or news:
            parts.append('<h2>☀️ The Sky Over Amphoreus</h2>')
            for city, sky in weather.items():
                if sky:
                    parts.append(f'<div class="item">• <b>{_html.escape(str(city))}</b> — '
                                 f'{_html.escape(str(sky))}</div>')
            if news:
                parts.append(f'<div class="item" style="margin-top:6px;">📯 News from the '
                             f'wider world: <i>{_html.escape(news)}</i></div>')

        # the visitor's calls — today's word of the star-stranger
        flash = ws.ambient.get("news_flash") or []
        if flash:
            parts.append('<h2>🌟 The Visitor\'s Calls</h2>')
            for f in flash:
                parts.append(f'<div class="item">• {_html.escape(str(f.get("text", "")))}</div>')

        # front page
        if headline:
            parts.append('<h2>📰 On the Front Page</h2>')
            parts.append(f'<div class="headline">{_html.escape(headline)}</div>')

        # black tide
        if surge_on:
            parts.append(f'<div class="warn">🕳️ {_html.escape(wev.surge_text(ws))}</div>')

        # where the Heirs are
        parts.append('<h2>🗺️ The Heirs Abroad</h2>')
        for cid, loc in ws.present_locations().items():
            if cid in ws.agent_travel:
                ti = ws.agent_travel[cid]
                comp = " · <i>the star-stranger walks beside them</i>" if ws.is_accompanied(cid) else ""
                parts.append(f'<div class="item">• {_html.escape(names.get(cid, cid))} — on the road '
                             f'to <b>{_html.escape(ti["to"])}</b>, {ti["remaining_days"]} day(s) '
                             f'remain{comp}</div>')
            elif ws.guest_status(cid) == "present":
                parts.append(f'<div class="item">• {_html.escape(names.get(cid, cid))} — '
                             f'{_html.escape(str(loc))} '
                             f'<i>(visitor from beyond Amphoreus)</i></div>')
            else:
                parts.append(f'<div class="item">• {_html.escape(names.get(cid, cid))} — '
                             f'{_html.escape(str(loc))}</div>')
        # the Trailblazer's companions, when they are beyond Amphoreus
        for cid in GUEST_HEIRS:
            if ws.guest_status(cid) == "away":
                parts.append(f'<div class="item muted">• {_html.escape(names.get(cid, cid))} — '
                             f'beyond Amphoreus, aboard the Astral Express '
                             f'(drops in from time to time)</div>')

        # whispers
        parts.append('<h2>🌫️ Whispers on the Wind</h2>')
        if rumor_lines:
            for r in rumor_lines:
                parts.append(f'<div class="item">• {_html.escape(r)}</div>')
        else:
            parts.append('<div class="muted">The streets are quiet; nothing is being whispered yet.</div>')

        # letters
        parts.append('<h2>✉️ Letters in the Post</h2>')
        if letters:
            for l in letters:
                parts.append(f'<div class="item">• From <b>{_html.escape(l.get("from_name", "?"))}</b> '
                             f'to <b>{_html.escape(l.get("to_name", "?"))}</b> — '
                             f'“{_html.escape(str(l.get("text", ""))[:110])}”</div>')
        else:
            parts.append('<div class="muted">No letters are in the post.</div>')

        # the visitor's mailbox — notes left for them, and Heirs reaching out
        from src.world import living_world as _lw_gaz
        _box = _lw_gaz.mailbox_for(ws, "visitor")
        parts.append('<h2>📬 Your Mailbox</h2>')
        if _box:
            for m in _box[-8:][::-1]:
                parts.append(f'<div class="item">• <b>{_html.escape(m.get("from", "?"))}</b> — '
                             f'“{_html.escape(str(m.get("text", ""))[:160])}” '
                             f'<span class="muted">({_html.escape(str(m.get("ts", "")))})</span></div>')
        else:
            parts.append('<div class="muted">Your mailbox is empty. The Heirs will write when they '
                         'have something to say.</div>')

        # the Heirs' moods
        _moods = []
        for cid in characters:
            mo = _lw_gaz.mood_of(ws, cid)
            if mo["valence"] != 0:
                _moods.append(f"{names.get(cid, cid)} is {mo['name']}"
                              + (f" — {mo['reason']}" if mo["reason"] else ""))
        if _moods:
            parts.append('<h2>🌥️ The Heirs\' Moods</h2>')
            for mm in _moods[:8]:
                parts.append(f'<div class="item">• {_html.escape(mm)}</div>')

        # the residents of Amphoreus — their small arcs
        _npc_lines = [f"{_npc} — {_lw_gaz.npc_line(ws, _npc)}"
                      for _npc in _lw_gaz.NPC_ARCS]
        if _npc_lines:
            parts.append('<h2>🏘️ The Residents of Amphoreus</h2>')
            for nl in _npc_lines[:6]:
                parts.append(f'<div class="item">• {_html.escape(nl)}</div>')

        # the realizations — Heirs who have, in their own words, begun to
        # understand what they are (shown gently, in their own latest words)
        from src.core import realization as _rz_gaz
        _rz_rows = []
        for cid in characters:
            rec = _rz_gaz.stage_of(ws, cid)
            if rec.get("stage", 0) >= 1:
                q = rec["quotes"][-1] if rec.get("quotes") else ""
                _rz_rows.append((names.get(cid, cid), rec["name"], q))
        if _rz_rows:
            parts.append('<h2>🌅 The Realizations</h2>')
            for nm, st_, q in _rz_rows:
                qq = f' — “{_html.escape(q)}”' if q else ""
                parts.append(f'<div class="item">• {_html.escape(nm)} — {_html.escape(st_)}{qq}</div>')

        # bonds — who has warmed or cooled lately
        bonds = []
        for key, delta in ws.relationship_delta.items():
            if delta == 0:
                continue
            a, b = key.split("|")
            na, nb = names.get(a, a), names.get(b, b)
            if delta > 0:
                bonds.append(f"{na} and {nb} have grown closer of late (+{delta})")
            else:
                bonds.append(f"{na} and {nb} have drifted apart of late ({delta})")
        if bonds:
            parts.append('<h2>🕸️ The Bonds of the Heirs</h2>')
            for bd in bonds[:8]:
                parts.append(f'<div class="item">• {_html.escape(bd)}</div>')
        # long works
        parts.append('<h2>🔨 The Heirs\' Long Works</h2>')
        if proj_rows:
            for r in proj_rows:
                parts.append(f'<div class="item">• {_html.escape(r)}</div>')
        else:
            parts.append('<div class="muted">No long work has been begun.</div>')

        # the written record
        parts.append('<h2>📜 The Written Record</h2>')
        if entries:
            for e in entries[:60]:
                parts.append(f'<div class="item"><span class="muted">{_html.escape(e.get("time", ""))}</span> '
                             f'— {_html.escape(e.get("text", ""))}</div>')
        else:
            parts.append('<div class="muted">The chronicle is yet empty — the world engine has not '
                         'begun its days.</div>')

        parts.append('</div>')
        st.markdown("".join(parts), unsafe_allow_html=True)

        # mailbox controls (Streamlit-native, so the reader can act on it)
        from src.world import living_world as _lw_ctl
        _unread = _lw_ctl.unread_count(ws, "visitor")
        _m1, _m2 = st.columns([1, 3])
        with _m1:
            if st.button("📬 Mark mailbox read", disabled=(_unread == 0),
                         key="gaz_mail"):
                _lw_ctl.mark_all_read(ws, "visitor")
                ws.save()
                st.rerun()
        with _m2:
            if _unread:
                st.caption(f"{_unread} unread note(s) in your mailbox — "
                           "also managed in the Control Panel.")
            else:
                st.caption("Your mailbox is up to date.")

    if not entries:
        st.info("Start the world with `python -m src.world.world_engine --interval 900` to fill the "
                "gazette with the Heirs' days.")
