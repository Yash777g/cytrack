"""
cytrack backend — FastAPI entrypoint.

Run locally:
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload

Docs will be at http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import agents, reports, scan, ws
from routers import agents, dashboard, reports, scan, ws

app = FastAPI(title="cytrack API", version="0.1.0")

# open CORS for local frontend dev; tighten before deploying
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router)
app.include_router(agents.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}