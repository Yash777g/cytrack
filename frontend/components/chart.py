"""
frontend/components/chart.py
Pure SVG chart builders — no Plotly, no external deps.
All functions return HTML strings ready to embed in any component.

Available charts:
  - donut_chart()     → scan progress ring (single value, % in center)
  - pie_chart()       → report severity breakdown (multi-segment donut)
  - sparkline()       → estimated time area chart
  - progress_bar()    → horizontal bar (used in agent table + vuln list)

Usage:
    from components.chart import donut_chart, pie_chart, sparkline, CHART_CSS
"""

import math


# CSS
CHART_CSS = """
  /* ── donut / pie wrapper ── */
  .donut-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 8px 0 16px;
    position: relative;
  }
  .donut-center {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    pointer-events: none;
  }
  .donut-pct {
    font-size: 22px; font-weight: 700;
    color: var(--text-p); line-height: 1;
  }
  .donut-lbl {
    font-size: 11px; color: var(--text-m);
    margin-top: 3px;
  }

  /* ── pie legend ── */
  .pie-legend { font-size: 12px; color: var(--text-s); }
  .pie-legend-row {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 5px;
  }
  .pie-legend-dot {
    display: inline-block;
    width: 9px; height: 9px;
    border-radius: 50%; margin-right: 6px;
    flex-shrink: 0;
  }

  /* ── sparkline ── */
  .sparkline-wrap { margin-top: 12px; width: 100%; }

  /* ── inline progress bar ── */
  .pbar-wrap  { display: flex; align-items: center; gap: 6px; flex: 1; }
  .pbar-bg    {
    flex: 1; height: 6px; background: var(--pbar-bg);
    border-radius: 99px; overflow: hidden;
  }
  .pbar-fill  { height: 100%; border-radius: 99px; }
  .pbar-pct   { font-size: 12px; color: var(--text-s); width: 32px; text-align: right; }
"""


# HELPERS

def _circle_point(cx: float, cy: float, r: float, angle_deg: float) -> tuple[float, float]:
    """Returns (x, y) on a circle given centre, radius, and angle in degrees."""
    rad = math.radians(angle_deg - 90)   # -90 so 0° starts at top
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _svg_arc_path(cx, cy, r, start_deg, end_deg) -> str:
    """
    Builds an SVG arc path string for use with stroke-dasharray approach.
    Not used directly — kept for reference. We use stroke-dasharray instead
    because it works cleanly with CSS transitions.
    """
    x1, y1 = _circle_point(cx, cy, r, start_deg)
    x2, y2 = _circle_point(cx, cy, r, end_deg)
    large  = 1 if (end_deg - start_deg) > 180 else 0
    return f"M {x1:.2f} {y1:.2f} A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f}"


# DONUT CHART

def donut_chart(
    pct: int,
    size: int = 160,
    stroke: int = 16,
    color: str = "#3b5bdb",
    center_text: str | None = None,
    center_sub: str = "Overall Progress",
) -> str:
    """
    Single-value donut ring chart.

    Args:
        pct:         Fill percentage (0–100).
        size:        SVG width & height in px.
        stroke:      Ring stroke width in px.
        color:       Fill colour of the progress arc.
        center_text: Text shown in the centre (defaults to "{pct}%").
        center_sub:  Smaller label under the center text.

    Returns:
        HTML string containing the SVG wrapped in .donut-wrap.
    """
    r           = (size / 2) - (stroke / 2)
    cx = cy     = size / 2
    circumf     = 2 * math.pi * r
    filled      = circumf * (pct / 100)
    empty       = circumf - filled
    label       = center_text if center_text is not None else f"{pct}%"

    return f"""
    <div class="donut-wrap">
      <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
        <!-- track ring -->
        <circle
          cx="{cx}" cy="{cy}" r="{r:.2f}"
          fill="none"
          stroke="var(--pbar-bg)"
          stroke-width="{stroke}"/>
        <!-- progress arc -->
        <circle
          cx="{cx}" cy="{cy}" r="{r:.2f}"
          fill="none"
          stroke="{color}"
          stroke-width="{stroke}"
          stroke-dasharray="{filled:.2f} {empty:.2f}"
          stroke-linecap="round"
          transform="rotate(-90 {cx} {cy})"/>
      </svg>
      <div class="donut-center">
        <div class="donut-pct">{label}</div>
        <div class="donut-lbl">{center_sub}</div>
      </div>
    </div>"""


# PIE CHART (multi-segment donut)

def pie_chart(
    segments: list[dict],
    size: int = 140,
    stroke: int = 20,
    center_value: str = "",
    center_label: str = "Reports",
    show_legend: bool = True,
) -> str:
    """
    Multi-segment donut (pie) chart using SVG stroke-dasharray.

    Args:
        segments: List of dicts with keys:
                    label  : str   — legend label
                    value  : int   — raw count
                    color  : str   — hex colour
                    pct    : float — percentage (0–100)
        size:         SVG size in px.
        stroke:       Ring stroke width in px.
        center_value: Bold text in centre (e.g. "18").
        center_label: Small text below centre value.
        show_legend:  Whether to render the legend below.

    Returns:
        HTML string with SVG + optional legend.
    """
    r       = (size / 2) - (stroke / 2)
    cx = cy = size / 2
    circumf = 2 * math.pi * r

    # build segments — each offset from the last
    circles_html = ""
    offset = 0.0
    for seg in segments:
        filled  = circumf * (seg["pct"] / 100)
        empty   = circumf - filled
        circles_html += f"""
        <circle
          cx="{cx}" cy="{cy}" r="{r:.2f}"
          fill="none"
          stroke="{seg['color']}"
          stroke-width="{stroke}"
          stroke-dasharray="{filled:.2f} {empty:.2f}"
          stroke-dashoffset="{-offset:.2f}"
          transform="rotate(-90 {cx} {cy})"/>"""
        offset += filled

    # legend
    legend_html = ""
    if show_legend:
        rows = ""
        for seg in segments:
            rows += f"""
            <div class="pie-legend-row">
              <span>
                <span class="pie-legend-dot" style="background:{seg['color']}"></span>
                {seg['label']}
              </span>
              <span>{seg['value']} ({seg['pct']:.0f}%)</span>
            </div>"""
        legend_html = f'<div class="pie-legend">{rows}</div>'

    return f"""
    <div class="donut-wrap">
      <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
        {circles_html}
      </svg>
      <div class="donut-center">
        <div class="donut-pct" style="font-size:18px">{center_value}</div>
        <div class="donut-lbl">{center_label}</div>
      </div>
    </div>
    {legend_html}"""


# SPARKLINE

def sparkline(
    values: list[float],
    width: int = 220,
    height: int = 70,
    color: str = "#3b5bdb",
    fill_opacity: float = 0.25,
) -> str:
    """
    Area sparkline chart built with SVG path.

    Args:
        values:       List of y values (auto-normalised to fit height).
        width:        SVG viewBox width.
        height:       SVG viewBox height.
        color:        Line and fill colour.
        fill_opacity: Opacity of the area fill at the top.

    Returns:
        HTML string containing the SVG wrapped in .sparkline-wrap.
    """
    if not values or len(values) < 2:
        return ""

    n      = len(values)
    lo, hi = min(values), max(values)
    rng    = hi - lo if hi != lo else 1

    # map values to SVG coords (y inverted — SVG 0 is top)
    pad = height * 0.1
    def to_x(i):   return (i / (n - 1)) * width
    def to_y(v):   return height - pad - ((v - lo) / rng) * (height - 2 * pad)

    pts       = [(to_x(i), to_y(v)) for i, v in enumerate(values)]
    line_d    = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    fill_d    = line_d + f" L {pts[-1][0]:.2f},{height} L {pts[0][0]:.2f},{height} Z"
    grad_id   = "sg_" + str(abs(hash(str(values))))[:6]

    return f"""
    <div class="sparkline-wrap">
      <svg width="100%" height="{height}"
           viewBox="0 0 {width} {height}"
           preserveAspectRatio="none">
        <defs>
          <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stop-color="{color}" stop-opacity="{fill_opacity}"/>
            <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <path d="{fill_d}" fill="url(#{grad_id})"/>
        <path d="{line_d}" fill="none" stroke="{color}"
              stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
      </svg>
    </div>"""


# PROGRESS BAR

def progress_bar(
    pct: int,
    color: str = "linear-gradient(90deg, #3b82f6, #6366f1)",
    show_label: bool = True,
) -> str:
    """
    Inline horizontal progress bar.
    Used in the agent table and vulnerability list.

    Args:
        pct:        Fill percentage (0–100).
        color:      CSS background for the fill (hex or gradient string).
        show_label: Whether to show the % number to the right.

    Returns:
        HTML string for the bar (no outer wrapper — caller provides flex row).
    """
    label_html = f'<span class="pbar-pct">{pct}%</span>' if show_label else ""
    return f"""
    <div class="pbar-wrap">
      <div class="pbar-bg">
        <div class="pbar-fill" style="width:{pct}%;background:{color}"></div>
      </div>
      {label_html}
    </div>"""


# PRESET DATA BUILDERS
# Convenience functions that accept api_client dicts and return ready-to-use HTML.

def scan_progress_donut(scan_data: dict) -> str:
    """
    Builds the scan progress donut from api_client.get_scan_status() dict.
    Expected keys: overall_progress (int), targets_scanned (int), total_targets (int),
                   running_agents (int), estimated_minutes (int)
    """
    pct = scan_data.get("overall_progress", 0)
    return donut_chart(pct=pct, size=160, color="#3b5bdb", center_sub="Overall Progress")


def report_pie_chart(report_data: dict) -> str:
    """
    Builds the 7-day report severity pie from api_client data.
    Expected keys: high (int), medium (int), low (int), info (int)
    """
    high   = report_data.get("high",   6)
    medium = report_data.get("medium", 7)
    low    = report_data.get("low",    4)
    info   = report_data.get("info",   1)
    total  = high + medium + low + info or 1

    segments = [
        {"label": "High",   "value": high,   "color": "#ef4444", "pct": high   / total * 100},
        {"label": "Medium", "value": medium, "color": "#f97316", "pct": medium / total * 100},
        {"label": "Low",    "value": low,    "color": "#eab308", "pct": low    / total * 100},
        {"label": "Info",   "value": info,   "color": "#3b82f6", "pct": info   / total * 100},
    ]
    return pie_chart(
        segments=segments,
        size=140,
        stroke=20,
        center_value=str(total),
        center_label="Reports",
    )


def estimated_time_sparkline() -> str:
    """
    Builds the estimated time sparkline with mock trend data.
    Replace values with real historical data from api_client when available.
    """
    values = [0.35, 0.42, 0.38, 0.50, 0.48, 0.60, 0.58, 0.70, 0.75, 0.82]
    return sparkline(values=values, color="#3b5bdb")