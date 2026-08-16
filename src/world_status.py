"""src/world_status.py — a read-only snapshot of the little Amphoreus.

Used by the public world-status page (tools/world_status_server.py) and its
/api/status JSON, so any terminal anywhere can check how the world is doing.
Pure read-only: nothing here mutates the world.
"""

import html
import json
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UI_URL_FILE = PROJECT_ROOT / "world_runtime" / "ui_url.txt"
URLS_JSON = PROJECT_ROOT / "world_runtime" / "status_urls.json"


def public_ui_url() -> str:
    """The public URL of the full Sanctuary UI (written by status_guard)."""
    try:
        for ln in UI_URL_FILE.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln.startswith("http"):
                return ln
    except Exception:
        pass
    return ""


def engine_running() -> bool:
    """Is the world engine daemon alive right now?"""
    try:
        import psutil
        for p in psutil.process_iter(["name", "cmdline"]):
            try:
                cl = " ".join(p.info.get("cmdline") or [])
                if "python" in (p.info.get("name") or "").lower() \
                        and "world_engine" in cl:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "if (Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'world_engine' }) { exit 0 } "
             "else { exit 1 }"],
            capture_output=True, timeout=20)
        return out.returncode == 0
    except Exception:
        return False


def _heir_name(cid: str) -> str:
    try:
        from src.core.character_loader import CharacterLoader
        return CharacterLoader("src/characters").load(cid)["meta"]["name"]
    except Exception:
        return cid


def world_status() -> dict:
    """The whole world in one dictionary (JSON-safe)."""
    from src.world.world_state import WorldState
    from src.world import living_world as lw
    from src.world import world_events as wev

    try:
        ws = WorldState()
    except Exception as e:
        return {"ok": False, "error": f"world state unreadable: {e}"}

    clock = getattr(ws, "clock", None)
    heirs = []
    for cid in sorted((ws.agent_location or {}).keys()):
        traveling = (ws.agent_travel or {}).get(cid)
        mo = lw.mood_of(ws, cid)
        try:
            guest = ws.guest_status(cid)
        except Exception:
            guest = "resident"
        heirs.append({
            "id": cid,
            "name": _heir_name(cid),
            "location": ws.agent_location.get(cid, "?"),
            "traveling_to": traveling.get("to") if traveling else None,
            "road_days_left": traveling.get("remaining_days") if traveling else None,
            "mood": mo.get("name") if mo.get("valence") != 0 else "calm",
            "mood_valence": mo.get("valence"),
            "guest": guest,
        })

    try:
        surge = wev.surge_active(ws)
        surge_text = wev.surge_text(ws) if surge else ""
    except Exception:
        surge, surge_text = False, ""

    try:
        events = [ln for ln in (ws.recent_events_text(limit=8) or "").splitlines()
                  if ln.strip()][-6:]
    except Exception:
        events = []

    return {
        "ok": True,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "clock": clock.format() if clock else "?",
        "season": getattr(clock, "season", "?") if clock else "?",
        "month": getattr(clock, "month_name", "?") if clock else "?",
        "time_scale": float(getattr(ws, "time_scale", 1.0) or 1.0),
        "play_mode": getattr(ws, "play_mode", None) or "journey",
        "engine_running": engine_running(),
        "visitor": ws.visitor_place(),
        "weather": dict((ws.ambient or {}).get("weather") or {}),
        "black_tide": {"active": bool(surge), "text": surge_text},
        "mailbox_unread": int(lw.unread_count(ws, "visitor") or 0),
        "heirs": heirs,
        "recent_events": events,
    }


def _esc(s) -> str:
    return html.escape(str(s or ""))


def _current_urls() -> dict:
    """The live URL list the guard publishes (gitignored world_runtime/)."""
    try:
        return json.loads(URLS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}


def status_html(st: dict) -> str:
    """A clean, phone-friendly, read-only page of the world's status."""
    if not st.get("ok"):
        return f"<pre>status unavailable: {_esc(st.get('error'))}</pre>"

    engine = ("<span style='color:#7fd68a'>running</span>" if st["engine_running"]
              else "<span style='color:#ff8f8f'>stopped</span>")
    vp = st["visitor"]
    if vp.get("kind") == "traveling":
        vis = (f"On the road <b>{_esc(vp.get('from'))} → {_esc(vp.get('to'))}</b>"
               f" — {int(vp.get('remaining', 0))} day(s) left")
    else:
        vis = f"In <b>{_esc(vp.get('at'))}</b>"

    tide = st["black_tide"]
    tide_line = (f"<div style='color:#ffb45e;margin:6px 0'><b>Black tide active</b> — "
                 f"{_esc(tide['text'])}</div>"
                 if tide["active"] else
                 "<div style='color:#8d84a8'>The tide is at rest.</div>")

    weather_rows = "".join(
        f"<li><b>{_esc(city)}</b> — {_esc(sky)}</li>"
        for city, sky in sorted(st["weather"].items()) if sky)
    weather_html = (f"<h3>Sky</h3><ul>{weather_rows}</ul>" if weather_rows else "")

    heir_rows = []
    for h in sorted(st["heirs"], key=lambda x: x["name"]):
        where = h["location"]
        if h.get("traveling_to"):
            where = f"{where} → {h['traveling_to']} ({h['road_days_left']} d)"
        tag = " guest" if h.get("guest") in ("present", "away") else ""
        heir_rows.append(
            f"<tr><td>{_esc(h['name'])}{tag}</td><td>{_esc(where)}</td>"
            f"<td>{_esc(h['mood'])}</td></tr>")
    heirs_html = ("<h3>Heirs</h3><table>"
                  "<tr><th>Heir</th><th>Where</th><th>Mood</th></tr>"
                  + "".join(heir_rows) + "</table>")

    events_html = ("<h3>Recent events</h3><ul>"
                   + "".join(f"<li>{_esc(e)}</li>" for e in st["recent_events"])
                   + "</ul>" if st["recent_events"] else "")

    urls = _current_urls()
    rows = []
    pub = (urls.get("status") or {}).get("public") or []
    if pub:
        rows.append("<li>Public (Internet): "
                    f"<a href='{_esc(pub[0])}'>{_esc(pub[0])}</a>"
                    " — this page; changes only if the machine restarts</li>")
    for u in (urls.get("status") or {}).get("lan") or []:
        rows.append("<li>LAN (same network, no Internet): "
                    f"<a href='{_esc(u)}'>{_esc(u)}</a></li>")
    for u in (urls.get("ui") or {}).get("lan") or []:
        rows.append("<li>Full interface (LAN only): "
                    f"<a href='{_esc(u)}'>{_esc(u)}</a></li>")
    reach = (f"<h3>Reach this world</h3><ul>{''.join(rows)}</ul>"
             if rows else "")

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>Amphoreus — world status</title>
<style>
 body{{background:#0b0a14;color:#e8dfc8;font-family:system-ui,Segoe UI,sans-serif;
      margin:0;padding:16px}}
 .wrap{{max-width:720px;margin:0 auto}}
 h1{{font-size:1.3rem;margin:.2rem 0}} h2{{font-size:1rem;margin:1rem 0 .3rem}}
 h3{{font-size:.95rem;margin:.9rem 0 .2rem}}
 .muted{{color:#8d84a8;font-size:.8rem}}
 table{{border-collapse:collapse;width:100%;font-size:.9rem}}
 td,th{{text-align:left;padding:3px 8px;border-bottom:1px solid #232038}}
 ul{{margin:.2rem 0;padding-left:1.2rem;font-size:.9rem}}
 .badge{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.75rem;
        background:#1d1830;border:1px solid #3a3260}}
 .enter{{display:inline-block;padding:9px 18px;border-radius:9px;
        background:#1d4ed8;color:#fff;text-decoration:none;font-weight:600;
        margin:10px 0}}
</style></head><body><div class="wrap">
<h1>Amphoreus — the little world, live</h1>
<div class="muted">Updated {_esc(st['ts'])} · auto-refreshes every 30 s</div>
<a class="enter" href="/app">Enter the Sanctuary — the full interface</a>
<h2>{_esc(st['clock'])}</h2>
<div><span class="badge">{_esc(st['season'])}</span>
<span class="badge">{_esc(st['month'])}</span>
<span class="badge">{_esc(st['play_mode'])}</span>
<span class="badge">time ×{st['time_scale']:g}</span>
<span class="badge">engine {engine}</span></div>
<div style="margin:8px 0">Visitor: {vis}
 · Mailbox unread: <b>{int(st['mailbox_unread'])}</b></div>
{tide_line}
{weather_html}
{heirs_html}
{events_html}
{reach}
<div class="muted" style="margin-top:1rem">Read-only status — the Sanctuary at
{_esc(str(PROJECT_ROOT))} · API: /api/status</div>
</div></body></html>"""


def status_json(st: dict) -> str:
    import json
    return json.dumps(st, ensure_ascii=False, indent=2)


def ui_page(public_url: str = "", lan_url: str = "") -> str:
    """The /app subpage: the full Sanctuary UI, embedded in a frame.

    public_url is the public tunnel URL of the UI (port 8501), lan_url a
    same-network URL derived from the request's Host header. The page also
    offers a direct "open in its own tab" link (full-app browsing is better
    in a real tab than in a frame).
    """
    src = public_url or lan_url or ""
    if not src:
        inner = ("<div style='padding:24px;color:#e8dfc8'>"
                 "<p>The Sanctuary interface is not running right now "
                 "(port 8501 is down). Start it, and this page comes alive.</p>"
                 "<p><a href='/'>Back to the world status</a></p></div>")
        direct = ""
    else:
        inner = (f'<iframe src="{_esc(src)}" title="Amphoreus Sanctuary" '
                 'style="position:absolute;top:0;left:0;width:100%;height:100%;'
                 'border:0"></iframe>')
        direct = (f'<a href="{_esc(src)}" target="_blank" rel="noopener" '
                  'style="color:#7fb0ff">open it in its own tab</a>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amphoreus — the Sanctuary</title>
<style>
 body{{margin:0;background:#0b0a14;color:#e8dfc8;font-family:system-ui,Segoe UI,sans-serif}}
 .bar{{padding:8px 14px;background:#141128;border-bottom:1px solid #2a2440;
       font-size:.85rem;display:flex;gap:14px;align-items:center}}
 a{{color:#7fb0ff;text-decoration:none}}
</style></head><body>
<div class="bar">
  <span><a href="/">World status</a></span>
  <span>The Sanctuary — full interface</span>
  <span style="margin-left:auto">{direct}</span>
</div>
<div style="position:fixed;inset:37px 0 0 0">{inner}</div>
</body></html>"""
