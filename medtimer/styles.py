"""The MedTimer design system.

One CSS source, two themes. Every colour is a token so light and dark are
generated from the same rules — no duplicated selectors.

    inject_styles(dark=False)   # light
    inject_styles(dark=True)    # dark
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Theme tokens
# ---------------------------------------------------------------------------
LIGHT: dict[str, str] = {
    "--ink": "#0B1220",
    "--ink-2": "#334155",
    "--muted": "#5B6B80",
    "--line": "#E6EBF2",
    "--surface": "#FFFFFF",
    "--surface-2": "#FBFCFE",
    "--canvas": "#F6F8FA",
    "--input-bg": "#FBFCFE",
    "--hero-1": "#FFFFFF",
    "--hero-2": "#F3FBF9",
    "--hero-3": "#EEF4FF",
    "--tag-bg": "rgba(255,255,255,.85)",
    "--brand": "#0D9488",
    "--brand-2": "#12B3A6",
    "--brand-soft": "#E8F7F4",
    "--brand-ink": "#0B6F66",
    "--brand-line": "#CBE9E4",
    "--ok": "#0E9F6E",
    "--ok-soft": "#E6F7F0",
    "--warn": "#B4710A",
    "--warn-soft": "#FDF3E3",
    "--danger": "#D92D20",
    "--danger-soft": "#FDEDEC",
    "--art-bg": "#F7FBFA",
    "--track": "#EDF1F6",
    "--empty-bg": "#FBFCFE",
    "--empty-line": "#D7DFE9",
    "--shadow-sm": "0 1px 2px rgba(11,18,32,.05)",
    "--shadow-md": "0 2px 4px rgba(11,18,32,.04), 0 20px 40px -30px rgba(11,18,32,.5)",
}

DARK: dict[str, str] = {
    "--ink": "#E9EFF7",
    "--ink-2": "#BAC7D6",
    "--muted": "#8A9AAD",
    "--line": "#22303F",
    "--surface": "#111A24",
    "--surface-2": "#0D151E",
    "--canvas": "#0A121A",
    "--input-bg": "#0D151E",
    "--hero-1": "#12202B",
    "--hero-2": "#0F2A2A",
    "--hero-3": "#141F33",
    "--tag-bg": "rgba(255,255,255,.06)",
    "--brand": "#2DD4BF",
    "--brand-2": "#14B8A6",
    "--brand-soft": "#0E2E2B",
    "--brand-ink": "#7FE9DB",
    "--brand-line": "#1C4A45",
    "--ok": "#34D399",
    "--ok-soft": "#0D2A22",
    "--warn": "#FBBF24",
    "--warn-soft": "#33270C",
    "--danger": "#F87171",
    "--danger-soft": "#33191A",
    "--art-bg": "#0D1A1E",
    "--track": "#1B2734",
    "--empty-bg": "#0D151E",
    "--empty-line": "#243140",
    "--shadow-sm": "0 1px 2px rgba(0,0,0,.6)",
    "--shadow-md": "0 2px 6px rgba(0,0,0,.5), 0 24px 48px -32px rgba(0,0,0,.9)",
}

# ---------------------------------------------------------------------------
# Base rules — identical for both themes, driven entirely by tokens
# ---------------------------------------------------------------------------
_BASE = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

*{box-sizing:border-box;}

/* Streamlit paints its own containers with the boot-time (light) theme, so the
   theme has to be forced onto them or a dark switch only recolours our cards. */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stMainBlockContainer"], .main{
  background-color:var(--canvas) !important;
  color:var(--ink) !important;
}
.stApp{
  background-image:
    radial-gradient(1100px 520px at 12% -12%, var(--brand-soft) 0%, rgba(0,0,0,0) 62%),
    radial-gradient(900px 460px at 92% 0%, var(--surface-2) 0%, rgba(0,0,0,0) 58%) !important;
  background-color:var(--canvas) !important;
  color:var(--ink) !important;
  font-family:'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
[data-testid="stHeader"]{background:transparent !important;}
[data-testid="stMarkdownContainer"]{color:var(--ink);}
/* Safety net: if markup ever lands in a code block, keep it readable instead
   of showing a white slab on the dark canvas. */
.stApp pre, .stApp code, .stApp kbd{
  background:var(--surface-2) !important;
  color:var(--ink) !important;
  border:1px solid var(--line);
  border-radius:8px;
}

/* Live clock strip */
.mt-clock{
  display:flex; align-items:center; gap:10px; flex-wrap:wrap;
  width:fit-content; max-width:100%;
  padding:10px 18px; margin:0 0 18px;
  background:linear-gradient(180deg,var(--surface),var(--surface-2));
  border:1px solid var(--line);
  border-radius:999px;
  box-shadow:var(--shadow-sm);
}
.mt-clock:hover{border-color:var(--brand-line);}
.mt-clock__pulse{
  width:9px; height:9px; border-radius:50%; background:var(--ok);
  box-shadow:0 0 0 0 rgba(14,159,110,.45);
  animation:mt-pulse 2s infinite;
}
@keyframes mt-pulse{
  0%{box-shadow:0 0 0 0 rgba(14,159,110,.45)}
  70%{box-shadow:0 0 0 9px rgba(14,159,110,0)}
  100%{box-shadow:0 0 0 0 rgba(14,159,110,0)}
}
.mt-clock__time{
  font-variant-numeric:tabular-nums;
  font-weight:800; font-size:1.03rem; color:var(--ink); letter-spacing:.01em;
}
.mt-clock__sep{color:var(--muted);}
.mt-clock__next{font-size:.9rem; font-weight:600; color:var(--ink-2);}
.mt-clock__next--ok{color:var(--ok);}
.mt-clock__next--warn{color:var(--warn);}
.mt-clock__next--danger{color:var(--danger);}
.mt-clock__next--brand{color:var(--brand-ink);}
#MainMenu, footer, [data-testid="stToolbar"]{visibility:hidden;}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"]{display:none;}
.block-container{max-width:1260px; padding-top:1.1rem; padding-bottom:3.4rem;}

h1,h2,h3,h4,h5,h6,p,span,div,label,button,input,text{
  font-family:'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons{
  font-family:'Material Symbols Rounded' !important;
}
h1,h2,h3{color:var(--ink); letter-spacing:-.02em;}

/* ---------- buttons ---------- */
div[data-testid="stButton"] > button,
div[data-testid="stPopover"] > button,
div[data-testid="stFormSubmitButton"] > button{
  width:100%;
  border-radius:12px;
  border:1px solid var(--line);
  background:var(--surface);
  color:var(--ink);
  font-weight:650;
  font-size:.95rem;
  min-height:46px;
  padding:.6rem .9rem;
  box-shadow:var(--shadow-sm);
  transition:transform .12s ease, box-shadow .12s ease, background .12s ease, border-color .12s ease;
}
div[data-testid="stButton"] > button:hover,
div[data-testid="stPopover"] > button:hover{
  border-color:var(--brand-line); transform:translateY(-1px);
  background:var(--surface-2);
}
button[kind="primary"],
button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(180deg,var(--brand-2),var(--brand)) !important;
  background-color:var(--brand) !important;
  border:none !important; color:#04211F !important;
  box-shadow:0 10px 22px -16px rgba(13,148,136,.95) !important;
}
button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover{
  transform:translateY(-1px);
  box-shadow:0 14px 26px -16px rgba(13,148,136,1) !important;
}
button[disabled]{opacity:.5 !important; box-shadow:none !important; cursor:not-allowed;}
div[data-testid="stButton"] > button:active,
div[data-testid="stPopover"] > button:active{transform:translateY(0) scale(.99);}
/* Keyboard users must be able to see where they are. */
button:focus-visible, a:focus-visible, input:focus-visible,
[role="button"]:focus-visible, [data-baseweb="input"]:focus-within{
  outline:3px solid var(--brand) !important;
  outline-offset:2px;
}

/* ---------- containers ---------- */
div[data-testid="stVerticalBlockBorderWrapper"]{
  border-radius:20px;
  background:var(--surface);
  border:1px solid var(--line);
  box-shadow:var(--shadow-md);
  padding:.4rem .5rem;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div{padding:0;}

/* ---------- inputs ---------- */
div[data-baseweb="input"], div[data-baseweb="base-input"]{
  border-radius:12px !important;
  background:var(--input-bg) !important;
  border-color:var(--line) !important;
}
div[data-baseweb="input"] input, input{
  background:transparent !important;
  color:var(--ink) !important;
  border-radius:12px !important;
  font-size:.98rem !important;
}
[data-testid="stWidgetLabel"] p, label p{color:var(--ink-2) !important; font-weight:600;}
[data-testid="stCaptionContainer"], .stCaption{color:var(--muted) !important;}

/* ---------- hero ---------- */
.mt-hero{
  position:relative; overflow:hidden;
  border:1px solid var(--line); border-radius:26px;
  background:linear-gradient(135deg,var(--hero-1) 0%,var(--hero-2) 55%,var(--hero-3) 100%);
  box-shadow:var(--shadow-md);
  padding:32px 36px 28px; margin-bottom:22px;
}
/* Soft brand glow in the corner — depth without a background image. */
.mt-hero::after{
  content:""; position:absolute; right:-90px; top:-110px;
  width:320px; height:320px; border-radius:50%; pointer-events:none;
  background:radial-gradient(circle at 50% 50%, var(--brand-soft) 0%, rgba(0,0,0,0) 68%);
}
.mt-hero__brand{display:flex; align-items:center; gap:10px; font-weight:800;
  color:var(--brand); letter-spacing:-.02em; font-size:1rem;}
.mt-logo{
  display:inline-flex; align-items:center; justify-content:center;
  width:30px; height:30px; border-radius:10px; color:#04211F; font-size:.95rem;
  background:linear-gradient(160deg,var(--brand-2),var(--brand));
  box-shadow:0 8px 18px -12px rgba(13,148,136,1);
}
.mt-hero__title{margin:15px 0 7px; font-size:clamp(1.75rem, 2.6vw, 2.35rem);
  line-height:1.12; font-weight:800; color:var(--ink); letter-spacing:-.03em;}
.mt-hero__sub{margin:0; color:var(--muted); font-size:1rem; max-width:56ch; line-height:1.5;}
.mt-hero__meta{display:flex; flex-wrap:wrap; gap:8px; margin-top:18px;}
.mt-tag{
  display:inline-flex; align-items:center; gap:6px;
  padding:7px 13px; border-radius:999px; font-size:.82rem; font-weight:650;
  background:var(--tag-bg); color:var(--ink-2); border:1px solid var(--line);
}
.mt-tag--brand{background:var(--brand-soft); color:var(--brand-ink); border-color:var(--brand-line);}

/* ---------- kpi ---------- */
.mt-kpi{
  position:relative; overflow:hidden;
  background:var(--surface); border:1px solid var(--line); border-radius:20px;
  padding:20px 18px 18px; box-shadow:var(--shadow-md); height:100%;
  transition:transform .18s ease, border-color .18s ease;
}
.mt-kpi::after{
  content:""; position:absolute; top:0; left:0; right:0; height:3px;
  background:linear-gradient(90deg, var(--brand-2), var(--brand) 65%, var(--brand-2));
  opacity:.85;
}
.mt-kpi:hover{transform:translateY(-2px); border-color:var(--brand-line);}
.mt-kpi__label{font-size:.75rem; font-weight:700; letter-spacing:.07em;
  text-transform:uppercase; color:var(--muted);}
.mt-kpi__value{font-size:2rem; font-weight:800; color:var(--ink);
  letter-spacing:-.03em; line-height:1.1; margin-top:8px;}
.mt-kpi__value small{font-size:.95rem; font-weight:700; color:var(--muted);}
.mt-kpi__foot{margin-top:12px;}
.mt-bar{height:8px; border-radius:999px; background:var(--track); overflow:hidden;}
.mt-bar > span{display:block; height:100%; border-radius:999px;
  background:linear-gradient(90deg,var(--brand-2),var(--brand));}
.mt-ring{display:flex; align-items:center; gap:14px;}
.mt-ring__caption{font-size:.8rem; color:var(--muted); line-height:1.4;}
.mt-ring svg circle{stroke:var(--track);}
.mt-ring svg circle + circle{stroke:var(--brand);}
.mt-ring svg text{fill:var(--ink);}

/* ---------- section ---------- */
.mt-section{margin:8px 0 13px;}
.mt-section h2{display:flex; align-items:center; gap:10px;
  font-size:1.2rem; margin:0; font-weight:750; color:var(--ink);}
.mt-section h2::before{
  content:""; width:4px; height:18px; border-radius:3px; flex:none;
  background:linear-gradient(180deg, var(--brand-2), var(--brand));
}
.mt-section p{margin:4px 0 0; color:var(--muted); font-size:.87rem;}

/* ---------- dose row ---------- */
.mt-dose{position:relative; display:flex; justify-content:space-between;
  align-items:flex-start; gap:14px; padding:3px 0 6px 12px;}
/* Status rail: the colour reads even at arm's length. */
.mt-dose::before{content:""; position:absolute; left:0; top:3px; bottom:6px;
  width:4px; border-radius:4px; background:var(--rail, var(--line));}
.mt-dose--ok{--rail:var(--ok);}
.mt-dose--warn{--rail:var(--warn);}
.mt-dose--danger{--rail:var(--danger);}
.mt-dose__name{font-size:1.08rem; font-weight:700; color:var(--ink);
  letter-spacing:-.01em;}
.mt-dose__meta{font-size:.88rem; color:var(--muted); margin-top:3px;}
.mt-pill{
  display:inline-flex; align-items:center; gap:6px; white-space:nowrap;
  padding:7px 13px; border-radius:999px; font-size:.8rem; font-weight:750;
}
.mt-pill--ok{background:var(--ok-soft); color:var(--ok);}
.mt-pill--warn{background:var(--warn-soft); color:var(--warn);}
.mt-pill--danger{background:var(--danger-soft); color:var(--danger);}
.mt-dot{width:7px; height:7px; border-radius:50%; background:currentColor;}

/* ---------- week bars ---------- */
.mt-bars{display:flex; align-items:flex-end; gap:10px; padding:8px 2px 0;}
.mt-bcol{flex:1; display:flex; flex-direction:column; align-items:center; gap:6px;}
.mt-bval{font-size:.75rem; font-weight:700; color:var(--muted);
  transition:color .15s ease;}
.mt-bcol:hover .mt-bval{color:var(--ink);}
.mt-btrack{width:100%; height:120px; display:flex; align-items:flex-end;
  background:var(--track); border-radius:10px; overflow:hidden;}
.mt-btrack > span{display:block; width:100%;
  background:linear-gradient(180deg,var(--brand-2),var(--brand)); border-radius:10px;}
.mt-bday{font-size:.74rem; font-weight:650; color:var(--muted);}

/* ---------- misc ---------- */
.mt-art{border-radius:18px; overflow:hidden; background:var(--art-bg);
  border:1px solid var(--line); padding:6px;}
.mt-art svg{display:block; width:100%; height:auto;}
.mt-quote{position:relative; padding:14px 10px 14px 40px; font-size:.97rem;
  color:var(--ink-2); line-height:1.65;}
.mt-quote::before{content:"\u201c"; position:absolute; left:8px; top:0;
  font-family:Georgia,'Times New Roman',serif; font-size:46px; line-height:1.1;
  color:var(--brand-line);}
/* Status legend — spells out what the three colours mean. */
.mt-legend{display:flex; gap:8px; flex-wrap:wrap; margin:0 0 13px;}
.mt-legend__chip{display:inline-flex; align-items:center; gap:6px;
  padding:5px 11px; border-radius:999px; font-size:.76rem; font-weight:700;}
.mt-legend__chip--ok{background:var(--ok-soft); color:var(--ok);}
.mt-legend__chip--warn{background:var(--warn-soft); color:var(--warn);}
.mt-legend__chip--danger{background:var(--danger-soft); color:var(--danger);}
.mt-note{background:var(--brand-soft); border:1px solid var(--brand-line);
  color:var(--brand-ink); border-radius:14px; padding:14px 16px;
  font-size:.89rem; font-weight:550; line-height:1.5;}
.mt-empty{border:1.5px dashed var(--empty-line); border-radius:20px;
  padding:26px; text-align:center; color:var(--muted); font-size:.91rem;
  background:var(--empty-bg);}
.mt-foot{margin-top:26px; padding-top:16px; border-top:1px solid var(--line);
  color:var(--muted); font-size:.78rem; text-align:center;}
"""

# ---------------------------------------------------------------------------
# Dark-only overrides for Streamlit's own chrome, which follows the config
# theme rather than our tokens.
# ---------------------------------------------------------------------------
_DARK_EXTRA = """
.stApp p, .stApp li, .stApp span, .stApp label, .stApp div{color:inherit;}
[data-testid="stMarkdownContainer"] p{color:var(--ink-2);}
[data-testid="stWidgetLabel"] p, label p{color:var(--ink-2) !important;}
[data-testid="stPopoverBody"]{background:var(--surface) !important;
  border:1px solid var(--line) !important;}
[data-testid="stToast"]{background:var(--surface) !important;
  color:var(--ink) !important; border:1px solid var(--line) !important;}
[data-baseweb="popover"] div{background:var(--surface);}
div[data-testid="stButton"] > button,
div[data-testid="stPopover"] > button,
div[data-testid="stFormSubmitButton"] > button{background:var(--surface); color:var(--ink);}
div[data-baseweb="input"], div[data-baseweb="base-input"]{
  background:var(--input-bg) !important; border:1px solid var(--line) !important;
}
[data-testid="stTimeInput"] input{color:var(--ink) !important;}
svg[data-testid="stExpanderToggleIcon"]{fill:var(--ink);}
a{color:var(--brand);}
"""


def build_css(dark: bool = False) -> str:
    """Return the complete stylesheet for the requested theme."""
    tokens = DARK if dark else LIGHT
    root = "".join(f"{name}:{value};" for name, value in tokens.items())
    extra = _DARK_EXTRA if dark else ""
    return f"<style>:root{{{root}}}{_BASE}{extra}</style>"


# Backwards-compatible default used where a theme is not supplied.
CSS = build_css()
