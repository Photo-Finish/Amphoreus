"""Galgame-style (visual-novel) view for the Sanctuary.

A separate, OPTIONAL tab — the Classic interface is left completely untouched.
This view renders the selected Heir's conversation as a visual-novel scene:

  • background art (Amphoreus)
  • the Heir's sprite (their portrait), gently floating, with a name plate
  • a dialogue box whose latest line types itself out (browser-side JS;
    it only re-types when the line actually changes)
  • a small conversation log + bond tag

It shares the SAME conversation store as the Classic tab
(st.session_state.messages), so both views see the same dialogue.
"""

import base64
import html as _html
import json
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"
BG = ASSETS / "amphoreus_bg.jpg"
HEIRS = ASSETS / "heirs"


@st.cache_data(show_spinner=False)
def _data_uri(path, mime="image/png", max_width=1200):
    """Return a base64 data URI for embedding an image in the HTML scene.
    Large art is downscaled first so the embedded scene stays light."""
    if not Path(path).exists():
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


def _sprite(character_id):
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = HEIRS / f"{character_id}.{ext}"
        if p.exists():
            return p
    return None


def _esc(t):
    return _html.escape(str(t))


def _last(role, messages):
    for m in reversed(messages):
        if m.get("role") == role:
            return m["content"]
    return ""


def _scene_html(bg_uri, sprite_uri, name, last_user, last_heir, bond, cid, wx=None):
    """The full visual-novel scene with a JS typewriter for the dialogue line."""
    bg_css = f"background-image:url('{bg_uri}');" if bg_uri else "background:#0d0b18;"
    sprite_css = f"<img src='{sprite_uri}' " if sprite_uri else ""
    name_txt = _esc(name)
    bond_txt = _esc(str(bond))
    last_user_txt = _esc(last_user) if last_user else ""
    heir_json = json.dumps(_esc(last_heir))  # safe for embedding in <script>
    # Weather overlay (from the Keeper's sky), if any.
    wx_html = ""
    if wx:
        wx_html = wx

    parts = []
    parts.append("""
<div style="font-family:Georgia,serif;color:#f0e6c8;">
  <div style="position:relative;height:520px;border-radius:14px;overflow:hidden;
              border:1px solid rgba(232,213,163,.18);background:#0d0b18;">
""")
    # background
    if bg_uri:
        parts.append(
            f"<div style=\"position:absolute;inset:0;{bg_css}background-size:cover;"
            f"background-position:center;opacity:.5;\"></div>"
        )
    # today's weather over the art (the Keeper's sky, e.g. rain, storm, tide)
    if wx_html:
        parts.append(wx_html)
    # vignette toward the bottom (so the dialogue box reads cleanly)
    parts.append(
        "<div style=\"position:absolute;inset:0;background:linear-gradient(180deg,"
        "rgba(11,10,20,0) 25%, rgba(11,10,20,.92) 90%);\"></div>"
    )
    # sprite, gently floating
    if sprite_uri:
        parts.append(
            f"<div style=\"position:absolute;left:50%;transform:translateX(-50%);"
            f"bottom:128px;height:400px;filter:drop-shadow(0 0 22px rgba(232,213,163,.28));"
            f"animation:galfloat 5s ease-in-out infinite;\">"
            f"<img src='{sprite_uri}' style=\"height:100%;width:auto;object-fit:contain;\"/></div>"
        )
    # bond tag (top-right)
    parts.append(
        f"<div style=\"position:absolute;top:14px;right:16px;font-size:12.5px;"
        f"color:#e8d5a3;letter-spacing:.5px;opacity:.85;\">♡ {bond_txt}</div>"
    )
    # name plate
    parts.append(
        f"<div style=\"position:absolute;left:44px;bottom:128px;"
        f"background:linear-gradient(90deg,#e8d5a3,#c9a86a);color:#141126;"
        f"font-weight:700;padding:5px 18px;border-radius:8px 8px 0 0;"
        f"font-size:16px;letter-spacing:1.5px;box-shadow:0 -2px 10px rgba(0,0,0,.4);\">"
        f"{name_txt}</div>"
    )
    # dialogue box
    parts.append(
        f"<div style=\"position:absolute;left:0;right:0;bottom:0;min-height:128px;"
        f"padding:12px 44px 12px;background:rgba(13,11,24,.93);"
        f"border-top:1px solid rgba(232,213,163,.28);\">"
    )
    if last_user_txt:
        parts.append(
            f"<div style=\"font-size:13px;color:#b8a97f;font-style:italic;"
            f"margin-bottom:6px;\">You: {last_user_txt[:180]}</div>"
        )
    parts.append(
        f"<div id=\"galtype-{_esc(cid)}\" style=\"font-size:17px;line-height:1.6;"
        f"min-height:52px;\"></div>"
    )
    parts.append(
        "<div style=\"text-align:right;color:#e8d5a3;font-size:14px;"
        "animation:galblink 1.1s steps(2,start) infinite;\">▼</div>"
    )
    parts.append("</div></div>")
    parts.append("""
<style>
@keyframes galfloat { 0%,100% { transform:translateX(-50%) translateY(0); }
                       50%     { transform:translateX(-50%) translateY(-8px); } }
@keyframes galblink { to { visibility:hidden; } }
</style>
<script>
(function(){
  var el = document.getElementById('galtype-__CID__');
  var text = __TEXT__;
  var key = 'gal_last___CID__';
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
    return "".join(parts).replace("__CID__", _esc(cid)).replace("__TEXT__", heir_json)


def render_galgame(manager, selected, info):
    """Render the selected Heir's conversation as a visual-novel scene."""
    if "messages" not in st.session_state:
        st.session_state.messages = {}
    if selected not in st.session_state.messages:
        st.session_state.messages[selected] = [
            {"role": "assistant", "content": info["greeting"]},
        ]

    msgs = st.session_state.messages[selected]
    name = info["name"]

    bond = "stranger"
    try:
        bond = manager.get_bond_info(selected).get("friendship_level", "stranger")
    except Exception:
        pass

    with st.expander("Conversation log"):
        for m in msgs:
            who = name if m["role"] == "assistant" else "You"
            st.markdown(f"**{who}:** {m['content']}")

    st.caption(f"Galgame view — talking with **{name}** · Bond: **{bond}**")
    try:
        from src.world.world_state import WorldState as _WState
        if _WState().is_accompanied(selected):
            st.caption("The star-stranger walks beside them on the road.")
    except Exception:
        pass

    from src.ui_backgrounds import bg_path as _bg_path, current_location as _loc_now
    from src.ui_weather import overlay_for as _wx_overlay
    bg_path = _bg_path(selected)
    bg = _data_uri(bg_path, "image/jpeg", max_width=1400) if bg_path else None
    sp = _sprite(selected)
    sprite = _data_uri(sp, "image/png", max_width=700) if sp else None
    # Today's weather over the scene (the Keeper's sky for the Heir's place).
    _loc = _loc_now(selected)
    wx = _wx_overlay(_loc, _loc or "Amphoreus")

    html = _scene_html(
        bg, sprite, name,
        _last("user", msgs),
        _last("assistant", msgs) or "...",
        bond, selected, wx=wx,
    )
    st.components.v1.html(html, height=560)

    from src.ui_role import is_visitor
    if is_visitor():
        st.caption("Read-only view — sign in as the operator to speak with "
                   f"{name}.")
    else:
        prompt = st.chat_input(f"Speak to {name}...", key=f"gal_input_{selected}")
        if prompt:
            try:
                from src.world.world_state import WorldState
                WorldState().mark_visitor_present()
            except Exception:
                pass
            msgs.append({"role": "user", "content": prompt})
            with st.spinner(f"{name} is thinking..."):
                try:
                    response = manager.chat(selected, prompt)
                    msgs.append({"role": "assistant", "content": response})
                except Exception as e:
                    msgs.append({"role": "assistant", "content": f"*[Error: {str(e)}]*"})
            st.rerun()
