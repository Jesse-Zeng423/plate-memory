"""Versioned source data, explicit guesses, paging and negative-query boundaries."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.catalog.index import Catalog
from src.catalog.schema import validate_pack
from src.food_adapter import ValidationError
from src.paths import ROOT
from src.terminal import main
from src.services.search import discover
from src.storage.meal_store import MealStore
from src.domain.meals import empty_meal


class V2Tests(unittest.TestCase):
    def test_frozen_public_query_set_has_hits_and_preserves_negative_queries(self):
        cases=json.loads((ROOT/'examples/catalog-queries-v2.json').read_text())
        catalog=Catalog()
        for query in cases['positive']:
            with self.subTest(query=query):self.assertTrue(catalog.search(query))
        for query in cases['negative']:
            with self.subTest(query=query):self.assertEqual(catalog.search(query),[])
        for query in ('egg','鸡蛋'):
            self.assertEqual(catalog.search(query)[0]['kind'],'ingredient')
            self.assertEqual(catalog.search(query)[0]['id'],'usda:2707152')
        self.assertEqual(catalog.search('pizza')[0]['id'],'wikidata:Q177')

    def test_suggestions_are_labeled_and_source_records_are_not_mutated(self):
        catalog=Catalog()
        self.assertEqual(catalog.search('piza')[0]['match_kind'],'suggested')
        self.assertEqual(catalog.search('xyz123'),[])
        before=catalog.search('rice',limit=6)
        self.assertEqual(catalog.search('rice',offset=3),before[3:])
        catalog.items.reverse()
        self.assertEqual(catalog.search('rice',limit=6),before)
        self.assertTrue(all('match_kind' not in item for item in catalog.items))
        self.assertTrue(all(item.get('category')=='Pizza' for item in catalog.search('',category='Pizza')))
        self.assertEqual(catalog.search('',limit=0),[])

    def test_bad_source_url_and_unknown_version_are_rejected(self):
        pack=json.loads((ROOT/'data/catalog/v2/dishes.json').read_text())
        pack['items'][0]['source']['url']='https://evil.example/q'
        with self.assertRaises(ValidationError):validate_pack(pack)
        pack['schema_version']=9
        with self.assertRaises(ValidationError):validate_pack(pack)

    def test_saved_and_public_pages_have_no_skipped_or_duplicate_choices(self):
        store=MealStore()
        try:
            for n in range(4):
                item=empty_meal('cafeteria');item['name']='Pizza '+str(n);store.save(item)
            catalog=Catalog()
            first=discover(store,'cafeteria','pizza',catalog,offset=0)
            second=discover(store,'cafeteria','pizza',catalog,offset=3)
            third=discover(store,'cafeteria','pizza',catalog,offset=6)
            self.assertEqual(len(first[0]),3)
            self.assertEqual(len(second[0]),1)
            self.assertEqual(second[1][0][1]['id'],'wikidata:Q177')
            ids=[i['id'] for a,b in (first,second,third) for _,i in a+b]
            self.assertEqual(len(ids),len(set(ids)))
        finally:store.close()

    def test_terminal_pages_categories_and_guess_confirmation_are_offline(self):
        with tempfile.TemporaryDirectory() as work:
            with patch('builtins.input',side_effect=['today','2','piza','1','back','pizza','next','previous','categories','1','1','pick','quit']),patch('socket.socket',side_effect=AssertionError('No runtime network')),redirect_stdout(StringIO()) as out:
                self.assertEqual(main(['--profile',str(Path(work)/'f.json'),'--plain']),0)
            self.assertIn('[suggested match]',out.getvalue())
            self.assertIn('Browse a food family',out.getvalue())
            self.assertEqual(list(Path(work).iterdir()),[])
