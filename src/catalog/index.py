"""Verified local catalog loading and deterministic keyword lookup."""
import hashlib
import re
from ..paths import ROOT
from ..json_contract import loads
from ..food_adapter import ValidationError
from .normalize import normalized,contains,NEGATION
from .schema import validate_pack
from ..file_io import read_text


class Catalog:
    def __init__(self, directory=None):
        directory = directory or ROOT / 'data/catalog/v3'
        raw = read_text(directory / 'dishes.json', maximum=8_000_000).encode('utf-8')
        if len(raw) > 8_000_000:
            raise ValidationError('Public catalog is too large.')
        manifest = loads(read_text(directory / 'manifest.json',maximum=32000))
        if type(manifest.get('schema_version')) is not int or manifest.get('schema_version') not in (1,2) or manifest.get('file') != 'dishes.json' or manifest.get('license') != 'CC0-1.0' or hashlib.sha256(raw).hexdigest() != manifest.get('sha256'):
            raise ValidationError('Public catalog manifest or fingerprint mismatch.')
        pack=validate_pack(loads(raw.decode('utf-8')))
        self.version=pack['schema_version']
        if self.version!=manifest['schema_version']:raise ValidationError('Catalog version mismatch.')
        self.items=pack['items']
        self.terms={item['id']:[normalized(t) for t in [item['name'],*item['names'].values(),*item['aliases'],*item['search_terms']]] for item in self.items}
        self.vocabulary=sorted({term for terms in self.terms.values() for term in terms if len(term)<=80})
        if type(manifest.get('count')) is not int or manifest['count'] != len(self.items):
            raise ValidationError('Public catalog count mismatch.')

    def search(self, query='', limit=3, offset=0, category=None):
        if not isinstance(query,str) or len(query)>160 or type(limit) is not int or not 0<=limit<=100 or type(offset) is not int or offset<0:
            raise ValidationError('Use a short food query and valid page size.')
        if limit==0:return []
        query=normalized(query)
        if re.search(NEGATION,query):return []
        matches=[]
        for item in self.items:
            if category is not None and item.get('category')!=category:continue
            terms=self.terms[item['id']]
            if not query or any(contains(term,query) for term in terms):
                exact=[normalized(t) for t in [item['name'],*item['names'].values(),*item['aliases']]]
                score=0 if query in exact else 1
                if not query and self.version==2:
                    score={'wikidata:Q28803':0,'wikidata:Q41415':1,'wikidata:Q192874':2}.get(item['id'],3)
                    if item.get('kind')=='ingredient':continue
                matches.append((score,len(item['name']) if query else 0,item))
        suggested=False
        if not matches and query and self.version==2 and len(query)>=3:
            # Suggestions never establish an exact match; UI labels and confirms.
            from difflib import get_close_matches
            close=set(get_close_matches(query,self.vocabulary,n=3,cutoff=.86))
            for item in self.items:
                if category is not None and item.get('category')!=category:continue
                if close.intersection(self.terms[item['id']]):matches.append((2,len(item['name']),item))
            suggested=True
        matches.sort(key=lambda row:(row[0],row[1],normalized(row[2]['name']),row[2]['id']))
        return [dict(item,match_kind='suggested' if suggested else 'literal') for _,_,item in matches[offset:offset+limit]]

    def categories(self):
        return sorted({item['category'] for item in self.items if item.get('category')})
