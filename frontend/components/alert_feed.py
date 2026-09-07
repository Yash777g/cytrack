"""
frontend/components/alert_feed.py
───────────────────────────────────
Builds HTML for:
  - alert_row()        → single Recent Alert row (badge + title + target + time)
  - alert_feed()       → full Recent Alerts card (list + view link)
  - vuln_row()         → single Top Vulnerability row (rank + bar + count)
  - vuln_list()        → full Top Vulnerabilities card

Usage:
    from components.alert_feed import alert_feed, vuln_list, ALERT_CSS
"""

# ── CSS ───────────────────────────────────────────────────────────────────────
ALERT_CSS = """
  /* ── SECTION CARD (shared) ── */
  .card {
    background: var(--bg-card);
    border-radius: 14px;
    padding: 20px;
    box-shadow: var(--card-shadow);
    border: 1px solid var(--border-card);
    transition: background 0.3s, border-color 0.3s;
  }
  .card-title {
    font-size: 15px; font-weight: 600;
    color: var(--text-p); margin-bottom: 16px;
  }
  .view-link {
    display: block; text-align: center;
    margin-top: 14px; color: var(--accent);
    font-size: 13px; font-weight: 500; cursor: pointer;
  }
  .view-link:hover { text-decoration: underline; }

  /* ── ALERT ROWS ── */
  .alert-row {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
  }
  .alert-row:last-child { border-bottom: none; }

  .badge {
    padding: 3px 9px; border-radius: 6px;
    font-size: 10px; font-weight: 700;
    letter-spacing: .5px; flex-shrink: 0;
    white-space: nowrap;
  }
  .b-high   { background: var(--alert-hi-bg); color: var(--alert-hi-c); }
  .b-medium { background: var(--alert-md-bg); color: var(--alert-md-c); }
  .b-low    { background: var(--alert-lo-bg); color: var(--alert-lo-c); }
  .b-info   { background: #eff6ff;            color: #3b82f6; }

  .alert-info   { flex: 1; min-width: 0; }
  .alert-title  { font-weight: 500; color: var(--text-p);
                  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .alert-target { font-size: 11px; color: var(--text-m); margin-top: 2px; }
  .alert-time   { font-size: 11px; color: var(--text-m); flex-shrink: 0; }

  /* ── VULN ROWS ── */
  .vuln-row {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 0; font-size: 13px;
  }
  .vrank {
    width: 22px; height: 22px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; color: #fff;
    flex-shrink: 0;
  }
  .vname { flex: 2; font-weight: 500; color: var(--text-p); min-width: 0; }
  .vbar-bg {
    flex: 3; height: 6px; background: var(--pbar-bg);
    border-radius: 99px; overflow: hidden;
  }
  .vbar-fill { height: 100%; border-radius: 99px; }
  .vcnt { font-weight: 600; color: var(--text-p); width: 20px; text-align: right; }
"""

# ── SEVERITY CONFIG ───────────────────────────────────────────────────────────
_SEVERITY = {
    "HIGH":   ("b-high",   "#ef4444"),
    "MEDIUM": ("b-medium", "#f97316"),
    "LOW":    ("b-low",    "#22c55e"),
    "INFO":   ("b-info",   "#3b82f6"),
}

# vuln rank colours — index 0 = rank 1
_RANK_COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6"]


# ── ALERT ROW ─────────────────────────────────────────────────────────────────

def alert_row(alert: dict) -> str:
    """
    Single alert row HTML.

    Expected dict keys:
        severity : "HIGH" | "MEDIUM" | "LOW" | "INFO"
        title    : str
        target   : str   (e.g. "api.example.com")
        time     : str   (e.g. "2m ago")
    """
    sev       = alert.get("severity", "INFO").upper()
    badge_cls, _ = _SEVERITY.get(sev, ("b-info", "#3b82f6"))
    title     = alert.get("title",  "Unknown alert")
    target    = alert.get("target", "")
    time      = alert.get("time",   "")

    return f"""
    <div class="alert-row">
      <span class="badge {badge_cls}">{sev}</span>
      <div class="alert-info">
        <div class="alert-title">{title}</div>
        <div class="alert-target">Target: {target}</div>
      </div>
      <div class="alert-time">{time}</div>
    </div>"""


def alert_feed(alerts: list[dict], navigate_to: str = "reports") -> str:
    """
    Full Recent Alerts card.

    Args:
        alerts:      List of alert dicts (from api_client.get_recent_alerts()).
        navigate_to: Page key the "View All Alerts" link navigates to.

    Returns:
        HTML string for the full card including title and view link.
    """
    if not alerts:
        empty = '<div style="color:var(--text-m);font-size:13px;padding:12px 0">No recent alerts.</div>'
        rows_html = empty
    else:
        rows_html = "".join(alert_row(a) for a in alerts)

    return f"""
    <div class="card">
      <div class="card-title">Recent Alerts</div>
      {rows_html}
      <a class="view-link" onclick="navigate('{navigate_to}')">View All Alerts →</a>
    </div>"""


# ── VULN ROW ──────────────────────────────────────────────────────────────────

def vuln_row(vuln: dict, rank: int) -> str:
    """
    Single vulnerability row HTML.

    Expected dict keys:
        name  : str   (e.g. "SQL Injection")
        count : int
        max_count: int  (used to calculate bar width relative to top vuln)
    """
    name      = vuln.get("name",  "Unknown")
    count     = vuln.get("count", 0)
    max_count = vuln.get("max_count", count) or 1
    pct       = int((count / max_count) * 100)
    color     = _RANK_COLORS[min(rank - 1, len(_RANK_COLORS) - 1)]

    return f"""
    <div class="vuln-row">
      <div class="vrank" style="background:{color}">{rank}</div>
      <div class="vname">{name}</div>
      <div class="vbar-bg">
        <div class="vbar-fill" style="width:{pct}%;background:{color}"></div>
      </div>
      <div class="vcnt">{count}</div>
    </div>"""


def vuln_list(vulns: list[dict], navigate_to: str = "reports") -> str:
    """
    Full Top Vulnerabilities card.

    Args:
        vulns:       List of vuln dicts (from api_client.get_top_vulns()).
                     Each dict needs: name, count.
                     max_count is auto-calculated from the first item.
        navigate_to: Page key for "View Full Report" link.

    Returns:
        HTML string for the full card.
    """
    if not vulns:
        empty = '<div style="color:var(--text-m);font-size:13px;padding:12px 0">No vulnerabilities found.</div>'
        return f"""
        <div class="card">
          <div class="card-title">Top Vulnerabilities</div>
          {empty}
        </div>"""

    # attach max_count to every item (based on the highest count in the list)
    max_count = max(v.get("count", 0) for v in vulns)
    enriched  = [{**v, "max_count": max_count} for v in vulns]

    rows_html = "".join(vuln_row(v, i + 1) for i, v in enumerate(enriched))

    return f"""
    <div class="card">
      <div class="card-title">Top Vulnerabilities</div>
      {rows_html}
      <a class="view-link" onclick="navigate('{navigate_to}')">View Full Report →</a>
    </div>"""


# ── MOCK DATA (used until api_client is wired) ────────────────────────────────

MOCK_ALERTS = [
    {"severity": "HIGH",   "title": "SQL Injection Detected",   "target": "api.example.com",    "time": "2m ago"},
    {"severity": "MEDIUM", "title": "Outdated Software Version", "target": "portal.example.com", "time": "15m ago"},
    {"severity": "LOW",    "title": "Directory Listing Enabled", "target": "test.example.com",   "time": "30m ago"},
]

MOCK_VULNS = [
    {"name": "SQL Injection",            "count": 7},
    {"name": "Cross-Site Scripting (XSS)", "count": 5},
    {"name": "Sensitive Data Exposure",  "count": 3},
    {"name": "Security Misconfiguration","count": 2},
]