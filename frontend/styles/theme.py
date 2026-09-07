"""
frontend/styles/theme.py
Single source of truth for all CyTrack colour/spacing tokens.

Usage (in any component or page):
    from styles.theme import get_css_tokens
    tokens = get_css_tokens(st.session_state.theme)  # "light" | "dark"

Returns a <style> block string ready to inject inside an HTML component.
Nothing here imports streamlit — this is pure Python string building.
"""


# LIGHT THEME TOKENS 
_LIGHT = """
  :root, [data-theme="light"] {
    /* surfaces */
    --bg-page:       #f1f5f9;
    --bg-sidebar:    #0f172a;
    --bg-topbar:     #ffffff;
    --bg-card:       #ffffff;

    /* borders */
    --border:        #f1f5f9;
    --border-sb:     #1e293b;
    --border-card:   #f1f5f9;

    /* text */
    --text-p:        #0f172a;
    --text-s:        #64748b;
    --text-m:        #94a3b8;

    /* sidebar text */
    --text-sb:       #94a3b8;
    --text-sb-act:   #ffffff;
    --sb-section:    #475569;

    /* topbar */
    --topbar-bdr:    #e2e8f0;

    /* dark mode toggle */
    --toggle-bg:     #e2e8f0;
    --toggle-knob:   #ffffff;

    /* card shadow */
    --card-shadow:   0 1px 3px rgba(0,0,0,.06);

    /* progress / chart bg */
    --pbar-bg:       #f1f5f9;

    /* stat card icon backgrounds */
    --icon-blue:     #eff6ff;
    --icon-red:      #fff1f2;
    --icon-orange:   #fff7ed;
    --icon-green:    #f0fdf4;

    /* severity alert colours */
    --alert-hi-bg:   #fef2f2;
    --alert-hi-c:    #dc2626;
    --alert-md-bg:   #fff7ed;
    --alert-md-c:    #ea580c;
    --alert-lo-bg:   #f0fdf4;
    --alert-lo-c:    #16a34a;

    /* accent (same in both themes) */
    --accent:        #3b82f6;
    --accent-dark:   #3b5bdb;
  }
"""

# DARK THEME TOKENS
_DARK = """
  [data-theme="dark"] {
    /* surfaces */
    --bg-page:       #0a0f1e;
    --bg-sidebar:    #060b14;
    --bg-topbar:     #162035;
    --bg-card:       #0f1729;

    /* borders */
    --border:        #1e2d4a;
    --border-sb:     #1a2540;
    --border-card:   #1e2d4a;

    /* text */
    --text-p:        #e2e8f0;
    --text-s:        #94a3b8;
    --text-m:        #475569;

    /* sidebar text */
    --text-sb:       #64748b;
    --text-sb-act:   #ffffff;
    --sb-section:    #334155;

    /* topbar */
    --topbar-bdr:    #1e2d4a;

    /* dark mode toggle */
    --toggle-bg:     #3b5bdb;
    --toggle-knob:   #ffffff;

    /* card shadow */
    --card-shadow:   0 1px 6px rgba(0,0,0,.35);

    /* progress / chart bg */
    --pbar-bg:       #1e2d4a;

    /* stat card icon backgrounds */
    --icon-blue:     #1d3b6e;
    --icon-red:      #3d1a1a;
    --icon-orange:   #3d2210;
    --icon-green:    #0d3320;

    /* severity alert colours */
    --alert-hi-bg:   #3d1a1a;
    --alert-hi-c:    #f87171;
    --alert-md-bg:   #3d2210;
    --alert-md-c:    #fb923c;
    --alert-lo-bg:   #0d3320;
    --alert-lo-c:    #4ade80;

    /* accent (same in both themes) */
    --accent:        #3b82f6;
    --accent-dark:   #3b5bdb;
  }
"""

# GLOBAL BASE STYLES
# Shared across both themes — resets, font, transitions.
_BASE = """
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg-page);
    display: flex;
    height: 100vh;
    overflow: hidden;
    transition: background 0.3s ease;
  }

  a { text-decoration: none; }

  /* scrollbar styling */
  ::-webkit-scrollbar       { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
"""


# PUBLIC API 

def get_css_tokens(theme: str = "light") -> str:
    """
    Returns a full <style> block with base resets, light tokens, and dark tokens.

    Both light AND dark token sets are always injected — CSS picks the correct
    one based on the data-theme attribute on <html>, which layout.py sets from
    st.session_state.theme. The theme arg here is unused at runtime but kept
    for clarity/documentation of intent.
    """
    return f"<style>{_BASE}{_LIGHT}{_DARK}</style>"


def get_initial_theme(theme: str = "light") -> str:
    """
    Returns the data-theme attribute value for the <html> tag.
    layout.py calls this to set the correct starting theme.
    """
    return theme if theme in ("light", "dark") else "light"