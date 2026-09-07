"""
frontend/pages/agents.py
─────────────────────────
Agents monitoring page.

Layout:
  ┌─────────────────────────────────────────────────────┐
  │  [stat bar — Total | Working | Idle | Findings]     │
  ├──────────────────────────────────┬──────────────────┤
  │  Agent Cards Grid                │ Activity Feed    │
  │  (working first, idle below)     │ (live log panel) │
  └──────────────────────────────────┴──────────────────┘
"""

import streamlit as st
from components.layout import render_layout

# ── MOCK DATA ─────────────────────────────────────────────────────────────────
_MOCK_AGENTS = [
    {"name": "SQL Agent",              "status": "working", "progress": 75,  "last_activity": "2m ago",  "findings": 3, "high": 2, "medium": 1, "low": 0, "description": "Detects SQL injection vulnerabilities", "started": "11:20 AM"},
    {"name": "XSS Agent",             "status": "working", "progress": 60,  "last_activity": "5m ago",  "findings": 2, "high": 0, "medium": 2, "low": 0, "description": "Scans for cross-site scripting flaws",   "started": "11:21 AM"},
    {"name": "SSRF Agent",            "status": "working", "progress": 90,  "last_activity": "1m ago",  "findings": 1, "high": 1, "medium": 0, "low": 0, "description": "Tests for server-side request forgery",    "started": "11:19 AM"},
    {"name": "CSRF Agent",            "status": "idle",    "progress": 0,   "last_activity": "10m ago", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Checks CSRF token implementation",         "started": "—"},
    {"name": "IDOR Agent",            "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests insecure direct object references",   "started": "—"},
    {"name": "SAST Agent",            "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Static analysis of discovered endpoints",  "started": "—"},
    {"name": "AuthZ Agent",           "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests authorisation and access controls",  "started": "—"},
    {"name": "NoSQL Agent",           "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Scans for NoSQL injection vectors",         "started": "—"},
    {"name": "Upload Agent",          "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests file upload security",                "started": "—"},
    {"name": "Password Policy Agent", "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Audits password and auth policies",         "started": "—"},
]

_MOCK_FEED = [
    {"time": "11:34",  "agent": "SSRF Agent",  "event": "Found potential SSRF vector at /api/fetch",        "level": "high"},
    {"time": "11:33",  "agent": "SQL Agent",   "event": "Detected SQLi in parameter ?id= on /users",        "level": "high"},
    {"time": "11:32",  "agent": "XSS Agent",   "event": "Reflected XSS found in search endpoint",           "level": "medium"},
    {"time": "11:31",  "agent": "SQL Agent",   "event": "Testing /api/products endpoint for injection",      "level": "info"},
    {"time": "11:30",  "agent": "XSS Agent",   "event": "Scanning form inputs on /contact",                 "level": "info"},
    {"time": "11:29",  "agent": "SSRF Agent",  "event": "Probing internal endpoints via URL parameter",      "level": "info"},
    {"time": "11:28",  "agent": "SQL Agent",   "event": "Blind SQLi confirmed on /login endpoint",           "level": "medium"},
    {"time": "11:27",  "agent": "XSS Agent",   "event": "DOM-based XSS attempt on /dashboard",              "level": "info"},
]

# ── ICON MAP ──────────────────────────────────────────────────────────────────
_ICONS = {
    "sql": "🔴", "xss": "🟠", "ssrf": "🟡", "csrf": "🟡",
    "idor": "🔵", "sast": "🟣", "authz": "🔐",
    "nosql": "🟤", "upload": "📁", "password": "🔑",
}

def _icon(name: str) -> str:
    nl = name.lower()
    for k, v in _ICONS.items():
        if k in nl:
            return v
    return "🤖"

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', sans-serif; background: var(--bg-page); color: var(--text-p); }

/* ── PAGE HEADER ── */
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px; flex-wrap: wrap; gap: 12px;
}
.page-title { font-size: 22px; font-weight: 700; color: var(--text-p); }
.run-btn {
  padding: 8px 20px; background: var(--accent-dark);
  color: #fff; border: none; border-radius: 8px;
  font-size: 13px; font-weight: 600; cursor: pointer;
  transition: opacity 0.2s; font-family: 'Inter', sans-serif;
}
.run-btn:hover { opacity: 0.88; }
.run-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── STAT BAR ── */
.stat-bar {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 14px; margin-bottom: 20px;
}
.stat-pill {
  background: var(--bg-card); border-radius: 12px;
  padding: 16px 18px; border: 1px solid var(--border-card);
  box-shadow: var(--card-shadow);
  display: flex; align-items: center; gap: 14px;
}
.stat-pill-icon {
  width: 42px; height: 42px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.spi-blue   { background: var(--icon-blue); }
.spi-green  { background: var(--icon-green); }
.spi-gray   { background: var(--pbar-bg); }
.spi-red    { background: var(--icon-red); }
.stat-pill-val  { font-size: 24px; font-weight: 700; color: var(--text-p); line-height: 1; }
.stat-pill-lbl  { font-size: 12px; color: var(--text-s); margin-top: 2px; }

/* ── MAIN GRID ── */
.agents-main {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 16px; align-items: start;
}

/* ── SECTION LABEL ── */
.section-lbl {
  font-size: 11px; font-weight: 600; color: var(--text-m);
  text-transform: uppercase; letter-spacing: 1px;
  margin-bottom: 10px;
}

/* ── AGENT CARDS ── */
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}
.agent-card {
  background: var(--bg-card); border-radius: 14px; padding: 18px;
  border: 1px solid var(--border-card); box-shadow: var(--card-shadow);
  display: flex; flex-direction: column; gap: 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
  position: relative; overflow: hidden;
}
.agent-card.working {
  border-color: rgba(59,130,246,0.35);
  box-shadow: 0 0 0 1px rgba(59,130,246,0.15), var(--card-shadow);
}
.agent-card-top {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 8px;
}
.agent-name-row { display: flex; align-items: center; gap: 8px; }
.agent-icon { font-size: 18px; flex-shrink: 0; }
.agent-name { font-size: 14px; font-weight: 600; color: var(--text-p); }
.agent-desc { font-size: 11px; color: var(--text-m); margin-top: 2px; }

/* ── STATUS PILL ── */
.status-pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px;
  font-size: 11px; font-weight: 600; flex-shrink: 0;
}
.sp-working { background: #dcfce7; color: #16a34a; }
.sp-idle    { background: var(--pbar-bg); color: var(--text-m); }
.sp-error   { background: #fef2f2; color: #dc2626; }

/* ── SPINNER ── */
@keyframes spin { to { transform: rotate(360deg); } }
.spinner {
  width: 12px; height: 12px; border-radius: 50%;
  border: 2px solid #bbf7d0;
  border-top-color: #16a34a;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

/* ── PROGRESS BAR ── */
.pbar-label { font-size: 11px; color: var(--text-m); margin-bottom: 4px; display: flex; justify-content: space-between; }
.pbar-bg { height: 6px; background: var(--pbar-bg); border-radius: 99px; overflow: hidden; }
.pbar-fill { height: 100%; border-radius: 99px; transition: width 0.4s ease; }
.pbar-active { background: linear-gradient(90deg, #3b82f6, #6366f1); }
.pbar-idle   { background: var(--pbar-bg); }

/* ── FINDINGS ROW ── */
.findings-row {
  display: flex; align-items: center;
  justify-content: space-between; font-size: 12px;
}
.findings-badges { display: flex; gap: 5px; }
.fbadge {
  padding: 2px 7px; border-radius: 5px;
  font-size: 10px; font-weight: 700;
}
.fb-h { background: var(--alert-hi-bg); color: var(--alert-hi-c); }
.fb-m { background: var(--alert-md-bg); color: var(--alert-md-c); }
.fb-l { background: var(--alert-lo-bg); color: var(--alert-lo-c); }
.fb-none { color: var(--text-m); font-size: 11px; }
.agent-time { font-size: 11px; color: var(--text-m); }

/* ── WORKING PULSE LINE ── */
.pulse-line {
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  background-size: 200% 100%;
  animation: pulse-slide 2s linear infinite;
}
@keyframes pulse-slide {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── DIVIDER ── */
.group-divider {
  font-size: 11px; font-weight: 600; color: var(--text-m);
  text-transform: uppercase; letter-spacing: 1px;
  margin: 16px 0 10px; padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 8px;
}
.divider-count {
  background: var(--pbar-bg); color: var(--text-s);
  padding: 1px 7px; border-radius: 10px; font-size: 10px;
}

/* ── ACTIVITY FEED ── */
.feed-card {
  background: var(--bg-card); border-radius: 14px;
  border: 1px solid var(--border-card);
  box-shadow: var(--card-shadow);
  overflow: hidden; position: sticky; top: 0;
}
.feed-header {
  padding: 16px 18px 12px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.feed-title { font-size: 14px; font-weight: 600; color: var(--text-p); }
.feed-live {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; color: #16a34a; font-weight: 500;
}
.live-dot {
  width: 7px; height: 7px; border-radius: 50%; background: #22c55e;
  animation: blink 1.2s ease-in-out infinite;
}
@keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

.feed-body { padding: 10px 0; max-height: 520px; overflow-y: auto; }
.feed-item {
  padding: 10px 18px; border-bottom: 1px solid var(--border);
  font-size: 12px;
}
.feed-item:last-child { border-bottom: none; }
.feed-item-top {
  display: flex; align-items: center; gap: 6px; margin-bottom: 3px;
}
.feed-agent { font-weight: 600; color: var(--text-p); }
.feed-time  { color: var(--text-m); font-size: 11px; margin-left: auto; }
.feed-event { color: var(--text-s); line-height: 1.4; }
.feed-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.fd-high   { background: #ef4444; }
.fd-medium { background: #f97316; }
.fd-info   { background: #3b82f6; }

/* ── RESPONSIVE ── */
@media (max-width: 960px) {
  .agents-main { grid-template-columns: 1fr; }
  .stat-bar    { grid-template-columns: repeat(2,1fr); }
}
@media (max-width: 480px) {
  .stat-bar { grid-template-columns: 1fr 1fr; }
}
"""

# ── BUILDERS ─────────────────────────────────────────────────────────────────

def _stat_bar(agents: list) -> str:
    total    = len(agents)
    working  = sum(1 for a in agents if a["status"] == "working")
    idle     = sum(1 for a in agents if a["status"] == "idle")
    findings = sum(a.get("findings", 0) for a in agents)

    return f"""
    <div class="stat-bar">
      <div class="stat-pill">
        <div class="stat-pill-icon spi-blue">🤖</div>
        <div>
          <div class="stat-pill-val">{total}</div>
          <div class="stat-pill-lbl">Total Agents</div>
        </div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-icon spi-green">⚡</div>
        <div>
          <div class="stat-pill-val">{working}</div>
          <div class="stat-pill-lbl">Working</div>
        </div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-icon spi-gray">💤</div>
        <div>
          <div class="stat-pill-val">{idle}</div>
          <div class="stat-pill-lbl">Idle</div>
        </div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-icon spi-red">🎯</div>
        <div>
          <div class="stat-pill-val">{findings}</div>
          <div class="stat-pill-lbl">Findings So Far</div>
        </div>
      </div>
    </div>"""


def _agent_card(agent: dict) -> str:
    name    = agent["name"]
    status  = agent["status"]
    pct     = agent.get("progress", 0)
    desc    = agent.get("description", "")
    started = agent.get("started", "—")
    time    = agent.get("last_activity", "—")
    high    = agent.get("high", 0)
    medium  = agent.get("medium", 0)
    low     = agent.get("low", 0)
    total_f = agent.get("findings", 0)
    icon    = _icon(name)

    is_working = status == "working"

    # status pill
    if is_working:
        pill = '<span class="status-pill sp-working"><div class="spinner"></div>Working</span>'
    elif status == "error":
        pill = '<span class="status-pill sp-error">● Error</span>'
    else:
        pill = '<span class="status-pill sp-idle">● Idle</span>'

    # progress bar
    bar_cls  = "pbar-active" if is_working else "pbar-idle"
    pbar     = f"""
    <div>
      <div class="pbar-label">
        <span>Progress</span><span>{pct}%</span>
      </div>
      <div class="pbar-bg">
        <div class="pbar-fill {bar_cls}" style="width:{pct}%"></div>
      </div>
    </div>"""

    # findings badges
    if total_f > 0:
        badges = '<div class="findings-badges">'
        if high:   badges += f'<span class="fbadge fb-h">H:{high}</span>'
        if medium: badges += f'<span class="fbadge fb-m">M:{medium}</span>'
        if low:    badges += f'<span class="fbadge fb-l">L:{low}</span>'
        badges += '</div>'
    else:
        badges = '<span class="fb-none">No findings yet</span>'

    # pulse line when working
    pulse = '<div class="pulse-line"></div>' if is_working else ''

    # started row
    started_html = f'<div class="agent-time">Started: {started}</div>' if is_working else f'<div class="agent-time">Last active: {time}</div>'

    working_cls = "working" if is_working else ""

    return f"""
    <div class="agent-card {working_cls}">
      <div class="agent-card-top">
        <div>
          <div class="agent-name-row">
            <span class="agent-icon">{icon}</span>
            <span class="agent-name">{name}</span>
          </div>
          <div class="agent-desc">{desc}</div>
        </div>
        {pill}
      </div>
      {pbar}
      <div class="findings-row">
        {badges}
        {started_html}
      </div>
      {pulse}
    </div>"""


def _agents_grid(agents: list) -> str:
    working = [a for a in agents if a["status"] == "working"]
    idle    = [a for a in agents if a["status"] != "working"]

    html = ""

    if working:
        w_count = len(working)
        html += f"""
        <div class="group-divider">
          ⚡ Active
          <span class="divider-count">{w_count}</span>
        </div>
        <div class="agents-grid">
          {"".join(_agent_card(a) for a in working)}
        </div>"""

    if idle:
        i_count = len(idle)
        html += f"""
        <div class="group-divider">
          💤 Idle
          <span class="divider-count">{i_count}</span>
        </div>
        <div class="agents-grid">
          {"".join(_agent_card(a) for a in idle)}
        </div>"""

    return html


def _activity_feed(feed: list) -> str:
    level_cls = {"high": "fd-high", "medium": "fd-medium", "info": "fd-info"}

    items = ""
    for entry in feed:
        dot_cls = level_cls.get(entry.get("level", "info"), "fd-info")
        items += f"""
        <div class="feed-item">
          <div class="feed-item-top">
            <div class="feed-dot {dot_cls}"></div>
            <span class="feed-agent">{entry['agent']}</span>
            <span class="feed-time">{entry['time']}</span>
          </div>
          <div class="feed-event">{entry['event']}</div>
        </div>"""

    return f"""
    <div class="feed-card">
      <div class="feed-header">
        <div class="feed-title">Activity Feed</div>
        <div class="feed-live"><div class="live-dot"></div>Live</div>
      </div>
      <div class="feed-body">{items}</div>
    </div>"""


def _build_page(agents: list, feed: list) -> str:
    working_count = sum(1 for a in agents if a["status"] == "working")
    btn_disabled  = "" if working_count > 0 else "disabled"

    return f"""
    <div class="page-header">
      <div class="page-title">Agents</div>
      <button class="run-btn" {btn_disabled} onclick="alert('Start scan from the Scan page first')">
        ▶ Run All Agents
      </button>
    </div>

    {_stat_bar(agents)}

    <div class="agents-main">
      <div>{_agents_grid(agents)}</div>
      {_activity_feed(feed)}
    </div>
    """


# ── RENDER ────────────────────────────────────────────────────────────────────
def render() -> None:
    from styles.theme import get_css_tokens, get_initial_theme
    from components.layout import render_layout

    agents = _MOCK_AGENTS
    feed   = _MOCK_FEED

    page_html = f"""
    <style>{_CSS}</style>
    {_build_page(agents, feed)}
    """

    render_layout(
        active_page="agents",
        page_content_html=page_html,
        height=980,
    )