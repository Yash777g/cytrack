"""
frontend/pages/scan.py
───────────────────────
Scan page — URL input, config options, start button, live log terminal.

Layout:
  ┌─────────────────────────────────────────────────────┐
  │  Page title + status badge                          │
  ├────────────────────────┬────────────────────────────┤
  │  Scan Config Card      │  Live Log Terminal         │
  │  - Target URL          │  (scrolling log output)    │
  │  - Scan Depth          │                            │
  │  - Timeout             │                            │
  │  - Agent toggles       │                            │
  │  - Start / Stop btn    │                            │
  └────────────────────────┴────────────────────────────┘
"""

import streamlit as st
from components.layout import render_layout

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """
.page-title {
  font-size: 22px; font-weight: 700;
  color: var(--text-p); margin-bottom: 6px;
}
.page-sub {
  font-size: 13px; color: var(--text-s); margin-bottom: 20px;
}

/* status badge */
.scan-status-row {
  display: flex; align-items: center; gap: 10px; margin-bottom: 20px;
}
.status-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
}
.sb-idle    { background: var(--pbar-bg); color: var(--text-m); }
.sb-running { background: #dcfce7; color: #16a34a; }
.sb-done    { background: #eff6ff; color: #3b82f6; }
.sb-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.sb-running .sb-dot { animation: blink 1.2s infinite; }

/* main grid */
.scan-grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 20px;
  align-items: start;
}

/* config card */
.config-card {
  background: var(--bg-card);
  border-radius: 14px; padding: 24px;
  border: 1px solid var(--border-card);
  box-shadow: var(--card-shadow);
  display: flex; flex-direction: column; gap: 18px;
}
.config-title {
  font-size: 15px; font-weight: 600;
  color: var(--text-p); margin-bottom: 2px;
}
.field-label {
  font-size: 12px; font-weight: 500;
  color: var(--text-s); margin-bottom: 6px;
  display: block;
}
.field-input {
  width: 100%; padding: 10px 14px;
  background: var(--pbar-bg);
  border: 1px solid var(--border);
  border-radius: 8px; font-size: 13px;
  color: var(--text-p); font-family: 'Inter', sans-serif;
  outline: none; transition: border-color 0.2s;
  box-sizing: border-box;
}
.field-input:focus { border-color: #3b82f6; }
.field-input::placeholder { color: var(--text-m); }

/* depth + timeout row */
.config-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
}
.field-select {
  width: 100%; padding: 10px 14px;
  background: var(--pbar-bg); border: 1px solid var(--border);
  border-radius: 8px; font-size: 13px; color: var(--text-p);
  font-family: 'Inter', sans-serif; outline: none;
  cursor: pointer; transition: border-color 0.2s;
}
.field-select:focus { border-color: #3b82f6; }

/* agent toggles */
.agents-section-title {
  font-size: 12px; font-weight: 600;
  color: var(--text-s); margin-bottom: 10px;
  text-transform: uppercase; letter-spacing: .8px;
}
.agent-toggles {
  display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
}
.agent-toggle {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; border-radius: 8px;
  background: var(--pbar-bg); border: 1px solid var(--border);
  cursor: pointer; transition: all 0.15s; user-select: none;
}
.agent-toggle.selected {
  background: rgba(59,91,219,0.12);
  border-color: #3b5bdb;
}
.agent-toggle-icon { font-size: 14px; }
.agent-toggle-name {
  font-size: 12px; font-weight: 500;
  color: var(--text-s);
}
.agent-toggle.selected .agent-toggle-name { color: #3b82f6; }
.toggle-check {
  margin-left: auto; width: 16px; height: 16px;
  border-radius: 4px; border: 1.5px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; flex-shrink: 0;
}
.agent-toggle.selected .toggle-check {
  background: #3b5bdb; border-color: #3b5bdb; color: #fff;
}

/* start / stop button */
.start-btn {
  width: 100%; padding: 12px;
  background: linear-gradient(135deg, #3b5bdb, #3b82f6);
  color: #fff; border: none; border-radius: 10px;
  font-size: 14px; font-weight: 600;
  font-family: 'Inter', sans-serif;
  cursor: pointer; transition: opacity 0.2s;
  display: flex; align-items: center;
  justify-content: center; gap: 8px;
}
.start-btn:hover { opacity: 0.9; }
.stop-btn {
  width: 100%; padding: 12px;
  background: #fef2f2; color: #dc2626;
  border: 1px solid #fca5a5; border-radius: 10px;
  font-size: 14px; font-weight: 600;
  font-family: 'Inter', sans-serif;
  cursor: pointer; transition: opacity 0.2s;
  display: flex; align-items: center;
  justify-content: center; gap: 8px;
}
.stop-btn:hover { opacity: 0.85; }

/* log terminal */
.log-card {
  background: var(--bg-card);
  border-radius: 14px;
  border: 1px solid var(--border-card);
  box-shadow: var(--card-shadow);
  overflow: hidden;
}
.log-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center;
  justify-content: space-between;
}
.log-title {
  font-size: 14px; font-weight: 600; color: var(--text-p);
  display: flex; align-items: center; gap: 8px;
}
.log-live {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; color: #22c55e; font-weight: 500;
}
@keyframes blink2 { 0%,100%{opacity:1} 50%{opacity:.2} }
.log-live-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #22c55e; animation: blink2 1.2s infinite;
}
.log-terminal {
  background: #0d1117;
  padding: 20px;
  height: 520px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.7;
}
.log-empty {
  color: #4b5563;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100%; gap: 12px; text-align: center;
}
.log-empty-icon { font-size: 36px; opacity: 0.4; }
.log-line { display: flex; gap: 12px; margin-bottom: 2px; }
.log-time { color: #6b7280; flex-shrink: 0; }
.log-agent { flex-shrink: 0; font-weight: 600; }
.log-msg { color: #d1d5db; }
.log-high   .log-agent { color: #f87171; }
.log-medium .log-agent { color: #fb923c; }
.log-info   .log-agent { color: #60a5fa; }
.log-system .log-agent { color: #a78bfa; }
.log-success .log-agent { color: #4ade80; }

/* progress bar below terminal */
.scan-progress-bar {
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  display: flex; align-items: center; gap: 14px;
}
.spb-label { font-size: 12px; color: var(--text-s); white-space: nowrap; }
.spb-bg {
  flex: 1; height: 6px; background: var(--pbar-bg);
  border-radius: 99px; overflow: hidden;
}
.spb-fill {
  height: 100%; border-radius: 99px;
  background: linear-gradient(90deg, #3b5bdb, #3b82f6);
  transition: width 0.4s ease;
}
.spb-pct { font-size: 12px; font-weight: 600; color: var(--text-p); }

@media (max-width: 900px) {
  .scan-grid { grid-template-columns: 1fr; }
  .log-terminal { height: 360px; }
}
"""

# ── MOCK LOG DATA ─────────────────────────────────────────────────────────────
_MOCK_LOGS = [
    {"time": "11:20:01", "agent": "[SYSTEM]",      "msg": "Scan initiated for target: api.example.com", "level": "system"},
    {"time": "11:20:02", "agent": "[SYSTEM]",      "msg": "Hellhound crawler starting...",               "level": "system"},
    {"time": "11:20:05", "agent": "[CRAWLER]",     "msg": "Discovered 24 endpoints, 8 open ports",       "level": "info"},
    {"time": "11:20:06", "agent": "[LLM]",         "msg": "DeepHat formatting crawler output...",        "level": "info"},
    {"time": "11:20:09", "agent": "[LLM]",         "msg": "Context ready, dispatching to CVE agents",    "level": "success"},
    {"time": "11:20:10", "agent": "[SQL Agent]",   "msg": "Starting SQL injection analysis",             "level": "info"},
    {"time": "11:20:11", "agent": "[XSS Agent]",   "msg": "Starting XSS scan on 24 endpoints",          "level": "info"},
    {"time": "11:20:12", "agent": "[SSRF Agent]",  "msg": "Probing URL parameters for SSRF",            "level": "info"},
    {"time": "11:21:03", "agent": "[SQL Agent]",   "msg": "⚠ SQLi detected in /api/users?id= param",    "level": "high"},
    {"time": "11:21:15", "agent": "[XSS Agent]",   "msg": "⚠ Reflected XSS at /search?q= endpoint",    "level": "medium"},
    {"time": "11:22:01", "agent": "[SSRF Agent]",  "msg": "⚠ SSRF vector found at /api/fetch",          "level": "high"},
    {"time": "11:22:30", "agent": "[SQL Agent]",   "msg": "Blind SQLi confirmed on /login endpoint",    "level": "high"},
    {"time": "11:23:00", "agent": "[CSRF Agent]",  "msg": "Starting CSRF token analysis",               "level": "info"},
    {"time": "11:23:45", "agent": "[SYSTEM]",      "msg": "Scan 63% complete — 5/8 targets done",       "level": "system"},
]

_AGENTS = [
    ("sql",      "🔴", "SQL"),
    ("xss",      "🟠", "XSS"),
    ("ssrf",     "🟡", "SSRF"),
    ("csrf",     "🟡", "CSRF"),
    ("idor",     "🔵", "IDOR"),
    ("sast",     "🟣", "SAST"),
    ("authz",    "🔐", "AuthZ"),
    ("nosql",    "🟤", "NoSQL"),
    ("upload",   "📁", "Upload"),
    ("password", "🔑", "PassPol"),
]

# ── BUILDERS ─────────────────────────────────────────────────────────────────

def _agent_toggles(selected: list) -> str:
    html = ""
    for key, icon, name in _AGENTS:
        sel = "selected" if key in selected else ""
        check = "✓" if key in selected else ""
        html += f"""
        <div class="agent-toggle {sel}" onclick="toggleAgent('{key}', this)">
          <span class="agent-toggle-icon">{icon}</span>
          <span class="agent-toggle-name">{name}</span>
          <span class="toggle-check">{check}</span>
        </div>"""
    return html


def _log_lines(logs: list, running: bool) -> str:
    if not logs:
        return """
        <div class="log-empty">
          <div class="log-empty-icon">⚡</div>
          <div style="color:#6b7280;font-size:13px">
            Configure your scan and press Start to begin
          </div>
        </div>"""

    lines = ""
    for entry in logs:
        cls = entry.get("level", "info")
        lines += f"""
        <div class="log-line log-{cls}">
          <span class="log-time">{entry['time']}</span>
          <span class="log-agent">{entry['agent']}</span>
          <span class="log-msg">{entry['msg']}</span>
        </div>"""

    if running:
        lines += """
        <div class="log-line log-system">
          <span class="log-time">  ···  </span>
          <span class="log-agent" style="animation:blink 1s infinite">[SCANNING]</span>
          <span class="log-msg" style="color:#4b5563">waiting for agent output...</span>
        </div>"""
    return lines


def _build_page(running: bool, progress: int, logs: list, selected_agents: list) -> str:
    status_cls  = "sb-running" if running else "sb-idle"
    status_txt  = "Scan Running" if running else "Ready"
    btn_html    = (
        '<button class="stop-btn" onclick="handleStop()">⏹ Stop Scan</button>'
        if running else
        '<button class="start-btn" onclick="handleStart()">▶ Start Scan</button>'
    )
    live_html   = (
        '<div class="log-live"><div class="log-live-dot"></div>Live</div>'
        if running else
        '<span style="font-size:11px;color:var(--text-m)">Idle</span>'
    )
    progress_bar = f"""
    <div class="scan-progress-bar">
      <span class="spb-label">Overall Progress</span>
      <div class="spb-bg"><div class="spb-fill" style="width:{progress}%"></div></div>
      <span class="spb-pct">{progress}%</span>
    </div>""" if running or progress > 0 else ""

    toggles  = _agent_toggles(selected_agents)
    log_html = _log_lines(logs, running)

    return f"""
    <div class="page-title">Scan</div>
    <div class="page-sub">Configure your target and launch a vulnerability scan</div>

    <div class="scan-status-row">
      <div class="status-badge {status_cls}">
        <div class="sb-dot"></div>{status_txt}
      </div>
      {'<span style="font-size:12px;color:var(--text-m)">Target: api.example.com &nbsp;·&nbsp; Started 11:20 AM</span>' if running else ''}
    </div>

    <div class="scan-grid">

      <!-- CONFIG CARD -->
      <div class="config-card">
        <div class="config-title">🎯 Scan Configuration</div>

        <div>
          <label class="field-label">Target URL</label>
          <input class="field-input" type="text" id="targetUrl"
            placeholder="https://target.example.com"
            value="{'https://api.example.com' if running else ''}"
            {'readonly' if running else ''}/>
        </div>

        <div class="config-row">
          <div>
            <label class="field-label">Scan Depth</label>
            <select class="field-select" id="scanDepth" {'disabled' if running else ''}>
              <option value="1">Shallow (1)</option>
              <option value="2" selected>Normal (2)</option>
              <option value="3">Deep (3)</option>
              <option value="4">Exhaustive (4)</option>
            </select>
          </div>
          <div>
            <label class="field-label">Timeout (seconds)</label>
            <select class="field-select" id="timeout" {'disabled' if running else ''}>
              <option value="30">30s</option>
              <option value="60" selected>60s</option>
              <option value="120">120s</option>
              <option value="300">300s</option>
            </select>
          </div>
        </div>

        <div>
          <div class="agents-section-title">CVE Agents to Run</div>
          <div class="agent-toggles">{toggles}</div>
        </div>

        {btn_html}
      </div>

      <!-- LOG TERMINAL -->
      <div class="log-card">
        <div class="log-header">
          <div class="log-title">
            <span>🖥️</span> Live Output
          </div>
          {live_html}
        </div>
        <div class="log-terminal" id="logTerminal">
          {log_html}
        </div>
        {progress_bar}
      </div>

    </div>
    """


# ── JS ────────────────────────────────────────────────────────────────────────
_JS = """
<script>
  // auto-scroll terminal to bottom
  const term = document.getElementById('logTerminal');
  if (term) term.scrollTop = term.scrollHeight;

  // agent toggle
  function toggleAgent(key, el) {
    el.classList.toggle('selected');
    const check = el.querySelector('.toggle-check');
    if (el.classList.contains('selected')) {
      check.textContent = '✓';
    } else {
      check.textContent = '';
    }
  }

  // start / stop — in real app these call api_client
  function handleStart() {
    const url = document.getElementById('targetUrl').value.trim();
    if (!url) {
      alert('Please enter a target URL');
      return;
    }
    // TODO: call api_client.start_scan(url) when FastAPI is ready
    alert('Scan started for: ' + url + '\\n\\n(Connect FastAPI backend to run real scans)');
  }

  function handleStop() {
    // TODO: call api_client.stop_scan(scan_id)
    alert('Scan stopped.\\n\\n(Connect FastAPI backend to stop real scans)');
  }
</script>
"""

# ── RENDER ────────────────────────────────────────────────────────────────────
def render() -> None:
    running         = st.session_state.get("scan_running", False)
    progress        = 63 if running else 0
    logs            = _MOCK_LOGS if running else []
    selected_agents = ["sql","xss","ssrf","csrf","idor","sast","authz","nosql","upload","password"]

    page_html = f"<style>{_CSS}</style>" + _build_page(running, progress, logs, selected_agents) + _JS
    render_layout(active_page="scan", page_content_html=page_html, height=880)