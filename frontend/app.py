"""
frontend/app.py
───────────────
CyTrack entry point.
    streamlit run frontend/app.py

Navigation strategy:
  - Sidebar JS calls window.open(url, '_top') with ?p=pagename
  - Streamlit reads st.query_params on every rerun
"""

import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

# ── 1. PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CyTrack",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 2. SESSION STATE ──────────────────────────────────────────────────────────
VALID_PAGES = {"dashboard", "scan", "agents", "reports", "settings"}

def _init_state():
    defaults = {
        "page":         "dashboard",
        "theme":        "light",
        "sidebar_open": True,
        "scan_id":      None,
        "scan_running": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ── 3. READ QUERY PARAMS ──────────────────────────────────────────────────────
_params  = st.query_params
_changed = False

if "p" in _params:
    _page = _params["p"]
    if _page in VALID_PAGES and _page != st.session_state.page:
        st.session_state.page = _page
        _changed = True

if "t" in _params:
    _theme = _params["t"]
    if _theme in ("light", "dark") and _theme != st.session_state.theme:
        st.session_state.theme = _theme
        _changed = True

if _changed:
    st.query_params.clear()
    st.rerun()

# ── 4. HIDE STREAMLIT CHROME ──────────────────────────────────────────────────
_bg = "#0a0f1e" if st.session_state.theme == "dark" else "#f1f5f9"
st.markdown(f"""
<style>
  #MainMenu, footer, header  {{ visibility: hidden; }}
  .block-container           {{ padding: 0 !important; max-width: 100% !important; }}
  div[data-testid="stAppViewContainer"] {{ background: {_bg}; }}
  section[data-testid="stSidebar"]      {{ display: none !important; }}
  div[data-testid="stVerticalBlock"]    {{ gap: 0 !important; }}
  div[data-testid="stVerticalBlockV2"]  {{ gap: 0 !important; }}
  iframe                     {{ border: none !important; }}
</style>
""", unsafe_allow_html=True)

# ── 5. PAGE ROUTER ────────────────────────────────────────────────────────────
def _load_page(page_key: str):
    if page_key == "dashboard":
        from pages.dashboard import render
    elif page_key == "scan":
        from pages.scan import render
    elif page_key == "agents":
        from pages.agents import render
    elif page_key == "reports":
        from pages.reports import render
    elif page_key == "settings":
        from pages.settings import render
    else:
        st.session_state.page = "dashboard"
        from pages.dashboard import render
    render()

_load_page(st.session_state.page)