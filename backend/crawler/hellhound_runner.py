import subprocess
import time
from pathlib import Path


class HellhoundRunner:
    """
    Runs Hellhound Spider and saves crawl output.
    """

    def __init__(self, hellhound_dir: Path, output_file: Path):
        self.hellhound_dir = hellhound_dir
        self.output_file = output_file

    def run(self, url: str) -> bool:

        command = [
            "spider",
            url,
            "-o",
            str(self.output_file)
        ]

        print("=" * 60)
        print("Starting Hellhound Spider...")
        print(f"Target : {url}")
        print("=" * 60)

        start = time.time()

        try:

            result = subprocess.run(
                command,
                cwd=self.hellhound_dir,
                text=True
            )

            elapsed = time.time() - start

            print("\n" + "=" * 60)
            print("Hellhound Finished")
            print(f"Time : {elapsed:.2f} seconds")
            print(f"Output : {self.output_file}")
            print("=" * 60)

            return result.returncode == 0

        except Exception as e:

            print(f"\nError running Hellhound\n{e}")

            return False