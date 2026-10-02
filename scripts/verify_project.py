#!/usr/bin/env python3
"""Verify provenance, fixture integrity and packaging, without network/model calls."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.cli import load_demo
from src.food_adapter import menu_lines, targets, validate_profile


def main():
    metadata = json.loads((ROOT / "docs/provenance.json").read_text())
    engine = ROOT / metadata["destination"]
    assert hashlib.sha256(engine.read_bytes()).hexdigest() == metadata["sha256"], "Upstream guard fingerprint changed"
    text = engine.read_text().lower()
    assert "peanut" not in text and "menu" not in text, "Food concept leaked into generic engine"
    for required in ("README.md", "LICENSE", "AGENTS.md", "docs/core-api.md", "docs/devto-post.md", "src/cli.py", "src/extraction.py", "src/food_adapter.py", "src/terminal.py", "src/profile_store.py", "src/food_cache.py", "start.command"):
        assert (ROOT / required).is_file(), f"Missing {required}"
    profile = validate_profile(json.loads((ROOT / "examples/profile.json").read_text()))
    assert profile["friend"].startswith("Synthetic"), "Public examples must identify synthetic origin"
    scenarios = json.loads((ROOT / "examples/scenarios.json").read_text())
    for item in scenarios:
        menu = (ROOT / "examples" / item["menu"]).read_text()
        load_demo(ROOT / "examples" / item["extraction"], menu, targets(profile), menu_lines(menu))
    print(json.dumps({"status": "pass", "provenance_sha256": metadata["sha256"],
                      "synthetic_scenarios": len(scenarios), "external_api_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
