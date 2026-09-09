# cytrack backend

FastAPI service exposing the scan / agent / report / websocket routers.

## Run locally

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn main:app --reload
```

Interactive docs: http://127.0.0.1:8000/docs

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/scan/start` | Start a scan job. Body: `{"target_url": "...", "depth": 3, "agent_name": "optional"}` → returns `job_id`, `agent_id` |
| GET | `/scan/status?job_id=...` | Poll job status |
| POST | `/scan/stop` | Body: `{"job_id": "..."}` — stop a running job |
| GET | `/agents` | List all agents |
| GET | `/agents/{id}/logs` | Full log history for one agent |
| GET | `/reports` | List generated reports |
| GET | `/reports/{id}/export` | Download a report as JSON |
| WS | `/ws/scan?agent_id=...` | Live-tail an agent's log lines as they're produced |

## Quick manual test

```bash
# 1. start a scan
curl -X POST http://127.0.0.1:8000/scan/start \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com", "depth": 3}'
# -> {"job_id": "...", "agent_id": "...", "status": "running"}

# 2. check status
curl "http://127.0.0.1:8000/scan/status?job_id=<job_id>"

# 3. watch it live over websocket (e.g. with websocat or the browser devtools console)
websocat "ws://127.0.0.1:8000/ws/scan?agent_id=<agent_id>"
```

## Notes / next steps

- `store.py` is an in-memory stand-in for real persistence. Swap it for
  Postgres/Redis/etc. once ready — router code doesn't need to change.
- `store.run_fake_scan()` simulates crawling with `asyncio.sleep`. Replace
  its body with a real call into the crawler/agent pipeline from
  `crawler-deephat-implement` when that integration point is ready.
- CORS is wide open (`allow_origins=["*"]`) for local frontend dev —
  restrict this before deploying anywhere real.
