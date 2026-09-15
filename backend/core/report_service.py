import json

from store import reports


def get_all_reports():
    """Return all generated reports."""
    return list(reports.values())


def get_report(report_id: str):
    """Return one report by ID, or None if it does not exist."""
    return reports.get(report_id)


def format_report_json(report) -> str:
    """Convert a report into formatted JSON for export."""
    return json.dumps(
        report.model_dump(),
        indent=2,
    )