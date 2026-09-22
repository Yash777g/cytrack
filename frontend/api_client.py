"""
frontend/api_client.py
──────────────────────
HTTP client for the CyTrack FastAPI backend (http://127.0.0.1:8000).

Used by server-side Streamlit pages that need to read real backend data
(e.g. Dashboard stats, Agent list, Reports).  The Scan page does its own
JS fetch/WebSocket calls directly from the browser, so it doesn't use this.
Used by server-side Streamlit pages that need to read real backend data:
  - Dashboard stats & charts
  - Agent list & live activity feed
  - Real scan reports & vulnerability discoveries

All functions return sensible fallback values if the backend is unreachable
so the UI degrades gracefully rather than crashing.
Graceful fallbacks ensure the UI never crashes if the backend is starting up.
"""

import requests

_BASE = "http://127.0.0.1:8000"
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
        r = requests.get(f"{_BASE}/health", timeout=2)
        r = requests.get(f"{_BASE}/health", timeout=1.5)
        return r.ok
    except Exception:
        return False


# ── SCAN ─────────────────────────────────────────────────────────────────────

def start_scan(target_url: str, depth: int = 2) -> dict | None:
    """POST /scan/start — returns {job_id, agent_id, status} or None."""
    return _post("/scan/start", {"target_url": target_url, "depth": depth})


def get_scan_status(job_id: str) -> dict | None:
    """GET /scan/status — returns scan status dict or None."""
    return _get("/scan/status", {"job_id": job_id})


def stop_scan(job_id: str) -> dict | None:
    """POST /scan/stop — returns updated status dict or None."""
    return _post("/scan/stop", {"job_id": job_id})


# ── DASHBOARD & STATS ────────────────────────────────────────────────────────

def get_dashboard_summary() -> dict:
    """
    GET /dashboard/summary — aggregates live targets, scans, vulnerabilities,
    alerts, and agent counts.
    """
    res = _get("/dashboard/summary")
    if isinstance(res, dict):
        return res
    # Sensible fallback
    return {
        "active_agents": 0,
        "agents_working": 0,
        "targets": 0,
        "targets_critical": 0,
        "scan_progress": 0,
        "reports_generated": 0,
        "targets_scanned": 0,
        "total_targets": 0,
        "running_agents": 0,
        "estimated_minutes": 0,
        "report_breakdown": {"high": 0, "medium": 0, "low": 0, "info": 0},
        "recent_alerts": [],
        "top_vulns": [],
    }


def get_dashboard_stats() -> dict:
    """Returns the 4 stat cards data."""
    summary = get_dashboard_summary()
    return {
        "active_agents": summary.get("active_agents", 0),
        "agents_working": summary.get("agents_working", 0),
        "targets": summary.get("targets", 0),
        "targets_critical": summary.get("targets_critical", 0),
        "scan_progress": summary.get("scan_progress", 0),
        "reports_generated": summary.get("reports_generated", 0),
    }


def get_scan_progress_data() -> dict:
    """Returns data for the scan progress card & donut."""
    summary = get_dashboard_summary()
    return {
        "overall_progress": summary.get("scan_progress", 0),
        "targets_scanned": summary.get("targets_scanned", 0),
        "total_targets": summary.get("total_targets", 0),
        "running_agents": summary.get("running_agents", 0),
        "estimated_minutes": summary.get("estimated_minutes", 0),
    }


def get_report_breakdown() -> dict:
    """Returns the vulnerability breakdown dict for pie chart."""
    summary = get_dashboard_summary()
    bd = summary.get("report_breakdown", {})
    # If no findings yet, show a clean initial distribution or zeros
    if sum(bd.values()) == 0:
        return {"high": 0, "medium": 0, "low": 0, "info": 0}
    return bd


def get_recent_alerts() -> list[dict]:
    """Returns latest alerts discovered on scanned targets."""
    summary = get_dashboard_summary()
    alerts = summary.get("recent_alerts", [])
    if alerts:
        return alerts
    return [
        {"severity": "INFO", "title": "Ready for Discovery", "target": "Local", "time": "Now"}
    ]


def get_top_vulns() -> list[dict]:
    """Returns top vulnerabilities discovered across scans."""
    summary = get_dashboard_summary()
    vulns = summary.get("top_vulns", [])
    if vulns:
        return vulns
    return [
        {"name": "No vulnerabilities detected yet", "count": 0}
    ]


# ── AGENTS ───────────────────────────────────────────────────────────────────

def get_agents() -> list[dict]:
    """GET /agents — returns list of agent dicts (empty on error)."""
    """GET /agents — returns list of 10 CyTrack agents with dynamic status and findings."""
    result = _get("/agents")
    if isinstance(result, list):
    if isinstance(result, list) and len(result) > 0:
        return result
    # Fallback mock so dashboard never crashes
    return [
        {"name": "SQL Agent",  "status": "idle", "progress": 0, "last_activity": "—"},
        {"name": "XSS Agent",  "status": "idle", "progress": 0, "last_activity": "—"},
        {"name": "SSRF Agent", "status": "idle", "progress": 0, "last_activity": "—"},
        {"id": "agent-sql", "name": "SQL Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Detects SQL injection vulnerabilities", "started": "—"},
        {"id": "agent-xss", "name": "XSS Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Scans for cross-site scripting flaws", "started": "—"},
        {"id": "agent-authz", "name": "AuthZ Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests authorisation and access controls", "started": "—"},
        {"id": "agent-ssrf", "name": "SSRF Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests for server-side request forgery", "started": "—"},
        {"id": "agent-nosql", "name": "NoSQL Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Scans for NoSQL injection vectors", "started": "—"},
        {"id": "agent-csrf", "name": "CSRF Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Checks CSRF token implementation", "started": "—"},
        {"id": "agent-idor", "name": "IDOR Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests insecure direct object references", "started": "—"},
        {"id": "agent-sast", "name": "SAST Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Static analysis of discovered endpoints", "started": "—"},
        {"id": "agent-upload", "name": "Upload Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Tests file upload security", "started": "—"},
        {"id": "agent-password", "name": "Password Policy Agent", "status": "idle", "progress": 0, "last_activity": "Ready", "findings": 0, "high": 0, "medium": 0, "low": 0, "description": "Audits password and auth policies", "started": "—"},
    ]


def get_agent_feed() -> list[dict]:
    """GET /agents/feed — returns live event activity feed."""
    result = _get("/agents/feed")
    if isinstance(result, list) and len(result) > 0:
        return result
    return [
        {"time": "12:00", "agent": "Crawler", "event": "Spider engine ready to crawl targets", "level": "info"},
        {"time": "12:00", "agent": "System", "event": "Agent registry initialized", "level": "info"},
    ]


def get_agent_logs(agent_id: str) -> list[str]:
    """GET /agents/{agent_id}/logs — returns list of log lines (empty on error)."""
    """GET /agents/{agent_id}/logs — returns list of log lines."""
    result = _get(f"/agents/{agent_id}/logs")
    if isinstance(result, dict):
        return result.get("lines", [])
    return []


# ── REPORTS ──────────────────────────────────────────────────────────────────

def get_reports() -> list[dict]:
    """GET /reports — returns list of report dicts (empty on error)."""
    """GET /reports — returns real scan reports with structured findings."""
    result = _get("/reports")
    if isinstance(result, list):
    if isinstance(result, list) and len(result) > 0:
        return result
    return []


# ── DASHBOARD STATS ───────────────────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    """
    Derives dashboard stat card values from live backend data.
    Falls back to zero-state if the backend is unreachable.
    """
    agents  = get_agents()
    reports = get_reports()

    active   = sum(1 for a in agents if a.get("status") == "running")
    targets  = len(agents)
    rpt_cnt  = len(reports)

    return {
        "active_agents":      active,
        "agents_working":     active,
        "targets":            targets,
        "targets_critical":   0,
        "scan_progress":      0,
        "reports_generated":  rpt_cnt,
    }


def get_recent_alerts() -> list[dict]:
    """Returns mock alerts (real alerts come from agent findings, not yet wired)."""
    return [
        {"severity": "HIGH",   "title": "SQL Injection Detected",    "target": "api.example.com",    "time": "—"},
        {"severity": "MEDIUM", "title": "Outdated Software Version",  "target": "portal.example.com", "time": "—"},
        {"severity": "LOW",    "title": "Directory Listing Enabled",  "target": "test.example.com",   "time": "—"},
    ]