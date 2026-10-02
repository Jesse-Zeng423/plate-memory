#!/usr/bin/env python3
"""Execute fingerprint-bound demo scenarios; never call a model."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    scenarios = json.loads((ROOT / "examples/scenarios.json").read_text())
    with tempfile.TemporaryDirectory(prefix="plate-memory-demo-") as work:
        for item in scenarios:
            command = [sys.executable, "-B", str(ROOT / "src/cli.py"),
                       "--menu", str(ROOT / "examples" / item["menu"]),
                       "--offline", "--demo-extraction", str(ROOT / "examples" / item["extraction"]),
                       "--date", item["date"], "--json"]
            result = subprocess.run(command, cwd=work, capture_output=True, text=True)
            if result.returncode:
                raise SystemExit(result.stderr)
            report = json.loads(result.stdout)
            expected = json.loads((ROOT / "examples" / item["expected"]).read_text())
            if report != expected:
                raise SystemExit(f"Unexpected output: {item['name']}")
            print(f"PASS {item['name']} (unrelated working directory, no API calls)")


if __name__ == "__main__":
    main()
