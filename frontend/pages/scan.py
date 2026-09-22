"""
frontend/pages/scan.py
───────────────────────
Scan page — URL input, config options, start button, live log terminal.
Fully wired to the FastAPI backend at http://127.0.0.1:8000.

Flow:
  Start  → POST /scan/start        → returns {job_id, agent_id}
  Logs   → WS  /ws/scan?agent_id=… → streams log lines live
  Poll   → GET /scan/status?job_id=…→ updates badge / progress bar
  Stop   → POST /scan/stop          → terminates the crawl
  Reload → sessionStorage keeps job_id/agent_id so reconnect works
"""

import streamlit as st
from components.layout import render_layout

# ── BACKEND CONFIG ─────────────────────────────────────────────────────────────
_API_BASE = "http://127.0.0.1:8000"
_WS_BASE  = "ws://127.0.0.1:8000"

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
.sb-idle    { background: var(--pbar-bg);  color: var(--text-m); }
.sb-running { background: #dcfce7; color: #16a34a; }
.sb-done    { background: #eff6ff; color: #3b82f6; }
.sb-stop    { background: #fef9c3; color: #a16207; }
.sb-fail    { background: #fef2f2; color: #dc2626; }
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

/* connection error banner */
.conn-error {
  background: #fef2f2; border: 1px solid #fca5a5;
  border-radius: 10px; padding: 12px 16px;
  font-size: 13px; color: #dc2626; font-weight: 500;
  display: none; align-items: center; gap: 8px;
}
.conn-error.visible { display: flex; }

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
  display: none; align-items: center; gap: 5px;
  font-size: 11px; color: #22c55e; font-weight: 500;
}
.log-live.active { display: flex; }
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
.log-time { color: #6b7280; flex-shrink: 0; min-width: 70px; }
.log-agent { flex-shrink: 0; font-weight: 600; min-width: 90px; }
.log-msg { color: #d1d5db; word-break: break-all; }
.log-high    .log-agent { color: #f87171; }
.log-medium  .log-agent { color: #fb923c; }
.log-info    .log-agent { color: #60a5fa; }
.log-system  .log-agent { color: #a78bfa; }
.log-success .log-agent { color: #4ade80; }

/* progress bar below terminal */
.scan-progress-bar {
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  display: none; align-items: center; gap: 14px;
}
.scan-progress-bar.visible { display: flex; }
.spb-label { font-size: 12px; color: var(--text-s); white-space: nowrap; }
.spb-bg {
  flex: 1; height: 6px; background: var(--pbar-bg);
  border-radius: 99px; overflow: hidden;
}
.spb-fill {
  height: 100%; border-radius: 99px;
  background: linear-gradient(90deg, #3b5bdb, #3b82f6);
  transition: width 0.6s ease;
  width: 0%;
}
.spb-pct { font-size: 12px; font-weight: 600; color: var(--text-p); min-width: 38px; }

@media (max-width: 900px) {
  .scan-grid { grid-template-columns: 1fr; }
  .log-terminal { height: 360px; }
}
"""

# ── AGENTS ────────────────────────────────────────────────────────────────────
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

_DEFAULT_SELECTED = [k for k, _, _ in _AGENTS]


# ── BUILDERS ──────────────────────────────────────────────────────────────────

def _agent_toggles(selected: list) -> str:
    html = ""
    for key, icon, name in _AGENTS:
        sel   = "selected" if key in selected else ""
        check = "✓"        if key in selected else ""
        html += f"""
        <div class="agent-toggle {sel}" onclick="toggleAgent('{key}', this)">
          <span class="agent-toggle-icon">{icon}</span>
          <span class="agent-toggle-name">{name}</span>
          <span class="toggle-check">{check}</span>
        </div>"""
    return html


def _build_page(selected_agents: list) -> str:
    """
    Always renders the idle shell.
    JS restores any in-progress scan from sessionStorage on load.
    """
    toggles = _agent_toggles(selected_agents)

    return f"""
    <div class="page-title">Scan</div>
    <div class="page-sub">Configure your target and launch a vulnerability scan</div>

    <div class="scan-status-row">
      <div id="statusBadge" class="status-badge sb-idle">
        <div class="sb-dot"></div>
        <span id="statusTxt">Ready</span>
      </div>
      <span id="targetLabel" style="font-size:12px;color:var(--text-m)"></span>
    </div>

    <div id="connError" class="conn-error">
      ⚠️ Cannot reach backend on port 8000 — run <code>start_backend.ps1</code> first.
    </div>

    <div class="scan-grid">

      <!-- CONFIG CARD -->
      <div class="config-card">
        <div class="config-title">🎯 Scan Configuration</div>

        <div>
          <label class="field-label">Target URL</label>
          <input class="field-input" type="text" id="targetUrl"
            placeholder="https://target.example.com"/>
        </div>

        <div class="config-row">
          <div>
            <label class="field-label">Scan Depth</label>
            <select class="field-select" id="scanDepth">
              <option value="1">Shallow (1)</option>
              <option value="2" selected>Normal (2)</option>
              <option value="3">Deep (3)</option>
              <option value="4">Exhaustive (4)</option>
            </select>
          </div>
          <div>
            <label class="field-label">Timeout (seconds)</label>
            <select class="field-select" id="timeout">
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

        <div id="actionBtn">
          <button class="start-btn" onclick="handleStart()">▶ Start Scan</button>
        </div>
      </div>

      <!-- LOG TERMINAL -->
      <div class="log-card">
        <div class="log-header">
          <div class="log-title">
            <span>🖥️</span> Live Output
          </div>
          <div id="liveIndicator" class="log-live">
            <div class="log-live-dot"></div>Live
          </div>
          <span id="idleIndicator" style="font-size:11px;color:var(--text-m)">Idle</span>
        </div>
        <div class="log-terminal" id="logTerminal">
          <div class="log-empty">
            <div class="log-empty-icon">⚡</div>
            <div style="color:#6b7280;font-size:13px">
              Configure your scan and press Start to begin
            </div>
          </div>
        </div>
        <div id="progressBar" class="scan-progress-bar">
          <span class="spb-label">Overall Progress</span>
          <div class="spb-bg"><div id="pbFill" class="spb-fill"></div></div>
          <span id="pbPct" class="spb-pct">0%</span>
        </div>
      </div>

    </div>
    """


# ── JS ────────────────────────────────────────────────────────────────────────
def _build_js(api_base: str, ws_base: str) -> str:
    return f"""
<script>
/* ── CONSTANTS ─────────────────────────────────────── */
const API = '{api_base}';
const WS  = '{ws_base}';

/* ── STATE (survives Streamlit reruns via sessionStorage) ── */
let _jobId   = sessionStorage.getItem('ct_job_id')   || null;
let _agentId = sessionStorage.getItem('ct_agent_id') || null;
let _running = false;
let _ws      = null;
let _poll    = null;
let _logCount = 0;

/* ── DOM HELPERS ────────────────────────────────────── */
const $  = id => document.getElementById(id);
const term = () => $('logTerminal');

/* ── INIT ───────────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', () => {{
  if (_jobId && _agentId) {{
    reconnect();
  }} else {{
    checkBackend();
  }}
}});

async function checkBackend() {{
  try {{
    const r = await fetch(`${{API}}/health`, {{ signal: AbortSignal.timeout(3000) }});
    if (!r.ok) throw new Error();
    $('connError').classList.remove('visible');
  }} catch (_) {{
    $('connError').classList.add('visible');
  }}
}}

/* ── RECONNECT (after Streamlit rerun while scan was active) ── */
async function reconnect() {{
  try {{
    const r = await fetch(`${{API}}/scan/status?job_id=${{_jobId}}`);
    if (!r.ok) {{ clearState(); return; }}
    const data = await r.json();

    if (data.status === 'running') {{
      /* fetch backlog first */
      const lr = await fetch(`${{API}}/agents/${{_agentId}}/logs`);
      const ld = await lr.json();
      ld.lines.forEach(l => appendLogRaw(l));

      setRunning(true, data.target_url);
      openWS();
      startPoll();
    }} else {{
      /* scan finished while page was away */
      const lr = await fetch(`${{API}}/agents/${{_agentId}}/logs`);
      const ld = await lr.json();
      ld.lines.forEach(l => appendLogRaw(l));
      setDone(data.status);
      clearState();
    }}
  }} catch (_) {{ clearState(); }}
}}

/* ── START ──────────────────────────────────────────── */
async function handleStart() {{
  const url   = ($('targetUrl').value || '').trim();
  const depth = parseInt($('scanDepth').value || '2');
  if (!url) {{ alert('Please enter a target URL'); return; }}

  setBtn('<button class="start-btn" disabled style="opacity:.5;cursor:default">⏳ Starting...</button>');
  appendSysLog('Connecting to CyTrack backend...');

  try {{
    const r = await fetch(`${{API}}/scan/start`, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ target_url: url, depth: depth }})
    }});

    if (!r.ok) {{
      const msg = await r.text();
      throw new Error(`${{r.status}} ${{msg}}`);
    }}

    const data = await r.json();
    _jobId   = data.job_id;
    _agentId = data.agent_id;
    sessionStorage.setItem('ct_job_id',   _jobId);
    sessionStorage.setItem('ct_agent_id', _agentId);

    setRunning(true, url);
    appendSysLog(`Scan started — job ${{_jobId}}`);
    openWS();
    startPoll();

  }} catch (err) {{
    appendSysLog('ERROR: ' + err.message, 'high');
    setBtn('<button class="start-btn" onclick="handleStart()">▶ Start Scan</button>');
    $('connError').classList.add('visible');
  }}
}}

/* ── STOP ───────────────────────────────────────────── */
async function handleStop() {{
  if (!_jobId) {{ setDone('stopped'); return; }}
  setBtn('<button class="stop-btn" disabled style="opacity:.5;cursor:default">⏳ Stopping...</button>');
  appendSysLog('Stopping scan...');

  try {{
    await fetch(`${{API}}/scan/stop`, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ job_id: _jobId }})
    }});
  }} catch (_) {{}}

  if (_ws)   {{ _ws.close();         _ws   = null; }}
  if (_poll) {{ clearInterval(_poll); _poll = null; }}
  appendSysLog('Scan stopped.', 'medium');
  setDone('stopped');
  clearState();
}}

/* ── WEBSOCKET ──────────────────────────────────────── */
function openWS() {{
  if (_ws) {{ _ws.close(); }}
  _ws = new WebSocket(`${{WS}}/ws/scan?agent_id=${{_agentId}}`);

  _ws.onopen = () => appendSysLog('WebSocket connected — streaming live logs...');

  _ws.onmessage = e => {{
    try {{
      const d = JSON.parse(e.data);
      if (d.error) {{ appendSysLog(d.error, 'high'); return; }}
      if (d.line)  appendLogRaw(d.line);
    }} catch (_) {{}}
  }};

  _ws.onerror = () => appendSysLog('WebSocket error — reconnect in 5s...', 'medium');

  _ws.onclose = () => {{
    if (_running) {{
      /* WS closed while still running — poll to confirm final status */
      setTimeout(() => _running && checkFinalStatus(), 2000);
    }}
  }};
}}

/* ── STATUS POLLING ─────────────────────────────────── */
function startPoll() {{
  if (_poll) clearInterval(_poll);
  _poll = setInterval(async () => {{
    if (!_jobId || !_running) {{ clearInterval(_poll); return; }}
    try {{
      const r = await fetch(`${{API}}/scan/status?job_id=${{_jobId}}`);
      const d = await r.json();
      handleStatus(d.status);
    }} catch (_) {{}}
  }}, 4000);
}}

async function checkFinalStatus() {{
  if (!_jobId) return;
  try {{
    const r = await fetch(`${{API}}/scan/status?job_id=${{_jobId}}`);
    const d = await r.json();
    handleStatus(d.status);
  }} catch (_) {{}}
}}

function handleStatus(status) {{
  if (status === 'completed') {{
    if (_poll) {{ clearInterval(_poll); _poll = null; }}
    if (_ws)   {{ _ws.close();          _ws   = null; }}
    appendSysLog('✅ Scan completed successfully!', 'success');
    setProgress(100);
    setDone('completed');
    clearState();
  }} else if (status === 'failed') {{
    if (_poll) {{ clearInterval(_poll); _poll = null; }}
    appendSysLog('❌ Scan pipeline failed — check agent logs.', 'high');
    setDone('failed');
    clearState();
  }} else if (status === 'stopped') {{
    if (_poll) {{ clearInterval(_poll); _poll = null; }}
    setDone('stopped');
    clearState();
  }}
}}

/* ── UI STATE ───────────────────────────────────────── */
function setRunning(on, url) {{
  _running = on;
  const badge = $('statusBadge');
  const txt   = $('statusTxt');
  const lbl   = $('targetLabel');
  const lv    = $('liveIndicator');
  const idle  = $('idleIndicator');
  const pb    = $('progressBar');
  const urlEl = $('targetUrl');
  const depEl = $('scanDepth');

  if (on) {{
    badge.className = 'status-badge sb-running';
    if (txt)  txt.textContent  = 'Scan Running';
    if (lbl)  lbl.textContent  = url ? `Target: ${{url}}` : '';
    if (lv)   lv.classList.add('active');
    if (idle) idle.style.display = 'none';
    if (pb)   pb.classList.add('visible');
    if (urlEl) urlEl.setAttribute('readonly', true);
    if (depEl) depEl.setAttribute('disabled', true);
    setBtn('<button class="stop-btn" onclick="handleStop()">⏹ Stop Scan</button>');
  }}
}}

function setDone(finalStatus) {{
  _running = false;
  const badge = $('statusBadge');
  const txt   = $('statusTxt');
  const lbl   = $('targetLabel');
  const lv    = $('liveIndicator');
  const idle  = $('idleIndicator');
  const urlEl = $('targetUrl');
  const depEl = $('scanDepth');

  const labels = {{ completed: 'Complete', failed: 'Failed', stopped: 'Stopped' }};
  const clses  = {{ completed: 'sb-done',  failed: 'sb-fail', stopped: 'sb-stop'  }};

  badge.className = `status-badge ${{clses[finalStatus] || 'sb-idle'}}`;
  if (txt)  txt.textContent = labels[finalStatus] || 'Ready';
  if (lbl)  lbl.textContent = '';
  if (lv)   lv.classList.remove('active');
  if (idle) idle.style.display = '';
  if (urlEl) urlEl.removeAttribute('readonly');
  if (depEl) depEl.removeAttribute('disabled');
  setBtn('<button class="start-btn" onclick="handleStart()">▶ Start Scan</button>');
}}

function setBtn(html) {{
  const el = $('actionBtn');
  if (el) el.innerHTML = html;
}}

/* ── LOG HELPERS ────────────────────────────────────── */
function appendLogRaw(line) {{
  /* strip job-id prefix: "[job_1_abc123] actual message" */
  const msg  = line.replace(/^\\[job_\\d+_[a-f0-9]+\\]\\s*/, '').trim();
  if (!msg) return;
  const now  = new Date().toLocaleTimeString('en-US', {{ hour12: false }});
  let level  = 'info';
  if      (/error|fail|exception/i.test(msg))      level = 'high';
  else if (/warn|⚠/i.test(msg))                    level = 'medium';
  else if (/complet|success|✅|done/i.test(msg))   level = 'success';
  else if (/pipeline|analysis|started|generated/i.test(msg)) level = 'system';
  appendLog(now, detectAgent(msg), msg, level);

  /* increment pseudo-progress (caps at 92% until status says done) */
  _logCount++;
  const pct = parseInt($('pbPct')?.textContent || '0');
  if (_running && pct < 92) setProgress(Math.min(92, pct + Math.max(1, Math.floor(2 / (_logCount / 5 + 1)))));
}}

function detectAgent(msg) {{
  if (/crawler|spider/i.test(msg))  return '[CRAWLER]';
  if (/sql/i.test(msg))             return '[SQL Agent]';
  if (/xss/i.test(msg))             return '[XSS Agent]';
  if (/ssrf/i.test(msg))            return '[SSRF Agent]';
  if (/analysis|pipeline/i.test(msg)) return '[ANALYSIS]';
  if (/report/i.test(msg))          return '[REPORT]';
  return '[SYSTEM]';
}}

function appendSysLog(msg, level = 'system') {{
  const now = new Date().toLocaleTimeString('en-US', {{ hour12: false }});
  appendLog(now, '[SYSTEM]', msg, level);
}}

function appendLog(time, agent, msg, level) {{
  const t = term();
  if (!t) return;
  const empty = t.querySelector('.log-empty');
  if (empty) empty.remove();

  const div = document.createElement('div');
  div.className = `log-line log-${{level}}`;
  div.innerHTML =
    `<span class="log-time">${{esc(time)}}</span>` +
    `<span class="log-agent">${{esc(agent)}}</span>` +
    `<span class="log-msg">${{esc(msg)}}</span>`;
  t.appendChild(div);
  t.scrollTop = t.scrollHeight;
}}

function setProgress(pct) {{
  const fill = $('pbFill');
  const lbl  = $('pbPct');
  if (fill) fill.style.width = pct + '%';
  if (lbl)  lbl.textContent  = pct + '%';
}}

function esc(s) {{
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

/* ── SESSION STORAGE CLEANUP ────────────────────────── */
function clearState() {{
  sessionStorage.removeItem('ct_job_id');
  sessionStorage.removeItem('ct_agent_id');
  _jobId   = null;
  _agentId = null;
  _logCount = 0;
}}

/* ── AGENT TOGGLE ────────────────────────────────────── */
function toggleAgent(key, el) {{
  el.classList.toggle('selected');
  const check = el.querySelector('.toggle-check');
  check.textContent = el.classList.contains('selected') ? '✓' : '';
}}
</script>
"""


# ── RENDER ────────────────────────────────────────────────────────────────────
def render() -> None:
    selected_agents = _DEFAULT_SELECTED
    page_html = (
        f"<style>{_CSS}</style>"
        + _build_page(selected_agents)
        + _build_js(_API_BASE, _WS_BASE)
    )
    render_layout(active_page="scan", page_content_html=page_html, height=900)