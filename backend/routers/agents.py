"""
Agent listing + log retrieval.

    GET /agents            -> list all known agents
    GET /agents/{id}/logs   -> full log history for one agent
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from store import Agent, ScanStatus, agent_logs, agents

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentLogsResponse(BaseModel):
    agent_id: str
    status: ScanStatus
    lines: list[str]


@router.get("", response_model=list[Agent])
async def list_agents():
    return list(agents.values())


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
