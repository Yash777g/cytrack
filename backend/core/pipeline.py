"""
Analysis pipeline: turns a finished crawl into an actionable report.

    crawl JSON
       -> CrawlParser        (raw spider output -> normalised context)
       -> ContextBuilder     (optimised context + heuristic vulns)
       -> DeepHat (optional)  (LLM enrichment of potential_vulnerabilities)
       -> Planner            (which active agents should run, per endpoint)
       -> Report             (persisted + surfaced in the API)

Every stage is defensive: a failure in DeepHat or the parser degrades the
run rather than killing it, and each step publishes log lines so the
existing /agents/{id}/logs and /ws/scan streams show progress live.

Active exploit agents are dispatched only when config.RUN_AGENTS is set —
see core.agent_registry — because they launch real attacks at the target.
"""
import json
import time
from pathlib import Path

import config
from store import Report, ScanJob, agents, new_id, publish_log, reports


def _log(agent_id: str, job_id: str, msg: str) -> None:
    publish_log(agent_id, f"[{job_id}] {msg}")


def run_analysis(job: ScanJob, crawl_output: Path) -> Report | None:
    """Run the full analysis chain for a completed crawl.

    Returns the created Report, or None if the crawl output was unusable.
    """
    agent = agents[job.agent_id]
    _log(agent.id, job.id, "analysis pipeline started")

    # ---- 1. parse + build context ------------------------------------
    try:
        from crawler.parser import CrawlParser
        from analysis.context_builder import ContextBuilder

        parser = CrawlParser(crawl_output)
        parser.load()
        raw_context = parser.build_context()
        context = ContextBuilder(raw_context).build()
    except FileNotFoundError:
        _log(agent.id, job.id, f"analysis skipped: no crawl output at {crawl_output}")
        return None
    except Exception as exc:  # noqa: BLE001 - never crash the scan on bad data
        _log(agent.id, job.id, f"analysis failed while parsing: {type(exc).__name__}: {exc}")
        return None

    context["crawl_output"] = str(crawl_output)
    heuristic_vulns = context.get("potential_vulnerabilities", [])
    _log(
        agent.id,
        job.id,
        f"context built: {len(heuristic_vulns)} heuristic attack surface(s)",
    )

    # ---- 2. optional DeepHat enrichment ------------------------------
    if config.USE_DEEPHAT:
        try:
            from llm.prompts import PromptBuilder
            from llm.deephat import DeepHat

            _log(agent.id, job.id, "querying DeepHat for analysis...")
            prompt = PromptBuilder(context).build()
            deephat_result = DeepHat().analyze(prompt)
            # DeepHat's normalised potential_vulnerabilities feed the planner
            if deephat_result.get("potential_vulnerabilities"):
                context["potential_vulnerabilities"] = deephat_result[
                    "potential_vulnerabilities"
                ]
            context["deephat"] = deephat_result
            _log(agent.id, job.id, "DeepHat analysis complete")
        except Exception as exc:  # noqa: BLE001 - LLM is best-effort
            _log(
                agent.id,
                job.id,
                f"DeepHat unavailable, using heuristics only: {type(exc).__name__}: {exc}",
            )

    # ---- 3. plan active agents ---------------------------------------
    try:
        from orchestrator.planner import Planner

        plan = Planner(context).build_execution_plan()
    except Exception as exc:  # noqa: BLE001
        _log(agent.id, job.id, f"planner failed: {type(exc).__name__}: {exc}")
        plan = []

    _log(agent.id, job.id, f"execution plan: {len(plan)} agent task(s)")

    # ---- 4. optionally run the active agents -------------------------
    agent_results = []
    if plan and config.RUN_AGENTS:
        from core.agent_registry import run_planned_agents

        agent_results = run_planned_agents(job, plan, context)
    elif plan:
        _log(
            agent.id,
            job.id,
            "active agents NOT run (set CYTRACK_RUN_AGENTS=1 to enable)",
        )

    # ---- 5. build + persist the report -------------------------------
    details = {
        "target": context.get("target"),
        "summary": context.get("summary", {}),
        "statistics": context.get("statistics", {}),
        "potential_vulnerabilities": context.get("potential_vulnerabilities", []),
        "execution_plan": plan,
        "agent_results": agent_results,
        "deephat": context.get("deephat"),
    }

    report_path = config.report_output_for(job.id)
    try:
        report_path.write_text(json.dumps(details, indent=2), encoding="utf-8")
    except OSError as exc:
        _log(agent.id, job.id, f"could not persist report file: {exc}")

    report = Report(
        id=new_id("rpt"),
        agent_id=agent.id,
        scan_id=job.id,
        title=f"Scan report — {job.target_url}",
        created_at=time.time(),
        summary=(
            f"{len(context.get('potential_vulnerabilities', []))} potential "
            f"vulnerabilities, {len(plan)} agent task(s) planned for "
            f"{job.target_url}."
        ),
    )
    reports[report.id] = report
    _log(agent.id, job.id, f"report generated: {report.id}")
    return report
