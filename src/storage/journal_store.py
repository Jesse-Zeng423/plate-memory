"""Private versioned observed checkins with transactional, conflict-checked updates."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3

from ..domain.checkin import MAX_CHECKINS, validate_checkin
from ..food_adapter import ValidationError
from ..json_contract import loads


class JournalStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else None
        self.connection = None

    def _db(self):
        if self.connection is not None:
            return self.connection
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
            os.close(fd)
            os.chmod(self.path, 0o600)
        db = sqlite3.connect(str(self.path) if self.path is not None else ':memory:', timeout=5)
        try:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise ValidationError('Journal database version is newer than this app. No migration was attempted.')
            db.execute('PRAGMA secure_delete = ON')
            if version == 0:
                # Never repurpose an unrelated SQLite file.
                if db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                    raise ValidationError('Unrecognized journal database; refusing to change it.')
                with db:
                    db.execute('CREATE TABLE checkins (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, payload TEXT NOT NULL)')
                    db.execute('PRAGMA user_version = 1')
        except Exception:
            db.close()
            raise
        self.connection = db
        return db

    def list(self):
        # Browsing an empty real account does not create files.
        if self.connection is None and self.path is not None and not self.path.exists():
            return []
        rows = self._db().execute('SELECT payload, revision FROM checkins ORDER BY id').fetchall()
        if len(rows) > MAX_CHECKINS:
            raise ValidationError('Journal database exceeds its record limit.')
        return [(deepcopy(validate_checkin(loads(payload))), revision) for payload, revision in rows]

    def save(self, meal, expected_revision=None):
        validate_checkin(meal)
        db = self._db()
        with db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT revision FROM checkins WHERE id=?', (meal['id'],)).fetchone()
            if row is None:
                if expected_revision is not None:
                    raise ValidationError('This record was removed elsewhere. Reload your meal records.')
                if db.execute('SELECT COUNT(*) FROM checkins').fetchone()[0] >= MAX_CHECKINS:
                    raise ValidationError(f'Keep at most {MAX_CHECKINS} meal records.')
                revision = 1
                db.execute('INSERT INTO checkins VALUES (?, ?, ?)', (meal['id'], revision, json.dumps(meal, ensure_ascii=False)))
            else:
                if expected_revision != row[0]:
                    raise ValidationError('This record changed elsewhere. Reload it before saving.')
                revision = row[0] + 1
                db.execute('UPDATE checkins SET revision=?, payload=? WHERE id=?',
                           (revision, json.dumps(meal, ensure_ascii=False), meal['id']))
        return revision

    def delete(self, meal_id, expected_revision):
        db = self._db()
        with db:
            deleted = db.execute('DELETE FROM checkins WHERE id=? AND revision=?', (meal_id, expected_revision))
            if deleted.rowcount != 1:
                raise ValidationError('This record changed elsewhere. Reload it before deleting.')

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
