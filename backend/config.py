import os
from pathlib import Path

# Project Root
BASE_DIR = Path(__file__).resolve().parent

# Hellhound Project
HELLHOUND_DIR = BASE_DIR / "Hellhound-Spider"

# Output Folder
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Crawl Output (default, single-run convenience path)
CRAWL_OUTPUT = OUTPUT_DIR / "crawl.json"


def crawl_output_for(job_id: str) -> Path:
    """Deterministic per-job crawl output path so the analysis pipeline
    can reliably locate the JSON the spider produced for a given scan."""
    return OUTPUT_DIR / f"crawl_{job_id}.json"


def report_output_for(job_id: str) -> Path:
    """Where the analysis pipeline persists the structured report JSON."""
    return OUTPUT_DIR / f"report_{job_id}.json"


# ---- Feature flags --------------------------------------------------------
# DeepHat (local Ollama LLM) analysis is optional; when it is unavailable the
# pipeline falls back to ContextBuilder's heuristic potential_vulnerabilities.
USE_DEEPHAT = os.getenv("CYTRACK_USE_DEEPHAT", "0") == "1"

# Active exploit agents (SQLi/XSS/etc.) launch real attacks against the target.
# They are OFF by default so a crawl never silently weaponises the host.
RUN_AGENTS = os.getenv("CYTRACK_RUN_AGENTS", "0") == "1"
