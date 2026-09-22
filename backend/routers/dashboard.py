"""
backend/routers/dashboard.py
────────────────────────────
Aggregates live dashboard metrics from active scans, crawler discovery,
and generated reports.

Endpoint:
    GET /dashboard/summary  -> full summary needed by the CyTrack dashboard
"""

import time
from collections import Counter
from fastapi import APIRouter
from store import scans, agent_logs, ScanStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary() -> dict:
    # Import here to avoid circular imports at module level
    from routers.reports import load_all_persisted_reports
    from routers.agents import list_agents

    reports = load_all_persisted_reports()

    # Determine currently running scan
    active_scans = [s for s in scans.values() if s.status == ScanStatus.RUNNING]
    is_running = len(active_scans) > 0
    current_scan = active_scans[0] if is_running else None

    # Calculate live progress and elapsed time for running scan
    active_scan_info = None
    live_progress = 0
    if current_scan:
        elapsed = int(time.time() - current_scan.created_at)
        logs = agent_logs.get(current_scan.agent_id, [])
        # Estimate progress based on log volume & elapsed time (capped at 92% until done)
        live_progress = min(92, max(15, int(elapsed * 3) + len(logs)))
        active_scan_info = {
            "job_id": current_scan.id,
            "target_url": current_scan.target_url,
            "depth": current_scan.depth,
            "status": "running",
            "elapsed_seconds": elapsed,
            "log_count": len(logs),
            "progress": live_progress,
        }

    # Total unique targets set
    targets_set = set()
    for r in reports:
        if r.get("target"):
            targets_set.add(r["target"])
    for s in scans.values():
        if s.target_url:
            targets_set.add(s.target_url)

    # Calculate overall vulnerability counts across all reports
    total_high = sum(r.get("high", 0) for r in reports)
    total_med  = sum(r.get("medium", 0) for r in reports)
    total_low  = sum(r.get("low", 0) for r in reports)
    total_info = sum(r.get("info", 0) for r in reports)

    # Targets with critical/high issues
    targets_critical = sum(1 for r in reports if r.get("high", 0) > 0)

    # Recent alerts: flatten findings across reports (most recent first)
    all_alerts: list[dict] = []
    vuln_counter: Counter = Counter()

    for r in reports:
        target_name = r.get("target", "")
        clean_target = target_name.replace("https://", "").replace("http://", "").rstrip("/")
        for f in r.get("findings", []):
            all_alerts.append({
                "severity": f.get("severity", "LOW"),
                "title": f.get("title", "Discovery Finding"),
                "target": clean_target or target_name,
                "time": r.get("time", "Recent"),
            })
            vuln_counter[f.get("title", "Security Finding")] += 1

    # Top vulnerabilities
    top_vulns = [
        {"name": name, "count": count}
        for name, count in vuln_counter.most_common(5)
    ]
    if not top_vulns:
        top_vulns = [
            {"name": "No vulnerabilities detected yet — start a scan", "count": 0},
        ]

    # Fetch agents list with live statuses
    all_agents = await list_agents()
    working_agents = sum(1 for a in all_agents if a.get("status") == "working")

    # Overall progress
    if is_running:
        progress_pct = live_progress
    elif reports or scans:
        progress_pct = 100
    else:
        progress_pct = 0

    elapsed_secs = active_scan_info.get("elapsed_seconds", 0) if active_scan_info else 0

    return {
        "active_scan": active_scan_info,
        "active_agents": working_agents if is_running else 0,
        "agents_working": working_agents if is_running else 0,
        "targets": len(targets_set) or len(reports),
        "targets_critical": targets_critical,
        "scan_progress": progress_pct,
        "reports_generated": len(reports),
        "targets_scanned": len(reports),
        "total_targets": len(targets_set) or max(1, len(reports)),
        "running_agents": working_agents if is_running else 0,
        "estimated_minutes": max(1, 15 - int(elapsed_secs / 60)) if is_running else 0,
        "report_breakdown": {
            "high": total_high,
            "medium": total_med,
            "low": total_low,
            "info": total_info,
        },
        "recent_alerts": all_alerts[:5],
        "top_vulns": top_vulns,
        "agents": all_agents[:5],
    }
