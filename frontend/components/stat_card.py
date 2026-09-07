"""
frontend/components/stat_card.py
Builds the HTML string for a single stat card.

Usage (inside any page's HTML string):
    from components.stat_card import stat_card, stat_cards_row

    # single card
    html = stat_card(
        icon="🤖",
        icon_color="blue",
        value="12",
        label="Active Agents",
        sub="● 3 working",
        sub_color="green",
    )

    # all 4 dashboard cards in one row
    html = stat_cards_row(stats_dict)

Icon color options : "blue" | "red" | "orange" | "green"
Sub color options  : "green" | "red" | "muted" | None
"""

# CSS 
# Injected once per page that uses stat cards.
STAT_CARD_CSS = """
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
  }

  .stat-card {
    background: var(--bg-card);
    border-radius: 14px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: var(--card-shadow);
    border: 1px solid var(--border-card);
    transition: background 0.3s, border-color 0.3s;
  }

  .stat-icon {
    width: 52px; height: 52px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; flex-shrink: 0;
    transition: background 0.3s;
  }
  .icon-blue   { background: var(--icon-blue); }
  .icon-red    { background: var(--icon-red); }
  .icon-orange { background: var(--icon-orange); }
  .icon-green  { background: var(--icon-green); }

  .stat-body  { min-width: 0; }
  .stat-val   { font-size: 28px; font-weight: 700; color: var(--text-p); line-height: 1.1; }
  .stat-lbl   { font-size: 13px; color: var(--text-s); margin-top: 3px; }
  .stat-sub   { font-size: 12px; margin-top: 4px; }

  .sub-green  { color: #22c55e; }
  .sub-red    { color: #ef4444; }
  .sub-muted  { color: var(--text-m); }

  /* progress bar variant (used by Scan Progress card) */
  .stat-pbar-bg {
    height: 6px; background: var(--pbar-bg);
    border-radius: 99px; overflow: hidden; margin-top: 8px;
    min-width: 80px;
  }
  .stat-pbar-fill {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, #f97316, #fbbf24);
    transition: width 0.4s ease;
  }

  @media (max-width: 900px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
  }
  @media (max-width: 480px) {
    .stats-grid { grid-template-columns: 1fr 1fr; }
    .stat-val   { font-size: 22px; }
  }
"""


# BUILDERS

def stat_card(
    icon: str,
    icon_color: str,       # "blue" | "red" | "orange" | "green"
    value: str,
    label: str,
    sub: str | None = None,
    sub_color: str | None = None,   # "green" | "red" | "muted"
    progress_pct: int | None = None,  # if set, renders a progress bar instead of sub
) -> str:
    """
    Returns the HTML string for one stat card.

    Args:
        icon:         Emoji icon shown in the coloured square.
        icon_color:   Background colour key for the icon box.
        value:        Large number/text shown prominently.
        label:        Smaller descriptor below the value.
        sub:          Optional small text below the label (e.g. "● 3 working").
        sub_color:    Colour class for the sub text.
        progress_pct: If provided, renders a progress bar instead of sub text.
    """
    # sub content — either a progress bar or a text line
    if progress_pct is not None:
        sub_html = f"""
        <div class="stat-pbar-bg">
          <div class="stat-pbar-fill" style="width:{progress_pct}%"></div>
        </div>"""
    elif sub:
        color_cls = f"sub-{sub_color}" if sub_color else ""
        sub_html = f'<div class="stat-sub {color_cls}">{sub}</div>'
    else:
        sub_html = ""

    return f"""
    <div class="stat-card">
      <div class="stat-icon icon-{icon_color}">{icon}</div>
      <div class="stat-body">
        <div class="stat-val">{value}</div>
        <div class="stat-lbl">{label}</div>
        {sub_html}
      </div>
    </div>"""


def stat_cards_row(stats: dict) -> str:
    """
    Builds all 4 dashboard stat cards in a grid from a stats dict.

    Expected dict keys (all from api_client.get_dashboard_stats()):
        active_agents   : int
        agents_working  : int
        targets         : int
        targets_critical: int
        scan_progress   : int   (0-100)
        reports_generated: int

    Returns the full <div class="stats-grid">...</div> HTML string.
    """
    cards_html = ""

    cards_html += stat_card(
        icon="🤖",
        icon_color="blue",
        value=str(stats.get("active_agents", 0)),
        label="Active Agents",
        sub=f"● {stats.get('agents_working', 0)} working",
        sub_color="green",
    )

    cards_html += stat_card(
        icon="🎯",
        icon_color="red",
        value=str(stats.get("targets", 0)),
        label="Targets",
        sub=f"● {stats.get('targets_critical', 0)} critical",
        sub_color="red",
    )

    cards_html += stat_card(
        icon="⚡",
        icon_color="orange",
        value=f"{stats.get('scan_progress', 0)}%",
        label="Scan Progress",
        progress_pct=stats.get("scan_progress", 0),
    )

    cards_html += stat_card(
        icon="📋",
        icon_color="green",
        value=str(stats.get("reports_generated", 0)),
        label="Reports Generated",
        sub="This Month",
        sub_color="muted",
    )

    return f'<div class="stats-grid">{cards_html}</div>'