"""
frontend/components/layout.py
──────────────────────────────
Renders the full CyTrack shell: sidebar + topbar.

Navigation strategy:
  - Sidebar JS builds URL with ?p=pagename and calls
    window.open(url, '_top')  — escapes st.iframe sandbox
  - Streamlit reads st.query_params on every rerun
  - No postMessage, no listener iframe
"""

import streamlit as st
from styles.theme import get_css_tokens, get_initial_theme


# ── NAV ITEMS ─────────────────────────────────────────────────────────────────
_NAV = [
    ("scan",      "🎯",  "Scan",      "TARGET / SCOPING"),
    ("dashboard", "🏠",  "Dashboard", "AGENTS"),
    ("agents",    "🤖",  "Agents",    None),
    ("reports",   "📄",  "Report",    None),
]

_BOTTOM_NAV = [
    ("settings", "⚙️", "Settings", True),
    ("logout",   "🚪", "Logout",   False),
]


def _build_nav_items(active_page: str) -> str:
    html = ""
    for page_key, icon, label, section in _NAV:
        if section:
            html += f'<div class="sb-section">{section}</div>'
        active_cls = "active" if page_key == active_page else ""
        html += f"""
        <a class="sb-item {active_cls}" onclick="navigate('{page_key}')" href="javascript:void(0)">
          {icon} &nbsp;{label}
        </a>"""
    return html


def _build_bottom_nav(active_page: str) -> str:
    html = ""
    for page_key, icon, label, is_page in _BOTTOM_NAV:
        active_cls = "active" if (is_page and page_key == active_page) else ""
        onclick    = f"navigate('{page_key}')" if is_page else "alert('Logout coming soon')"
        html += f"""
        <a class="sb-item {active_cls}" onclick="{onclick}" href="javascript:void(0)">
          {icon} &nbsp;{label}
        </a>"""
    return html


# ── CSS ───────────────────────────────────────────────────────────────────────
_LAYOUT_CSS = """
  .sidebar {
    width: 220px; min-width: 220px;
    background: var(--bg-sidebar);
    height: 100vh;
    display: flex; flex-direction: column;
    transition: width 0.3s ease, min-width 0.3s ease, opacity 0.25s ease;
    overflow: hidden; z-index: 100; flex-shrink: 0;
  }
  .sidebar.collapsed { width: 0; min-width: 0; opacity: 0; }

  .sb-logo {
    padding: 24px 20px 12px;
    font-size: 20px; font-weight: 800;
    color: #3b82f6; white-space: nowrap; letter-spacing: -0.5px; flex-shrink: 0;
  }
  .sb-logo span { color: #f8fafc; }

  .sb-section {
    font-size: 10px; font-weight: 600; color: var(--sb-section);
    letter-spacing: 1.2px; text-transform: uppercase;
    padding: 16px 20px 6px; white-space: nowrap;
  }

  .sb-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 20px; color: var(--text-sb);
    font-size: 13px; font-weight: 500;
    cursor: pointer; white-space: nowrap;
    transition: background 0.15s, color 0.15s; text-decoration: none;
  }
  .sb-item:hover  { background: #1e293b; color: #e2e8f0; }
  .sb-item.active {
    background: var(--accent-dark); color: var(--text-sb-act);
    border-radius: 8px; margin: 2px 10px; padding: 10px 12px;
  }

  .sb-bottom { margin-top: auto; border-top: 1px solid var(--border-sb); padding: 8px 0; }

  .main { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; min-width: 0; }

  .topbar {
    background: var(--bg-topbar); border-bottom: 1px solid var(--topbar-bdr);
    padding: 0 24px; height: 60px;
    display: flex; align-items: center; justify-content: space-between;
    flex-shrink: 0; z-index: 50; transition: background 0.3s, border-color 0.3s;
  }
  .topbar-left  { display: flex; align-items: center; gap: 14px; }
  .topbar-right { display: flex; align-items: center; gap: 14px; }

  .hamburger {
    background: none; border: none; cursor: pointer;
    font-size: 20px; color: var(--text-s);
    width: 36px; height: 36px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s;
  }
  .hamburger:hover { background: var(--pbar-bg); }

  .brand {
    font-size: 18px; font-weight: 800; color: var(--accent-dark);
    letter-spacing: -0.4px; display: flex; align-items: center; gap: 6px;
  }
  .brand-dark { color: var(--text-p); }

  .theme-toggle { display: flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; }
  .toggle-track {
    width: 44px; height: 24px; border-radius: 12px;
    background: var(--toggle-bg); position: relative; transition: background 0.3s; flex-shrink: 0;
  }
  .toggle-knob {
    width: 18px; height: 18px; border-radius: 50%; background: var(--toggle-knob);
    position: absolute; top: 3px; left: 3px;
    transition: transform 0.3s cubic-bezier(.34,1.56,.64,1);
    box-shadow: 0 1px 3px rgba(0,0,0,.2);
  }
  [data-theme="dark"] .toggle-knob { transform: translateX(20px); }
  .toggle-label { font-size: 13px; color: var(--text-s); font-weight: 500; white-space: nowrap; }

  .notif {
    position: relative; font-size: 18px; cursor: pointer;
    width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
    border-radius: 8px; transition: background 0.15s;
  }
  .notif:hover { background: var(--pbar-bg); }
  .notif-dot {
    position: absolute; top: 5px; right: 6px; width: 8px; height: 8px;
    background: #ef4444; border-radius: 50%; border: 2px solid var(--bg-topbar);
  }

  .user-area { display: flex; align-items: center; gap: 8px; cursor: pointer; }
  .avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 700; font-size: 13px;
  }
  .user-name { font-size: 13px; font-weight: 500; color: var(--text-p); }

  .content { flex: 1; overflow-y: auto; padding: 24px; background: var(--bg-page); transition: background 0.3s; }

  @media (max-width: 560px) {
    .user-name, .toggle-label { display: none; }
    .content { padding: 14px; }
  }
"""

# ── JS — window.open escapes st.iframe sandbox ───────────────────────────────
_LAYOUT_JS = """
  const sidebar    = document.getElementById('sidebar');
  const htmlEl     = document.documentElement;
  const themeEmoji = document.getElementById('themeEmoji');
  const themeLabel = document.getElementById('themeLabel');

  function toggleSidebar() { sidebar.classList.toggle('collapsed'); }

  /* ───────────────────────────────────────────────────────────────
     Inject a navigation listener INTO THE PARENT (Streamlit) window.
     st.iframe sandbox blocks window.open(_top) and direct
     window.parent.location writes, BUT same-origin DOM access is
     allowed — so we append a <script> to the parent document.
     That script executes in the parent's context and can change
     window.location.href freely.
  ─────────────────────────────────────────────────────────────── */
  (function installParentListener() {
    try {
      if (window.parent && window.parent !== window
          && !window.parent.__cytrack_listener) {
        window.parent.__cytrack_listener = true;
        const s = window.parent.document.createElement('script');
        s.textContent = `
          window.addEventListener('message', function(e) {
            if (!e || !e.data || !e.data.type) return;
            const u = new URL(window.location.href);
            if (e.data.type === 'cytrack_nav') {
              u.searchParams.set('p', e.data.page);
              window.location.href = u.toString();
            } else if (e.data.type === 'cytrack_theme') {
              u.searchParams.set('t', e.data.theme);
              window.location.href = u.toString();
            }
          });
          console.log('[CyTrack] parent navigation listener installed');
        `;
        window.parent.document.body.appendChild(s);
      }
    } catch (err) {
      console.error('[CyTrack] listener injection failed:', err);
    }
  })();

  function navigate(page) {
    /* Send message to parent — postMessage works across origins
       and is NOT blocked by the sandbox. */
    window.parent.postMessage({ type: 'cytrack_nav', page: page }, '*');
  }

  function toggleTheme() {
    const isDark = htmlEl.getAttribute('data-theme') === 'dark';
    const next   = isDark ? 'light' : 'dark';
    htmlEl.setAttribute('data-theme', next);
    themeEmoji.textContent = isDark ? '🌙' : '☀️';
    themeLabel.textContent = isDark ? 'Dark' : 'Light';
    window.parent.postMessage({ type: 'cytrack_theme', theme: next }, '*');
  }
"""

# ❌ REMOVED: PARENT_LISTENER_JS — postMessage listener was unreachable
#    and st.iframe sandbox blocked window.parent.location.href anyway.
#    Navigation now uses window.open(url, '_top') directly from LAYOUT_JS.


# ── RENDER ────────────────────────────────────────────────────────────────────

def render_layout(active_page: str, page_content_html: str = "", height: int = 900) -> None:
    """
    Renders the full CyTrack shell via st.iframe.
    Navigation uses window.open(url, '_top') to escape the sandbox.
    app.py reads st.query_params on rerun to update session state.
    """
    theme         = st.session_state.get("theme", "light")
    css_tokens    = get_css_tokens(theme)
    initial_theme = get_initial_theme(theme)

    nav_items    = _build_nav_items(active_page)
    bottom_items = _build_bottom_nav(active_page)
    theme_emoji  = "☀️" if theme == "dark" else "🌙"
    theme_label  = "Light" if theme == "dark" else "Dark"

    html = f"""<!DOCTYPE html>
<html data-theme="{initial_theme}">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{css_tokens}
<style>{_LAYOUT_CSS}</style>
</head>
<body>

<nav class="sidebar" id="sidebar">
  <div class="sb-logo">CY<span>TRACK</span></div>
  {nav_items}
  <div class="sb-bottom">{bottom_items}</div>
</nav>

<div class="main">
  <div class="topbar">
    <div class="topbar-left">
      <button class="hamburger" onclick="toggleSidebar()">☰</button>
      <div class="brand">🛡️ <span class="brand-dark">CY</span>TRACK</div>
    </div>
    <div class="topbar-right">
      <div class="theme-toggle" onclick="toggleTheme()">
        <span id="themeEmoji">{theme_emoji}</span>
        <div class="toggle-track"><div class="toggle-knob"></div></div>
        <span class="toggle-label" id="themeLabel">{theme_label}</span>
      </div>
      <div class="notif">🔔<div class="notif-dot"></div></div>
      <div class="user-area">
        <div class="avatar">A</div>
        <div class="user-name">Admin User ▾</div>
      </div>
    </div>
  </div>

  <div class="content">
    {page_content_html}
  </div>
</div>

<script>{_LAYOUT_JS}</script>
</body>
</html>"""

    st.iframe(html, height=height)


def get_layout_shell() -> tuple[str, str]:
    return _LAYOUT_CSS, _LAYOUT_JS