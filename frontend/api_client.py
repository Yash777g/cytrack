# api_client.py  MOCK VERSION (replace with real calls when FastAPI is ready)

def get_dashboard_stats():
    return {
        "active_agents": 12,
        "targets": 8,
        "scan_progress": 63,
        "reports_generated": 24,
    }

def get_recent_alerts():
    return [
        {"severity": "HIGH",   "title": "SQL Injection Detected",    "target": "api.example.com",    "time": "2m ago"},
        {"severity": "MEDIUM", "title": "Outdated Software Version",  "target": "portal.example.com", "time": "15m ago"},
        {"severity": "LOW",    "title": "Directory Listing Enabled",  "target": "test.example.com",   "time": "30m ago"},
    ]

def get_agents():
    return [
        {"name": "SQL Agent",     "status": "working", "progress": 75, "last_activity": "2m ago"},
        {"name": "XSS Agent",     "status": "working", "progress": 60, "last_activity": "5m ago"},
        {"name": "SSRF Agent",    "status": "working", "progress": 90, "last_activity": "1m ago"},
        {"name": "CSRF Agent",    "status": "idle",    "progress": 0,  "last_activity": "10m ago"},
        {"name": "IDOR Agent",    "status": "idle",    "progress": 0,  "last_activity": "15m ago"},
    ]