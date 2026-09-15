# -*- coding: utf-8 -*-
"""An Eternal Page — desktop-buddy circle, distinct from Visit chatboxes.

Stickers stand on the parchment. Click to stand near (or away). Double-click
to speak with only that Heir. Whisper into the dock below the stage — not a
Visit transcript. Wheel over the stage is passed to the parent page so scroll
is never stolen. No weather, no ecosystem.
"""
from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Iterable, Optional

STAGE_H = 560
_CLICK_Q = "ep_click"
_SOLO_Q = "ep_solo"

_CSS_PAGE = """
<style>
html.amp-mode-eternal .st-key-amp_look_chrome { display: none !important; }
html.amp-mode-eternal iframe[data-amp-land="1"],
html.amp-mode-eternal iframe[data-amp-land-life="1"],
html.amp-mode-eternal [data-amp-land-wrap="1"],
html.amp-mode-eternal #amp-land-photo-host,
html.amp-mode-eternal #amp-land-notice-host {
  display: none !important;
}
iframe[data-amp-eternal="1"] {
  display: block;
  width: 100%;
  max-width: 100%;
  height: __H__px !important;
  border: 0 !important;
  background: transparent !important;
  position: relative !important;
  z-index: 2 !important;
}
.st-key-amp_eternal_dock,
.st-key-amp_eternal_bar {
  position: relative !important;
  z-index: 6 !important;
}
</style>
"""

_WATCHER = """
<script>
(function(){
  var doc = window.parent.document;
  function tabName(el){
    return ((el && el.innerText) || '').replace(/\\s+/g, ' ').trim();
  }
  function sync(){
    var eternal = false;
    try {
      var p = window.parent.location.pathname || '';
      if (/An_Eternal_Page/i.test(p)) eternal = true;
    } catch (e) {}
    if (!eternal) {
      var t = doc.querySelector('[role="tab"][aria-selected="true"]');
      eternal = tabName(t) === 'An Eternal Page';
    }
    doc.documentElement.classList.toggle('amp-mode-eternal', eternal);
    if (eternal) {
      doc.documentElement.classList.add('amp-land-off');
      doc.documentElement.classList.remove('amp-mode-visit', 'amp-mode-walk');
    }
  }
  sync();
  doc.addEventListener('click', function(){ setTimeout(sync, 40); }, true);
  try {
    new MutationObserver(sync).observe(doc.body, {
      attributes: true, subtree: true, attributeFilter: ['aria-selected']
    });
  } catch (e) {}
})();
</script>
"""


def _data_uri(path: Path) -> str:
    raw = path.read_bytes()
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def _mark_iframe_js() -> str:
    return """
(function(){
  try {
    var f = window.frameElement;
    if (f) {
      f.setAttribute('data-amp-eternal', '1');
      f.setAttribute('scrolling', 'no');
    }
  } catch (e) {}
  function passWheel(e){
    try { window.parent.scrollBy(0, e.deltaY); } catch (err) {}
  }
  document.addEventListener('wheel', passWheel, {passive: true});
  document.addEventListener('mousewheel', passWheel, {passive: true});
})();
"""


def build_stage_html(
    *,
    selected: Iterable[str],
    bubbles: Optional[list] = None,
    art: Optional[dict] = None,
    parchment_uri: str = "",
    names: Optional[dict] = None,
) -> str:
    from src.world import eternal_page as ep

    selected_ids = ep.normalize_selected(selected)
    art = art or {}
    names = names or {}
    bubble_by = {}
    for row in bubbles or []:
        cid = str(row.get("id") or "")
        text = str(row.get("text") or "").strip()
        if cid and text:
            bubble_by[cid] = text

    buddies = []
    for cid in ep.all_ids():
        src = art.get(cid) or ""
        if not src:
            continue
        left, bottom = ep.LAYOUT.get(cid, (50.0, 50.0))
        on = " on" if cid in selected_ids else ""
        label = html.escape(names.get(cid) or ep.short_name(cid))
        spoken = bubble_by.get(cid, "")
        bubble = ""
        if spoken:
            bubble = (
                f'<div class="bubble" data-amp-bubble="1">'
                f"{html.escape(spoken)}</div>"
            )
        buddies.append(
            f'<button type="button" class="buddy{on}" data-heir="{html.escape(cid)}" '
            f'style="left:{left}%;bottom:{bottom}%;z-index:{3 if cid in selected_ids else 2}">'
            f'{bubble}'
            f'<img alt="{label}" src="{src}" draggable="false" />'
            f'<span class="name">{label}</span>'
            f"</button>"
        )

    bg = ""
    if parchment_uri:
        bg = (
            f"background-image:url('{parchment_uri}');"
            "background-size:cover;background-position:center;"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
html, body {{
  margin: 0; padding: 0; width: 100%; height: 100%;
  overflow: hidden; background: #1a140c;
  font-family: "Segoe UI", "Palatino Linotype", Georgia, serif;
}}
.stage {{
  position: relative;
  width: 100%;
  height: 100%;
  {bg}
  background-color: #cbb58a;
}}
.stage::before {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 50% 18%, rgba(255,248,220,.22), transparent 55%),
    linear-gradient(180deg, rgba(20,12,6,.12), rgba(20,12,6,.28));
}}
.buddy {{
  position: absolute;
  width: 12.5%;
  min-width: 72px;
  transform: translateX(-50%);
  background: none;
  border: 0;
  padding: 0;
  cursor: pointer;
  animation: amp-bob 3.1s ease-in-out infinite;
  pointer-events: auto;
}}
.buddy:nth-child(odd) {{ animation-duration: 2.7s; animation-delay: -.4s; }}
.buddy:nth-child(3n) {{ animation-duration: 3.4s; animation-delay: -.8s; }}
.buddy img {{
  display: block;
  width: 100%;
  height: auto;
  user-select: none;
  -webkit-user-drag: none;
  filter: drop-shadow(0 8px 10px rgba(20,12,6,.45));
}}
.buddy.on img {{
  filter: drop-shadow(0 0 10px rgba(240,215,140,.95)) drop-shadow(0 8px 10px rgba(20,12,6,.45));
}}
.buddy .name {{
  display: block;
  margin-top: 2px;
  color: #f7edd2;
  font-size: 12px;
  letter-spacing: .04em;
  text-align: center;
  text-shadow: 0 1px 2px #1a140c, 0 0 6px #1a140c;
}}
.buddy.on::after {{
  content: "";
  position: absolute;
  left: 18%;
  right: 18%;
  bottom: 16px;
  height: 10px;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse, rgba(240,215,140,.7), transparent 70%);
}}
.bubble {{
  position: absolute;
  left: 50%;
  bottom: 92%;
  transform: translateX(-50%);
  z-index: 8;
  max-width: 220px;
  min-width: 90px;
  padding: 8px 10px;
  border-radius: 14px 14px 14px 4px;
  background: rgba(255,250,240,.94);
  color: #2a2014;
  font-size: 12px;
  line-height: 1.35;
  box-shadow: 0 4px 14px rgba(20,12,6,.28);
  pointer-events: none;
}}
@keyframes amp-bob {{
  0%, 100% {{ transform: translateX(-50%) translateY(0); }}
  50% {{ transform: translateX(-50%) translateY(-7px); }}
}}
.hint {{
  position: absolute;
  top: 10px;
  left: 14px;
  z-index: 6;
  color: #f7edd2;
  font-size: 13px;
  text-shadow: 0 1px 3px #1a140c;
  pointer-events: none;
}}
</style>
</head>
<body>
<div class="stage" data-amp-eternal-stage="1">
  <div class="hint">Click a companion to stand near them · double-click to speak with only them</div>
  {''.join(buddies)}
</div>
<script>
{_mark_iframe_js()}
(function(){{
  var timers = {{}};
  function nav(key, id){{
    try {{
      var u = new URL(window.parent.location.href);
      u.searchParams.set(key, id);
      window.parent.location.href = u.href;
    }} catch (e) {{}}
  }}
  document.querySelectorAll('.buddy').forEach(function(el){{
    var id = el.getAttribute('data-heir');
    el.addEventListener('click', function(e){{
      e.preventDefault();
      e.stopPropagation();
      clearTimeout(timers[id]);
      timers[id] = setTimeout(function(){{ nav('ep_click', id); }}, 220);
    }});
    el.addEventListener('dblclick', function(e){{
      e.preventDefault();
      e.stopPropagation();
      clearTimeout(timers[id]);
      nav('ep_solo', id);
    }});
  }});
}})();
</script>
</body>
</html>
"""


def _consume_clicks(st) -> bool:
    from src.world import eternal_page as ep

    selected = ep.normalize_selected(st.session_state.get(ep.STATE_SELECTED))
    changed = False
    try:
        click = str(st.query_params.get(_CLICK_Q) or "").strip()
        solo = str(st.query_params.get(_SOLO_Q) or "").strip()
    except Exception:
        click, solo = "", ""
    if click:
        selected = ep.toggle_member(selected, click)
        changed = True
        try:
            del st.query_params[_CLICK_Q]
        except Exception:
            pass
    if solo:
        selected = ep.solo_member(solo)
        changed = True
        try:
            del st.query_params[_SOLO_Q]
        except Exception:
            pass
    if changed:
        st.session_state[ep.STATE_SELECTED] = selected
    return changed


def _names(manager) -> dict:
    from src.world import eternal_page as ep

    out = {}
    for cid in ep.all_ids():
        name = ep.short_name(cid)
        try:
            info = manager.get_character_info(cid)
            raw = str((info or {}).get("name") or "").strip()
            if raw:
                if cid == "dan-heng-permansor-terrae":
                    name = "Dan Heng"
                else:
                    name = raw.split("•")[0].strip() or raw
        except Exception:
            pass
        out[cid] = name
    return out


def render_eternal_page(manager, *, key_prefix: str = "eternal") -> None:
    import streamlit as st
    import streamlit.components.v1 as components

    from src.ui_role import is_visitor
    from src.world import eternal_page as ep

    st.markdown(_CSS_PAGE.replace("__H__", str(STAGE_H)), unsafe_allow_html=True)
    try:
        components.html(_WATCHER, height=0, scrolling=False)
    except Exception:
        pass

    if _consume_clicks(st):
        st.rerun()

    if ep.STATE_SELECTED not in st.session_state:
        st.session_state[ep.STATE_SELECTED] = list(ep.all_ids())
    selected = ep.normalize_selected(st.session_state.get(ep.STATE_SELECTED))
    bubbles = list(st.session_state.get(ep.STATE_BUBBLES) or [])
    names = _names(manager)

    st.title("An Eternal Page")
    st.caption(
        "Beyond Time — the page where every Chrysos Heir may stand near you. "
        "This is not Visit an Heir: companions live on the parchment. "
        "Click to choose one, several, or all. The same memories are kept."
    )

    missing = ep.art_missing()
    if missing:
        st.warning(
            "Cute companion art is missing for: "
            + ", ".join(ep.short_name(c) for c in missing)
            + ". Run `python tools/fetch_eternal_page_art.py`."
        )

    with st.container(key="amp_eternal_bar"):
        c1, c2, c3, c4 = st.columns([1.2, 1.2, 2.2, 3])
        with c1:
            if st.button("All thirteen", key=f"{key_prefix}_all"):
                st.session_state[ep.STATE_SELECTED] = list(ep.all_ids())
                st.rerun()
        with c2:
            if st.button("Clear", key=f"{key_prefix}_clear"):
                st.session_state[ep.STATE_SELECTED] = []
                st.rerun()
        with c3:
            everyone = st.checkbox(
                "Everyone near answers",
                key=ep.STATE_EVERYONE,
                help="When off, a handful answer and the rest still hear you.",
            )
        with c4:
            if selected:
                st.caption(
                    "Standing near: "
                    + ", ".join(names.get(c, c) for c in selected)
                )
            else:
                st.caption("No one is standing near yet — click a companion.")

    art_uris = {}
    for cid in ep.all_ids():
        path = ep.cute_art(cid)
        if path:
            art_uris[cid] = _data_uri(path)
    parchment = ep.parchment_path()
    parchment_uri = _data_uri(parchment) if parchment else ""

    html_doc = build_stage_html(
        selected=selected,
        bubbles=bubbles,
        art=art_uris,
        parchment_uri=parchment_uri,
        names=names,
    )
    components.html(html_doc, height=STAGE_H, scrolling=False)

    with st.container(key="amp_eternal_dock"):
        if is_visitor():
            st.caption(
                "Read-only view — sign in as the operator to whisper on the page."
            )
        else:
            with st.form(f"{key_prefix}_whisper_form", clear_on_submit=True):
                left, right = st.columns([5, 1])
                with left:
                    said = st.text_input(
                        "Whisper",
                        placeholder="Speak to those who stand near…",
                        label_visibility="collapsed",
                    )
                with right:
                    go = st.form_submit_button("Speak")
            if go:
                said = (said or "").strip()
                if not said:
                    st.info("Say something first.")
                elif not selected:
                    st.info("Click at least one companion so they stand near you.")
                else:
                    with st.spinner("Those who stand near are listening…"):
                        result = ep.eternal_talk(
                            manager,
                            selected,
                            said,
                            everyone=bool(st.session_state.get(ep.STATE_EVERYONE)),
                            rotate=int(st.session_state.get(ep.STATE_ROTATE) or 0),
                            name_of=lambda c: names.get(c, ep.short_name(c)),
                        )
                    if result.get("ok"):
                        st.session_state[ep.STATE_BUBBLES] = result.get("replies") or []
                        st.session_state[ep.STATE_ROTATE] = result.get("next_rotate") or 0
                        st.rerun()
                    elif result.get("reason") == "none_near":
                        st.info("Click at least one companion so they stand near you.")

    heard = [r for r in bubbles if r.get("spoke") and r.get("text")]
    quiet = [r for r in bubbles if not r.get("spoke")]
    if heard:
        lines = " · ".join(
            f"{r.get('name') or r.get('id')} answered" for r in heard
        )
        extra = ""
        if quiet:
            extra = (
                "  \nAlso listening: "
                + ", ".join(str(r.get("name") or r.get("id")) for r in quiet)
                + "."
            )
        st.caption(lines + extra)
