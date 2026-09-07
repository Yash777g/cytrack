"""
frontend/components/agent_card.py
───────────────────────────────────
Builds HTML for:
  - agent_table_row()  → single row in the dashboard Agent/Working table
  - agent_table()      → full Agent/Working card (header + rows + view link)
  - agent_card()       → detailed card used on the Agents page (per-agent)

Usage:
    from components.agent_card import agent_table, AGENT_CSS
"""

from components.chart import progress_bar

# ── CSS ───────────────────────────────────────────────────────────────────────
AGENT_CSS = """
  /* ── AGENT TABLE (dashboard) ── */
  .agent-table-wrap { width: 100%; }

  .tbl-head {
    display: flex; gap: 8px;
    font-size: 11px; color: var(--text-m);
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
  }

  .agent-row {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
  }
  .agent-row:last-child { border-bottom: none; }

  .col-name {
    flex: 2; font-weight: 500; color: var(--text-p);
    display: flex; align-items: center; gap: 7px;
    min-width: 0; overflow: hidden;
  }
  .col-name span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .col-status { flex: 1.5; }
  .col-prog   { flex: 2; display: flex; align-items: center; }
  .col-time   { flex: 1.2; color: var(--text-m); font-size: 12px; text-align: right; white-space: nowrap; }

  .pill-work { color: #22c55e; font-size: 12px; font-weight: 500; white-space: nowrap; }
  .pill-idle { color: var(--text-m); font-size: 12px; font-weight: 500; white-space: nowrap; }
  .pill-err  { color: #ef4444; font-size: 12px; font-weight: 500; white-space: nowrap; }

  /* ── AGENT CARD (agents page) ── */
  .agent-card {
    background: var(--bg-card);
    border-radius: 14px; padding: 20px;
    box-shadow: var(--card-shadow);
    border: 1px solid var(--border-card);
    transition: background 0.3s, border-color 0.3s;
    display: flex; flex-direction: column; gap: 12px;
  }
  .agent-card-header {
    display: flex; align-items: center;
    justify-content: space-between; gap: 10px;
  }
  .agent-card-name {
    font-size: 14px; font-weight: 600;
    color: var(--text-p); display: flex;
    align-items: center; gap: 8px;
  }
  .agent-card-meta {
    font-size: 12px; color: var(--text-m); margin-top: 2px;
  }
  .agent-card-body { display: flex; flex-direction: column; gap: 6px; }
  .agent-card-label { font-size: 11px; color: var(--text-m); margin-bottom: 2px; }

  /* agents page grid */
  .agents-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
"""

# ── AGENT ICON MAP ────────────────────────────────────────────────────────────
# Maps agent name keywords → emoji icon
_AGENT_ICONS = {
    "sql":      "🔴",
    "xss":      "🟠",
    "ssrf":     "🟡",
    "csrf":     "🟡",
    "idor":     "🔵",
    "sast":     "🟣",
    "authz":    "🔐",
    "nosql":    "🟤",
    "upload":   "📁",
    "password": "🔑",
}

def _agent_icon(name: str) -> str:
    name_lower = name.lower()
    for key, icon in _AGENT_ICONS.items():
        if key in name_lower:
            return icon
    return "🤖"


# ── STATUS PILL ───────────────────────────────────────────────────────────────

def _status_pill(status: str) -> str:
    s = status.lower()
    if s == "working":
        return '<span class="pill-work">● Working</span>'
    elif s == "error":
        return '<span class="pill-err">● Error</span>'
    else:
        return '<span class="pill-idle">● Idle</span>'


# ── AGENT TABLE ROW ───────────────────────────────────────────────────────────

def agent_table_row(agent: dict) -> str:
    """
    Single row in the dashboard Agent/Working table.

    Expected dict keys (from api_client.get_agents()):
        name          : str
        status        : "working" | "idle" | "error"
        progress      : int  (0–100)
        last_activity : str  (e.g. "2m ago")
    """
    name     = agent.get("name", "Unknown Agent")
    status   = agent.get("status", "idle")
    pct      = agent.get("progress", 0)
    time     = agent.get("last_activity", "—")
    icon     = _agent_icon(name)

    # progress bar colour — grey when idle
    bar_color = (
        "linear-gradient(90deg,#3b82f6,#6366f1)"
        if status == "working"
        else "var(--pbar-bg)"
    )
    bar_html = progress_bar(pct, color=bar_color, show_label=True)

    return f"""
    <div class="agent-row">
      <div class="col-name">{icon}<span>{name}</span></div>
      <div class="col-status">{_status_pill(status)}</div>
      <div class="col-prog">{bar_html}</div>
      <div class="col-time">{time}</div>
    </div>"""


def agent_table(agents: list[dict], navigate_to: str = "agents") -> str:
    """
    Full Agent/Working card for the dashboard.

    Args:
        agents:      List of agent dicts (from api_client.get_agents()).
        navigate_to: Page key for "View All Agents" link.

    Returns:
        HTML string for the full card.
    """
    if not agents:
        empty = '<div style="color:var(--text-m);font-size:13px;padding:16px 0">No agents running.</div>'
        rows_html = empty
    else:
        rows_html = "".join(agent_table_row(a) for a in agents)

    return f"""
    <div class="card">
      <div class="card-title">Agent / Working</div>
      <div class="agent-table-wrap">
        <div class="tbl-head">
          <span style="flex:2">Agent Name</span>
          <span style="flex:1.5">Status</span>
          <span style="flex:2">Progress</span>
          <span style="flex:1.2;text-align:right">Last Activity</span>
        </div>
        {rows_html}
      </div>
      <a class="view-link" onclick="navigate('{navigate_to}')">View All Agents →</a>
    </div>"""


# ── AGENT CARD (agents page) ──────────────────────────────────────────────────

def agent_card(agent: dict) -> str:
    """
    Detailed card for the Agents page — one card per agent.

    Expected dict keys:
        name          : str
        status        : "working" | "idle" | "error"
        progress      : int  (0–100)
        last_activity : str
        findings      : int  (vulnerabilities found so far)
        description   : str  (short description of what this agent scans)
    """
    name        = agent.get("name",         "Unknown Agent")
    status      = agent.get("status",       "idle")
    pct         = agent.get("progress",     0)
    time        = agent.get("last_activity","—")
    findings    = agent.get("findings",     0)
    description = agent.get("description", "Scans for vulnerabilities.")
    icon        = _agent_icon(name)

    bar_color = (
        "linear-gradient(90deg,#3b82f6,#6366f1)"
        if status == "working"
        else "var(--pbar-bg)"
    )
    bar_html = progress_bar(pct, color=bar_color, show_label=True)

    findings_color = "#ef4444" if findings > 0 else "var(--text-m)"

    return f"""
    <div class="agent-card">
      <div class="agent-card-header">
        <div>
          <div class="agent-card-name">{icon} {name}</div>
          <div class="agent-card-meta">{description}</div>
        </div>
        {_status_pill(status)}
      </div>
      <div class="agent-card-body">
        <div class="agent-card-label">Progress</div>
        {bar_html}
      </div>
      <div style="display:flex;justify-content:space-between;font-size:12px;">
        <span style="color:var(--text-m)">Last active: {time}</span>
        <span style="color:{findings_color};font-weight:600">
          {findings} finding{"s" if findings != 1 else ""}
        </span>
      </div>
    </div>"""


def agents_grid(agents: list[dict]) -> str:
    """
    Renders all agent cards in a responsive grid for the Agents page.
    """
    if not agents:
        return '<div style="color:var(--text-m);font-size:13px;padding:24px 0">No agents available.</div>'
    cards_html = "".join(agent_card(a) for a in agents)
    return f'<div class="agents-grid">{cards_html}</div>'


# ── MOCK DATA ─────────────────────────────────────────────────────────────────

MOCK_AGENTS = [
    {"name": "SQL Agent",              "status": "working", "progress": 75,  "last_activity": "2m ago",  "findings": 3, "description": "Detects SQL injection vulnerabilities"},
    {"name": "XSS Agent",             "status": "working", "progress": 60,  "last_activity": "5m ago",  "findings": 2, "description": "Scans for cross-site scripting flaws"},
    {"name": "SSRF Agent",            "status": "working", "progress": 90,  "last_activity": "1m ago",  "findings": 1, "description": "Tests for server-side request forgery"},
    {"name": "CSRF Agent",            "status": "idle",    "progress": 0,   "last_activity": "10m ago", "findings": 0, "description": "Checks CSRF token implementation"},
    {"name": "IDOR Agent",            "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "description": "Tests insecure direct object references"},
    {"name": "SAST Agent",            "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "description": "Static analysis of discovered endpoints"},
    {"name": "AuthZ Agent",           "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "description": "Tests authorisation and access controls"},
    {"name": "NoSQL Agent",           "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "description": "Scans for NoSQL injection vectors"},
    {"name": "Upload Agent",          "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "description": "Tests file upload security"},
    {"name": "Password Policy Agent", "status": "idle",    "progress": 0,   "last_activity": "15m ago", "findings": 0, "description": "Audits password and auth policies"},
]