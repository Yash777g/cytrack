"""
frontend/api_client.py
──────────────────────
HTTP client for the CyTrack FastAPI backend (http://127.0.0.1:8000).

Used by server-side Streamlit pages that need to read real backend data:
  - Dashboard stats & charts
  - Agent list & live activity feed
  - Real scan reports & vulnerability discoveries

Graceful fallbacks ensure the UI never crashes if the backend is starting up.
"""

import requests

_BASE    = "http://127.0.0.1:8000"
_TIMEOUT = 3  # seconds


def _get(path: str, params: dict | None = None) -> dict | list | None:
    """GET helper — returns parsed JSON or None on error."""
    try:
        r = requests.get(f"{_BASE}{path}", params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _post(path: str, body: dict) -> dict | None:
    """POST helper — returns parsed JSON or None on error."""
    try:
        r = requests.post(f"{_BASE}{path}", json=body, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def is_backend_alive() -> bool:
    """Quick health-check — True if the backend is reachable."""
    try:
        r = requests.get(f"{_BASE}/health", timeout=1.5)
        return r.ok
    except Exception:
        return False


# ── SCAN ──────────────────────────────────────────────────────────────────────

def start_scan(target_url: str, depth: int = 2) -> dict | None:
    """POST /scan/start — returns {job_id, agent_id, status} or None."""
    return _post("/scan/start", {"target_url": target_url, "depth": depth})


def get_scan_status(job_id: str) -> dict | None:
    """GET /scan/status — returns scan status dict or None."""
    return _get("/scan/status", {"job_id": job_id})


def stop_scan(job_id: str) -> dict | None:
    """POST /scan/stop — returns updated status dict or None."""
    return _post("/scan/stop", {"job_id": job_id})


# ── DASHBOARD & STATS ─────────────────────────────────────────────────────────

def get_dashboard_summary() -> dict:
    """
    GET /dashboard/summary — aggregates live targets, scans, vulnerabilities,
    alerts, and agent counts.
    """
    res = _get("/dashboard/summary")
    if isinstance(res, dict):
        return res
    # Fallback when backend is unreachable
    return {
        "active_scan":       None,
        "active_agents":     0,
        "agents_working":    0,
        "targets":           0,
        "targets_critical":  0,
        "scan_progress":     0,
        "reports_generated": 0,
        "targets_scanned":   0,
        "total_targets":     0,
        "running_agents":    0,
        "estimated_minutes": 0,
        "report_breakdown":  {"high": 0, "medium": 0, "low": 0, "info": 0},
        "recent_alerts":     [],
        "top_vulns":         [],
        "agents":            [],
    }


def get_dashboard_stats() -> dict:
    """Returns the 4 stat card values derived from the summary."""
    s = get_dashboard_summary()
    return {
        "active_agents":     s.get("active_agents",     0),
        "agents_working":    s.get("agents_working",    0),
        "targets":           s.get("targets",           0),
        "targets_critical":  s.get("targets_critical",  0),
        "scan_progress":     s.get("scan_progress",     0),
        "reports_generated": s.get("reports_generated", 0),
    }


def get_scan_progress_data() -> dict:
    """Returns data for the scan progress card & donut."""
    s = get_dashboard_summary()
    return {
        "overall_progress": s.get("scan_progress",     0),
        "targets_scanned":  s.get("targets_scanned",   0),
        "total_targets":    s.get("total_targets",     0),
        "running_agents":   s.get("running_agents",    0),
        "estimated_minutes":s.get("estimated_minutes", 0),
    }


def get_report_breakdown() -> dict:
    """Returns the vulnerability breakdown dict for the pie chart."""
    s  = get_dashboard_summary()
    bd = s.get("report_breakdown", {})
    return bd if sum(bd.values()) > 0 else {"high": 0, "medium": 0, "low": 0, "info": 0}


def get_recent_alerts() -> list[dict]:
    """Returns latest alerts from scanned targets."""
    s      = get_dashboard_summary()
    alerts = s.get("recent_alerts", [])
    if alerts:
        return alerts
    return [{"severity": "INFO", "title": "Ready for Discovery", "target": "Local", "time": "Now"}]


def get_top_vulns() -> list[dict]:
    """Returns top vulnerabilities discovered across scans."""
    s     = get_dashboard_summary()
    vulns = s.get("top_vulns", [])
    if vulns:
        return vulns
    return [{"name": "No vulnerabilities detected yet — start a scan", "count": 0}]


# ── AGENTS ────────────────────────────────────────────────────────────────────

_AGENT_FALLBACK = [
    {"id": "agent-sql",      "name": "SQL Agent",             "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Detects SQL injection vulnerabilities",           "started": "-"},
    {"id": "agent-xss",      "name": "XSS Agent",             "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Scans for cross-site scripting flaws",             "started": "-"},
    {"id": "agent-authz",    "name": "AuthZ Agent",           "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests authorisation and access controls",          "started": "-"},
    {"id": "agent-ssrf",     "name": "SSRF Agent",            "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests for server-side request forgery",             "started": "-"},
    {"id": "agent-nosql",    "name": "NoSQL Agent",           "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Scans for NoSQL injection vectors",                 "started": "-"},
    {"id": "agent-csrf",     "name": "CSRF Agent",            "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Checks CSRF token implementation",                 "started": "-"},
    {"id": "agent-idor",     "name": "IDOR Agent",            "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests insecure direct object references",           "started": "-"},
    {"id": "agent-sast",     "name": "SAST Agent",            "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Static analysis of discovered endpoints",           "started": "-"},
    {"id": "agent-upload",   "name": "Upload Agent",          "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests file upload security",                        "started": "-"},
    {"id": "agent-password", "name": "Password Policy Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Audits password and auth policies",                 "started": "-"},
]


def get_agents() -> list[dict]:
    """GET /agents — returns list of 10 CyTrack agents with live status and findings."""
    result = _get("/agents")
    if isinstance(result, list) and len(result) > 0:
        return result
    return _AGENT_FALLBACK


def get_agent_feed() -> list[dict]:
    """GET /agents/feed — returns live event activity feed."""
    result = _get("/agents/feed")
    if isinstance(result, list) and len(result) > 0:
        return result
    return [
        {"time": "—", "agent": "Crawler", "event": "Spider engine ready — start a scan to see live activity", "level": "info"},
        {"time": "—", "agent": "System",  "event": "Agent registry initialized",                              "level": "info"},
    ]


def get_agent_logs(agent_id: str) -> list[str]:
    """GET /agents/{agent_id}/logs — returns list of log lines."""
    result = _get(f"/agents/{agent_id}/logs")
    if isinstance(result, dict):
        return result.get("lines", [])
    return []


# ── REPORTS ───────────────────────────────────────────────────────────────────

def get_reports() -> list[dict]:
    """GET /reports — returns real scan reports with structured findings."""
    result = _get("/reports")
    if isinstance(result, list) and len(result) > 0:
        return result
    return []