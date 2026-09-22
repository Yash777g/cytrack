"""
frontend/pages/dashboard.py
─────────────────────────────
CyTrack Dashboard page — assembles all components into the full dashboard view.

Layout:
  ┌─────────────────────────────────────────────────┐
  │  [stat cards row — 4 cards]                     │
  ├──────────────────┬──────────────┬───────────────┤
  │  Agent / Working │ Scan Progress│ Scan Report   │
  │  (table)         │ (donut)      │ (pie + legend)│
  ├──────────────────┴──────────────┴───────────────┤
  │  Recent Alerts   │ Top Vulns    │ Est. Time     │
  └──────────────────┴──────────────┴───────────────┘

Called by app.py via:
    from pages.dashboard import render
    render()
"""

import streamlit as st

from components.layout    import render_layout
from components.stat_card import stat_cards_row, STAT_CARD_CSS
from components.chart     import (
    scan_progress_donut,
    report_pie_chart,
    estimated_time_sparkline,
    CHART_CSS,
)
from components.agent_card  import agent_table,  AGENT_CSS
from components.alert_feed  import alert_feed, vuln_list, ALERT_CSS




# ── PAGE CSS ──────────────────────────────────────────────────────────────────

_PAGE_CSS = """
  /* ── page title ── */
  .page-title {
    font-size: 22px; font-weight: 700;
    color: var(--text-p); margin-bottom: 20px;
  }

  /* ── mid + bottom grid ── */
  .dash-grid {
    display: grid;
    grid-template-columns: 2.2fr 1.8fr 1.5fr;
    gap: 16px;
    margin-bottom: 20px;
  }

  /* ── scan progress stats below donut ── */
  .scan-stats {
    display: flex; gap: 20px;
    flex-wrap: wrap; margin-top: 4px;
  }
  .ss-lbl { font-size: 11px; color: var(--text-m); margin-bottom: 2px; }
  .ss-val { font-size: 14px; font-weight: 600; color: var(--text-p); }

  /* ── estimated time hero ── */
  .time-hero {
    display: flex; align-items: center;
    gap: 12px; margin-bottom: 6px;
  }
  .time-val { font-size: 24px; font-weight: 700; color: var(--text-p); }
  .time-sub { font-size: 11px; color: var(--text-m); }
  .time-note { font-size: 11px; color: var(--text-m); margin-bottom: 10px; }

  /* ── responsive ── */
  @media (max-width: 1024px) {
    .dash-grid { grid-template-columns: 1fr 1fr; }
  }
  @media (max-width: 640px) {
    .dash-grid { grid-template-columns: 1fr; }
  }
"""


# ── SECTION BUILDERS ──────────────────────────────────────────────────────────

def _scan_progress_card(scan: dict) -> str:
    targets_scanned  = scan.get("targets_scanned",  5)
    total_targets    = scan.get("total_targets",     8)
    running_agents   = scan.get("running_agents",    3)
    est_mins         = scan.get("estimated_minutes", 85)
    hrs, mins        = divmod(est_mins, 60)
    est_str          = f"{hrs}h {mins}m" if hrs else f"{mins}m"

    donut_html = scan_progress_donut(scan)

    return f"""
    <div class="card">
      <div class="card-title">Scan Progress</div>
      {donut_html}
      <div class="scan-stats">
        <div>
          <div class="ss-lbl">Targets Scanned</div>
          <div class="ss-val">{targets_scanned} / {total_targets}</div>
        </div>
        <div>
          <div class="ss-lbl">Running Agents</div>
          <div class="ss-val">{running_agents}</div>
        </div>
        <div>
          <div class="ss-lbl">Estimated Time</div>
          <div class="ss-val">{est_str} remaining</div>
        </div>
      </div>
      <a class="view-link" onclick="navigate('scan')">View Scan Details →</a>
    </div>"""


def _report_card(breakdown: dict) -> str:
    pie_html = report_pie_chart(breakdown)
    return f"""
    <div class="card">
      <div class="card-title">Scan Report<br>Last 7 Days</div>
      {pie_html}
      <a class="view-link" onclick="navigate('reports')">View All Reports →</a>
    </div>"""


def _estimated_time_card(scan: dict) -> str:
    est_mins  = scan.get("estimated_minutes", 85)
    hrs, mins = divmod(est_mins, 60)
    est_str   = f"{hrs}h {mins}m" if hrs else f"{mins}m"
    spark     = estimated_time_sparkline()

    return f"""
    <div class="card">
      <div class="card-title">Estimated Time</div>
      <div class="time-hero">
        <span style="font-size:28px">🕐</span>
        <div>
          <div class="time-val">{est_str}</div>
          <div class="time-sub">remaining</div>
        </div>
      </div>
      <div class="time-note">Based on current scan progress</div>
      {spark}
    </div>"""


# ── MAIN BUILDER ──────────────────────────────────────────────────────────────

def _build_dashboard_html() -> str:
    """
    Assembles the full dashboard inner HTML.
    Swap MOCK_* constants for api_client calls here when FastAPI is ready.
    Assembles the full dashboard inner HTML from live backend data.
    """
    import api_client

    # ── live data from api_client ──
    stats     = api_client.get_dashboard_stats()
    scan      = api_client.get_scan_progress_data()
    breakdown = api_client.get_report_breakdown()
    agents    = api_client.get_agents()[:5]
    alerts    = api_client.get_recent_alerts()
    vulns     = api_client.get_top_vulns()

    # ── build each section ──
    stat_row          = stat_cards_row(stats)
    agent_tbl         = agent_table(agents)
    scan_card         = _scan_progress_card(scan)
    report_card_html  = _report_card(breakdown)
    alerts_card       = alert_feed(alerts)
    vulns_card        = vuln_list(vulns)
    time_card         = _estimated_time_card(scan)

    return f"""
    <style>
      {_PAGE_CSS}
    </style>

    <div class="page-title">Dashboard</div>

    <!-- STAT CARDS -->
    {stat_row}

    <!-- MIDDLE ROW: agent table | scan donut | report pie -->
    <div class="dash-grid">
      {agent_tbl}
      {scan_card}
      {report_card_html}
    </div>

    <!-- BOTTOM ROW: alerts | vulns | est time -->
    <div class="dash-grid">
      {alerts_card}
      {vulns_card}
      {time_card}
    </div>
    """


# ── RENDER (called by app.py) ─────────────────────────────────────────────────

def render() -> None:
    """
    Entry point called by app.py.
    Builds the dashboard HTML and passes it to render_layout().
    """
    # collect all CSS into one block to avoid duplicates
    all_css = f"""
    <style>
      {STAT_CARD_CSS}
      {CHART_CSS}
      {AGENT_CSS}
      {ALERT_CSS}
    </style>
    """

    page_html = all_css + _build_dashboard_html()

    render_layout(
        active_page="dashboard",
        page_content_html=page_html,
        height=950,
    )