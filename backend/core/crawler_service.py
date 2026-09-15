import asyncio
import os
import subprocess
import time

from store import (
    ScanJob,
    ScanStatus,
    agents,
    scans,
    publish_log,
)


async def start_crawl(job: ScanJob) -> None:
    """
    Run HellHound in a worker thread so subprocess execution
    works reliably with FastAPI/Uvicorn on Windows.
    """
    agent = agents[job.agent_id]

    publish_log(
        agent.id,
        f"[{job.id}] crawler started for {job.target_url}",
    )

    def run_spider() -> int:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        process = subprocess.Popen(
            [
                "spider",
                job.target_url,
                "--depth",
                str(job.depth),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        assert process.stdout is not None

        for line in process.stdout:
            current_job = scans.get(job.id)

            if (
                current_job is None
                or current_job.status != ScanStatus.RUNNING
            ):
                publish_log(
                    agent.id,
                    f"[{job.id}] crawler stopping...",
                )

                process.terminate()

                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

                return process.returncode or 0

            text = line.strip()

            if text:
                publish_log(
                    agent.id,
                    f"[{job.id}] {text}",
                )

        return process.wait()

    try:
        return_code = await asyncio.to_thread(run_spider)

        if job.status == ScanStatus.STOPPED:
            return

        job.finished_at = time.time()

        if return_code == 0:
            job.status = ScanStatus.COMPLETED
            agent.status = ScanStatus.COMPLETED

            publish_log(
                agent.id,
                f"[{job.id}] crawler completed",
            )

        else:
            job.status = ScanStatus.FAILED
            agent.status = ScanStatus.FAILED

            publish_log(
                agent.id,
                f"[{job.id}] crawler failed with code {return_code}",
            )

    except Exception as exc:
        job.status = ScanStatus.FAILED
        job.finished_at = time.time()
        agent.status = ScanStatus.FAILED

        publish_log(
            agent.id,
            f"[{job.id}] crawler error: "
            f"{type(exc).__name__}: {repr(exc)}",
        )