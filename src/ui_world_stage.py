"""Control Panel + Admin Console: Keeper ambient + lived world (operator)."""
from __future__ import annotations


def render_world_stage(ws, manager=None, *, key_prefix: str = "wstage") -> None:
    """Read-only status of weather / errands / news / lived entities / mechanisms."""
    import streamlit as st
    from src.world import lived_entities as le
    from src.world import lived_mechanisms as lm

    snap = le.snapshot(ws)
    der = lm.derive(ws)
    st.markdown("### The living world")
    st.caption(
        "Operator view: Keeper ambient, coarse entities, active mechanisms, "
        "and residents this hour. Visit and Gazette show a stage sentence — "
        "not this census."
    )
    st.markdown(
        f"**Clock:** {snap.get('clock') or '—'}  \n"
        f"**You / this scene:** "
        f"{'on the road from ' if snap.get('traveling') else ''}"
        f"**{snap.get('place')}**"
        + ("  · tide at this edge" if snap.get("surged") else "")
    )

    weather = snap.get("weather") or {}
    news = (snap.get("news") or "").strip()
    errands = snap.get("errands") or {}

    st.markdown("#### Ambient (the Keeper)")
    if weather:
        with st.expander("Weather — today's sky by city", expanded=True):
            for city, sky in weather.items():
                if sky:
                    mark = " ← here" if city == snap.get("place") else ""
                    st.markdown(f"- **{city}**{mark} — {sky}")
    else:
        st.caption("No Keeper weather yet — start the world engine for a daily sky, "
                   "or the fallback will fill it on the next tick.")
    if news:
        st.markdown(f"*News from the wider world:* {news}")
    if errands:
        with st.expander(f"Errands laid at doors today ({len(errands)})"):
            for cid, raw in errands.items():
                txt = le.errand_text(raw)
                if not txt:
                    continue
                name = cid
                if manager is not None:
                    try:
                        name = manager.get_character_info(cid)["name"]
                    except Exception:
                        name = cid
                st.markdown(f"- **{name}** — {txt}")

    flags = der.get("flags") or {}
    active = der.get("active") or []
    lived = {}
    try:
        lived = (getattr(ws, "vivid") or {}).get("lived") or {}
    except Exception:
        lived = {}
    st.markdown("#### Active mechanisms this hour")
    if active:
        bits = [f"**{r['name']}** — {r['fact']}" for r in active[:12]]
        st.markdown("\n\n".join(f"- {b}" for b in bits))
    else:
        st.caption("No mechanism snapshot yet.")
    flag_bits = []
    for k in ("resting", "market_open", "device_withdrawn", "gathering",
              "carrying", "making", "teaching", "crossing"):
        if k in flags:
            flag_bits.append(f"{k}={'yes' if flags[k] else 'no'}")
    if flags.get("harvest_phase"):
        flag_bits.append(f"harvest={flags['harvest_phase']}")
    if flags.get("lighting"):
        flag_bits.append(f"lighting={flags['lighting']}")
    if flag_bits:
        st.caption("Tick flags: " + " · ".join(flag_bits))
    tick_facts = lived.get("facts") or der.get("facts") or []
    if tick_facts:
        with st.expander(f"Last tick facts ({len(tick_facts)})"):
            for f in tick_facts:
                st.markdown(f"- {f}")

    st.markdown("#### Lived entities (positive, coarse)")
    here = [r for r in snap["entities"] if r.get("presence") == "here"]
    near = [r for r in snap["entities"] if r.get("presence") == "near"]
    distant = [r for r in snap["entities"] if r.get("presence") == "distant"]

    def _block(title: str, rows: list, expanded: bool) -> None:
        if not rows:
            return
        with st.expander(f"{title} ({len(rows)})", expanded=expanded):
            for r in rows:
                st.markdown(
                    f"- **{r['name']}** — {r['status']}  \n"
                    f"  *Mechanism:* {r['mechanism']}"
                )

    _block("Here — you can meet them this hour", here, True)
    _block("Near — the day's wider stage", near, False)
    _block("Elsewhere — present in Amphoreus, not this scene", distant, False)

    try:
        from src.world import resident_npcs as rn
        place = snap.get("place") or "Okhema"
        vis = [] if snap.get("traveling") else rn.visible_in_city(ws, place)
        st.markdown("#### Residents this hour")
        if vis:
            with st.expander(f"Here in {place} ({len(vis)} visible)", expanded=True):
                for r in vis[:12]:
                    st.markdown(
                        f"- **{r['name']}** — {r.get('role')} at the {r.get('spot')}"
                    )
        else:
            st.caption("No residents standing in this scene this hour.")
        enc = ((getattr(ws, "vivid") or {}).get("residents") or {}).get("encounters") or []
        if enc:
            with st.expander(f"Last tick encounters ({len(enc)})"):
                for e in enc:
                    st.markdown(f"- {e.get('line')}")
    except Exception as _e:
        st.caption(f"(residents unavailable: {_e})")

    faults = le.logic_faults(snap) + lm.logic_faults(der)
    try:
        from src.world import ecosystem as eco
        eco_scene = eco.derive_scene(ws, place=snap.get("place"))
        st.markdown("#### Ecosystem (living presence)")
        if eco_scene:
            with st.expander(f"On this stage ({len(eco_scene)})", expanded=True):
                for b in eco_scene:
                    st.markdown(
                        f"- **{b.get('name')}** [{b.get('kind')}] — "
                        f"{b.get('status')}: {b.get('doing')}"
                    )
            audit = (getattr(ws, "vivid") or {}).get("eco", {}).get("audit") or []
            if audit:
                with st.expander(f"Care audit ({len(audit)})"):
                    for a in audit[-8:]:
                        st.caption(
                            f"{a.get('ts')}: {a.get('heir')} · {a.get('action')} · "
                            f"{a.get('object_id')} ({a.get('from')}→{a.get('to')})"
                        )
        faults = faults + eco.logic_faults(eco_scene, snap.get("place") or "")
    except Exception as _e:
        st.caption(f"(ecosystem unavailable: {_e})")

    if faults:
        st.warning("World-logic check: " + "; ".join(faults))
    else:
        st.caption("World-logic check: sky, hour, place, harvest, and mechanisms agree.")
