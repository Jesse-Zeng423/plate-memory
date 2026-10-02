"""Private cache of grounded food spans only; never cache policy decisions."""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
from pathlib import Path
from .food_adapter import ValidationError, candidates_from_foods
from .json_contract import loads


def key(lines, model):
    from .extraction import PROMPT_VERSION, SYSTEM, LABEL_SCHEMA
    payload = [lines, model, PROMPT_VERSION, SYSTEM, LABEL_SCHEMA]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def checked(values, lines):
    if not isinstance(values, list) or len(values) != len(lines):
        raise ValidationError("Invalid food cache. Delete the local cache file and retry.")
    for line, value in zip(lines, values):
        candidates_from_foods(value, line, [])
    return values


def read_cache(directory, lines, model):
    path = Path(directory) / (key(lines, model) + '.json')
    if not path.exists():
        return None
    if path.stat().st_size > 256000:
        raise ValidationError("Food cache exceeds size limit. Delete the local cache file and retry.")
    data = loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or set(data) != {'key', 'foods'} or data['key'] != key(lines, model):
        raise ValidationError("Food cache fingerprint mismatch. Delete the local cache file and retry.")
    return checked(data['foods'], lines)


def write_cache(directory, lines, model, values):
    checked(values, lines)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / (key(lines, model) + '.json')
    # Publish only a complete file; cancellation cannot leave a partial cache entry.
    fd, temporary = tempfile.mkstemp(dir=directory, prefix='.foods-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump({'key': key(lines, model), 'foods': values}, stream, ensure_ascii=False)
        try:
            os.link(temporary, path)
        except FileExistsError:
            read_cache(directory, lines, model)
    finally:
        os.unlink(temporary)
