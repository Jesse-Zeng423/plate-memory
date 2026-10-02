"""Validated private profiles with immutable revisions and atomic current pointer."""
from __future__ import annotations
from copy import deepcopy
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4
from .cli import read_text
from .food_adapter import ValidationError, validate_profile
from .json_contract import loads


def load_profile(path):
    return validate_profile(loads(read_text(Path(path))))


def save_profile(path, profile):
    validate_profile(profile)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    history = path.parent / (path.stem + '-history')
    history.mkdir(exist_ok=True, mode=0o700)
    data = json.dumps(profile, ensure_ascii=False, indent=2) + '\n'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    revision = history / (stamp + '-' + uuid4().hex + '.json')
    fd = os.open(revision, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(data)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.profile-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return revision


def update_record(profile, memory_id, action, today=None):
    updated = deepcopy(profile)
    fact = next((f for f in updated['memories'] if f['id'] == memory_id), None)
    if fact is None:
        raise ValidationError('Unknown record id.')
    if action == 'confirm':
        if fact['permission'] != 'ALLOWED':
            raise ValidationError('Confirmation does not grant permission. Explicitly allow use first.')
        if fact['superseded_by']:
            raise ValidationError('Confirm the replacement record instead.')
        fact['confirmed_on'] = (today or date.today()).isoformat()
    elif action == 'revoke':
        fact['permission'] = 'REVOKED'
    elif action == 'allow':
        fact['permission'] = 'ALLOWED'
    else:
        raise ValidationError('Unknown profile action.')
    return validate_profile(updated)
