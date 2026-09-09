"""
Live log streaming over WebSocket.

    ws://.../ws/scan?agent_id=<id>   -> streams live agent logs as they're produced

Connect after calling POST /scan/start (which returns an agent_id), and
you'll get every log line pushed in real time, plus the backlog that
was already recorded for that agent.
"""
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from store import agent_logs, agents, subscribe, unsubscribe

router = APIRouter(tags=["ws"])


@router.websocket("/ws/scan")
async def ws_scan_logs(websocket: WebSocket, agent_id: str):
    await websocket.accept()

    if agent_id not in agents:
        await websocket.send_json({"error": f"unknown agent_id: {agent_id}"})
        await websocket.close()
        return

    # send whatever's already been logged, then live-tail new lines
    for line in agent_logs.get(agent_id, []):
        await websocket.send_json({"agent_id": agent_id, "line": line})

    queue = subscribe(agent_id)
    try:
        while True:
            line = await queue.get()
            await websocket.send_json({"agent_id": agent_id, "line": line})
    except WebSocketDisconnect:
        pass
    finally:
        unsubscribe(agent_id, queue)
