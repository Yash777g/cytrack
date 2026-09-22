"""
Maps planner agent names to the active exploit-agent wrapper classes and
dispatches them defensively.

Each agent module under backend/agents/ exposes a thin wrapper class
(SQLAgent, XSSAgent, NoSQLAgent, AuthZAgent, PasswordPolicyAgent, SASTAgent)
whose .scan(...) signature differs, so every entry below is a small adapter
that knows how to call its agent from the planner's {agent, endpoint} task
plus the shared crawl context.

WARNING: these agents send real attack traffic to the target. They run only
when config.RUN_AGENTS is enabled (see core.pipeline).
"""
from store import ScanJob, agents, publish_log


def _log(agent_id: str, job_id: str, msg: str) -> None:
    publish_log(agent_id, f"[{job_id}] {msg}")


# -- adapters: each returns whatever the underlying agent produces ----------

def _run_sql(target, endpoint, context):
    from agents.sql_agent import SQLAgent

    return SQLAgent().scan(target=endpoint or target)


def _run_nosql(target, endpoint, context):
    from agents.nosql_agent import NoSQLAgent

    return NoSQLAgent().scan(url=endpoint or target)


def _run_password(target, endpoint, context):
    from agents.password_policy_agent import PasswordPolicyAgent

    return PasswordPolicyAgent().scan(target=endpoint or target)


def _run_xss(target, endpoint, context):
    from agents.xss_agent import XSSAgent

    # XSS agent consumes the spider JSON directly rather than a single URL.
    return XSSAgent().scan(spider_json=context.get("crawl_output"))


def _run_authz(target, endpoint, context):
    from agents.authz_agent import AuthZAgent

    endpoints = [e.get("url") for e in context.get("endpoints", []) if e.get("url")]
    return AuthZAgent().scan(base_url=target, endpoints=endpoints)


# sast_agent operates on a git repository, not a crawled URL, so it is not
# auto-dispatched from a web-crawl plan.
_REGISTRY = {
    "sql_agent": _run_sql,
    "nosql_agent": _run_nosql,
    "password_policy_agent": _run_password,
    "xss_agent": _run_xss,
    "authz_agent": _run_authz,
}


def run_planned_agents(job: ScanJob, plan: list[dict], context: dict) -> list[dict]:
    """Execute each planned agent task, one at a time, logging progress.

    Returns a list of {agent, endpoint, status, error?} result records.
    Agents are heavy and network-active; failures are isolated per task.
    """
    agent = agents[job.agent_id]
    results: list[dict] = []

    for task in plan:
        name = task.get("agent")
        endpoint = task.get("endpoint")
        runner = _REGISTRY.get(name)

        if runner is None:
            _log(agent.id, job.id, f"no adapter for agent '{name}', skipping")
            results.append({"agent": name, "endpoint": endpoint, "status": "skipped"})
            continue

        _log(agent.id, job.id, f"running {name} against {endpoint or job.target_url}")
        try:
            output = runner(job.target_url, endpoint, context)
            results.append(
                {
                    "agent": name,
                    "endpoint": endpoint,
                    "status": "completed",
                    "findings": _summarise(output),
                }
            )
            _log(agent.id, job.id, f"{name} completed")
        except Exception as exc:  # noqa: BLE001 - isolate per-agent failures
            _log(agent.id, job.id, f"{name} failed: {type(exc).__name__}: {exc}")
            results.append(
                {
                    "agent": name,
                    "endpoint": endpoint,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    return results


def _summarise(output):
    """Best-effort count of findings from heterogeneous agent return types."""
    if output is None:
        return 0
    try:
        return len(output)
    except TypeError:
        return "n/a"
