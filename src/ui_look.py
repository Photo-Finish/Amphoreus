"""Land look — full-screen art vs inset window, and whether life is painted on it."""
from __future__ import annotations

LOOK_PICTORIAL = "pictorial"
LOOK_CLASSIC = "classic"
_QUERY = "amp_ui"
_STATE = "amp_land_look"
_RADIO = "amp_land_look_radio"

_LIFE_Q = "amp_life"
_LIFE_STATE = "amp_land_life"
_LIFE_KEY = "amp_land_life_check"

_LABELS = (
    ("Pictures on the land", LOOK_PICTORIAL),
    ("Classic (inset + names)", LOOK_CLASSIC),
)
_NAME_FOR = {v: n for n, v in _LABELS}
_VALUE_FOR = {n: v for n, v in _LABELS}


def land_look() -> str:
    """Current land look. Session first, then ``?amp_ui=``, else pictorial."""
    import streamlit as st

    saved = str(st.session_state.get(_STATE) or "").strip().lower()
    if saved in (LOOK_PICTORIAL, LOOK_CLASSIC):
        return saved
    try:
        q = str(st.query_params.get(_QUERY) or "").strip().lower()
    except Exception:
        q = ""
    if q in (LOOK_PICTORIAL, LOOK_CLASSIC):
        st.session_state[_STATE] = q
        return q
    return LOOK_PICTORIAL


def is_pictorial() -> bool:
    return land_look() == LOOK_PICTORIAL


def show_entities() -> bool:
    """Whether chimera, grass, stalls… are painted on the land."""
    import streamlit as st

    if _LIFE_STATE in st.session_state:
        return bool(st.session_state[_LIFE_STATE])
    try:
        q = str(st.query_params.get(_LIFE_Q) or "").strip().lower()
    except Exception:
        q = ""
    if q in {"0", "off", "no", "false"}:
        st.session_state[_LIFE_STATE] = False
        return False
    if q in {"1", "on", "yes", "true"}:
        st.session_state[_LIFE_STATE] = True
        return True
    return True


def _write_query(value: str) -> None:
    import streamlit as st

    try:
        st.query_params[_QUERY] = value
    except Exception:
        pass


def _write_life_query(on: bool) -> None:
    import streamlit as st

    try:
        st.query_params[_LIFE_Q] = "1" if on else "0"
    except Exception:
        pass


def classic_page_css() -> str:
    """Solid sanctuary colour — no location photo behind the page."""
    return """
<style>
html.amp-classic .stApp,
.stApp {
  background: linear-gradient(160deg, #0b0a14 0%, #131022 45%, #0d0b18 100%) !important;
}
html.amp-classic [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] {
  background-image: none !important;
  background-color: #0b0a14 !important;
  background: linear-gradient(160deg, #0b0a14 0%, #131022 45%, #0d0b18 100%) !important;
}
[data-testid="stAppViewContainer"]::before { display: none !important; }
[data-testid="stAppViewContainer"] > .main,
.block-container {
  pointer-events: auto !important;
  background: transparent !important;
}
iframe[data-amp-land="1"],
[data-amp-land-wrap="1"] { display: none !important; }
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
  z-index: 90 !important;
  pointer-events: auto !important;
}
[data-testid="stHeader"],
[data-testid="stSidebarNav"],
[data-testid="stTabs"],
[data-baseweb="tab-list"],
[role="tablist"] {
  z-index: 90 !important;
  pointer-events: auto !important;
}
</style>
"""


_WATCHER = """
<script>
(function(){
  var doc = window.parent.document;
  function isLand(name){
    name = (name || '').replace(/\\s+/g, ' ').trim();
    return name === 'Visit an Heir' || name === 'Walk the Land';
  }
  function pathLand(){
    try {
      var p = window.parent.location.pathname || '';
      if (/Walk_the_Land/i.test(p)) return true;
      if (/Control_Panel/i.test(p)) return false;
    } catch (e) {}
    return null;
  }
  function sync(){
    var forced = pathLand();
    var on;
    if (forced === true) on = true;
    else if (forced === false) on = false;
    else {
      var t = doc.querySelector('[role="tab"][aria-selected="true"]');
      on = isLand(t && t.innerText);
    }
    doc.documentElement.classList.toggle('amp-land-off', !on);
  }
  sync();
  doc.addEventListener('click', function(){ setTimeout(sync, 40); }, true);
  try {
    new MutationObserver(sync).observe(doc.body, {
      attributes: true, subtree: true, attributeFilter: ['aria-selected']
    });
  } catch (e) {}
  try {
    window.parent.Function(
      'if(window.__ampNoticeBound)return;window.__ampNoticeBound=true;'
      + 'window.addEventListener("message",function(ev){try{var d=ev.data;'
      + 'if(!d||d.amp!=="notice"||!d.oid)return;var u=new URL(location.href);'
      + 'u.searchParams.set("amp_notice",String(d.oid));location.href=u.toString();}'
      + 'catch(e){}});'
    )();
  } catch (e) {}
})();
</script>
"""


def render_look_picker() -> None:
    """Land look + Life — sit in the main top bar so they stay visible."""
    import streamlit as st

    current = land_look()
    if _RADIO not in st.session_state:
        st.session_state[_RADIO] = _NAME_FOR[current]
    if _LIFE_KEY not in st.session_state:
        st.session_state[_LIFE_KEY] = show_entities()

    left, right = st.columns([3, 2])
    with left:
        pick = st.radio(
            "Land look",
            list(_VALUE_FOR.keys()),
            key=_RADIO,
            horizontal=True,
            help=(
                "Pictures on the land: the area art fills the page. "
                "Classic: a 16:9 weather window on a solid page — no full-page art. "
                "Named Presence only while Life on the land is on."
            ),
        )
    with right:
        _toggle = getattr(st, "toggle", None) or st.checkbox
        life_pick = _toggle(
            "Life on the land",
            key=_LIFE_KEY,
            help=(
                "On: chimera, grass, stalls, and the rest are painted on the picture. "
                "Off: the place only."
            ),
        )

    value = _VALUE_FOR.get(pick, LOOK_PICTORIAL)
    st.session_state[_STATE] = value
    try:
        qnow = str(st.query_params.get(_QUERY) or "")
    except Exception:
        qnow = ""
    if qnow != value:
        _write_query(value)

    life_now = show_entities()
    st.session_state[_LIFE_STATE] = bool(life_pick)
    try:
        lq = str(st.query_params.get(_LIFE_Q) or "")
    except Exception:
        lq = ""
    want = "1" if life_pick else "0"
    if lq != want:
        _write_life_query(bool(life_pick))

    if value == LOOK_CLASSIC:
        try:
            st.markdown(
                '<script>document.documentElement.classList.add("amp-classic");</script>',
                unsafe_allow_html=True,
            )
        except Exception:
            pass
        st.markdown(classic_page_css(), unsafe_allow_html=True)
    else:
        try:
            import streamlit.components.v1 as components
            components.html(_WATCHER, height=0, scrolling=False)
        except Exception:
            pass
    if value != current or bool(life_pick) != life_now:
        st.rerun()
