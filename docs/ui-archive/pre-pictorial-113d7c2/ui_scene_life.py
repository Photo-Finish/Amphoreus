"""Visit scene life — ambient visuals + clickable ecosystem objects.

Extends the weather backdrop with grass / leaf / chimera / shore motion, and
exposes Streamlit controls for interact (Awoo, NPC identity) and gated care.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def _css() -> str:
    return """
<style>
@keyframes amp-grass-sway {
  0%,100% { transform: rotate(-4deg) translateY(0); }
  50% { transform: rotate(5deg) translateY(-2px); }
}
@keyframes amp-chimera-wander {
  0% { left: 8%; opacity: 0; }
  10% { opacity: .92; }
  50% { left: 55%; }
  90% { opacity: .92; }
  100% { left: 88%; opacity: 0; }
}
@keyframes amp-leaf-drift {
  0% { transform: translateY(0) rotate(0deg); opacity: .0; }
  15% { opacity: .7; }
  100% { transform: translateY(110px) rotate(40deg); opacity: 0; }
}
@keyframes amp-shore-glint {
  0%,100% { opacity: .15; }
  50% { opacity: .45; }
}
@keyframes amp-wheat-nod {
  0%,100% { transform: skewX(-2deg); }
  50% { transform: skewX(3deg); }
}
@keyframes amp-courier-arc {
  0% { left: 8%; top: 18%; opacity: 0; }
  12% { opacity: .85; }
  88% { opacity: .85; }
  100% { left: 88%; top: 10%; opacity: 0; }
}
@keyframes amp-fountain-glint {
  0%,100% { opacity: .2; }
  50% { opacity: .55; }
}
@keyframes amp-laundry-sway {
  0%,100% { transform: rotate(-6deg); }
  50% { transform: rotate(7deg); }
}
.amp-life-layer { position:absolute; inset:0; pointer-events:none; overflow:hidden; }
.amp-hotspot {
  pointer-events: none;
  position: absolute;
  width: 44px; height: 44px;
  margin-left: -22px; margin-bottom: -8px;
  border-radius: 50%;
  z-index: 6;
  background: radial-gradient(circle, rgba(240,230,200,.38), transparent 72%);
  border: 1px solid rgba(232,213,163,.45);
  box-shadow: 0 0 10px rgba(232,213,163,.15);
}
.amp-grass-blade {
  position:absolute; bottom:0; width:3px; height:18px;
  background: linear-gradient(180deg, rgba(120,160,80,.0), rgba(90,130,55,.75));
  transform-origin: bottom center;
  animation: amp-grass-sway 2.8s ease-in-out infinite;
}
.amp-chimera-dot {
  position:absolute; bottom:18%; width:22px; height:16px;
  border-radius: 10px 10px 6px 6px;
  background: radial-gradient(circle at 30% 40%, #f2e6c9, #c9a86a 70%);
  box-shadow: 0 0 0 1px rgba(0,0,0,.25);
  animation: amp-chimera-wander 14s linear infinite;
}
.amp-chimera-dot::after {
  content:"Awoo"; position:absolute; top:-14px; left:-4px;
  font-size:9px; color:#f0e6c8; opacity:.0;
  text-shadow:0 1px 4px #000;
}
.amp-chimera-dot.ailing { background: radial-gradient(circle at 30% 40%, #d8c8a8, #8a7060 70%); filter:saturate(.6); }
.amp-leaf {
  position:absolute; top:8%; width:10px; height:14px; border-radius:2px 10px;
  background: rgba(70,120,60,.65);
  animation: amp-leaf-drift 7s ease-in infinite;
}
.amp-shore-band {
  position:absolute; left:0; right:0; bottom:0; height:28%;
  background: linear-gradient(180deg, transparent, rgba(80,140,170,.35));
  animation: amp-shore-glint 4s ease-in-out infinite;
}
.amp-wheat-row {
  position:absolute; left:5%; right:5%; bottom:6%; height:22px;
  background: repeating-linear-gradient(90deg,
    rgba(200,170,70,.0) 0 6px, rgba(210,180,80,.55) 6px 9px);
  animation: amp-wheat-nod 3.2s ease-in-out infinite;
  transform-origin: bottom center;
}
.amp-fountain {
  position:absolute; width:28px; height:18px; border-radius:50%;
  background: radial-gradient(circle, rgba(160,200,220,.55), transparent 70%);
  animation: amp-fountain-glint 3.4s ease-in-out infinite;
}
.amp-laundry {
  position:absolute; width:36px; height:3px;
  background: rgba(220,210,190,.55);
  transform-origin: left center;
  animation: amp-laundry-sway 3.6s ease-in-out infinite;
}
.amp-courier {
  position:absolute; width:10px; height:6px; border-radius: 6px 2px;
  background: #c9b896;
  animation: amp-courier-arc 11s linear infinite;
}
.amp-life-tag {
  position:absolute; bottom:10px; right:12px; font-size:11px;
  color:#f0e6c8; letter-spacing:.4px;
  text-shadow:0 1px 6px rgba(0,0,0,.85);
  background:rgba(10,8,20,.5); padding:2px 10px; border-radius:999px;
}
</style>
"""


def life_overlay_html(scene: List[dict], place: str = "", *, dense: bool = False) -> str:
    """CSS/HTML layer for grass, chimeras, leaves, shore, wheat — visual only."""
    kinds = {b.get("kind") for b in (scene or [])}
    parts = ['<div class="amp-life-layer">']

    grass_xs = (6, 14, 22, 31, 40, 52, 61, 70, 78, 88)
    if dense:
        grass_xs = grass_xs + (10, 18, 26, 35, 45, 56, 65, 74, 82, 92)
    if "grass" in kinds or "wind" in kinds:
        for i, x in enumerate(grass_xs):
            delay = (i * 0.17) % 2.5
            parts.append(
                f'<div class="amp-grass-blade" style="left:{x}%;'
                f'animation-delay:{delay:.2f}s;height:{14 + (i % 5) * 3}px;"></div>'
            )

    chimeras = [b for b in scene if b.get("kind") == "chimera"]
    n_chim = min(len(chimeras), 3 if dense else 2)
    for i, ch in enumerate(chimeras[:n_chim]):
        cls = "amp-chimera-dot ailing" if ch.get("status") == "ailing" else "amp-chimera-dot"
        parts.append(
            f'<div class="{cls}" style="animation-delay:{i * 5.5}s;bottom:{16 + i * 8}%;"></div>'
        )

    if "grove_leaf" in kinds:
        leaf_xs = (18, 42, 67, 81) if not dense else (12, 28, 44, 58, 72, 86)
        for i, left in enumerate(leaf_xs):
            parts.append(
                f'<div class="amp-leaf" style="left:{left}%;'
                f'animation-delay:{i * 1.4}s;"></div>'
            )

    if "shore" in kinds:
        parts.append('<div class="amp-shore-band"></div>')

    if "wheat" in kinds:
        parts.append('<div class="amp-wheat-row"></div>')

    if "fountain" in kinds:
        parts.append(
            '<div class="amp-fountain" style="left:46%;bottom:16%;"></div>'
        )
    if "laundry" in kinds:
        parts.append(
            '<div class="amp-laundry" style="left:78%;bottom:34%;"></div>'
        )
    if "courier" in kinds:
        parts.append('<div class="amp-courier"></div>')

    label_bits = []
    for k in (
        "chimera", "dromas", "wheat", "shore", "grove_leaf", "grass",
        "fountain", "olive", "boat", "cicada", "mosaic",
    ):
        if k in kinds:
            label_bits.append(k.replace("_", " "))
    if label_bits:
        parts.append(
            f'<div class="amp-life-tag">{" · ".join(label_bits[:4])}</div>'
        )
    # Decorative glows only — Streamlit rewrites <a href> into new tabs
    # and drops the guest session. Real clicks live in render_stage_bar().
    import html as _html
    for b in (scene or []):
        if not b.get("clickable"):
            continue
        hs = b.get("hotspot") or {}
        left = hs.get("left") or "50%"
        bottom = hs.get("bottom") or "20%"
        title = _html.escape(str(b.get("name") or b.get("kind") or "life"))
        parts.append(
            f'<span class="amp-hotspot" title="{title}" '
            f'style="left:{left};bottom:{bottom};"></span>'
        )
    parts.append("</div>")
    return _css() + "".join(parts)


def inject_into_scene_html(scene_html: str, scene: List[dict], place: str = "",
                           *, dense: bool = False) -> str:
    """Slip the life layer into an existing weather scene container."""
    if not scene_html:
        return life_overlay_html(scene, place, dense=dense)
    overlay = life_overlay_html(scene, place, dense=dense)
    idx = scene_html.rfind("</div>")
    if idx < 0:
        return scene_html + overlay
    return scene_html[:idx] + overlay + scene_html[idx:]


def _do_notice(*, oid: str, heir_id: str, place: Optional[str],
               key_prefix: str) -> None:
    import streamlit as st
    from src.world import ecosystem as eco
    from src.world.world_state import WorldState

    res = eco.interact(
        WorldState(), oid, character_id=heir_id or None, place=place)
    noticed = st.session_state.setdefault("eco_noticed", {})
    if not isinstance(noticed, dict):
        noticed = {}
        st.session_state["eco_noticed"] = noticed
    if res.get("ok"):
        tb = res.get("textbox") or res.get("line") or ""
        st.session_state[f"{key_prefix}_flash"] = res.get("line") or tb
        b = res.get("being") or {}
        noticed[oid] = {
            "id": oid,
            "name": b.get("name"),
            "kind": b.get("kind"),
            "status": b.get("status"),
            "line": res.get("line"),
            "sound": res.get("sound"),
            "heir": heir_id,
            "place": place or b.get("place") or "",
        }
        st.session_state["eco_noticed"] = noticed
    else:
        st.session_state[f"{key_prefix}_flash"] = res.get("reason")


def render_stage_bar(
    scene: List[dict],
    *,
    heir_id: str = "",
    key_prefix: str,
    place: Optional[str] = None,
) -> None:
    """In-session name chips under the picture (no URL navigation)."""
    import streamlit as st

    clickable = [b for b in (scene or []) if b.get("clickable") and b.get("id")]
    if not clickable:
        return
    st.caption("On this stage — touch a name. Same session; nothing opens a new page.")
    for i in range(0, len(clickable), 4):
        cols = st.columns(4)
        for j, b in enumerate(clickable[i:i + 4]):
            oid = b.get("id") or ""
            label = (b.get("name") or b.get("kind") or "life").strip()
            with cols[j]:
                if st.button(label, key=f"{key_prefix}_glow_{oid}"):
                    _do_notice(
                        oid=oid, heir_id=heir_id, place=place,
                        key_prefix=key_prefix)
    _render_pocket()
    flash = st.session_state.pop(f"{key_prefix}_flash", None)
    if flash:
        st.info(flash)


def _render_pocket() -> None:
    import streamlit as st
    try:
        from src.world.world_state import WorldState
        from src.world import ecosystem as eco
        pocket = list((eco.eco_bucket(WorldState()).get("pocket") or []))
    except Exception:
        pocket = []
    if pocket:
        names = [str(p.get("name") or "a small thing") for p in pocket[-6:]]
        st.caption("In your pocket: " + " · ".join(names))


def render_life_interactions(
    scene: List[dict],
    *,
    heir_id: str,
    heir_name: str,
    manager,
    key_prefix: str,
    read_only: bool = False,
    place: Optional[str] = None,
) -> None:
    """Streamlit controls: click → textbox sound / identity; gated care."""
    import streamlit as st
    from src.world import ecosystem as eco
    from src.world.world_state import WorldState

    if not scene:
        st.caption("No living presence on this stage this hour.")
        return

    st.markdown("##### Life on this stage")
    st.caption(
        "Touch a **name under the picture**, or a row here. "
        "Sounds, names, a pebble in your pocket — Heir care only when that Heir is with you."
    )

    # Persist what the visitor noticed so chat can reference it.
    noticed = st.session_state.setdefault("eco_noticed", {})
    if not isinstance(noticed, dict):
        noticed = {}
        st.session_state["eco_noticed"] = noticed

    for b in scene:
        oid = b.get("id") or ""
        kind = b.get("kind") or ""
        label = b.get("name") or kind
        status = b.get("status") or ""
        col_a, col_b, col_c = st.columns([3, 1, 2])
        with col_a:
            mark = ""
            if status == "ailing":
                mark = " · ailing"
            elif status == "restless":
                mark = " · restless"
            elif status == "uneasy":
                mark = " · uneasy"
            st.markdown(f"**{label}**{mark}  \n*{b.get('doing') or ''}*")
        with col_b:
            if st.button("Notice", key=f"{key_prefix}_n_{oid}"):
                _do_notice(
                    oid=oid, heir_id=heir_id, place=place,
                    key_prefix=key_prefix)
        with col_c:
            acts = list(b.get("visitor_acts") or [])
            for aid in acts:
                pretty = aid.replace("_", " ")
                if st.button(pretty, key=f"{key_prefix}_v_{oid}_{aid}"):
                    ws = WorldState()
                    touch = eco.visitor_touch(
                        ws, oid, aid, place=place, save=True)
                    if touch.get("ok"):
                        st.session_state[f"{key_prefix}_flash"] = touch.get("note")
                        noticed[oid] = {
                            "id": oid, "name": label, "kind": kind,
                            "status": status, "line": touch.get("note"),
                            "heir": heir_id, "place": place or "",
                            "touched": aid,
                        }
                        st.session_state["eco_noticed"] = noticed
                    else:
                        st.session_state[f"{key_prefix}_flash"] = touch.get("reason")
            if read_only or not heir_id:
                continue
            actions = eco.authorized_actions(heir_id, b)
            for a in actions:
                btn = f"{a['label'].title()} ({heir_name})"
                if st.button(btn, key=f"{key_prefix}_c_{oid}_{a['id']}"):
                    ws = WorldState()
                    care = eco.apply_care(ws, heir_id, oid, a["id"], save=True)
                    if care.get("ok"):
                        st.session_state[f"{key_prefix}_flash"] = (
                            f"{heir_name}: {care.get('note')}"
                        )
                        msgs = st.session_state.setdefault("messages", {})
                        hist = msgs.setdefault(heir_id, [])
                        hist.append({
                            "role": "user",
                            "content": (
                                f"*(you ask {heir_name} to {a['label']} "
                                f"{label})*"
                            ),
                        })
                        hist.append({
                            "role": "assistant",
                            "content": (
                                f"*(the living world records: {care.get('note')})*"
                            ),
                        })
                        noticed[oid] = {
                            "id": oid,
                            "name": label,
                            "kind": kind,
                            "status": (care.get("being") or {}).get("status") or status,
                            "line": care.get("note"),
                            "cared": True,
                            "heir": heir_id,
                        }
                        st.session_state["eco_noticed"] = noticed
                        st.rerun()
                    else:
                        st.session_state[f"{key_prefix}_flash"] = care.get("reason")

    flash = st.session_state.pop(f"{key_prefix}_flash", None)
    if flash:
        st.info(flash)
    _render_pocket()

    if noticed and heir_id:
        bits = [
            v.get("name") for v in noticed.values()
            if v.get("heir") == heir_id
        ][:4]
        if bits:
            st.caption("You have noticed: " + " · ".join(bits)
                       + " — ask the Heir about them in chat.")


def noticed_prompt_addon(heir_id: str) -> str:
    """Extra injector from what the visitor clicked this session."""
    try:
        import streamlit as st
        noticed = st.session_state.get("eco_noticed") or {}
    except Exception:
        return ""
    rows = [
        v for v in noticed.values()
        if v.get("heir") == heir_id
    ]
    if not rows:
        return ""
    lines = ["# What the visitor just pointed at on the stage"]
    for v in rows[-5:]:
        lines.append(
            f"- {v.get('name')} ({v.get('kind')}, {v.get('status')}): "
            f"{v.get('line') or v.get('sound') or 'noticed'}"
        )
    lines.append(
        "If they ask who someone is, or about that chimera / grass / shore, "
        "answer from these facts. Do not invent other cities' life."
    )
    return "\n".join(lines)


def consume_notice_query(*, place: Optional[str] = None, heir_id: str = "",
                         key_prefix: str = "walk") -> None:
    """Handle a click on a scene hotspot (`?amp_notice=`)."""
    try:
        import streamlit as st
        from urllib.parse import unquote
        from src.world.world_state import WorldState
        from src.world import ecosystem as eco
    except Exception:
        return
    raw = st.query_params.get("amp_notice")
    if not raw:
        return
    if isinstance(raw, list):
        raw = raw[0] if raw else ""
    oid = unquote(str(raw or ""))
    if not oid:
        return
    res = eco.interact(
        WorldState(), oid, character_id=heir_id or None, place=place)
    if res.get("ok"):
        st.session_state[f"{key_prefix}_flash"] = res.get("line")
        noticed = st.session_state.setdefault("eco_noticed", {})
        b = res.get("being") or {}
        noticed[oid] = {
            "id": oid,
            "name": b.get("name"),
            "kind": b.get("kind"),
            "status": b.get("status"),
            "line": res.get("line"),
            "sound": res.get("sound"),
            "heir": heir_id,
            "place": place or b.get("place") or "",
        }
        st.session_state["eco_noticed"] = noticed
    else:
        st.session_state[f"{key_prefix}_flash"] = res.get("reason")
    try:
        del st.query_params["amp_notice"]
    except Exception:
        pass
