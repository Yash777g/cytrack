"""
Report listing + export.

    GET /reports            -> list all generated reports
    GET /reports/{id}/export -> download a report as JSON
"""
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from store import Report, reports

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[Report])
async def list_reports():
    return list(reports.values())


@router.get("/{report_id}/export")
async def export_report(report_id: str):
    report = reports.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")

    payload = json.dumps(report.model_dump(), indent=2)
    return StreamingResponse(
        iter([payload]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{report_id}.json"'},
    )
