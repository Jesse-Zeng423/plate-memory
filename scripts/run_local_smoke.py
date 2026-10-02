#!/usr/bin/env python3
"""Opt-in local inference on four public synthetic fixtures; no cloud endpoints.

Not part of routine verification. Run only after explicitly choosing to download
and exercise gemma3:4b. Saves a new evidence version, never overwrites a checkpoint.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.food_adapter import build_report, menu_lines, parse_date, targets, validate_profile
from src.extraction import ExtractionError, local_extract, SYSTEM, PROMPT_VERSION


def main():
    # Provenance + synthetic public-pack/fingerprint check BEFORE model requests.
    subprocess.run([sys.executable, "-B", str(ROOT / "scripts/verify_project.py")], check=True)
    if len(sys.argv) != 2 or not sys.argv[1].startswith("v") or not sys.argv[1][1:].isdigit():
        raise SystemExit("Usage: python3 scripts/run_local_smoke.py v1 (new version only)")
    output = ROOT / "docs" / f"local-smoke-{sys.argv[1]}.json"
    if output.exists():
        raise SystemExit("Evidence checkpoint already exists; select a new version.")
    p = validate_profile(json.loads((ROOT / "examples/profile.json").read_text()))
    scenarios = json.loads((ROOT / "examples/scenarios.json").read_text())
    results = []
    for item in scenarios:
        menu = (ROOT / "examples" / item["menu"]).read_text()
        start = time.monotonic()
        try:
            extraction = local_extract(menu_lines(menu), targets(p), "gemma3:4b", 180)
        except ExtractionError as error:
            results.append({"scenario": item["name"], "result": "rejected", "error": str(error),
                            "raw_model_response": error.raw_response,
                            "elapsed_seconds": round(time.monotonic()-start, 3)})
            print(f"{item['name']}: rejected ({error})", flush=True)
            continue
        report = build_report(p, extraction, parse_date(item["date"]), "local-ollama", "gemma3:4b")
        expected = json.loads((ROOT / "examples" / item["expected"]).read_text())
        expected_actions = {d["memory_id"]: (d["guard_verdict"], d["memory_action"]) for d in expected["decisions"]}
        actual_actions = {d["memory_id"]: (d["guard_verdict"], d["memory_action"]) for d in report["decisions"]}
        entry = {"scenario": item["name"], "menu_sha256": hashlib.sha256(menu.encode()).hexdigest(),
                 "elapsed_seconds": round(time.monotonic()-start, 3), "extraction": extraction,
                 "guard_actions_match_canned_scenario": actual_actions == expected_actions,
                 "report": report}
        if item["name"] == "weekend":
            friday = build_report(p, extraction, parse_date("2026-10-02"), "local-ollama", "gemma3:4b")
            entry["same_extraction_friday_report"] = friday
        results.append(entry)
        print(f"{item['name']}: {len(extraction['candidates'])} candidates, {entry['elapsed_seconds']}s, expected guard actions={entry['guard_actions_match_canned_scenario']}", flush=True)
    document = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "model": "gemma3:4b", "endpoint": "http://127.0.0.1:11434",
                "prompt_version": PROMPT_VERSION,
                "system_prompt_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
                "profile_sha256": hashlib.sha256((ROOT / "examples/profile.json").read_bytes()).hexdigest(),
                "synthetic_input_only": True, "public_pack_check": "scripts/verify_project.py passed before requests",
                "scenarios": len(results),
                "generation_calls_if_all_scenarios_complete": sum(len(menu_lines((ROOT / "examples" / item["menu"]).read_text())) for item in scenarios),
                "external_inference_calls": 0,
                "boundary": "Four hand-authored synthetic examples; not an extraction accuracy estimate or safety validation.",
                "results": results}
    with output.open("x") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(output)


if __name__ == "__main__":
    main()
