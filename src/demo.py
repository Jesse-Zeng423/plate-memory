"""Fingerprint-bound synthetic extraction fixtures; no model calls."""
import hashlib
import json
from pathlib import Path
from .file_io import read_text
from .food_adapter import ValidationError, validate_candidates
from .json_contract import loads


def load_demo(path: Path, menu: str, allowed: list[dict], lines: list[dict]) -> dict:
    value = loads(read_text(path))
    if not isinstance(value, dict) or set(value) != {"menu_sha256", "targets_sha256", "extraction"}:
        raise ValidationError("Demo fixture needs menu_sha256, targets_sha256 and extraction.")
    target_hash = hashlib.sha256(json.dumps(allowed, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if value["menu_sha256"] != hashlib.sha256(menu.encode()).hexdigest() or value["targets_sha256"] != target_hash:
        raise ValidationError("Demo fixture fingerprints do not match the exact menu and permitted targets.")
    return validate_candidates(value["extraction"], lines, allowed)
