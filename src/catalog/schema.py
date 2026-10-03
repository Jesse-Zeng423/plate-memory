"""Strict bounded catalog contract; references never establish actual ingredients."""
import re
from ..food_adapter import ValidationError


def text(value, maximum=160):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
        raise ValidationError('Invalid catalog text.')
    return value


def validate_pack(pack):
    if not isinstance(pack, dict) or set(pack) != {'schema_version', 'items'} or type(pack['schema_version']) is not int or pack['schema_version'] not in (1, 2):
        raise ValidationError('Unknown public catalog schema.')
    items = pack['items']
    if not isinstance(items, list) or not 1 <= len(items) <= (500 if pack['schema_version']==1 else 5000):
        raise ValidationError('Public catalog must contain a bounded number of concepts.')
    version=pack['schema_version']
    ids = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != ({'id', 'name', 'names', 'aliases', 'search_terms', 'source'} | ({'kind','category'} if version==2 else set())):
            raise ValidationError('Invalid public dish fields.')
        qid = text(item['id'])
        if not re.fullmatch(r'Q[1-9][0-9]*' if version==1 else r'(wikidata:Q|usda:)[1-9][0-9]*', qid) or qid in ids:
            raise ValidationError('Duplicate or invalid public dish ID.')
        ids.add(qid)
        text(item['name'],320)
        if not isinstance(item['names'], dict) or not 1 <= len(item['names']) <= 8:
            raise ValidationError('Invalid catalog names.')
        for lang, name in item['names'].items():
            if lang not in ('en', 'mul', 'zh', 'zh-hans', 'zh-hant'):
                raise ValidationError('Unsupported catalog language.')
            text(name,320)
        for field in ('aliases', 'search_terms'):
            if not isinstance(item[field], list) or len(item[field]) > 100:
                raise ValidationError('Invalid catalog terms.')
            for term in item[field]:
                text(term)
        source = item['source']
        if version==1:
            if not isinstance(source,dict) or set(source)!={'url','revision'} or source['url']!='https://www.wikidata.org/wiki/'+qid or type(source['revision']) is not int or source['revision']<=0:
                raise ValidationError('Invalid catalog provenance.')
        else:
            if item['kind'] not in ('dish','reference_food','ingredient'):
                raise ValidationError('Invalid concept kind.')
            if item['category'] is not None:text(item['category'])
            provider=qid.split(':')[0]
            expected='https://www.wikidata.org/wiki/'+qid.split(':')[1] if provider=='wikidata' else 'https://fdc.nal.usda.gov/food-details/'+qid.split(':')[1]+'/nutrients'
            if not isinstance(source,dict) or set(source)!={'provider','url','revision','license'} or source['provider']!=provider or source['url']!=expected or source['license']!='CC0-1.0':
                raise ValidationError('Invalid catalog provenance.')
            if provider=='wikidata':
                if type(source['revision']) is not int or source['revision']<=0:raise ValidationError('Invalid revision.')
            elif source['revision']!='FNDDS 2021-2023 / 2024-10-31':
                raise ValidationError('Unknown USDA release.')
    return pack
