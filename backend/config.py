from pathlib import Path

# Project Root
BASE_DIR = Path(__file__).resolve().parent

# Hellhound Project
HELLHOUND_DIR = BASE_DIR / "Hellhound-Spider"

# Output Folder
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Crawl Output
CRAWL_OUTPUT = OUTPUT_DIR / "crawl.json"