"""
frontend/components/log_stream.py
──────────────────────────────────
Live log streaming helper — renders a scrolling terminal panel
from a list of log-line dicts produced by the backend WebSocket.

Usage:
    from components.log_stream import render_log_stream
    html = render_log_stream(lines, running=True)
"""


def render_log_stream(lines: list[dict], running: bool = False) -> str:
    """
    Convert a list of log-line dicts into scrollable terminal HTML.

    Each dict may contain:
        time   (str)  – timestamp label
        agent  (str)  – source agent / component tag
        msg    (str)  – the log message
        level  (str)  – 'high' | 'medium' | 'info' | 'system' | 'success'
    """
    if not lines:
        return """
        <div class="log-empty">
          <div class="log-empty-icon">⚡</div>
          <div style="color:#6b7280;font-size:13px">
            Configure your scan and press Start to begin
          </div>
        </div>"""

    html = ""
    for entry in lines:
        cls = entry.get("level", "info")
        html += f"""
        <div class="log-line log-{cls}">
          <span class="log-time">{entry.get('time', '')}</span>
          <span class="log-agent">{entry.get('agent', '')}</span>
          <span class="log-msg">{entry.get('msg', '')}</span>
        </div>"""

    if running:
        html += """
        <div class="log-line log-system">
          <span class="log-time">  ···  </span>
          <span class="log-agent" style="animation:blink 1s infinite">[SCANNING]</span>
          <span class="log-msg" style="color:#4b5563">waiting for agent output...</span>
        </div>"""

    return html

