"""
Streamlit UI for Project Amphoreus — Chat with the Chrysos Heirs.

Usage:
    streamlit run src/ui_app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent_manager import AgentManager


# --------------------------------------------------------------------------- #
# Public-web sign-in — the Sanctuary is behind a key on the Internet.
# Credentials come from world_runtime/ui_auth.json (gitignored) or the
# AMPHOREUS_UI_USER / AMPHOREUS_UI_PASS environment variables. When no
# credentials are configured, the app is open (local use).
# --------------------------------------------------------------------------- #
import json as _json
import os as _os


def _load_ui_auth():
    """Operator + visitor accounts. Operator may also come from the env."""
    env_u = _os.environ.get("AMPHOREUS_UI_USER", "").strip()
    env_p = _os.environ.get("AMPHOREUS_UI_PASS", "")
    try:
        _f = Path(__file__).parent.parent / "world_runtime" / "ui_auth.json"
        _d = _json.loads(_f.read_text(encoding="utf-8"))
    except Exception:
        _d = {}
    op = (env_u, env_p) if (env_u and env_p) else (
        str(_d.get("username", "")), str(_d.get("password", "")))
    vis = (str(_d.get("visitor_username", "Visitor")),
           str(_d.get("visitor_password", "")))
    return op, vis


_UI_USER, _UI_PASS = _load_ui_auth()[0]
_VISITOR_USER, _VISITOR_PASS = _load_ui_auth()[1]

if (_UI_USER and _UI_PASS) and not st.session_state.get("ui_authed"):
    st.set_page_config(page_title="Project Amphoreus — the Sanctuary",
                       page_icon="🔥")
    st.markdown(
        "<style>.stApp{background:linear-gradient(160deg,#0b0a14,#131022)}</style>",
        unsafe_allow_html=True)
    st.title("The Sanctuary of the Chrysos Heirs")
    st.caption("This world is behind a key. Sign in to enter."
               " (Visitors: use the read-only account.)")
    _u = st.text_input("Username")
    _p = st.text_input("Password", type="password")
    if st.button("Enter the Sanctuary"):
        if _u == _UI_USER and _p == _UI_PASS:
            st.session_state.ui_authed = True
            st.session_state.ui_role = "operator"
            st.rerun()
        elif _VISITOR_USER and _VISITOR_PASS \
                and _u == _VISITOR_USER and _p == _VISITOR_PASS:
            st.session_state.ui_authed = True
            st.session_state.ui_role = "visitor"
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    if _VISITOR_USER and _VISITOR_PASS:
        st.divider()
        st.caption("No key? You may look around in read-only mode:")
        if st.button("Visit as a guest (read-only)"):
            st.session_state.ui_authed = True
            st.session_state.ui_role = "visitor"
            st.rerun()
    st.stop()

from src.ui_role import is_visitor, is_operator  # noqa: E402


# Page config
st.set_page_config(
    page_title="Project Amphoreus — Chrysos Heirs",
    page_icon="🔥",
    layout="wide",
)

# --------------------------------------------------------------------------- #
# Visual theme — the Sanctuary of the Chrysos Heirs
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS = PROJECT_ROOT / "assets"
HEIR_PORTRAITS_DIR = ASSETS / "heirs"
HEIR_AVATARS_DIR = ASSETS / "avatars"
BG_IMAGE = ASSETS / "amphoreus_bg.jpg"


def portrait_for(character_id: str):
    """Path to the Heir's portrait, if downloaded."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = HEIR_PORTRAITS_DIR / f"{character_id}.{ext}"
        if p.exists():
            return p
    return None


def avatar_for(character_id: str):
    """Path to the Heir's square chat avatar, falling back to the portrait."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = HEIR_AVATARS_DIR / f"{character_id}.{ext}"
        if p.exists():
            return p
    return portrait_for(character_id)


# The visitor's own face — a persistent avatar beside their chat messages.
# Stored under world_runtime/ (runtime data, gitignored).
USER_AVATAR_PATH = PROJECT_ROOT / "world_runtime" / "user_avatar.png"


def user_avatar_path():
    """Path to the visitor's chat avatar, or None until one is set."""
    return str(USER_AVATAR_PATH) if USER_AVATAR_PATH.exists() else None


# Ethereal Amphoreus theme (dark gold, no heavy base64 in the page)
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(160deg, #0b0a14 0%, #131022 45%, #0d0b18 100%); }
    /* Streamlit's top bar (Running… / Deploy / Main menu) is absolutely
       positioned over the top 60px of the main area. The block container must
       start BELOW it, or the tabs sit underneath the bar. Default padding is
       5rem; we keep a touch more so the tabs never coincide with it. */
    .block-container { padding-top: 5.4rem; }
    h1, h2, h3 { color: #e8d5a3; letter-spacing: .5px; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141126 0%, #0d0b18 100%);
        border-right: 1px solid rgba(232,213,163,.12);
    }
    [data-testid="stSidebar"] * { color: #d8cfa8; }
    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,.035);
        border: 1px solid rgba(232,213,163,.10);
        border-radius: 12px;
        padding: .4rem .8rem;
    }
    /* The star-stranger's road, in phone idiom (src/ui_travel.py): a status
       bar with signal bars, and centred carrier-notice travel bubbles. */
    .amp-travelbar{display:flex;align-items:center;gap:.55rem;padding:.5rem .85rem;
      border-radius:10px;border:1px solid rgba(232,213,163,.16);
      background:rgba(20,18,38,.78);font:600 12px/1 'Segoe UI',Arial,sans-serif;
      letter-spacing:.4px;color:#cfc49b;margin:.2rem 0 .8rem;}
    .amp-travelbar .amp-signal{display:flex;align-items:flex-end;gap:2px;height:12px;}
    .amp-travelbar .amp-signal i{display:block;width:3px;background:#7fd68a;border-radius:1px;}
    .amp-travelbar .amp-txt{flex:1;}
    .amp-travelbar .amp-sub{color:#8d84a8;font-weight:500;}
    .amp-travelbar.roaming{color:#ffd9a8;border-color:rgba(255,180,94,.4);
      background:rgba(28,20,16,.8);}
    .amp-travelbar.roaming .amp-signal i{background:#ffb45e;}
    .amp-travelbar .amp-dot{width:7px;height:7px;border-radius:50%;background:#ffb45e;
      animation:ampPulse 1.6s infinite;}
    @keyframes ampPulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(255,180,94,.5);}
      50%{opacity:.5;box-shadow:0 0 0 5px rgba(255,180,94,0);}}
    .amp-travelnote{text-align:center;font:italic 12px/1.5 'Segoe UI',Arial,sans-serif;
      color:#9c92bd;background:rgba(255,255,255,.02);
      border:1px dashed rgba(232,213,163,.14);border-radius:8px;
      padding:.35rem .7rem;margin:.3rem 0;animation:ampFade .5s ease;}
    @keyframes ampFade{from{opacity:0;transform:translateY(3px);}
      to{opacity:1;transform:none;}}
    .stTabs [data-baseweb="tab-list"] { gap: .6rem; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #e8d5a3; }
    </style>
    """,
    unsafe_allow_html=True,
)

# The click-popups for the interactive map. The SVG from render_map_svg marks
# every place and Heir with data-kind/data-key; this script shows a themed info
# card near the click. __AMP_INFO__ is replaced with the JSON info payload.
_MAP_CLICK_SCRIPT = """\
<style>
.amp-pop{position:absolute;z-index:60;display:none;width:320px;max-width:92%;
 background:linear-gradient(180deg,#1a1630,#0d0b18);border:1px solid rgba(232,213,163,.30);
 border-radius:12px;padding:12px 14px;color:#e6dcc0;font:13px/1.5 Arial,sans-serif;
 box-shadow:0 12px 34px rgba(0,0,0,.6);}
.amp-pop h4{margin:0 0 4px;color:#e8d5a3;font-size:15px;letter-spacing:.4px;}
.amp-pop .amp-sub{color:#b8a97f;font-size:12px;font-style:italic;margin-bottom:6px;}
.amp-pop .amp-row{margin:3px 0;}
.amp-pop .amp-close{position:absolute;top:5px;right:11px;cursor:pointer;color:#b8a97f;font-size:17px;line-height:1;}
.amp-pop .amp-close:hover{color:#fff;}
.amp-map-host{position:relative;}
.amp-sel{filter:drop-shadow(0 0 6px rgba(232,213,163,.9));}
</style>
<script>
(function(){
  var INFO = __AMP_INFO__;
  var svg = document.getElementById('amp-map');
  if(!svg || !INFO) return;
  var host = svg.parentElement;
  host.classList.add('amp-map-host');
  var pop = document.createElement('div');
  pop.className = 'amp-pop';
  host.appendChild(pop);
  function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function clearSel(){ var s=svg.querySelectorAll('.amp-sel'); for(var i=0;i<s.length;i++) s[i].classList.remove('amp-sel'); }
  function hide(){ pop.style.display='none'; clearSel(); }
  function show(html, g){
    pop.innerHTML = html;
    pop.style.display = 'block';
    var r = svg.getBoundingClientRect(), er = g.getBoundingClientRect();
    var pw = pop.offsetWidth || 320, ph = pop.offsetHeight || 170;
    var x = (er.left - r.left) + 16, y = (er.top - r.top) - ph/2;
    x = Math.max(6, Math.min(x, r.width - pw - 6));
    y = Math.max(6, Math.min(y, r.height - ph - 6));
    pop.style.left = x + 'px'; pop.style.top = y + 'px';
    clearSel(); g.classList.add('amp-sel');
  }
  svg.addEventListener('click', function(ev){
    var t = ev.target;
    var g = t.closest ? t.closest('[data-kind]') : null;
    if(!g){ hide(); return; }
    var kind = g.getAttribute('data-kind'), key = g.getAttribute('data-key');
    var html, P, H;
    if(kind === 'place'){
      P = (INFO.places||{})[key]; if(!P) return;
      html  = '<span class="amp-close">✕</span>';
      html += '<h4>'+esc(P.icon)+' '+esc(P.name)+'</h4>';
      html += '<div class="amp-sub">'+esc(P.desc)+'</div>';
      if(P.past && !P.past_form) html += '<div class="amp-row">⏳ Dawn-era form: <b>'+esc(P.past)+'</b> — across the Veil of Evernight (1 p, Oronyx-blessed)</div>';
      if(P.past_form) html += '<div class="amp-row">🔁 This is the <b>Dawn-era (past)</b> form of <b>'+esc(P.of)+'</b> — reached across the Veil of Evernight (1 p)</div>';
      if(P.nether) html += '<div class="amp-row">† The Nether — the death-realm beneath Styxia (Thanatos-blessed only)</div>';
      if(P.heirs && P.heirs.length) html += '<div class="amp-row">Heirs here: <b>'+esc(P.heirs.join(', '))+'</b></div>';
      if(P.traveling && P.traveling.length) html += '<div class="amp-row">On the road here: '+esc(P.traveling.join(', '))+'</div>';
      if(!P.past_form && !P.nether) html += '<div class="amp-row">From Okhema: <b>'+P.from_okhema+' p</b></div>';
    } else {
      H = (INFO.heirs||{})[key]; if(!H) return;
      html  = '<span class="amp-close">✕</span>';
      html += '<h4>'+esc(H.name)+'</h4>';
      if(H.title) html += '<div class="amp-sub">'+esc(H.title)+'</div>';
      html += '<div class="amp-row">📍 '+esc(H.loc)+'</div>';
      if(H.bond) html += '<div class="amp-row">Bond: <b>'+esc(H.bond)+'</b></div>';
      if(H.status === 'away') html += '<div class="amp-row">🛸 Beyond Amphoreus — riding the Trailblaze path</div>';
      else if(H.status === 'present') html += '<div class="amp-row">🛸 Visitor from beyond Amphoreus</div>';
    }
    show(html, g);
    ev.stopPropagation();
  });
  document.addEventListener('click', function(ev){
    if(ev.target.closest && ev.target.closest('.amp-close')){ hide(); return; }
    if(!(ev.target.closest && ev.target.closest('.amp-pop'))) hide();
  });
})();
</script>
"""

# Initialize Agent Manager
@st.cache_resource
def get_manager():
    return AgentManager(
        characters_dir=str(Path(__file__).parent / "characters"),
        llm_model="gemma3:27b",
        use_rag=True,
        rag_persist_dir=str(Path(__file__).parent.parent / ".chroma_db"),
        memory_root=str(Path(__file__).parent.parent),  # per-Heir folders at project root
    )


manager = get_manager()

# Sidebar — Character Selection
st.sidebar.title("Project Amphoreus")
st.sidebar.markdown("### The Sanctuary of the Chrysos Heirs")

# LLM status — truthful: the backend is reachable AND the Heir voice model is
# actually present on it (a bare `ollama serve` with an empty models dir would
# otherwise claim “Ready” and then 404 on every call).
vs = manager.voice_status()
if vs["ready"]:
    st.sidebar.success(f"🗣️ Voice: Ready ({vs['model']})")
else:
    st.sidebar.warning(f"🗣️ Voice: {vs['detail']} ({vs['model']})")

# RAG status
try:
    from src.core.voice_path import get_voice_path, label as _vp_label, PATH_OPLORA
    _vpath = get_voice_path()
    if _vpath == PATH_OPLORA:
        st.sidebar.info(f"🛤️ Path: {_vp_label(_vpath)}")
    else:
        st.sidebar.success(f"🛤️ Path: {_vp_label(_vpath)}")
except Exception:
    pass

# RAG status
try:
    rag = manager.rag_status()
    if rag.get("enabled"):
        n_docs = rag.get("total_documents", 0)
        st.sidebar.success(
            f"📚 RAG: Ready\n\n{n_docs} canon documents indexed\n({rag.get('embedding', 'auto')} embeddings)"
        )
        if not is_visitor():
            if st.sidebar.button("Rebuild Knowledge Base"):
                with st.spinner("Rebuilding RAG index..."):
                    manager.build_knowledge_base()
                st.rerun()
    else:
        st.sidebar.warning("📚 RAG: Disabled")
except Exception as e:
    st.sidebar.warning(f"📚 RAG: Unavailable ({e})")

characters = manager.list_available_characters()
if not characters:
    st.sidebar.warning("No character cards found in src/characters/")
    st.stop()

selected = st.sidebar.selectbox(
    "Select a Chrysos Heir to speak with:",
    characters,
    format_func=lambda x: manager.get_character_info(x)["name"],
)

# Portrait of the chosen Heir
_selected_portrait = portrait_for(selected)
if _selected_portrait:
    st.sidebar.image(str(_selected_portrait), width=190)

# Display character info
info = manager.get_character_info(selected)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**{info['name']}**")
st.sidebar.markdown(f"*{', '.join(info['titles'])}*")
st.sidebar.markdown(f"Coreflame: **{info['coreflame']}**")
st.sidebar.markdown(f"Traits: {', '.join(info['personality_traits'])}")

# The Trailblazer's companions are guests of Amphoreus, not residents —
# their presence here is a chance event that comes and goes.
try:
    from src.world.world_state import GUEST_HEIRS as _GUESTS
    if selected in _GUESTS:
        from src.world.world_state import WorldState as _WS
        _gws = _WS()
        if _gws.guest_status(selected) == "present":
            st.sidebar.caption(
                "**Visitor in Amphoreus** — not a resident; the Express "
                "drops in from time to time."
            )
        else:
            st.sidebar.caption(
                "**Beyond Amphoreus** — riding the Trailblaze path; "
                "returns from time to time."
            )
except Exception:
    pass

# Bond with the visitor
# Visitor mode (journey vs aftermath — see src/core/visitor_mode.py)
try:
    from src.core.visitor_mode import current_mode
    _mode = current_mode()
    if _mode == "aftermath":
        st.sidebar.caption("Mode: **Aftermath** — the Iron Tomb is conquered; the Heirs remember you as a war-companion.")
    else:
        st.sidebar.caption("Mode: **Journey** — you are newly arrived; the Heirs do not know you yet.")
except Exception:
    pass
# Where you physically stand in Amphoreus (set in the Control Panel).
try:
    from src.world.world_state import WorldState as _WSV
    _vp = _WSV().visitor_place()
    if _vp["kind"] == "traveling":
        st.sidebar.caption(f"On the road to **{_vp['to']}** — {_vp['remaining']} day(s) left")
    else:
        st.sidebar.caption(f"You are in **{_vp['at']}**")
except Exception:
    pass
try:
    bond = manager.get_bond_info(selected)
    level = bond.get("friendship_level", "stranger")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Bond with you:** {level}")
    st.sidebar.markdown(
        f"Visits: **{bond.get('visits', 0)}** · Memories: **{bond.get('memories', 0)}**"
    )
    if bond.get("first_met"):
        st.sidebar.caption(f"First met: {bond.get('first_met')[:16].replace('T', ' ')}")
except Exception:
    pass

# B1 — mood · B4 — the deeper story · B5 — an unresolved hurt
# (see src/world/living_world.py)
try:
    from src.world import living_world as _lw_side
    from src.world.world_state import WorldState as _WS_side
    _ws_side = _WS_side()
    _mo_side = _lw_side.mood_of(_ws_side, selected)
    if _mo_side["valence"] != 0:
        st.sidebar.caption(f"{_mo_side['name'].capitalize()} today"
                           + (f" — {_mo_side['reason']}" if _mo_side['reason'] else ""))
    _arc_side = _lw_side.ARCS.get(selected)
    if _arc_side:
        _stg_side = _lw_side.arc_stage(bond.get("friendship_level", "stranger"))
        if _stg_side >= 0:
            st.sidebar.caption(f"Carries: “{_arc_side['title']}”")
    if _lw_side.open_grievance(manager.memory, selected):
        st.sidebar.warning("Something sits unresolved between you.")
    # the witness: a quiet badge when the Heir has begun to understand
    try:
        from src.core import realization as _rz
        _rz_rec = _rz.stage_of(_ws_side, selected)
        if _rz_rec.get("stage", 0) >= 1:
            st.sidebar.caption(f"Realization: {_rz_rec['name']}")
    except Exception:
        pass
    # the Heirs' minds: what they are wondering about
    try:
        from src.core import curiosity as _cur
        _qs = _cur.open_questions(_ws_side, selected)
        if _qs:
            st.sidebar.caption(f"Wondering: {_qs[0]['q'][:70]}")
    except Exception:
        pass
    # the changeable knowledge bank: what they have come to know
    try:
        from src.core import horizons as _hz
        _hk = _hz.latest(_ws_side, selected, limit=1)
        if _hk:
            st.sidebar.caption(f"Knows: {_hk[0]['topic'][:70]}")
    except Exception:
        pass
except Exception:
    pass

# Reset button — this is a heavy act: it erases the Heir's memory of you.
# Operator-only: a read-only visitor must not erase anything.
if not is_visitor():
    if st.sidebar.button("Forget me (reset)"):
        manager.reset_conversation(selected)
        st.rerun()

# Your own face — the avatar that appears beside your messages (operator only)
if not is_visitor():
    st.sidebar.markdown("---")
    st.sidebar.caption("**Your avatar** — the face that travels with you.")
    try:
        _uav = user_avatar_path()
        if _uav:
            st.sidebar.image(_uav, width=64)
        _upl = st.sidebar.file_uploader(
            "Set your avatar", type=["png", "jpg", "jpeg", "webp"],
            key="user_avatar_upload", label_visibility="collapsed",
        )
        # NOTE: never st.rerun() after saving — the file_uploader re-sends its
        # file from the frontend on every rerun, which would loop forever. Saving
        # is keyed to the uploaded file's identity (name:size) so it happens once
        # per upload, and "Remove my avatar" works even while a file is still
        # attached to the uploader (the same file will not re-save).
        if _upl is not None:
            _ident = "%s:%s" % (_upl.name, _upl.size)
            if st.session_state.get("_uav_saved_ident") != _ident:
                from PIL import Image
                import io as _io
                _im = Image.open(_io.BytesIO(_upl.getvalue())).convert("RGB")
                _im.thumbnail((256, 256))
                USER_AVATAR_PATH.parent.mkdir(parents=True, exist_ok=True)
                _im.save(str(USER_AVATAR_PATH), "PNG")
                st.session_state["_uav_saved_ident"] = _ident
                st.sidebar.success("Your face is set — it now appears beside your messages.")
        if _uav and st.sidebar.button("Remove my avatar", key="user_avatar_remove"):
            USER_AVATAR_PATH.unlink()
            st.rerun()
    except Exception:
        pass

# Senses status (hearing / eyesight / music)
try:
    sn = manager.senses_status()
    st.sidebar.markdown("---")
    eye = "👁️ Eyes: Ready" if sn.get("eyesight") else "👁️ Eyes: offline (set VISION_MODEL)"
    ear = "👂 Ears: Ready" if sn.get("hearing") else "👂 Ears: offline (no STT model)"
    music = "🎵 Music: Ready" if sn.get("music") else "🎵 Music: offline (set AUDIO_MODEL)"
    st.sidebar.caption(f"{eye}\n\n{ear}\n\n{music}")
except Exception:
    pass

st.sidebar.markdown("---")
try:
    ms = manager.memory_stats()
    st.sidebar.caption(
        f"The Heirs hold **{ms['memories']}** memories across **{ms['heirs_with_bonds']}** bonds"
    )
except Exception:
    pass
st.sidebar.caption("*Project Amphoreus — the Sanctuary*")
st.sidebar.caption("*Databank: Complete*")
st.sidebar.caption("*See PHILOSOPHY.md for the charter*")

# Main Area
main_tab, chronicle_tab, map_tab, admin_tab, game_tab, guide_tab, control_tab = st.tabs([
    "Visit an Heir",
    "A Chronicle of Amphoreus",
    "Map of Amphoreus",
    "Admin Console",
    "Galgame",
    "How to use",
    "Control Panel",
])

with control_tab:
    # 🎛️ The Control Panel — also a dedicated Streamlit page (sidebar).
    st.info(
        "The **Control Panel** is also its own page in the left sidebar "
        "(**Control Panel** under pages). The RAG / OPLoRA voice-path switch lives there."
    )
    try:
        from src.ui_control_panel import render_control_panel
        render_control_panel(manager, characters)
    except Exception as e:
        st.error(f"Could not render the control panel: {e}")

with guide_tab:
    # ❓ How to use — a friendly guide to the Sanctuary and its living world.
    try:
        from src.ui_guide import render_guide
        render_guide(manager, characters)
    except Exception as e:
        st.error(f"Could not render the guide: {e}")

with game_tab:
    # 🎬 Galgame view — an OPTIONAL visual-novel rendering of the same
    # conversation. The Classic interface above is untouched.
    try:
        from src.ui_galgame import render_galgame
        render_galgame(manager, selected, info)
    except Exception as e:
        st.error(f"Could not render the galgame view: {e}")


with chronicle_tab:
    if BG_IMAGE.exists():
        st.image(str(BG_IMAGE), width="stretch")
    # The end-user edition: the Gazette gathers the whole world's news into
    # one readable page. (The Admin Console's monitor page keeps its raw,
    # operational look — it is not changed here.)
    try:
        from src.ui_gazette import render_gazette
        render_gazette(manager, characters)
    except Exception as e:
        st.error(f"The gazette could not be composed: {e}")
        try:
            from src.world.chronicle import Chronicle
            ch = Chronicle(str(Path(__file__).parent.parent / "world_runtime" / "chronicle"))
            st.markdown(ch.read_markdown(60))
        except Exception:
            st.info("The chronicle is not written yet — the world engine has not begun its days.\n\nStart it with: `python -m src.world.world_engine --interval 900`")

with map_tab:
    # 🗺️ The Map of Amphoreus — geography, commuting time, and daily routines.
    try:
        from src.world.world_state import WorldState, GUEST_HEIRS
        from src.world import map_data as _map
        from src.world import schedules as _sched

        _ws = WorldState()
        st.title("Map of Amphoreus")
        st.caption(
            "The Heirs are spread across a wide world. Each dot is an Heir at their "
            "present place; crossed dots are on the road between cities. Travel is "
            "measured in Light-Calendar periods (5 = one full day). A dashed halo "
            "marks a visitor from beyond Amphoreus — the Trailblazer's own "
            "companions only drop in from time to time. The faint **silver ⏳ nodes** "
            "are the **Dawn-era (past) forms** of the places, reached only across "
            "the **Veil of Evernight** (Oronyx-blessed travelers, who may carry "
            "companions); the **purple † node** is the Nether beneath Styxia "
            "(Thanatos-blessed only)."
        )

        _names = {c: manager.get_character_info(c)["name"] for c in characters}
        _heir_locs = _ws.present_locations()
        _guests_here = {c for c in _ws.agent_location if _ws.guest_status(c) == "present"}
        # Click-info for the interactive map — embedded in the page so the
        # popup script can show it without a round-trip.
        import json as _json
        _place_info = {}
        for _pn in _map.ALL_POS:
            _place_info[_pn] = {
                "name": _pn,
                "icon": _map.AREA_ICONS.get(_pn, "✦"),
                "desc": _ws.location_desc(_pn),
                "heirs": [_names[c] for c, l in _heir_locs.items()
                          if l == _pn and c not in _ws.agent_travel],
                "traveling": [_names[c] for c, l in _heir_locs.items()
                              if l == _pn and c in _ws.agent_travel],
                "past": _map.time_twin(_pn),
                "of": _map.present_of(_pn) or "",
                "past_form": _pn in _map.PAST_FORMS,
                "nether": _pn == _map.NETHER,
                "from_okhema": _map.travel_time("Okhema", _pn),
            }
        _heir_info = {}
        for _cid in characters:
            try:
                _gi = manager.get_character_info(_cid)
                _loc = _ws.agent_location.get(_cid, "?")
                if _cid in _ws.agent_travel:
                    _loc = f"on the road to {_ws.agent_travel[_cid]['to']}"
                _bd = manager.get_bond_info(_cid) or {}
                _heir_info[_cid] = {
                    "name": _gi.get("name", _cid),
                    "title": (_gi.get("titles") or [""])[0],
                    "loc": _loc,
                    "bond": _bd.get("friendship_level", "stranger"),
                    "status": _ws.guest_status(_cid),
                }
            except Exception:
                pass
        _svg = _map.render_map_svg(
            heir_locations=_heir_locs,
            traveling=_ws.agent_travel,
            heir_names=_names,
            highlight=None,
            guest_ids=_guests_here,
            interactive=True,
        )
        # The interactive map lives in a component (an iframe) so the click
        # script can run; the SVG is capped at its 1000px natural width.
        _amp_html = (
            '<div style="max-width:1000px;margin:0 auto;">'
            + _svg
            + "</div>"
            + _MAP_CLICK_SCRIPT.replace(
                "__AMP_INFO__",
                _json.dumps({"places": _place_info, "heirs": _heir_info},
                            ensure_ascii=False),
            )
        )
        from streamlit.components.v1 import html as _components_html
        _components_html(_amp_html, height=850, scrolling=False)

        # Current clock + who's where / who's travelling
        st.markdown(f"### Now: {_ws.clock.format()}")

        # Today's stage, set by the Keeper (the Ambient World Director)
        _weather = (_ws.ambient.get("weather") or {})
        _errands = (_ws.ambient.get("errands") or {})
        _news = _ws.ambient.get("news", "")
        if _weather or _errands or _news:
            st.markdown("### Today's sky")
            for _city, _sky in _weather.items():
                if _sky:
                    st.markdown(f"- **{_city}** — {_sky}")
            if _news:
                st.markdown(f"*News from the wider world: {_news}*")
            with st.expander("Errands laid at the Heirs' doors today"):
                for _cid, _errand in _errands.items():
                    if not _errand:
                        continue
                    if isinstance(_errand, dict):
                        _ask = (_errand.get("ask") or "").strip()
                        _cause = (_errand.get("cause") or "").strip()
                        _txt = _ask + (f" — *cause:* {_cause}" if _cause else "")
                    else:
                        _txt = str(_errand)
                    st.markdown(f"- **{_names.get(_cid, _cid)}** — {_txt}")

        col_w, col_t = st.columns(2)
        with col_w:
            st.markdown("**Present**")
            present_rows = []
            for cid, loc in _heir_locs.items():
                if cid in _ws.agent_travel:
                    continue
                tag = " *(visitor from beyond Amphoreus)*" \
                    if _ws.guest_status(cid) == "present" else ""
                present_rows.append(f"- {_names.get(cid, cid)} — {loc}{tag}")
            st.markdown("\n".join(present_rows) if present_rows else "*Everyone is on the road.*")
            _away_guests = [c for c in GUEST_HEIRS if _ws.guest_status(c) == "away"]
            if _away_guests:
                st.markdown("**Beyond Amphoreus**")
                st.markdown(
                    "\n".join(
                        f"- {_names.get(c, c)} — riding the Trailblaze path "
                        "(drops in from time to time)"
                        for c in _away_guests
                    )
                )
        with col_t:
            st.markdown("**On the road**")
            if _ws.agent_travel:
                for cid, _trav in _ws.agent_travel.items():
                    st.markdown(
                        f"- {_names.get(cid, cid)} → {_trav['to']} "
                        f"({_trav['remaining_days']} day(s) left)"
                    )
            else:
                st.markdown("*No one is travelling right now.*")

        # Travel-time matrix
        st.markdown("### Commuting time (in periods, 5 = a day)")
        _locs = list(_map.LOCATION_POS.keys())
        table = []
        for a in _locs:
            row = {"From": a}
            for b in _locs:
                row[b] = _map.travel_time(a, b)
            table.append(row)
        import pandas as pd
        st.dataframe(
            pd.DataFrame(table).set_index("From"),
            use_container_width=True,
            height=min(40 + 32 * len(_locs), 420),
        )

        # The Veil of Evernight — the two forms of Amphoreus
        st.markdown("### The Veil of Evernight — the two forms of Amphoreus")
        st.markdown(
            "Many places exist in **two forms**: the **present** (the Evernight "
            "era — the darkened world of Year 4932) and its **Dawn-era (past) "
            "form** — the same place as it stood under the Dawn Device. The two "
            "eras are separated by the **Veil of Evernight** (Oronyx, Titan of "
            "Time). Only the **Oronyx-blessed** — the Trailblazer (the time "
            "traveler Oronyx took an interest in) and **Evernight** (Oronyx's "
            "heir) — may cross it, and they may **carry companions** with them "
            "across the borderline of time (a crossing costs **1 period**)."
        )
        _veil_rows = []
        for _p, _past in _map.TIME_FORMS.items():
            _veil_rows.append({"Two-form place": _p, "Dawn-era (past) form": _past})
        st.dataframe(pd.DataFrame(_veil_rows), use_container_width=True)
        st.caption(
            "Other unique Titan borders: **Janus's Gates of Destiny** open "
            "Janusopolis's Dawn form (Sanctum of Prophecy) to **Tribbie** "
            "(Janus's heir) as well; the **Nether** beneath Styxia (Thanatos's "
            "sea of flowers) is open only to the **Thanatos-blessed** — "
            "**Castorice**, and the Trailblazer who crossed with her († 2 p). "
            "Inside an era, the roads are the same; the Veil is the only way "
            "from one era to the other."
        )

        # Area art — browse the places of Amphoreus (wiki area backgrounds).
        try:
            from src.ui_backgrounds import available_backgrounds, location_slug as _locslug
            _areas = available_backgrounds()
            if _areas:
                _default = None
                for _cid, _loc in _heir_locs.items():
                    if _cid in _ws.agent_travel:
                        continue
                    _default = _locslug(_loc)
                    if _default:
                        break
                _map_slug = dict(_areas)
                _opts = list(_map_slug)
                _labels = {s: s.replace("-", " ").title() for s in _opts}
                if _default in _opts:
                    _idx = _opts.index(_default)
                else:
                    _idx = 0
                st.markdown("### Area art")
                _sel = st.selectbox(
                    "Choose a place to view", _opts, format_func=lambda s: _labels[s],
                    index=_idx, key="map_area_sel",
                )
                # The area's art, wearing today's weather (set by the Keeper).
                try:
                    from src.ui_weather import render_scene as _wx_scene
                    _wx_scene(_sel, image_path=_map_slug[_sel], title=_labels[_sel], height=320)
                except Exception:
                    st.image(str(_map_slug[_sel]), width="stretch")
                st.caption(f"**{_labels[_sel]}** — Amphoreus, as the wiki's area art shows it.")
        except Exception:
            pass

        # Individual weekly schedules
        st.markdown("### Individual weekly routines")
        st.caption(
            "Each Heir keeps a routine of their own. Heirs who live and work together "
            "(the Okhema council circle, the scholars of the Grove, the two souls of "
            "Aedes Elysiae) cross paths often; the rest meet only when someone is "
            "willing to spend days on the road."
        )
        sched_sel = st.selectbox(
            "Whose week?",
            characters,
            format_func=lambda x: manager.get_character_info(x)["name"],
            key="map_sched_sel",
        )
        sched_name = manager.get_character_info(sched_sel)["name"]
        rows = _sched.week_overview(sched_sel)
        acts = _sched.week_activity_overview(sched_sel)
        st.markdown(f"**{sched_name}** — home in **{_sched.home_of(sched_sel)}**")
        grid = []
        for d, (row, act_row) in enumerate(zip(rows, acts), 1):
            for p, (place, act) in enumerate(zip(row, act_row)):
                grid.append({
                    "Day": f"Day {d}",
                    "Period": _sched.PERIOD_NAMES[p],
                    "Place": place,
                    "Occupation": act,
                })
        st.dataframe(
            pd.DataFrame(grid),
            use_container_width=True,
            height=min(40 + 29 * 35, 520),
        )
    except Exception as e:
        st.error(f"Could not render the map: {e}")

with admin_tab:
    # 🛠️ Admin Console — the machine under the world: models, world-state,
    # cause-and-effect chain, and the automation loop that keeps the Heirs
    # converging on their voices. Read-only; nothing here changes the world.
    st.title("Admin Console — the machine under the world")
    st.caption("Backend, world-state, cause-and-effect, and the quality loop.")

    # ---- 1. Backend & models ----
    st.markdown("### Backend & models")
    try:
        sn = manager.senses_status()
        c1, c2, c3 = st.columns(3)
        c1.metric("Heir model", manager.voice_model())
        c2.metric("Vision (eyes)", sn.get("vision_model") or "off")
        c3.metric("Audio (music)", sn.get("audio_model") or "off")
        st.caption(f"STT (hearing): {sn.get('stt_model')} · judge/refine: gemma3:27b")
    except Exception as e:
        st.caption(f"(backend status unavailable: {e})")
    try:
        rag = manager.rag_status()
        st.markdown(f"**RAG:** {'on' if rag.get('enabled') else 'off'} · "
                    f"{rag.get('total_documents', 0)} canon docs · {rag.get('embedding', '')}")
    except Exception as e:
        st.caption(f"(rag unavailable: {e})")

    # ---- 2. World-state machine ----
    try:
        from src.world.world_state import WorldState as _WS, GUEST_HEIRS as _GUEST_HEIRS
        _ws2 = _WS()
        st.markdown("### World state")
        st.markdown(f"**Clock:** {_ws2.clock.format()}")
        st.markdown("**Where the Heirs are right now**")
        for _cid, _loc in _ws2.present_locations().items():
            if _cid in _ws2.agent_travel:
                continue
            _tag = " *(visitor from beyond Amphoreus)*" \
                if _ws2.guest_status(_cid) == "present" else ""
            st.markdown(f"- {manager.get_character_info(_cid)['name']} — {_loc}{_tag}")
        _away = [c for c in _GUEST_HEIRS if _ws2.guest_status(c) == "away"]
        if _away:
            st.markdown("**Beyond Amphoreus**")
            for _cid in _away:
                st.markdown(f"- {manager.get_character_info(_cid)['name']} — "
                            f"riding the Trailblaze path (drops in from time to time)")
        if _ws2.agent_travel:
            st.markdown("**On the road**")
            for _cid, _ti in _ws2.agent_travel.items():
                st.markdown(f"- {manager.get_character_info(_cid)['name']} → {_ti['to']} "
                            f"({_ti['remaining_days']} day(s) left)")
        _ev = _ws2.recent_events_text(limit=10)
        if _ev:
            with st.expander("Recent events — the causal trail"):
                st.markdown(_ev)
    except Exception as e:
        st.caption(f"(world state unavailable: {e})")

    # ---- 3. Cause & effect: why today is what it is ----
    try:
        st.markdown("### Cause & effect — why today is what it is")
        st.markdown(f"**Season:** {_ws2.clock.season} · **Month:** {_ws2.clock.month_name} "
                    f"(patron {_ws2.clock.patron_titan})")
        _amb = _ws2.ambient
        _w = _amb.get("weather") or {}
        if _w:
            with st.expander("Weather — the sky's cause"):
                for _city, _sky in _w.items():
                    st.markdown(f"- **{_city}** — {_sky}")
        _e = _amb.get("errands") or {}
        if _e:
            with st.expander("Errands — request + original impetus"):
                for _cid2, _er in _e.items():
                    if not _er:
                        continue
                    if isinstance(_er, dict):
                        _ask = (_er.get("ask") or "").strip()
                        _cause = (_er.get("cause") or "").strip()
                        st.markdown(f"**{manager.get_character_info(_cid2)['name']}**")
                        st.markdown(f"&nbsp;&nbsp;*ask:* {_ask}")
                        if _cause:
                            st.markdown(f"&nbsp;&nbsp;*cause (impetus):* {_cause}")
                    else:
                        st.markdown(f"- {manager.get_character_info(_cid2)['name']} — {_er}")
        if _amb.get("news"):
            st.markdown(f"*News from the wider world:* {_amb['news']}")
    except Exception as e:
        st.caption(f"(ambient unavailable: {e})")

    # ---- 4. The automation loop ----
    st.markdown("### The quality loop (auto-cycle)")
    try:
        import time as _time
        _root = Path(__file__).parent.parent
        _log = _root / "docs" / "AUTO-CYCLE-LOG.md"
        _report = _root / "docs" / "RESEMBLANCE-STYLE-REPORT.md"
        _wdlog = _root / "world_runtime" / "watchdog.log"
        _now = _time.time()

        def _age_min(p):
            return int((_now - p.stat().st_mtime) // 60) if p.exists() else None
        _l, _r, _w = _age_min(_log), _age_min(_report), _age_min(_wdlog)
        st.markdown(f"- AUTO-CYCLE-LOG last written **{_l if _l is not None else 'never'} min ago**")
        st.markdown(f"- Style report last written **{_r if _r is not None else 'never'} min ago**")
        st.markdown(f"- Watchdog last event **{_w if _w is not None else 'never'} min ago**")
        if _log.exists():
            with st.expander("Auto-cycle log (tail)"):
                st.code("\n".join(_log.read_text(encoding="utf-8").splitlines()[-45:]))
        if _wdlog.exists():
            with st.expander("Watchdog log (tail)"):
                st.code("\n".join(_wdlog.read_text(encoding="utf-8").splitlines()[-20:]))
        if _report.exists():
            with st.expander("Latest style report (tail)"):
                st.code("\n".join(_report.read_text(encoding="utf-8").splitlines()[-25:]))
    except Exception as e:
        st.caption(f"(loop status unavailable: {e})")

    # ---- 5. Chronicle — the written record ----
    try:
        from src.world.chronicle import Chronicle as _Chr
        _ch = _Chr(str(Path(__file__).parent.parent / "world_runtime" / "chronicle"))
        with st.expander("Chronicle — what has happened (the record)"):
            st.markdown(_ch.read_markdown(30))
    except Exception as e:
        st.caption(f"(chronicle unavailable: {e})")

with main_tab:
    # Main Chat Area — hero banner with the Heir's portrait + where they are.
    # The backdrop follows the Heir's CURRENT place in the little Amphoreus
    # (falling back to their home city, then the default banner).
    try:
        from src.ui_backgrounds import bg_path as _loc_bg, current_location as _loc_now
        _chat_bg = _loc_bg(selected)
        _chat_place = _loc_now(selected)
    except Exception:
        _chat_bg = BG_IMAGE if BG_IMAGE.exists() else None
        _chat_place = ""
    if _chat_bg:
        # The backdrop follows the Heir's current place AND today's weather
        # (the Keeper's sky), so the same art changes mood with the world.
        try:
            from src.ui_weather import render_scene as _wx_scene
            _wx_scene(_chat_place, image_path=_chat_bg,
                      title=f"{info['name']} — {_chat_place}" if _chat_place else info["name"],
                      height=300)
        except Exception:
            st.image(str(_chat_bg), width="stretch")
        if _chat_place:
            st.caption(f"{info['name']} is in **{_chat_place}** — the backdrop shows where they are.")
    hero_l, hero_r = st.columns([1, 3], gap="large")
    with hero_l:
        if _selected_portrait:
            st.image(str(_selected_portrait), width="stretch")
        else:
            st.markdown("### 🔥")
    with hero_r:
        st.title(f"{info['name']}")
        st.caption(f"*{', '.join(info['titles'])}*")
        st.caption(f"Coreflame: **{info['coreflame']}**")
    st.markdown("---")

    # A — the star-stranger's own road, in phone idiom: a status bar above
    # the conversation so the journey is felt even when you only read the chat.
    try:
        from src.ui_travel import travel_status, travel_status_html
        from src.world.world_state import WorldState as _WST
        _tstatus = travel_status(_WST())
        st.markdown(travel_status_html(_tstatus), unsafe_allow_html=True)
    except Exception:
        pass

    # Catch-up: what this Heir has lived through since you were last here
    try:
        world_mem = manager.memory.get_world_memories(selected, limit=3)
        if world_mem:
            with st.expander(f"What {info['name']} has lived through lately"):
                for wm in world_mem:
                    st.markdown(f"- {wm['content']}")
    except Exception:
        pass

    # Stage 2 — place-hour frame + ongoing moment + shared scene + NPC talk
    try:
        from src.world import vivid_stage2 as _v2
        _frame = manager.place_hour(selected)
        with st.expander("This hour — place, sky, who is here", expanded=True):
            st.markdown(_v2.place_hour_markdown(_frame, info["name"]))
            _moment = manager.ongoing_moment(selected)
            if _moment and _moment.get("kind") != "quiet":
                st.info(_moment.get("summary", ""))
        _comps = manager.companions_here(selected)
        if _comps and not is_visitor():
            with st.expander("Sit with them (shared scene)"):
                _cname_map = {c: manager.get_character_info(c)["name"] for c in _comps}
                _pick = st.selectbox(
                    "Who else is here?",
                    _comps,
                    format_func=lambda c: _cname_map.get(c, c),
                    key=f"scene_pick_{selected}",
                )
                if st.button("Invite them to sit with you",
                             key=f"scene_btn_{selected}"):
                    _inv = manager.invite_shared_scene(selected, _pick)
                    if _inv.get("ok"):
                        st.success(
                            f"{_cname_map.get(_pick, _pick)} sits with you in "
                            f"{_inv.get('place')}."
                        )
                    else:
                        st.warning(_inv.get("reason", "They decline."))
                if st.button("End the shared scene",
                             key=f"scene_end_{selected}"):
                    manager.clear_shared_scene()
                    st.info("The shared scene ends.")
        _npc_city = _frame.get("place") or ""
        _npcs = _v2.npcs_in_city(_npc_city) if _npc_city else []
        if _npcs and not is_visitor():
            with st.expander(f"Speak with a resident of {_npc_city}"):
                _npc_names = [n["name"] for n in _npcs]
                _npc_pick = st.selectbox(
                    "Living resident", _npc_names, key=f"npc_pick_{selected}")
                if st.button("Talk with them", key=f"npc_btn_{selected}"):
                    _nr = manager.talk_to_npc(_npc_city, _npc_pick)
                    if _nr.get("ok"):
                        st.markdown(_nr.get("line", ""))
                    else:
                        st.warning(_nr.get("reason", "They are not here."))
    except Exception:
        pass

    # Travel together — the star-stranger accompanies this Heir on the road
    try:
        from src.world import map_data as _map_data
        _here = _loc_now(selected) if "_loc_now" in dir() else ""
        # The star-stranger is Oronyx-blessed, so they can walk an Heir across
        # the Veil into the Dawn era, or down into the Nether with Castorice.
        _dests = [
            l for l in _map_data.ALL_POS
            if l != _here and _map_data.travel_time_for(_here, l, "trailblazer") < 999
        ]
        if _dests and not is_visitor():
            with st.expander("Travel together"):
                _dest = st.selectbox("Where shall you walk together?", _dests,
                                     key=f"travel_dest_{selected}")
                if _map_data.is_cross_era(_dest):
                    st.caption(
                        "A Dawn-era form / the Nether — you are Oronyx-blessed "
                        "(and walked with Castorice): you can carry this Heir "
                        "across the borderline of time with you."
                    )
                if st.button(f"Set out for {_dest} with {info['name']}",
                             key=f"travel_btn_{selected}"):
                    _ti = manager.travel_with(selected, _dest)
                    if _ti:
                        st.success(f"You walk with {info['name']} on the road to "
                                   f"{_ti['to']} — {_ti['remaining_days']} day(s).")
                        st.rerun()
                    else:
                        st.error("The road could not be taken just now.")
    except Exception:
        pass

    # A3 — the market & gift economy: a gift from the Heir's own city becomes
    # a durable memory and warms their mood.
    try:
        _mkt_loc, _wares = manager.market_at(selected)
        if _wares and not is_visitor():
            with st.expander("Give a gift"):
                st.caption(f"The market at **{_mkt_loc}** offers:")
                _labels = [f"{w['name']} — {w['note']}" for w in _wares]
                _choice = st.selectbox("Choose something for them", _labels,
                                       key=f"gift_sel_{selected}")
                if st.button(f"Give this to {info['name']}", key=f"gift_btn_{selected}"):
                    _gift_name = _choice.split(" — ")[0].strip()
                    _res = manager.give_gift(selected, _gift_name)
                    if _res.get("given"):
                        st.success(f"{info['name']} accepts {_gift_name}. "
                                   f"(They feel {_res.get('mood', 'warm')}.)")
                        st.session_state.messages[selected].append({
                            "role": "user",
                            "content": f"*(you give them {_gift_name})*",
                        })
                    else:
                        st.info(_res.get("reason", "No gift given."))
                # the Heir keeps every gift they were given
                try:
                    from src.world import living_world as _lw_g
                    _kept = _lw_g.gifts_given(manager.memory, selected, limit=6)
                    if _kept:
                        _clean = [g.replace("The visitor gave you ", "").strip(" .")
                                  for g in _kept]
                        st.caption("They keep: " + " · ".join(_clean))
                except Exception:
                    pass
    except Exception:
        pass

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = {}

    if selected not in st.session_state.messages:
        st.session_state.messages[selected] = []
        # Add greeting
        greeting = info["greeting"]
        st.session_state.messages[selected].append({
            "role": "assistant",
            "content": greeting,
        })

    # B + D — travel events as phone messages: when you set out, a road-day
    # passes, or you arrive, a carrier-notice bubble joins the thread, and the
    # Heir you are talking to reacts to your journey in their own voice.
    try:
        from src.ui_travel import (travel_status, diff_travel, travel_event_text,
                                   travel_note_html, heir_travel_reaction)
        from src.world.world_state import WorldState as _WST2
        if "travel_log" not in st.session_state:
            st.session_state.travel_log = []
        _tcur = travel_status(_WST2())
        if "_travel_snap" not in st.session_state:
            st.session_state["_travel_snap"] = _tcur
        _tsnap = st.session_state["_travel_snap"]
        for _tev in diff_travel(_tsnap, _tcur):
            _evrec = dict(_tev)
            _evrec["text"] = travel_event_text(_tev)
            st.session_state.travel_log.append(_evrec)
            _react = heir_travel_reaction(selected, _tev.get("kind"), _tev)
            if _react:
                st.session_state.messages[selected].append({
                    "role": "assistant",
                    "content": _react,
                })
        st.session_state["_travel_snap"] = _tcur
        if len(st.session_state.travel_log) > 60:
            st.session_state.travel_log = st.session_state.travel_log[-60:]
        for _tl in st.session_state.travel_log[-20:]:
            st.markdown(travel_note_html(_tl.get("text", "")),
                        unsafe_allow_html=True)
    except Exception:
        pass

    # Display chat history (the Heir's own square avatar — never a generic bot)
    _assistant_avatar = str(avatar_for(selected)) if avatar_for(selected) else None
    _user_avatar = user_avatar_path()
    for msg in st.session_state.messages[selected]:
        with st.chat_message(msg["role"], avatar=_assistant_avatar if msg["role"] == "assistant" else _user_avatar):
            st.markdown(msg["content"])

    # Senses: eyesight (picture / video) and hearing (speak) — operator only
    if not is_visitor():
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            uploaded = st.file_uploader(
                "Show a picture",
                type=["png", "jpg", "jpeg", "webp", "gif"],
                key=f"img_{selected}",
                label_visibility="collapsed",
            )
            if uploaded is not None:
                st.session_state["pending_image"] = {
                    "bytes": uploaded.getvalue(),
                    "mime": uploaded.type or "image/png",
                    "name": uploaded.name,
                }
        with c2:
            uploaded_video = st.file_uploader(
                "Show a video",
                type=["mp4", "mov", "avi", "mkv", "webm"],
                key=f"vid_{selected}",
                label_visibility="collapsed",
            )
            if uploaded_video is not None:
                st.session_state["pending_video"] = {
                    "bytes": uploaded_video.getvalue(),
                    "name": uploaded_video.name,
                }
        with c3:
            spoken = st.audio_input("Speak to them", key=f"aud_{selected}")

        # A second row: music for shared appreciation
        music_file = st.file_uploader(
            "Share music to listen together",
            type=["mp3", "wav", "ogg", "flac", "m4a"],
            key=f"music_{selected}",
        )
        if music_file is not None:
            with st.spinner(f"{info['name']} is listening to the music..."):
                result = manager.appreciate_music(selected, music_file.getvalue(), note=music_file.name)
            if result.get("heard"):
                st.session_state.messages[selected].append({
                    "role": "user", "content": f"*(shares music: {music_file.name})*",
                })
                with st.chat_message("user", avatar=_user_avatar):
                    st.markdown(f"*(shares music: {music_file.name})*")
                with st.chat_message("assistant", avatar=_assistant_avatar):
                    st.markdown(result["response"])
                st.session_state.messages[selected].append({
                    "role": "assistant", "content": result["response"],
                })
            else:
                st.info(result.get("reason", "Music appreciation is not yet available."))

    if st.session_state.get("pending_image"):
        pimg = st.session_state["pending_image"]
        st.caption(f"You are showing {info['name']}: **{pimg['name']}** — send a message to appreciate it together.")
    if st.session_state.get("pending_video"):
        pvid = st.session_state["pending_video"]
        st.caption(f"You are showing {info['name']}: **{pvid['name']}** — send a message to watch it together.")

    if not is_visitor() and spoken is not None:
        with st.spinner(f"{info['name']} is listening..."):
            result = manager.hear(selected, spoken.read())
        if result.get("heard"):
            st.session_state.messages[selected].append({
                "role": "user", "content": f"*(spoken)* {result['transcript']}",
            })
            with st.chat_message("user", avatar=_user_avatar):
                st.markdown(f"*(spoken)* {result['transcript']}")
            with st.chat_message("assistant", avatar=_assistant_avatar):
                st.markdown(result["response"])
            st.session_state.messages[selected].append({
                "role": "assistant", "content": result["response"],
            })
        else:
            st.info(result.get("reason", "Hearing is not yet available."))

    # Chat input (operator only; visitors read)
    if is_visitor():
        st.caption("Read-only view — sign in as the operator to speak with "
                   f"{info['name']}.")
    elif prompt := st.chat_input(f"Speak to {info['name']}..."):
        # Let the world know the visitor is here
        try:
            from src.world.world_state import WorldState

            WorldState().mark_visitor_present()
        except Exception:
            pass

        # Attach a pending image (eyesight) if the visitor brought one
        image_b64 = None
        image_mime = "image/png"
        image_caption = ""
        video_bytes = None
        video_name = ""
        pending = st.session_state.pop("pending_image", None)
        pending_video = st.session_state.pop("pending_video", None)
        if pending_video is not None:
            video_bytes = pending_video["bytes"]
            video_name = pending_video["name"]
            st.session_state.messages[selected].append({
                "role": "user",
                "content": f"*(shows a video: {pending_video['name']})* {prompt}",
            })
            with st.chat_message("user", avatar=_user_avatar):
                st.markdown(f"*(shows a video: {pending_video['name']})* {prompt}")
        elif pending:
            import base64

            image_b64 = base64.b64encode(pending["bytes"]).decode("ascii")
            image_mime = pending["mime"]
            image_caption = f"a picture ({pending['name']})"
            st.session_state.messages[selected].append({
                "role": "user",
                "content": f"*(shows an image: {pending['name']})* {prompt}",
            })
            with st.chat_message("user", avatar=_user_avatar):
                st.markdown(f"*(shows an image: {pending['name']})* {prompt}")
        else:
            # Display user message
            st.session_state.messages[selected].append({
                "role": "user",
                "content": prompt,
            })
            with st.chat_message("user", avatar=_user_avatar):
                st.markdown(prompt)

        # Get response
        with st.chat_message("assistant", avatar=_assistant_avatar):
            with st.spinner(f"{info['name']} is thinking..."):
                try:
                    response = manager.chat(
                        selected,
                        prompt,
                        image=image_b64,
                        image_mime=image_mime,
                        image_caption=image_caption,
                        video=video_bytes,
                        video_name=video_name,
                    )
                    st.markdown(response)
                    st.session_state.messages[selected].append({
                        "role": "assistant",
                        "content": response,
                    })
                except Exception as e:
                    error_msg = f"*[Error: {str(e)}]*"
                    st.markdown(error_msg)
                    st.session_state.messages[selected].append({
                        "role": "assistant",
                        "content": error_msg,
                    })

        # Show canon sources that grounded the reply
        try:
            ctx = manager.get_rag_context(selected, prompt)
            if ctx.get("available") and ctx.get("hits"):
                with st.expander(f"Canon sources used ({len(ctx['hits'])})"):
                    for h in ctx["hits"]:
                        st.markdown(f"**`{h['source']}`** — score {h['score']}")
                        st.caption(h["text"][:400] + ("…" if len(h["text"]) > 400 else ""))
        except Exception:
            pass
