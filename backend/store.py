"""
In-memory data layer shared across routers.

This stands in for a real database / message queue for now. Swap the
dicts below for real persistence (Postgres, Redis, etc.) once the rest
of the crawler/agent pipeline (see crawler-deephat-implement) is wired
in — the router code doesn't need to change, only this module.
"""
import asyncio
import itertools
import time
import uuid
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class Agent(BaseModel):
    id: str
    name: str
    target_url: str
    status: ScanStatus
    created_at: float


class ScanJob(BaseModel):
    id: str
    agent_id: str
    target_url: str
    depth: int
    status: ScanStatus
    created_at: float
    finished_at: Optional[float] = None


class Report(BaseModel):
    id: str
    agent_id: str
    scan_id: str
    title: str
    created_at: float
    summary: str


# ---- in-memory tables -------------------------------------------------
agents: Dict[str, Agent] = {}
scans: Dict[str, ScanJob] = {}
reports: Dict[str, Report] = {}
agent_logs: Dict[str, List[str]] = {}

# one asyncio.Queue per agent_id, used to fan out live log lines to any
# websocket clients subscribed to that agent's scan
_subscribers: Dict[str, List["asyncio.Queue[str]"]] = {}

_id_counter = itertools.count(1)


def new_id(prefix: str) -> str:
    return f"{prefix}_{next(_id_counter)}_{uuid.uuid4().hex[:6]}"


def subscribe(agent_id: str) -> "asyncio.Queue[str]":
    q: "asyncio.Queue[str]" = asyncio.Queue()
    _subscribers.setdefault(agent_id, []).append(q)
    return q


def unsubscribe(agent_id: str, q: "asyncio.Queue[str]") -> None:
    subs = _subscribers.get(agent_id, [])
    if q in subs:
        subs.remove(q)


def publish_log(agent_id: str, line: str) -> None:
    agent_logs.setdefault(agent_id, []).append(line)
    for q in _subscribers.get(agent_id, []):
        q.put_nowait(line)


async def run_fake_scan(job: ScanJob) -> None:
    """Background task that pretends to crawl and streams log lines.

    Replace the body of this loop with a call into the real crawler
    (see the `crawler/` and `agents/` folders in crawler-deephat-implement)
    once that integration point is ready.
    """
    agent = agents[job.agent_id]
    publish_log(agent.id, f"[{job.id}] scan started for {job.target_url} (depth={job.depth})")

    for page in range(1, job.depth + 1):
        job_current = scans.get(job.id)
        if job_current is None or job_current.status != ScanStatus.RUNNING:
            publish_log(agent.id, f"[{job.id}] scan stopped early at depth {page}")
            return
        await asyncio.sleep(1)
        publish_log(agent.id, f"[{job.id}] crawled page depth={page} -> found 12 links, 3 new hosts")

    job.status = ScanStatus.COMPLETED
    job.finished_at = time.time()
    agent.status = ScanStatus.COMPLETED
    publish_log(agent.id, f"[{job.id}] scan completed")

    report = Report(
        id=new_id("rpt"),
        agent_id=agent.id,
        scan_id=job.id,
        title=f"Scan report — {job.target_url}",
        created_at=time.time(),
        summary=f"Crawled {job.depth} levels deep from {job.target_url}.",
    )
    reports[report.id] = report
