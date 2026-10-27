# -*- coding: utf-8 -*-
"""The As-I've-Written theme — one design system for every surface.

Grounded in the in-game book page, not in guesswork: `docs/UI-AIW.md` records the
reference screenshots and the colours sampled from them. The page is a cream
two-page spread with a gold egg-and-dart frieze, a gold corner bracket, Roman-numeral
index tabs, terracotta chevron controls and warm-brown serif ink — set on a deep
indigo world with a low horizon.

Use it two ways:

    from src import ui_theme
    ui_theme.apply(st)                 # Streamlit: inject the whole stylesheet
    ui_theme.PALETTE["gold"]           # custom HTML: the measured colours
    ui_theme.frieze()                  # custom HTML: the ornament strip

Nothing here changes layout or behaviour; it changes only colour, type and
ornament. Surfaces keep their structure so the art and the reading order stay put.
"""
from __future__ import annotations

# Sampled from the in-game book page (docs/UI-AIW.md lists each surface).
PALETTE = {
    "parchment": "#f4ecdc",
    "parchment_hi": "#fbf6ea",
    "parchment_lo": "#e9dfc8",
    "parchment_edge": "#d8c8a4",
    "ink": "#3b2c1e",
    "ink_soft": "#6d5a44",
    "ink_faint": "#8a7458",
    "gold": "#c8a03c",
    "gold_light": "#e6cd8a",
    "gold_deep": "#8f6f22",
    "terracotta": "#b9552b",
    "terracotta_deep": "#8f3f1f",
    "indigo": "#0d1631",
    "indigo_mid": "#16224a",
    "indigo_hi": "#243567",
    "ice": "#a9bbe4",
    "sky_glow": "#3a4f8f",
}


FONT_DISPLAY = ("'Palatino Linotype', 'Book Antiqua', Palatino, 'EB Garamond', "
                "Georgia, serif")
FONT_BODY = ("'Palatino Linotype', 'Book Antiqua', Palatino, Georgia, "
             "'Times New Roman', serif")

# Egg-and-dart, drawn with gradients so there is no image to load or licence.
FRIEZE_CSS = """
background-image:
  radial-gradient(circle at 12px 4px, {gold_light} 0 2px, transparent 3px),
  radial-gradient(circle at 12px 9px, transparent 0 5px, {gold} 6px 7px, transparent 8px),
  radial-gradient(circle at 12px 9px, {gold_deep} 0 1px, transparent 2px),
  repeating-linear-gradient(90deg, rgba(143,111,34,.55) 0 1px, transparent 1px 24px);
background-size: 24px 14px, 24px 14px, 24px 14px, 24px 100%;
background-repeat: repeat-x;
background-position: 0 0, 0 0, 0 0, 0 0;
""".format(gold=PALETTE["gold"], gold_light=PALETTE["gold_light"],
           gold_deep=PALETTE["gold_deep"])


def frieze(height: int = 10) -> str:
    """The gold egg-and-dart band that runs along the top of a book page."""
    return (f'<div class="aiw-frieze" style="height:{height}px" aria-hidden="true">'
            f'</div>')


def corner_bracket() -> str:
    """The gold corner ornament at the top-left of the page."""
    return '<span class="aiw-corner" aria-hidden="true"></span>'


def rulings() -> str:
    """The thin double rule that frames the spread."""
    return '<span class="aiw-ruling" aria-hidden="true"></span>'


def css() -> str:
    p = PALETTE
    return f"""
<style>
:root {{
  --aiw-parchment: {p['parchment']};
  --aiw-parchment-hi: {p['parchment_hi']};
  --aiw-parchment-lo: {p['parchment_lo']};
  --aiw-parchment-edge: {p['parchment_edge']};
  --aiw-ink: {p['ink']};
  --aiw-ink-soft: {p['ink_soft']};
  --aiw-gold: {p['gold']};
  --aiw-gold-light: {p['gold_light']};
  --aiw-gold-deep: {p['gold_deep']};
  --aiw-terracotta: {p['terracotta']};
  --aiw-terracotta-deep: {p['terracotta_deep']};
  --aiw-indigo: {p['indigo']};
  --aiw-indigo-mid: {p['indigo_mid']};
  --aiw-indigo-hi: {p['indigo_hi']};
  --aiw-ice: {p['ice']};
  --aiw-display: {FONT_DISPLAY};
  --aiw-body: {FONT_BODY};
}}

/* ---- the world behind the book: indigo, a low horizon, a scatter of stars ---- */
.stApp {{
  background:
    radial-gradient(1200px 420px at 50% 108%, rgba(58,79,143,.55), transparent 70%),
    radial-gradient(900px 300px at 18% -10%, rgba(36,53,103,.55), transparent 65%),
    radial-gradient(700px 260px at 84% 4%, rgba(36,53,103,.45), transparent 60%),
    linear-gradient(180deg, #0a1128 0%, {p['indigo']} 42%, {p['indigo_mid']} 100%);
  color: {p['ice']};
  font-family: var(--aiw-body);
}}
.stApp::before {{
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    radial-gradient(1.4px 1.4px at 12% 22%, rgba(233,225,196,.55), transparent 60%),
    radial-gradient(1.2px 1.2px at 27% 8%, rgba(233,225,196,.4), transparent 60%),
    radial-gradient(1.6px 1.6px at 41% 31%, rgba(233,225,196,.5), transparent 60%),
    radial-gradient(1.2px 1.2px at 63% 14%, rgba(233,225,196,.45), transparent 60%),
    radial-gradient(1.5px 1.5px at 78% 27%, rgba(233,225,196,.5), transparent 60%),
    radial-gradient(1.2px 1.2px at 91% 11%, rgba(233,225,196,.4), transparent 60%);
}}

/* ---- paper: every panel of content sits on a page ---- */
[data-testid="stAppViewContainer"] > .main .block-container,
section[data-testid="stSidebar"] > div {{
  font-family: var(--aiw-body);
}}
.block-container {{ padding-top: 2.2rem; }}

/* headings: gold small-caps over a hairline rule, as on the page */
h1, h2, h3, h4 {{
  font-family: var(--aiw-display) !important;
  color: var(--aiw-gold-light) !important;
  letter-spacing: .06em;
  font-weight: 600 !important;
}}
h1 {{ font-size: 2.0rem !important; }}
h2 {{ font-size: 1.45rem !important; }}
h3 {{ font-size: 1.15rem !important; color: var(--aiw-gold) !important; }}
h1::after, h2::after {{
  content: ""; display: block; height: 1px; margin-top: .5rem;
  background: linear-gradient(90deg, var(--aiw-gold-deep), transparent 78%);
}}

/* ---- the frieze and the corner bracket, for custom HTML blocks ---- */
.aiw-frieze {{ {FRIEZE_CSS} border-top: 1px solid var(--aiw-gold-deep); }}
.aiw-corner {{
  position: absolute; left: 0; top: 0; width: 46px; height: 46px;
  border-left: 3px solid var(--aiw-gold);
  border-top: 3px solid var(--aiw-gold);
  background:
    radial-gradient(circle at 0 0, transparent 0 30px, rgba(200,160,60,.9) 31px 32px, transparent 33px),
    radial-gradient(circle at 0 0, transparent 0 44px, rgba(200,160,60,.35) 45px 46px, transparent 47px);
}}
.aiw-ruling {{
  position: absolute; inset: 8px; border: 1px solid rgba(200,160,60,.35);
  pointer-events: none;
}}

/* ---- tabs as the book's index tabs ---- */
.stTabs [data-baseweb="tab-list"] {{
  gap: .3rem; border-bottom: 1px solid rgba(200,160,60,.35);
  padding-bottom: 0;
}}
.stTabs [data-baseweb="tab"] {{
  font-family: var(--aiw-display);
  font-size: .95rem; letter-spacing: .04em;
  color: var(--aiw-gold-light);
  background: linear-gradient(180deg, rgba(244,236,220,.10), rgba(244,236,220,.04));
  border: 1px solid rgba(200,160,60,.30);
  border-bottom: none;
  border-radius: 8px 8px 0 0;
  padding: .45rem 1.0rem;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
  color: #2a2016;
  background: linear-gradient(180deg, var(--aiw-parchment-hi), var(--aiw-parchment-lo));
  border-color: var(--aiw-gold);
  box-shadow: 0 -2px 0 var(--aiw-gold) inset;
}}
.stTabs [data-baseweb="tab-highlight"] {{ background: var(--aiw-gold) !important; }}

/* ---- buttons: the terracotta chevrons ---- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  font-family: var(--aiw-display) !important;
  letter-spacing: .05em;
  color: #fdf6e6 !important;
  background: linear-gradient(180deg, {p['terracotta']}, {p['terracotta_deep']}) !important;
  border: 1px solid var(--aiw-gold) !important;
  border-radius: 6px !important;
  box-shadow: 0 1px 0 rgba(255,255,255,.18) inset, 0 2px 8px rgba(0,0,0,.35);
}}
.stButton > button:hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {{
  background: linear-gradient(180deg, #c86636, {p['terracotta']}) !important;
  border-color: var(--aiw-gold-light) !important;
}}

/* ---- the chat: visitor on parchment, Heir on the indigo night ---- */
[data-testid="stChatMessage"] {{
  background: linear-gradient(180deg, var(--aiw-parchment-hi), var(--aiw-parchment-lo));
  border: 1px solid var(--aiw-parchment-edge);
  border-radius: 8px;
  color: var(--aiw-ink);
  box-shadow: 0 2px 10px rgba(0,0,0,.28);
}}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span {{ color: var(--aiw-ink); }}
[data-testid="stChatMessage"] a {{ color: var(--aiw-terracotta-deep); }}

/* ---- inputs, selects, sliders, expanders, metrics ---- */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {{
  background: var(--aiw-parchment-hi) !important;
  color: var(--aiw-ink) !important;
  border: 1px solid var(--aiw-parchment-edge) !important;
  border-radius: 5px !important;
  font-family: var(--aiw-body) !important;
}}
.streamlit-expanderHeader, [data-testid="stExpander"] summary {{
  font-family: var(--aiw-display);
  color: var(--aiw-gold-light) !important;
  letter-spacing: .04em;
}}
[data-testid="stExpander"] {{
  border: 1px solid rgba(200,160,60,.28) !important;
  border-radius: 8px;
  background: rgba(244,236,220,.04);
}}
[data-testid="stMetric"] {{
  background: linear-gradient(180deg, rgba(244,236,220,.07), rgba(244,236,220,.02));
  border: 1px solid rgba(200,160,60,.25);
  border-radius: 8px; padding: .6rem .8rem;
}}
[data-testid="stMetricValue"] {{ color: var(--aiw-gold-light) !important;
  font-family: var(--aiw-display) !important; }}

/* ---- sidebar: the book's spine ---- */
section[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #0b1226, {p['indigo_mid']});
  border-right: 1px solid rgba(200,160,60,.30);
}}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{ color: var(--aiw-gold) !important; }}
section[data-testid="stSidebar"] * {{ font-family: var(--aiw-body); }}

/* ---- misc chrome ---- */
hr {{ border-color: rgba(200,160,60,.25) !important; }}
a {{ color: var(--aiw-gold-light) !important; }}
.stAlert, [data-testid="stAlert"] {{
  background: rgba(244,236,220,.06) !important;
  border: 1px solid rgba(200,160,60,.30) !important;
  color: var(--aiw-ice) !important;
}}
.stProgress > div > div > div > div {{
  background: linear-gradient(90deg, var(--aiw-gold-deep), var(--aiw-gold-light)) !important;
}}

/* ---- the remaining widgets, so no surface is left in the old grey ---- */
[data-testid="stCaptionContainer"], .stCaption, small {{
  color: var(--aiw-ice) !important; opacity: .82;
  font-family: var(--aiw-body) !important;
  letter-spacing: .02em;
}}
code, pre, .stCodeBlock, [data-testid="stCode"] {{
  background: rgba(244,236,220,.06) !important;
  color: var(--aiw-gold-light) !important;
  border: 1px solid rgba(200,160,60,.22) !important;
  border-radius: 5px;
  font-family: 'Cascadia Mono', Consolas, monospace !important;
}}
[data-testid="stTable"] table, table {{ border-color: rgba(200,160,60,.28) !important; }}
[data-testid="stTable"] th {{ color: var(--aiw-gold-light) !important;
  font-family: var(--aiw-display) !important; letter-spacing: .04em; }}
[data-testid="stTable"] td {{ color: var(--aiw-ice) !important; }}
.stRadio label, .stCheckbox label, .stSlider label, [data-testid="stWidgetLabel"] p {{
  color: var(--aiw-ice) !important; font-family: var(--aiw-body) !important;
}}
[data-testid="stSlider"] div[role="slider"] {{ background: var(--aiw-gold) !important; }}
[data-testid="stFileUploader"] section {{
  background: rgba(244,236,220,.05) !important;
  border: 1px dashed rgba(200,160,60,.40) !important;
  border-radius: 8px;
}}
[data-testid="stTooltip"] {{ background: var(--aiw-parchment) !important;
  color: var(--aiw-ink) !important; border: 1px solid var(--aiw-gold) !important; }}
</style>
"""


def apply(st) -> None:
    """Inject the theme into a Streamlit page."""
    st.markdown(css(), unsafe_allow_html=True)


def palette() -> dict:
    """The measured colours, for custom HTML that builds its own markup."""
    return dict(PALETTE)
