"""Galgame-style (visual-novel) view for an *active group gathering*.

Optional companion to classic ``ui_galgame.py`` — leaves the 1:1 VN untouched.
When a Visit gathering is live, this tab shows up to four Heir portraits,
a nameplate for the current speaker, and a typed dialogue line for the
latest assistant turn. Shares the group-chat session store.
"""

from __future__ import annotations

import html as _html
import json
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"
HEIRS = ASSETS / "heirs"


def _esc(t) -> str:
    return _html.escape(str(t))


@st.cache_data(show_spinner=False)
def _data_uri(path, mime="image/png", max_width=1200):
    """Base64 data URI — same approach as classic ui_galgame."""
    if not path or not Path(path).exists():
        return None
    try:
        import base64
        import io
        from PIL import Image
        im = Image.open(path)
        if im.width > max_width:
            h = int(im.height * max_width / im.width)
            im = im.resize((max_width, h), Image.LANCZOS)
        if mime == "image/jpeg":
            im = im.convert("RGB")
            fmt = "JPEG"
        else:
            im = im.convert("RGBA")
            fmt = "PNG"
        buf = io.BytesIO()
        im.save(buf, format=fmt)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None
    return f"data:{mime};base64,{b64}"


def _sprite(character_id: str) -> Optional[Path]:
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = HEIRS / f"{character_id}.{ext}"
        if p.exists():
            return p
    return None


def last_group_heir_line(messages: Sequence[dict]) -> Tuple[str, str, str]:
    """Latest assistant line with a Heir speaker → (speaker_id, name, text)."""
    for m in reversed(list(messages or [])):
        if (m.get("role") or "") != "assistant":
            continue
        text = str(m.get("content") or "").strip()
        if not text:
            continue
        speaker = str(m.get("speaker") or "").strip()
        name = ""
        if speaker:
            try:
                from src.world.world_state import WorldState
                name = WorldState().name_of(speaker) or speaker
            except Exception:
                name = speaker
        if not name:
            name = "the gathering"
        return speaker, name, text
    return "", "the gathering", "..."


def _last_user(messages: Sequence[dict]) -> str:
    for m in reversed(list(messages or [])):
        if (m.get("role") or "") == "user":
            return str(m.get("content") or "")
    return ""


def _sprites_row(
    members: Sequence[str],
    name_of: Callable[[str], str],
    *,
    active_id: str = "",
) -> str:
    """Up to four Heir portraits side by side (gold-on-dark Amphoreus look)."""
    row = [c for c in (members or []) if c][:4]
    if not row:
        return ""
    n = len(row)
    height = {1: 380, 2: 340, 3: 300, 4: 270}.get(n, 270)
    gap = 10 if n >= 3 else 18
    parts = [
        f'<div style="position:absolute;left:0;right:0;bottom:128px;'
        f'display:flex;justify-content:center;align-items:flex-end;'
        f'gap:{gap}px;padding:0 28px;pointer-events:none;">'
    ]
    for cid in row:
        uri = None
        sp = _sprite(cid)
        if sp:
            uri = _data_uri(str(sp), "image/png", max_width=560)
        nm = _esc(name_of(cid) if name_of else cid)
        is_active = bool(active_id) and cid == active_id
        glow = (
            "rgba(232,213,163,.42)" if is_active else "rgba(232,213,163,.16)"
        )
        opacity = "1" if (not active_id or is_active) else ".72"
        scale = "1" if (not active_id or is_active) else ".92"
        border = (
            "2px solid rgba(232,213,163,.55)" if is_active
            else "1px solid rgba(232,213,163,.12)"
        )
        delay = (abs(hash(cid)) % 7) * 0.12
        parts.append(
            f'<div style="flex:0 1 auto;max-width:{max(12, 100 // n)}%;'
            f'text-align:center;opacity:{opacity};transform:scale({scale});'
            f'filter:drop-shadow(0 0 18px {glow});'
            f'animation:galfloat 5s ease-in-out infinite;'
            f'animation-delay:{delay:.2f}s;">'
        )
        if uri:
            parts.append(
                f'<img src="{uri}" alt="{nm}" title="{nm}" '
                f'style="height:{height}px;width:auto;max-width:100%;'
                f'object-fit:contain;border-radius:8px;border:{border};"/>'
            )
        else:
            parts.append(
                f'<div style="height:{height}px;min-width:90px;'
                f'display:flex;align-items:flex-end;justify-content:center;'
                f'color:#e8d5a3;font-size:14px;letter-spacing:1px;">{nm}</div>'
            )
        parts.append("</div>")
    parts.append("</div>")
    return "".join(parts)


def _member_chips(speakers_info: Sequence[dict], active_id: str) -> str:
    chips = []
    for info in speakers_info or []:
        cid = str(info.get("id") or "")
        nm = _esc(info.get("name") or cid)
        on = bool(cid) and cid == active_id
        bg = "rgba(232,213,163,.22)" if on else "rgba(232,213,163,.08)"
        color = "#f0e6c8" if on else "#b8a97f"
        border = (
            "1px solid rgba(232,213,163,.55)" if on
            else "1px solid rgba(232,213,163,.18)"
        )
        chips.append(
            f'<span style="display:inline-block;padding:2px 10px;'
            f'margin:0 4px 0 0;border-radius:999px;font-size:11.5px;'
            f'letter-spacing:.4px;background:{bg};color:{color};'
            f'border:{border};">{nm}</span>'
        )
    if not chips:
        return ""
    return (
        '<div style="position:absolute;top:14px;left:16px;right:120px;'
        'display:flex;flex-wrap:wrap;gap:4px;align-items:center;">'
        + "".join(chips)
        + "</div>"
    )


def _group_scene_html(
    bg_uri,
    speakers_info,
    last_user,
    last_lines,
    place,
    wx=None,
):
    """Multi-sprite VN scene; nameplate = current speaker; box types last line."""
    speakers_info = list(speakers_info or [])
    active_id = ""
    active_name = "the gathering"
    members = []
    for info in speakers_info:
        cid = str(info.get("id") or "")
        if cid:
            members.append(cid)
        if info.get("speaking"):
            active_id = cid
            active_name = str(info.get("name") or cid or active_name)

    def _name_of(cid: str) -> str:
        for info in speakers_info:
            if info.get("id") == cid:
                return str(info.get("name") or cid)
        return cid

    bg_css = (
        f"background-image:url('{bg_uri}');" if bg_uri else "background:#0d0b18;"
    )
    place_txt = _esc(place) if place else "Amphoreus"
    name_txt = _esc(active_name)
    last_user_txt = _esc(last_user) if last_user else ""
    heir_json = json.dumps(_esc(last_lines or "..."))
    type_id = _esc(active_id or "gathering")

    parts = []
    parts.append("""
<div style="font-family:Georgia,serif;color:#f0e6c8;">
  <div style="position:relative;height:520px;border-radius:14px;overflow:hidden;
              border:1px solid rgba(232,213,163,.18);background:#0d0b18;">
""")
    if bg_uri:
        parts.append(
            f'<div style="position:absolute;inset:0;{bg_css}background-size:cover;'
            f'background-position:center;opacity:.5;"></div>'
        )
    if wx:
        parts.append(wx)
    parts.append(
        '<div style="position:absolute;inset:0;background:linear-gradient(180deg,'
        'rgba(11,10,20,0) 25%, rgba(11,10,20,.92) 90%);"></div>'
    )
    parts.append(_member_chips(speakers_info, active_id))
    parts.append(
        f'<div style="position:absolute;top:14px;right:16px;font-size:12.5px;'
        f'color:#e8d5a3;letter-spacing:.5px;opacity:.85;">{place_txt}</div>'
    )
    parts.append(_sprites_row(members, _name_of, active_id=active_id))
    parts.append(
        f'<div style="position:absolute;left:44px;bottom:128px;'
        f'background:linear-gradient(90deg,#e8d5a3,#c9a86a);color:#141126;'
        f'font-weight:700;padding:5px 18px;border-radius:8px 8px 0 0;'
        f'font-size:16px;letter-spacing:1.5px;'
        f'box-shadow:0 -2px 10px rgba(0,0,0,.4);">{name_txt}</div>'
    )
    parts.append(
        '<div style="position:absolute;left:0;right:0;bottom:0;min-height:128px;'
        'padding:12px 44px 12px;background:rgba(13,11,24,.93);'
        'border-top:1px solid rgba(232,213,163,.28);">'
    )
    if last_user_txt:
        parts.append(
            f'<div style="font-size:13px;color:#b8a97f;font-style:italic;'
            f'margin-bottom:6px;">You: {last_user_txt[:180]}</div>'
        )
    parts.append(
        f'<div id="galtype-g-{type_id}" style="font-size:17px;line-height:1.6;'
        f'min-height:52px;"></div>'
    )
    parts.append(
        '<div style="text-align:right;color:#e8d5a3;font-size:14px;'
        'animation:galblink 1.1s steps(2,start) infinite;">▼</div>'
    )
    parts.append("</div></div>")
    parts.append("""
<style>
@keyframes galfloat { 0%,100% { transform:translateY(0); }
                       50%     { transform:translateY(-8px); } }
@keyframes galblink { to { visibility:hidden; } }
</style>
<script>
(function(){
  var el = document.getElementById('galtype-g-__CID__');
  if (!el) return;
  var text = __TEXT__;
  var key = 'gal_group_last___CID__';
  var prev = null;
  try { prev = sessionStorage.getItem(key); } catch(e) {}
  if (prev === text) { el.textContent = text; return; }
  el.textContent = '';
  var i = 0;
  var timer = setInterval(function(){
    i++;
    el.textContent = text.slice(0, i);
    if (i >= text.length) {
      clearInterval(timer);
      try { sessionStorage.setItem(key, text); } catch(e) {}
    }
  }, 14);
})();
</script>
""")
    return "".join(parts).replace("__CID__", type_id).replace("__TEXT__", heir_json)


def render_group_galgame(manager, store=None) -> None:
    """Render the active gathering as a VN scene, or a Visit hint."""
    from src.ui_group_chat import group_is_active, group_messages, store as gc_store

    sess = store if isinstance(store, dict) and "members" in store else gc_store()
    try:
        from src.world import group_chat as gc
        sess = gc.as_session(sess)
    except Exception:
        pass

    active = False
    try:
        active = group_is_active()
    except Exception:
        active = bool(sess.get("active") and len(sess.get("members") or []) >= 2)

    msgs = list(sess.get("messages") or []) or list(group_messages() or [])
    members = list(sess.get("members") or [])

    if not active or not msgs:
        st.info(
            "No gathering is on stage yet. On **Visit an Heir**, invite "
            "companions who stand in the same place — then return here for "
            "the multi-Heir visual-novel view."
        )
        return

    def _name_of(cid: str) -> str:
        try:
            return manager.get_character_info(cid)["name"]
        except Exception:
            try:
                from src.world.world_state import WorldState
                return WorldState().name_of(cid) or cid
            except Exception:
                return cid

    speaker_id, speaker_name, last_line = last_group_heir_line(msgs)
    last_user = _last_user(msgs)
    place = str(sess.get("place") or "")

    speakers_info = []
    for cid in members[:4]:
        speakers_info.append({
            "id": cid,
            "name": _name_of(cid),
            "speaking": bool(speaker_id) and cid == speaker_id,
        })
    if speaker_id and speaker_id not in {m for m in members}:
        speakers_info.append({
            "id": speaker_id,
            "name": speaker_name,
            "speaking": True,
        })

    with st.expander("Gathering log"):
        for m in msgs:
            role = m.get("role") or "assistant"
            if role == "user":
                st.markdown(f"**You:** {m.get('content') or ''}")
            else:
                sp = m.get("speaker") or ""
                who = _name_of(sp) if sp else "the gathering"
                st.markdown(f"**{who}:** {m.get('content') or ''}")

    names = ", ".join(_name_of(c) for c in members)
    st.caption(
        f"Galgame view — gathering at **{place or 'Amphoreus'}** · {names}"
    )

    from src.ui_backgrounds import bg_path, bg_path_for_place
    from src.ui_weather import overlay_for as _wx_overlay

    bg_file = bg_path_for_place(place) if place else None
    if not bg_file and members:
        try:
            bg_file = bg_path(members[0])
        except Exception:
            bg_file = None
    bg = _data_uri(bg_file, "image/jpeg", max_width=1400) if bg_file else None
    wx = _wx_overlay(place, place or "Amphoreus") if place else None

    html = _group_scene_html(
        bg,
        speakers_info,
        last_user,
        last_line,
        place,
        wx=wx,
    )
    st.components.v1.html(html, height=560)

    from src.ui_role import is_visitor
    if is_visitor():
        st.caption(
            "Read-only view — speak with the gathering from Visit as the operator."
        )
    else:
        st.caption(
            "Speak with the gathering on the **Visit an Heir** tab — "
            "this stage mirrors the same conversation."
        )
