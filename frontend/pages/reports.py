"""
frontend/pages/reports.py
──────────────────────────
Reports page — split layout: report list left, detail view right.

Layout:
  ┌──────────────────┬───────────────────────────────────┐
  │  Report List     │  Report Detail                    │
  │  (filter tabs)   │  - Summary stats                  │
  │  - Report cards  │  - Findings table by severity     │
  │                  │  - Export button                  │
  └──────────────────┴───────────────────────────────────┘
"""

import streamlit as st
from components.layout import render_layout

# ── MOCK DATA ─────────────────────────────────────────────────────────────────
_MOCK_REPORTS = [
    {
        "id": "RPT-001", "target": "api.example.com",
        "date": "Sep 03, 2026", "time": "11:20 AM",
        "duration": "1h 25m", "status": "complete",
        "high": 3, "medium": 4, "low": 2, "info": 1,
        "findings": [
            {"severity":"HIGH",   "title":"SQL Injection",          "endpoint":"/api/users?id=",     "agent":"SQL Agent",   "detail":"Blind SQL injection confirmed via time-based technique on the id parameter."},
            {"severity":"HIGH",   "title":"SSRF Vulnerability",     "endpoint":"/api/fetch",         "agent":"SSRF Agent",  "detail":"Server-side request forgery allows internal network probing via URL parameter."},
            {"severity":"HIGH",   "title":"Blind SQLi on Login",    "endpoint":"/login",             "agent":"SQL Agent",   "detail":"Boolean-based blind SQL injection detected in the username field."},
            {"severity":"MEDIUM", "title":"Reflected XSS",          "endpoint":"/search?q=",        "agent":"XSS Agent",   "detail":"Unsanitised input reflected in response without encoding."},
            {"severity":"MEDIUM", "title":"CSRF Missing on Forms",  "endpoint":"/account/update",   "agent":"CSRF Agent",  "detail":"No CSRF token present on state-changing form submission."},
            {"severity":"MEDIUM", "title":"Outdated Library",       "endpoint":"/static/jquery.js", "agent":"SAST Agent",  "detail":"jQuery 1.8.3 contains known XSS vulnerabilities (CVE-2015-9251)."},
            {"severity":"MEDIUM", "title":"Sensitive Data in URL",  "endpoint":"/api/token?key=",   "agent":"SAST Agent",  "detail":"API key passed as query parameter, exposed in server logs."},
            {"severity":"LOW",    "title":"Directory Listing",      "endpoint":"/uploads/",         "agent":"SAST Agent",  "detail":"Web server exposes directory listing on /uploads/ path."},
            {"severity":"LOW",    "title":"Missing Security Headers","endpoint":"All routes",        "agent":"SAST Agent",  "detail":"X-Frame-Options and Content-Security-Policy headers absent."},
            {"severity":"INFO",   "title":"Open Port 8080",         "endpoint":"port:8080",         "agent":"SSRF Agent",  "detail":"Non-standard port 8080 is open and serving HTTP traffic."},
        ]
    },
    {
        "id": "RPT-002", "target": "portal.example.com",
        "date": "Sep 02, 2026", "time": "09:15 AM",
        "duration": "52m", "status": "complete",
        "high": 1, "medium": 2, "low": 3, "info": 2,
        "findings": [
            {"severity":"HIGH",   "title":"IDOR on User Profile",   "endpoint":"/profile?user_id=", "agent":"IDOR Agent",  "detail":"Direct object reference allows access to other users' profiles."},
            {"severity":"MEDIUM", "title":"Weak Password Policy",   "endpoint":"/register",         "agent":"Password Policy Agent","detail":"Minimum password length is 4 characters with no complexity requirements."},
            {"severity":"MEDIUM", "title":"XSS in Comments",        "endpoint":"/posts/comment",    "agent":"XSS Agent",   "detail":"Stored XSS via comment field — script tags not sanitised."},
            {"severity":"LOW",    "title":"Cookie Missing HttpOnly", "endpoint":"All routes",        "agent":"SAST Agent",  "detail":"Session cookie lacks HttpOnly flag, accessible via JavaScript."},
            {"severity":"LOW",    "title":"Verbose Error Messages",  "endpoint":"/api/error",        "agent":"SAST Agent",  "detail":"Stack traces exposed in production error responses."},
            {"severity":"LOW",    "title":"Old TLS Version",         "endpoint":"TLS config",        "agent":"SAST Agent",  "detail":"TLS 1.0 still supported alongside TLS 1.3."},
            {"severity":"INFO",   "title":"Admin Panel Exposed",    "endpoint":"/admin",            "agent":"SAST Agent",  "detail":"Admin login page is publicly accessible (not behind VPN)."},
            {"severity":"INFO",   "title":"Open Port 3306",         "endpoint":"port:3306",         "agent":"SSRF Agent",  "detail":"MySQL port accessible from external network."},
        ]
    },
    {
        "id": "RPT-003", "target": "test.example.com",
        "date": "Sep 01, 2026", "time": "03:40 PM",
        "duration": "38m", "status": "complete",
        "high": 0, "medium": 1, "low": 4, "info": 3,
        "findings": [
            {"severity":"MEDIUM", "title":"File Upload No Validation","endpoint":"/upload",         "agent":"Upload Agent","detail":"File type not validated server-side — arbitrary file upload possible."},
            {"severity":"LOW",    "title":"Missing HSTS Header",     "endpoint":"All routes",       "agent":"SAST Agent",  "detail":"HTTP Strict Transport Security header not set."},
            {"severity":"LOW",    "title":"Open Redirect",           "endpoint":"/redirect?url=",  "agent":"SSRF Agent",  "detail":"Unvalidated redirect parameter allows phishing attacks."},
            {"severity":"LOW",    "title":"Sensitive Comment in HTML","endpoint":"/index.html",    "agent":"SAST Agent",  "detail":"Internal IP address found in HTML comment."},
            {"severity":"LOW",    "title":"Clickjacking Possible",   "endpoint":"All routes",       "agent":"SAST Agent",  "detail":"X-Frame-Options not set, page embeddable in iframes."},
            {"severity":"INFO",   "title":"robots.txt Exposes Paths","endpoint":"/robots.txt",     "agent":"SAST Agent",  "detail":"Disallowed paths in robots.txt reveal internal URL structure."},
            {"severity":"INFO",   "title":"Server Version Disclosed","endpoint":"HTTP headers",     "agent":"SAST Agent",  "detail":"Server header discloses Apache 2.4.41 version string."},
            {"severity":"INFO",   "title":"Insecure Referrer Policy","endpoint":"All routes",       "agent":"SAST Agent",  "detail":"Referrer-Policy not set, full URL sent to third parties."},
        ]
    },
]

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """
.page-title {
  font-size: 22px; font-weight: 700;
  color: var(--text-p); margin-bottom: 20px;
}

/* split layout */
.reports-split {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  align-items: start;
}

/* ── LIST PANEL ── */
.list-panel {
  background: var(--bg-card);
  border-radius: 14px;
  border: 1px solid var(--border-card);
  box-shadow: var(--card-shadow);
  overflow: hidden;
}
.list-header {
  padding: 16px 18px 12px;
  border-bottom: 1px solid var(--border);
}
.list-title {
  font-size: 14px; font-weight: 600;
  color: var(--text-p); margin-bottom: 10px;
}

/* filter tabs */
.filter-tabs {
  display: flex; gap: 4px;
}
.ftab {
  padding: 4px 12px; border-radius: 6px;
  font-size: 11px; font-weight: 600;
  cursor: pointer; border: none;
  font-family: 'Inter', sans-serif;
  background: var(--pbar-bg); color: var(--text-m);
  transition: all 0.15s;
}
.ftab.active { background: #3b5bdb; color: #fff; }
.ftab:hover:not(.active) { background: var(--border); color: var(--text-s); }

/* report list items */
.report-list { padding: 8px 0; max-height: 640px; overflow-y: auto; }
.report-item {
  padding: 14px 18px; cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
  border-left: 3px solid transparent;
}
.report-item:last-child { border-bottom: none; }
.report-item:hover { background: var(--pbar-bg); }
.report-item.active {
  background: rgba(59,91,219,0.08);
  border-left-color: #3b5bdb;
}
.ri-header {
  display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 6px;
}
.ri-id { font-size: 13px; font-weight: 600; color: var(--text-p); }
.ri-date { font-size: 11px; color: var(--text-m); }
.ri-target {
  font-size: 12px; color: var(--text-s);
  margin-bottom: 8px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;
}
.ri-badges { display: flex; gap: 5px; }
.ri-badge {
  padding: 2px 7px; border-radius: 5px;
  font-size: 10px; font-weight: 700;
}
.rb-h { background: var(--alert-hi-bg); color: var(--alert-hi-c); }
.rb-m { background: var(--alert-md-bg); color: var(--alert-md-c); }
.rb-l { background: var(--alert-lo-bg); color: var(--alert-lo-c); }
.rb-i { background: #eff6ff; color: #3b82f6; }

/* ── DETAIL PANEL ── */
.detail-panel {
  background: var(--bg-card);
  border-radius: 14px;
  border: 1px solid var(--border-card);
  box-shadow: var(--card-shadow);
  overflow: hidden;
}
.detail-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 16px;
}
.detail-title-row { flex: 1; }
.detail-id {
  font-size: 18px; font-weight: 700;
  color: var(--text-p); margin-bottom: 4px;
}
.detail-target {
  font-size: 13px; color: var(--text-s); margin-bottom: 8px;
}
.detail-meta {
  display: flex; gap: 16px; flex-wrap: wrap;
}
.detail-meta-item { font-size: 12px; color: var(--text-m); }
.detail-meta-item strong { color: var(--text-s); }
.export-btn {
  padding: 8px 18px;
  background: var(--pbar-bg);
  border: 1px solid var(--border);
  border-radius: 8px; font-size: 13px;
  font-weight: 600; color: var(--text-p);
  cursor: pointer; font-family: 'Inter', sans-serif;
  white-space: nowrap; transition: all 0.15s;
  display: flex; align-items: center; gap: 6px;
}
.export-btn:hover { border-color: #3b82f6; color: #3b82f6; }

/* summary stat pills */
.summary-row {
  display: flex; gap: 12px; padding: 16px 24px;
  border-bottom: 1px solid var(--border); flex-wrap: wrap;
}
.summary-pill {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; border-radius: 10px;
  border: 1px solid var(--border); flex: 1; min-width: 90px;
}
.sp-val { font-size: 22px; font-weight: 700; color: var(--text-p); }
.sp-lbl { font-size: 11px; color: var(--text-m); margin-top: 1px; }

/* findings table */
.findings-body { padding: 20px 24px; }
.findings-section-title {
  font-size: 13px; font-weight: 600; color: var(--text-p);
  margin-bottom: 14px;
}
.finding-row {
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
  display: grid;
  grid-template-columns: 80px 1fr 140px;
  gap: 12px; align-items: start;
}
.finding-row:last-child { border-bottom: none; }
.finding-sev {
  padding: 3px 9px; border-radius: 6px;
  font-size: 10px; font-weight: 700;
  letter-spacing: .4px; width: fit-content;
}
.fs-high   { background: var(--alert-hi-bg); color: var(--alert-hi-c); }
.fs-medium { background: var(--alert-md-bg); color: var(--alert-md-c); }
.fs-low    { background: var(--alert-lo-bg); color: var(--alert-lo-c); }
.fs-info   { background: #eff6ff; color: #3b82f6; }
.finding-title {
  font-size: 13px; font-weight: 600; color: var(--text-p);
  margin-bottom: 3px;
}
.finding-endpoint {
  font-size: 11px; color: #3b82f6;
  font-family: 'Courier New', monospace; margin-bottom: 4px;
}
.finding-detail { font-size: 12px; color: var(--text-s); line-height: 1.5; }
.finding-agent  { font-size: 11px; color: var(--text-m); text-align: right; }

/* empty state */
.detail-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 80px 24px; gap: 12px; text-align: center;
}
.detail-empty-icon { font-size: 48px; opacity: 0.3; }
.detail-empty-txt  { font-size: 14px; color: var(--text-m); }

@media (max-width: 900px) {
  .reports-split { grid-template-columns: 1fr; }
  .finding-row   { grid-template-columns: 70px 1fr; }
  .finding-agent { display: none; }
}
"""

# ── BUILDERS ─────────────────────────────────────────────────────────────────

def _sev_class(sev: str) -> str:
    return {"HIGH":"fs-high","MEDIUM":"fs-medium","LOW":"fs-low","INFO":"fs-info"}.get(sev,"fs-info")


def _report_item(r: dict, active_id: str, tab: str) -> str:
    total = r["high"] + r["medium"] + r["low"] + r["info"]
    if tab == "high"   and r["high"]   == 0: return ""
    if tab == "medium" and r["medium"] == 0: return ""
    if tab == "low"    and r["low"]    == 0: return ""

    active_cls = "active" if r["id"] == active_id else ""
    badges = ""
    if r["high"]:   badges += f'<span class="ri-badge rb-h">H:{r["high"]}</span>'
    if r["medium"]: badges += f'<span class="ri-badge rb-m">M:{r["medium"]}</span>'
    if r["low"]:    badges += f'<span class="ri-badge rb-l">L:{r["low"]}</span>'
    if r["info"]:   badges += f'<span class="ri-badge rb-i">I:{r["info"]}</span>'

    return f"""
    <div class="report-item {active_cls}" onclick="selectReport('{r['id']}')">
      <div class="ri-header">
        <span class="ri-id">{r['id']}</span>
        <span class="ri-date">{r['date']}</span>
      </div>
      <div class="ri-target">🎯 {r['target']}</div>
      <div class="ri-badges">{badges}</div>
    </div>"""


def _report_detail(r: dict) -> str:
    total = r["high"] + r["medium"] + r["low"] + r["info"]

    # summary pills
    pills = f"""
    <div class="summary-row">
      <div class="summary-pill">
        <div><div class="sp-val" style="color:#ef4444">{r['high']}</div><div class="sp-lbl">High</div></div>
      </div>
      <div class="summary-pill">
        <div><div class="sp-val" style="color:#f97316">{r['medium']}</div><div class="sp-lbl">Medium</div></div>
      </div>
      <div class="summary-pill">
        <div><div class="sp-val" style="color:#eab308">{r['low']}</div><div class="sp-lbl">Low</div></div>
      </div>
      <div class="summary-pill">
        <div><div class="sp-val" style="color:#3b82f6">{r['info']}</div><div class="sp-lbl">Info</div></div>
      </div>
      <div class="summary-pill">
        <div><div class="sp-val">{total}</div><div class="sp-lbl">Total</div></div>
      </div>
    </div>"""

    # findings
    rows = ""
    for sev in ["HIGH","MEDIUM","LOW","INFO"]:
        sev_findings = [f for f in r["findings"] if f["severity"] == sev]
        for f in sev_findings:
            rows += f"""
            <div class="finding-row">
              <div><span class="finding-sev {_sev_class(sev)}">{sev}</span></div>
              <div>
                <div class="finding-title">{f['title']}</div>
                <div class="finding-endpoint">{f['endpoint']}</div>
                <div class="finding-detail">{f['detail']}</div>
              </div>
              <div class="finding-agent">{f['agent']}</div>
            </div>"""

    return f"""
    <div class="detail-header">
      <div class="detail-title-row">
        <div class="detail-id">{r['id']}</div>
        <div class="detail-target">🎯 {r['target']}</div>
        <div class="detail-meta">
          <span class="detail-meta-item"><strong>Date:</strong> {r['date']} {r['time']}</span>
          <span class="detail-meta-item"><strong>Duration:</strong> {r['duration']}</span>
          <span class="detail-meta-item"><strong>Status:</strong> ✅ Complete</span>
        </div>
      </div>
      <button class="export-btn" onclick="exportReport('{r['id']}')">⬇ Export JSON</button>
    </div>
    {pills}
    <div class="findings-body">
      <div class="findings-section-title">Findings ({len(r['findings'])})</div>
      {rows}
    </div>"""


def _build_page(active_id: str, tab: str) -> str:
import json

def _build_page(reports: list[dict], active_id: str, tab: str) -> str:
    # report list
    items = "".join(_report_item(r, active_id, tab) for r in _MOCK_REPORTS)
    items = "".join(_report_item(r, active_id, tab) for r in reports)
    if not items:
        items = '<div style="padding:24px;text-align:center;color:var(--text-m);font-size:13px">No reports match this filter</div>'

    # detail
    active_report = next((r for r in _MOCK_REPORTS if r["id"] == active_id), None)
    detail_html = _report_detail(active_report) if active_report else f"""
    active_report = next((r for r in reports if r["id"] == active_id), None)
    if active_report is None and reports:
        active_report = reports[0]
        active_id = active_report["id"]

    detail_html = _report_detail(active_report) if active_report else """
    <div class="detail-empty">
      <div class="detail-empty-icon">📋</div>
      <div class="detail-empty-txt">Select a report to view details</div>
    </div>"""

    tab_btns = ""
    for t, lbl in [("all","All"),("high","High"),("medium","Medium"),("low","Low")]:
        cls = "active" if tab == t else ""
        tab_btns += f'<button class="ftab {cls}" onclick="filterTab(\'{t}\')">{lbl}</button>'

    return f"""
    <div class="page-title">Reports</div>
    <div class="reports-split">

      <!-- LIST -->
      <div class="list-panel">
        <div class="list-header">
          <div class="list-title">Scan Reports</div>
          <div class="filter-tabs">{tab_btns}</div>
        </div>
        <div class="report-list" id="reportList">
          {items}
        </div>
      </div>

      <!-- DETAIL -->
      <div class="detail-panel" id="detailPanel">
        {detail_html}
      </div>

    </div>"""


# ── JS ────────────────────────────────────────────────────────────────────────
_ALL_REPORTS_JS = "const _reports = " + str([
    {"id": r["id"], "target": r["target"], "date": r["date"], "time": r["time"],
     "duration": r["duration"], "high": r["high"], "medium": r["medium"],
     "low": r["low"], "info": r["info"], "findings": r["findings"]}
    for r in _MOCK_REPORTS
]).replace("True","true").replace("False","false").replace("None","null") + ";"
def _build_js(reports: list[dict], active_id: str) -> str:
    clean_reports = [
        {"id": r["id"], "target": r["target"], "date": r["date"], "time": r["time"],
         "duration": r["duration"], "high": r["high"], "medium": r["medium"],
         "low": r["low"], "info": r["info"], "findings": r.get("findings", [])}
        for r in reports
    ]
    reports_json = json.dumps(clean_reports)

_JS = f"""
    return f"""
<script>
{_ALL_REPORTS_JS}
const _reports = {reports_json};

let _activeId  = '{_MOCK_REPORTS[0]["id"]}';
let _activeId  = '{active_id}';
let _activeTab = 'all';

function selectReport(id) {{
  _activeId = id;
  // update list active state
  document.querySelectorAll('.report-item').forEach(el => {{
    el.classList.toggle('active', el.onclick.toString().includes(id));
  }});
  // render detail
  const r = _reports.find(x => x.id === id);
  if (!r) return;
  renderDetail(r);
}}

function filterTab(tab) {{
  _activeTab = tab;
  document.querySelectorAll('.ftab').forEach(el => {{
    el.classList.toggle('active', el.textContent.toLowerCase() === tab || (tab==='all' && el.textContent==='All'));
  }});
  const list = document.getElementById('reportList');
  list.innerHTML = _reports
    .filter(r => tab==='all' || r[tab] > 0)
    .map(r => reportItemHTML(r))
    .join('');
}}

function reportItemHTML(r) {{
  const active = r.id === _activeId ? 'active' : '';
  let badges = '';
  if (r.high)   badges += '<span class="ri-badge rb-h">H:'+r.high+'</span>';
  if (r.medium) badges += '<span class="ri-badge rb-m">M:'+r.medium+'</span>';
  if (r.low)    badges += '<span class="ri-badge rb-l">L:'+r.low+'</span>';
  if (r.info)   badges += '<span class="ri-badge rb-i">I:'+r.info+'</span>';
  return '<div class="report-item '+active+'" onclick="selectReport(\\''+r.id+'\\')">'+
    '<div class="ri-header"><span class="ri-id">'+r.id+'</span><span class="ri-date">'+r.date+'</span></div>'+
    '<div class="ri-target">🎯 '+r.target+'</div>'+
    '<div class="ri-badges">'+badges+'</div></div>';
}}

function sevClass(s) {{
  return {{HIGH:'fs-high',MEDIUM:'fs-medium',LOW:'fs-low',INFO:'fs-info'}}[s]||'fs-info';
}}

function renderDetail(r) {{
  const total = r.high + r.medium + r.low + r.info;
  const pills = `
    <div class="summary-row">
      <div class="summary-pill"><div><div class="sp-val" style="color:#ef4444">${{r.high}}</div><div class="sp-lbl">High</div></div></div>
      <div class="summary-pill"><div><div class="sp-val" style="color:#f97316">${{r.medium}}</div><div class="sp-lbl">Medium</div></div></div>
      <div class="summary-pill"><div><div class="sp-val" style="color:#eab308">${{r.low}}</div><div class="sp-lbl">Low</div></div></div>
      <div class="summary-pill"><div><div class="sp-val" style="color:#3b82f6">${{r.info}}</div><div class="sp-lbl">Info</div></div></div>
      <div class="summary-pill"><div><div class="sp-val">${{total}}</div><div class="sp-lbl">Total</div></div></div>
    </div>`;
  const order = ['HIGH','MEDIUM','LOW','INFO'];
  const rows = order.flatMap(sev =>
    r.findings.filter(f => f.severity===sev).map(f => `
      <div class="finding-row">
        <div><span class="finding-sev ${{sevClass(sev)}}">${{sev}}</span></div>
        <div>
          <div class="finding-title">${{f.title}}</div>
          <div class="finding-endpoint">${{f.endpoint}}</div>
          <div class="finding-detail">${{f.detail}}</div>
        </div>
        <div class="finding-agent">${{f.agent}}</div>
      </div>`)
  ).join('');
  document.getElementById('detailPanel').innerHTML = `
    <div class="detail-header">
      <div class="detail-title-row">
        <div class="detail-id">${{r.id}}</div>
        <div class="detail-target">🎯 ${{r.target}}</div>
        <div class="detail-meta">
          <span class="detail-meta-item"><strong>Date:</strong> ${{r.date}} ${{r.time}}</span>
          <span class="detail-meta-item"><strong>Duration:</strong> ${{r.duration}}</span>
          <span class="detail-meta-item"><strong>Status:</strong> ✅ Complete</span>
        </div>
      </div>
      <button class="export-btn" onclick="exportReport('${{r.id}}')">⬇ Export JSON</button>
    </div>
    ${{pills}}
    <div class="findings-body">
      <div class="findings-section-title">Findings (${{r.findings.length}})</div>
      ${{rows}}
    </div>`;
}}

function exportReport(id) {{
  const r = _reports.find(x => x.id === id);
  if (!r) return;
  const blob = new Blob([JSON.stringify(r, null, 2)], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = id + '_report.json';
  a.click();
}}
</script>
"""


# ── RENDER ────────────────────────────────────────────────────────────────────
def render() -> None:
    active_id = _MOCK_REPORTS[0]["id"]
    page_html = f"<style>{_CSS}</style>" + _build_page(active_id, "all") + _JS
    import api_client
    reports = api_client.get_reports()
    if not reports:
        reports = _MOCK_REPORTS

    active_id = reports[0]["id"]
    page_html = f"<style>{_CSS}</style>" + _build_page(reports, active_id, "all") + _build_js(reports, active_id)
    render_layout(active_page="reports", page_content_html=page_html, height=900)