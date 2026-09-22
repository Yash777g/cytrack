"""
Agent listing + log retrieval.
backend/routers/agents.py
─────────────────────────
Agent listing, status monitoring, and activity feed.

Endpoints:
    GET /agents             -> list all 10 CyTrack agents + crawler with live status & findings
    GET /agents/feed        -> recent log stream formatted as event feed
    GET /agents/{id}/logs   -> full log history for an agent
"""

import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from store import ScanStatus, agent_logs, agents, scans

router = APIRouter(prefix="/agents", tags=["agents"])

# The 10 core CyTrack security agents
_AGENT_SPECS = [
    {"key": "sql",      "name": "SQL Agent",             "description": "Detects SQL injection vulnerabilities and blind extraction points"},
    {"key": "xss",      "name": "XSS Agent",             "description": "Scans for reflected, stored, and DOM-based cross-site scripting"},
    {"key": "authz",    "name": "AuthZ Agent",           "description": "Tests authorization, privilege escalation, and access controls"},
    {"key": "ssrf",     "name": "SSRF Agent",            "description": "Tests for server-side request forgery against internal endpoints"},
    {"key": "nosql",    "name": "NoSQL Agent",           "description": "Scans for MongoDB and NoSQL query injection vectors"},
    {"key": "csrf",     "name": "CSRF Agent",            "description": "Validates anti-CSRF token implementation on state changes"},
    {"key": "idor",     "name": "IDOR Agent",            "description": "Tests insecure direct object references across user parameters"},
    {"key": "sast",     "name": "SAST Agent",            "description": "Static analysis of discovered JavaScript endpoints & sourcemaps"},
    {"key": "upload",   "name": "Upload Agent",          "description": "Tests file upload validation, extension filtering, and traversal"},
    {"key": "password", "name": "Password Policy Agent", "description": "Audits credential complexity, lockouts, and auth flows"},
]

# Per-agent progress stagger offsets so cards don't all show the same %
_PROGRESS_OFFSETS = {
    "sql": 0, "xss": 5, "authz": 10, "ssrf": -5,
    "nosql": 3, "csrf": 8, "idor": -3,
    "sast": 12, "upload": 6, "password": -8,
}

# Agents that are activated when a scan runs
_ACTIVE_AGENT_KEYS = {"sql", "xss", "authz", "ssrf", "sast"}


class AgentLogsResponse(BaseModel):
    agent_id: str
    status: ScanStatus
    lines: list[str]


@router.get("")
async def list_agents() -> list[dict]:
    """
    Returns the full list of agents decorated with findings and activity
    derived from active scans and completed discovery reports.
    """
    # Import here to avoid circular imports
    from routers.reports import load_all_persisted_reports

    reports = load_all_persisted_reports()
    latest_report = reports[0] if reports else {}
    latest_findings = latest_report.get("findings", [])

    # Check if a scan is currently running
    active_scans = [s for s in scans.values() if s.status == ScanStatus.RUNNING]
    is_running = len(active_scans) > 0
    active_job = active_scans[0] if is_running else None

    # Compute live progress when running
    elapsed = 0
    log_cnt = 0
    if active_job:
        elapsed = int(time.time() - active_job.created_at)
        log_cnt = len(agent_logs.get(active_job.agent_id, []))

    # Get planned agents from the latest execution plan
    planned_agent_keys = set()
    if latest_report.get("execution_plan"):
        for item in latest_report["execution_plan"]:
            raw_name = item.get("agent", "").lower()
            for spec in _AGENT_SPECS:
                if spec["key"] in raw_name:
                    planned_agent_keys.add(spec["key"])

    results = []
    for spec in _AGENT_SPECS:
        key = spec["key"]
        name = spec["name"]

        # Count findings attributed to this agent across recent reports
        matched_findings = [
            f for f in latest_findings
            if spec["key"] in f.get("agent", "").lower()
            or spec["key"] in f.get("title", "").lower()
        ]
        findings_count = len(matched_findings)

        high_cnt = sum(1 for f in matched_findings if f.get("severity") == "HIGH")
        med_cnt  = sum(1 for f in matched_findings if f.get("severity") == "MEDIUM")
        low_cnt  = sum(1 for f in matched_findings if f.get("severity") == "LOW")

        # Determine agent status
        if is_running:
            if key in _ACTIVE_AGENT_KEYS or key in planned_agent_keys:
                status = "working"
                offset = _PROGRESS_OFFSETS.get(key, 0)
                # Progress based on elapsed time + log volume, capped at 94% until done
                progress = min(94, max(15, int(elapsed * 2) + log_cnt + offset))
                activity = "Probing target endpoints..."
                started = "Active"
            else:
                status = "idle"
                progress = 0
                activity = "Standby"
                started = "-"
        else:
            status = "idle"
            progress = 100 if findings_count > 0 else 0
            activity = f"Completed ({findings_count} findings)" if findings_count > 0 else "Ready"
            started = latest_report.get("time", "-") if findings_count > 0 else "-"

        results.append({
            "id": f"agent-{key}",
            "name": name,
            "status": status,
            "progress": progress,
            "last_activity": activity,
            "findings": findings_count,
            "high": high_cnt,
            "medium": med_cnt,
            "low": low_cnt,
            "description": spec["description"],
            "started": started,
        })

    return results


@router.get("/feed")
async def get_agent_feed() -> list[dict]:
    """
    Returns the recent activity feed generated from scan log lines
    and discovery findings.
    """
    from routers.reports import load_all_persisted_reports

    feed = []

    # 1. First try to extract events from recent agent logs
    for aid, lines in agent_logs.items():
        for line in lines[-15:]:
            clean = line.strip()
            if not clean:
                continue
            # Determine level
            level = "info"
            if any(k in clean.lower() for k in ["error", "fail", "alert", "sqli", "xss", "cve"]):
                level = "high"
            elif any(k in clean.lower() for k in ["warn", "potential", "detected"]):
                level = "medium"
            elif any(k in clean.lower() for k in ["complet", "success", "done"]):
                level = "info"

            # Determine agent name
            agent_name = "Scanner"
            for spec in _AGENT_SPECS:
                if spec["key"] in clean.lower():
                    agent_name = spec["name"]
                    break

            feed.append({
                "time": time.strftime("%H:%M"),
                "agent": agent_name,
                "event": clean[:120],
                "level": level,
            })

    # 2. If log feed is empty, generate from latest report findings
    if not feed:
        reports = load_all_persisted_reports()
        if reports:
            latest = reports[0]
            for f in latest.get("findings", [])[:8]:
                endpoint = f.get("endpoint", "")
                endpoint_short = endpoint[:45] if endpoint else "target"
                feed.append({
                    "time": latest.get("time", time.strftime("%H:%M")),
                    "agent": f.get("agent", "Discovery"),
                    "event": f"{f.get('title', 'Finding')} detected on {endpoint_short}",
                    "level": f.get("severity", "info").lower(),
                })

    # 3. Fallback default feed if no scans run yet
    if not feed:
        feed = [
            {"time": time.strftime("%H:%M"), "agent": "Crawler", "event": "Spider engine ready to crawl targets", "level": "info"},
            {"time": time.strftime("%H:%M"), "agent": "System",  "event": "Agent registry initialized — start a scan to see live activity", "level": "info"},
        ]

    return feed


@router.get("/{agent_id}/logs", response_model=AgentLogsResponse)
async def get_agent_logs(agent_id: str):
    agent = agents.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return AgentLogsResponse(
        agent_id=agent_id,
        status=agent.status,
        lines=agent_logs.get(agent_id, []),
    )
