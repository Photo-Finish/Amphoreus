"""Walk the Land — stand in a region of Amphoreus (no Heir dialogue).

The region postcard is the land plane (full window, ground at the sill).
Figures and weather live on that picture. Glass panels hold clock / stage text.
Care that needs an Heir's voice stays on Visit.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Regions a walker can stand in — (label, world place name for eco/weather).
WALK_REGIONS: List[Tuple[str, str]] = [
    ("Okhema — Eternal Holy City", "Okhema"),
    ("Eternal Holy City (Dawn)", "Eternal Holy City"),
    ("Okhema under Evernight", "Okhema"),
    ("Dawncloud — Demigod Council", "Dawncloud"),
    ("Demigod Council (Dawn)", "Demigod Council"),
    ("Grove of Epiphany", "Grove of Epiphany"),
    ("Radiant Scarwood", "Radiant Scarwood"),
    ("Murmuring Woods", "Grove of Epiphany"),
    ("Janusopolis", "Janusopolis"),
    ("Sanctum of Prophecy", "Sanctum of Prophecy"),
    ("Abyss of Fate", "Janusopolis"),
    ("Castrum Kremnos", "Castrum Kremnos"),
    ("Bloodbathed Battlefront", "Bloodbathed Battlefront"),
    ("Strife Ruins of Kremnos", "Castrum Kremnos"),
    ("Styxia — Warbling Shores", "Styxia"),
    ("Warbling Shores (Dawn)", "Warbling Shores"),
    ("Dragonbone City", "Styxia"),
    ("Aedes Elysiae", "Aedes Elysiae"),
    ("Aedes Elysiae, of old", "Aedes Elysiae, of old"),
    ("Aidonia / Memortis Shore", "Aidonia"),
    ("Eye of Twilight", "Eye of Twilight"),
    ("Fortress of Dome", "Fortress of Dome"),
    ("Cloudedge Bastion", "Eye of Twilight"),
    ("Vortex of Genesis", "Vortex of Genesis"),
    ("Great Tomb", "Great Tomb"),
    ("Universal Matrix", "Universal Matrix"),
    ("The Nether", "The Nether"),
    ("Beyond Time", "Beyond Time"),
]

# label -> preferred bg slug (when several labels share a city).
_LABEL_SLUG: Dict[str, str] = {
    "Okhema — Eternal Holy City": "okhema",
    "Eternal Holy City (Dawn)": "okhema",
    "Okhema under Evernight": "okhema-evernight",
    "Dawncloud — Demigod Council": "dawncloud",
    "Demigod Council (Dawn)": "dawncloud",
    "Grove of Epiphany": "grove",
    "Radiant Scarwood": "grove",
    "Murmuring Woods": "murmuring-woods",
    "Janusopolis": "janusopolis",
    "Sanctum of Prophecy": "janusopolis",
    "Abyss of Fate": "abyss-of-fate",
    "Castrum Kremnos": "kremnos",
    "Bloodbathed Battlefront": "kremnos",
    "Strife Ruins of Kremnos": "kremnos-ruins",
    "Styxia — Warbling Shores": "styxia",
    "Warbling Shores (Dawn)": "styxia",
    "Dragonbone City": "dragonbone-city",
    "Aedes Elysiae": "aedes-elysiae",
    "Aedes Elysiae, of old": "aedes-elysiae",
    "Aidonia / Memortis Shore": "memortis-shore",
    "Eye of Twilight": "eye-of-twilight",
    "Fortress of Dome": "eye-of-twilight",
    "Cloudedge Bastion": "cloudedge-bastion",
    "Vortex of Genesis": "vortex-of-genesis",
    "Great Tomb": "great-tomb",
    "Universal Matrix": "great-tomb",
    "The Nether": "styxia",
    "Beyond Time": "beyond-time",
}


def region_options() -> List[Tuple[str, str, Optional[object]]]:
    """[(label, place, Path|None)] for every walk region with art if present."""
    from pathlib import Path
    from src.ui_backgrounds import GALGAME_DIR, bg_path_for_place

    out = []
    for label, place in WALK_REGIONS:
        slug = _LABEL_SLUG.get(label)
        path = None
        if slug:
            p = GALGAME_DIR / f"bg-{slug}.jpg"
            if p.exists():
                path = p
        if path is None:
            path = bg_path_for_place(place)
        out.append((label, place, path))
    return out


def _clock_line(ws) -> str:
    try:
        return ws.clock.format_short()
    except Exception:
        try:
            return str(ws.clock)
        except Exception:
            return "—"


def _stage_for(ws, place: str) -> str:
    try:
        from src.world import lived_mechanisms as lm
        return (lm.visitor_stage_paragraph(ws, place=place) or "").strip()
    except Exception:
        return ""


def _render_walk_classic(
    *,
    label: str,
    place: str,
    art,
    scene,
    clock: str,
    sky: str,
    key_prefix: str,
    entities: bool = True,
) -> None:
    """Small weather window + named presence. No full-page art."""
    import streamlit as st
    from src.ui_scene_life import render_presence_chips, render_inset_window

    st.title("Walk the Land")
    st.caption(
        "Stand in a region of Amphoreus — no Heir dialogue. "
        "The picture is a small weather window."
    )
    meta = f"{clock} · **{place}** · {label}"
    if sky:
        meta += f" · {sky}"
    st.caption(meta)
    if art is not None:
        render_inset_window(
            art, place, scene or [],
            dense=True, entities=entities,
            key=f"{key_prefix}_{place}_inset",
        )
    else:
        st.warning(
            "No area artwork on disk for this region yet. "
            "Run `python tools/fetch_galgame_backgrounds.py` "
            "(optionally `--force --width 1920`) when the wiki proxy is up."
        )
    render_presence_chips(
        scene, heir_id="", key_prefix=f"{key_prefix}_{place}", place=place,
    )
    try:
        from src.world.world_state import WorldState
        ws = WorldState()
        heirs_here = []
        for cid, loc in (ws.agent_location or {}).items():
            if loc == place and not ws.travel_info(cid):
                heirs_here.append(cid)
        if heirs_here:
            names = [cid.replace("-", " ").title() for cid in heirs_here[:8]]
            st.caption(
                "Heirs in this place (silent presence): "
                + ", ".join(names)
                + " — open Visit an Heir to speak with them."
            )
    except Exception:
        pass


def render_walk_page(*, key_prefix: str = "walk") -> None:
    """Pick a region and stand in it. Look follows the Land look radio."""
    import html as _html
    import streamlit as st
    from src.world.world_state import WorldState
    from src.world import ecosystem as eco
    from src.ui_look import is_pictorial, show_entities
    from src.ui_scene_life import (
        render_pictorial_stage,
        render_focus_strip,
        life_overlay_html,
        consume_notice_query,
    )
    from src.ui_weather import page_backdrop_css

    ws = WorldState()
    opts = region_options()
    labels = [o[0] for o in opts]
    by_label = {o[0]: o for o in opts}

    # Default: visitor's current place if it matches a region.
    default_idx = 0
    try:
        vp = ws.visitor_place()
        here = vp.get("at") if vp.get("kind") == "at" else vp.get("from")
        if here:
            for i, (lab, place, _) in enumerate(opts):
                if place == here or here.lower() in lab.lower():
                    default_idx = i
                    break
    except Exception:
        pass

    # Region picker first (before backdrop) so follow-road can choose art.
    c1, c2 = st.columns([2, 1])
    with c1:
        pick = st.selectbox(
            "Where you stand",
            labels,
            index=default_idx,
            key=f"{key_prefix}_region",
        )
    with c2:
        follow = st.checkbox(
            "Follow my road",
            value=False,
            key=f"{key_prefix}_follow",
            help="When on, jump to the star-stranger's current place each refresh.",
        )

    if follow:
        try:
            vp = ws.visitor_place()
            here = vp.get("at") if vp.get("kind") == "at" else None
            if here:
                for lab, place, _ in opts:
                    if place == here:
                        pick = lab
                        break
        except Exception:
            pass

    label, place, art = by_label[pick]

    consume_notice_query(place=place, heir_id="", key_prefix=f"{key_prefix}_{place}")
    clock = _clock_line(ws)
    sky = ""
    try:
        sky = ws.ambient_weather(place) or ""
    except Exception:
        sky = ""

    scene = eco.derive_scene(ws, place=place, include_residents=True)
    try:
        eco.apply_tick(ws)
    except Exception:
        pass

    life = show_entities()
    if not is_pictorial():
        _render_walk_classic(
            label=label, place=place, art=art, scene=scene,
            clock=clock, sky=sky, key_prefix=key_prefix,
            entities=life,
        )
        return

    if art is not None:
        css = page_backdrop_css(art, max_width=1920)
        if css:
            st.markdown(css, unsafe_allow_html=True)

    stage = _stage_for(ws, place)

    # Glass reading panel — title, clock, stage beat
    beat = f'<div class="beat">{_html.escape(stage)}</div>' if stage else ""
    sky_bit = f" · sky: {_html.escape(sky)}" if sky else ""
    st.markdown(
        f'<div class="amp-read">'
        f"<h1 style=\"font-family:Georgia,'Palatino Linotype',serif;"
        f"font-size:1.85rem;letter-spacing:.04em;margin:0 0 .35rem 0;\">"
        f"Walk the Land</h1>"
        f'<div class="sub">Stand in a region — sky, ground, and whoever is here. '
        f"No Heir dialogue; only the place itself.</div>"
        f'<div class="meta" style="margin-top:.65rem;">'
        f'{_html.escape(clock)} · <b>{_html.escape(place)}</b>'
        f"{sky_bit} · {_html.escape(label)}</div>"
        f"{beat}"
        f"</div>",
        unsafe_allow_html=True,
    )

    shown = art is not None
    if art is not None:
        try:
            from src.ui_weather import effect_for, classify
            effect, sky_fx = effect_for(place)
            if not sky_fx and sky:
                effect = classify(sky)
                sky_fx = sky
            render_pictorial_stage(
                art, place, effect, sky_fx, scene,
                max_width=1920, read_line="", dense=True,
                page_layer=True, entities=life,
                key=f"{key_prefix}_{place}",
            )
        except Exception as e:
            st.caption(f"(land overlay fallback: {e})")
            if life:
                try:
                    st.markdown(life_overlay_html(scene, place, dense=True),
                                unsafe_allow_html=True)
                except Exception:
                    pass
    if not shown:
        st.warning(
            "No area artwork on disk for this region yet. "
            "Run `python tools/fetch_galgame_backgrounds.py` "
            "(optionally `--force --width 1920`) when the wiki proxy is up."
        )
        if life:
            st.markdown(life_overlay_html(scene, place, dense=True),
                        unsafe_allow_html=True)

    render_focus_strip(
        scene,
        heir_id="",
        heir_name="",
        key_prefix=f"{key_prefix}_{place}",
        place=place,
        read_only=True,
    )

    if life:
        life_bits = [
            b for b in scene
            if b.get("kind") not in {"resident"} and b.get("status") not in {"resting"}
        ]
        if life_bits:
            with st.expander("What moves here this hour", expanded=False):
                for b in life_bits[:8]:
                    st.markdown(
                        f"- **{b.get('name')}** — {b.get('doing')}"
                    )

    try:
        heirs_here = []
        for cid, loc in (ws.agent_location or {}).items():
            if loc == place and not ws.travel_info(cid):
                heirs_here.append(cid)
        if heirs_here:
            names = []
            for cid in heirs_here[:8]:
                try:
                    names.append(cid.replace("-", " ").title())
                except Exception:
                    names.append(cid)
            st.caption(
                "Heirs in this place (silent presence): "
                + ", ".join(names)
                + " — open Visit an Heir to speak with them."
            )
    except Exception:
        pass
