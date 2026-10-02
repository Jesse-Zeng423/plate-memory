"""Strict bounded catalog contract; references never establish actual ingredients."""
import re
from ..food_adapter import ValidationError


def text(value, maximum=160):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
        raise ValidationError('Invalid catalog text.')
    return value


def validate_pack(pack):
    if not isinstance(pack, dict) or set(pack) != {'schema_version', 'items'} or type(pack['schema_version']) is not int or pack['schema_version'] != 1:
        raise ValidationError('Unknown public catalog schema.')
    items = pack['items']
    if not isinstance(items, list) or not 1 <= len(items) <= 500:
        raise ValidationError('Public catalog must contain 1–500 concepts.')
    ids = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {'id', 'name', 'names', 'aliases', 'search_terms', 'source'}:
            raise ValidationError('Invalid public dish fields.')
        qid = text(item['id'])
        if not re.fullmatch(r'Q[1-9][0-9]*', qid) or qid in ids:
            raise ValidationError('Duplicate or invalid public dish ID.')
        ids.add(qid)
        text(item['name'])
        if not isinstance(item['names'], dict) or not 1 <= len(item['names']) <= 8:
            raise ValidationError('Invalid catalog names.')
        for lang, name in item['names'].items():
            if lang not in ('en', 'mul', 'zh', 'zh-hans', 'zh-hant'):
                raise ValidationError('Unsupported catalog language.')
            text(name)
        for field in ('aliases', 'search_terms'):
            if not isinstance(item[field], list) or len(item[field]) > 100:
                raise ValidationError('Invalid catalog terms.')
            for term in item[field]:
                text(term)
        source = item['source']
        if not isinstance(source, dict) or set(source) != {'url', 'revision'} or source['url'] != 'https://www.wikidata.org/wiki/' + qid or type(source['revision']) is not int or source['revision'] <= 0:
            raise ValidationError('Invalid catalog provenance.')
    return pack
