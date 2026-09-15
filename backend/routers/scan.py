"""
Scan control endpoints.

    POST /scan/start   -> kick off a new crawl job for an agent
    GET  /scan/status   -> poll the status of a job
    POST /scan/stop     -> stop a running job
"""
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from store import Agent, ScanJob, ScanStatus, agents, new_id, scans
from core.crawler_service import start_crawl

router = APIRouter(prefix="/scan", tags=["scan"])


class ScanStartRequest(BaseModel):
    target_url: str = Field(..., examples=["https://example.com"])
    depth: int = Field(default=3, ge=1, le=20)
    agent_name: str | None = Field(default=None, description="Optional label for the agent")


class ScanStartResponse(BaseModel):
    job_id: str
    agent_id: str
    status: ScanStatus


class ScanStatusResponse(BaseModel):
    job_id: str
    agent_id: str
    status: ScanStatus
    target_url: str
    depth: int
    created_at: float
    finished_at: float | None


class ScanStopRequest(BaseModel):
    job_id: str


@router.post("/start", response_model=ScanStartResponse)
async def start_scan(payload: ScanStartRequest):
    agent = Agent(
        id=new_id("agent"),
        name=payload.agent_name or f"agent-{payload.target_url}",
        target_url=payload.target_url,
        status=ScanStatus.RUNNING,
        created_at=time.time(),
    )
    agents[agent.id] = agent

    job = ScanJob(
        id=new_id("job"),
        agent_id=agent.id,
        target_url=payload.target_url,
        depth=payload.depth,
        status=ScanStatus.RUNNING,
        created_at=time.time(),
    )
    scans[job.id] = job

    # fire-and-forget background crawl simulation; publishes log lines
    # that GET /agents/{id}/logs and the /ws/scan websocket both read from
    import asyncio

    asyncio.create_task(start_crawl(job))

    return ScanStartResponse(job_id=job.id, agent_id=agent.id, status=job.status)


@router.get("/status", response_model=ScanStatusResponse)
async def scan_status(job_id: str):
    job = scans.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return ScanStatusResponse(
        job_id=job.id,
        agent_id=job.agent_id,
        status=job.status,
        target_url=job.target_url,
        depth=job.depth,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


@router.post("/stop", response_model=ScanStatusResponse)
async def stop_scan(payload: ScanStopRequest):
    job = scans.get(payload.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if job.status == ScanStatus.RUNNING:
        job.status = ScanStatus.STOPPED
        job.finished_at = time.time()
        agent = agents.get(job.agent_id)
        if agent:
            agent.status = ScanStatus.STOPPED
    return ScanStatusResponse(
        job_id=job.id,
        agent_id=job.agent_id,
        status=job.status,
        target_url=job.target_url,
        depth=job.depth,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )
