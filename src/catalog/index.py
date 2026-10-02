"""Verified local catalog loading and deterministic keyword lookup."""
import hashlib
import re
from ..paths import ROOT
from ..json_contract import loads
from ..food_adapter import ValidationError
from ..services.meal_choices import normalized
from .schema import validate_pack


class Catalog:
    def __init__(self, directory=None):
        directory = directory or ROOT / 'data/catalog/v1'
        raw = (directory / 'dishes.json').read_bytes()
        if len(raw) > 2_000_000:
            raise ValidationError('Public catalog is too large.')
        manifest = loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('schema_version') != 1 or manifest.get('file') != 'dishes.json' or manifest.get('license') != 'CC0-1.0' or hashlib.sha256(raw).hexdigest() != manifest.get('sha256'):
            raise ValidationError('Public catalog manifest or fingerprint mismatch.')
        self.items = validate_pack(loads(raw.decode('utf-8')))['items']
        if type(manifest.get('count')) is not int or manifest['count'] != len(self.items):
            raise ValidationError('Public catalog count mismatch.')

    def search(self, query='', limit=3):
        if not isinstance(query, str) or len(query) > 160:
            raise ValidationError('Use a dish keyword up to 160 characters.')
        query = normalized(query)
        # Constraints must never become positive dish matches. Literal mode asks
        # the user to review a real menu instead of pretending to parse wishes.
        if re.search(r'\b(no|not|without|avoid|free|under|less)\b|不要|不吃|不含|过敏|過敏|以内|以內', query):
            return []
        matches = []
        for item in self.items:
            terms = [normalized(t) for t in [item['name'], *item['names'].values(), *item['aliases'], *item['search_terms']]]
            def contains(term):
                return all((token in term if any('\u3400' <= c <= '\u9fff' for c in token) else re.search(r'(?<!\w)' + re.escape(token) + r'(?!\w)', term)) for token in query.split())
            if not query or any(contains(term) for term in terms):
                matches.append((0 if query in terms else 1, item))
        matches.sort(key=lambda row: (row[0], normalized(row[1]['name']), row[1]['id']))
        return [item for _, item in matches[:limit]]
