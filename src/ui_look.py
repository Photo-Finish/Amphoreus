"""Land look — pictorial (figures on the art) vs classic (inset + names)."""
from __future__ import annotations

LOOK_PICTORIAL = "pictorial"
LOOK_CLASSIC = "classic"
_QUERY = "amp_ui"
_STATE = "amp_land_look"
_RADIO = "amp_land_look_radio"

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


def _write_query(value: str) -> None:
    import streamlit as st

    try:
        st.query_params[_QUERY] = value
    except Exception:
        pass


def classic_page_css() -> str:
    """Drop full-bleed art and click-through so Streamlit chrome works."""
    return """
<style>
.stApp { background: #0b0a14 !important; }
[data-testid="stAppViewContainer"] {
  background-image: none !important;
  background-color: #0b0a14 !important;
}
[data-testid="stAppViewContainer"]::before { display: none !important; }
[data-testid="stAppViewContainer"] > .main,
.block-container {
  pointer-events: auto !important;
  background: transparent !important;
}
iframe[data-amp-land="1"],
[data-amp-land-wrap="1"] { display: none !important; }
section[data-testid="stSidebar"] {
  z-index: 50 !important;
  pointer-events: auto !important;
}
[data-testid="stHeader"],
[data-testid="stSidebarNav"],
[data-testid="stTabs"],
[data-baseweb="tab-list"] {
  z-index: 40 !important;
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
    """Sidebar radio — switch looks without losing guest auth."""
    import streamlit as st

    current = land_look()
    if _RADIO not in st.session_state:
        st.session_state[_RADIO] = _NAME_FOR[current]
    pick = st.sidebar.radio(
        "Land look",
        list(_VALUE_FOR.keys()),
        key=_RADIO,
        help=(
            "Pictures on the land: figures live on the area art. "
            "Classic: one inset picture and named buttons — no weather overlay, "
            "no grass/rain layer, no full-page figures."
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
    if value == LOOK_CLASSIC:
        st.markdown(classic_page_css(), unsafe_allow_html=True)
    else:
        try:
            import streamlit.components.v1 as components
            components.html(_WATCHER, height=0, scrolling=False)
        except Exception:
            pass
    if value != current:
        st.rerun()
