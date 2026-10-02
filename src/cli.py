"""Run with python3 -m src.cli, or python3 /absolute/path/src/cli.py."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import date

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "src"

from .food_adapter import (ValidationError, build_report, menu_lines, parse_date,
                     targets, validate_candidates, validate_profile)
from .extraction import ExtractionError, local_extract, model_name
from .json_contract import JsonContractError, loads

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path, maximum: int = 128000) -> str:
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValidationError(f"Input file exceeds {maximum} bytes.")
    return raw.decode("utf-8")


def load_demo(path: Path, menu: str, allowed: list[dict], lines: list[dict]) -> dict:
    value = loads(read_text(path))
    if not isinstance(value, dict) or set(value) != {"menu_sha256", "targets_sha256", "extraction"}:
        raise ValidationError("Demo fixture needs menu_sha256, targets_sha256 and extraction.")
    target_hash = hashlib.sha256(json.dumps(allowed, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if value["menu_sha256"] != hashlib.sha256(menu.encode()).hexdigest() or value["targets_sha256"] != target_hash:
        raise ValidationError("Demo fixture fingerprints do not match the exact menu and permitted targets.")
    return validate_candidates(value["extraction"], lines, allowed)


def render(report: dict) -> str:
    output = [f"Plate Memory · {report['friend']} · {report['meal_date']}",
              f"Extraction: {report['extraction_mode']}" + (f" ({report['model']})" if report['model'] else " — canned fixture, no AI inference"),
              report["notice"], ""]
    for d in report["decisions"]:
        output.extend([f"[{d['guard_verdict']} / {d['memory_action']}] {d['memory_id']}: {d['memory']}",
                       f"  Reason: {d['reason_code']}", f"  {d['advice']}"])
        for candidate in d["candidates"]:
            output.append(f"  {candidate['line_id']} · {candidate['match']} · {candidate['quote']}")
        if d["observations"]:
            output.append("  Context: " + ", ".join(d["observations"]))
        output.append("")
    return "\n".join(output).rstrip() + "\n"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Local menu extraction, deterministic memory applicability. No food safety clearance.")
    p.add_argument("--profile", type=Path, default=ROOT / "examples/profile.json", help="Local profile JSON; default is explicitly synthetic.")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--menu", type=Path, help="UTF-8 menu file.")
    source.add_argument("--stdin", action="store_true", help="Read pasted menu from standard input.")
    p.add_argument("--date", type=parse_date, default=date.today(), help="Meal date YYYY-MM-DD (default: local today).")
    p.add_argument("--model", type=model_name, default="gemma3:4b", help="Downloaded local Ollama model.")
    p.add_argument("--timeout", type=float, default=180, help="Local request timeout in seconds, 1–600.")
    p.add_argument("--offline", action="store_true", help="Explicit canned demo mode; does not run AI.")
    p.add_argument("--demo-extraction", type=Path, help="Fingerprint-bound canned extraction; required with --offline.")
    p.add_argument("--json", action="store_true", help="Print structured decisions instead of text.")
    return p


def main(argv: list[str] | None = None) -> int:
    p = parser()
    try:
        args = p.parse_args(argv)
        if not 1 <= args.timeout <= 600:
            raise ValidationError("--timeout must be 1–600 seconds.")
        if args.offline != (args.demo_extraction is not None):
            raise ValidationError("--offline and --demo-extraction must be supplied together.")
        profile = validate_profile(loads(read_text(args.profile)))
        menu = sys.stdin.read(12001) if args.stdin else read_text(args.menu, 48000)
        lines = menu_lines(menu)
        allowed = targets(profile)
        if args.offline:
            extraction = load_demo(args.demo_extraction, menu, allowed, lines)
            mode, model = "canned-demo", None
        elif not allowed:
            extraction = {"candidates": []}
            mode, model = "permission-withheld-no-inference", None
        else:
            extraction = local_extract(lines, allowed, args.model, args.timeout)
            mode, model = "local-ollama", args.model
        report = build_report(profile, extraction, args.date, mode, model)
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render(report), end="\n" if args.json else "")
        return 0
    except (ValidationError, ExtractionError, JsonContractError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Plate Memory: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
