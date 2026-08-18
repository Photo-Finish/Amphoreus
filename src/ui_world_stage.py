"""Control Panel + Admin Console: Keeper ambient + lived world entities."""
from __future__ import annotations

import streamlit as st


def render_world_stage(ws, manager=None, *, key_prefix: str = "wstage") -> None:
    """Read-only status of weather / errands / news / lived entities."""
    from src.world import lived_entities as le

    snap = le.snapshot(ws)
    st.markdown("### The living world")
    st.caption(
        "Keeper ambient (sky, errands, news) plus coarse physical entities. "
        "Status is derived from the Light Calendar, today's sky, and where "
        "you stand — not a second random weather."
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

    faults = le.logic_faults(snap)
    if faults:
        st.warning("World-logic check: " + "; ".join(faults))
    else:
        st.caption("World-logic check: sky, hour, place, and harvest agree.")
