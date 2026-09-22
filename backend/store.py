"""
In-memory data layer shared across routers.

This stands in for a real database / message queue for now. Swap the
dicts below for real persistence (Postgres, Redis, etc.) once the rest
of the crawler/agent pipeline (see crawler-deephat-implement) is wired
in — the router code doesn't need to change, only this module.
"""
import asyncio
import itertools
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
