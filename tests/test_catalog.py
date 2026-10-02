"""Public discovery coverage, provenance rejection and offline terminal behavior."""
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


class CatalogTests(unittest.TestCase):
    def test_common_words_and_multilingual_aliases(self):
        catalog = Catalog()
        for query, qid in [('pizza','Q177'),('披萨','Q177'),('比薩','Q177'),('Sandwich','Q28803'),('三明治','Q28803'),('egg','Q20129'),('鸡蛋','Q20129'),('burger','Q6663'),('日本拉面','Q234646')]:
            with self.subTest(query=query):
                self.assertEqual(catalog.search(query)[0]['id'], qid)
        self.assertEqual(catalog.search('pizzazz'), [])
        self.assertEqual(catalog.search('not pizza'), [])
        self.assertEqual(catalog.search('不要鸡蛋'), [])
        self.assertEqual(catalog.search('pizza under 5 dollars'), [])
        self.assertEqual(catalog.search('unknown dish'), [])
        catalog.items.reverse()
        self.assertEqual(catalog.search('')[0]['name'], 'biryani')

    def test_manifest_and_schema_reject_corrupt_or_unattributed_data(self):
        original = ROOT/'data/catalog/v1'
        with tempfile.TemporaryDirectory() as work:
            target = Path(work)
            for name in ('manifest.json','dishes.json'):
                (target/name).write_bytes((original/name).read_bytes())
            (target/'dishes.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValidationError,'fingerprint'):
                Catalog(target)
        pack=json.loads((original/'dishes.json').read_text())
        pack['items'].append(pack['items'][0])
        with self.assertRaisesRegex(ValidationError,'Duplicate'):
            validate_pack(pack)
        pack['items'].pop()
        pack['items'][0]['name']='pizza\x1b[0m'
        with self.assertRaisesRegex(ValidationError,'text'):
            validate_pack(pack)

    def test_terminal_empty_account_search_refinement_selection_is_offline_and_private(self):
        for route, query in [('1','pizza'),('2','披萨')]:
            with self.subTest(route=route), tempfile.TemporaryDirectory() as work:
                path=Path(work)/'friend.json'
                answers=['today',route,query,'Sandwich','egg','1','review','1','select','quit']
                with patch('builtins.input',side_effect=answers), patch('socket.socket',side_effect=AssertionError('Network forbidden')), patch('src.services.review.local_extract') as model, redirect_stdout(StringIO()) as out:
                    self.assertEqual(main(['--profile',str(path),'--plain']),0)
                output=out.getvalue()
                self.assertIn('pizza',output)
                self.assertIn('sandwich',output)
                self.assertIn('omelette',output)
                self.assertIn('[food idea]',output)
                self.assertIn('Ingredients, availability and price are unknown',output)
                self.assertIn('paste the actual menu',output)
                self.assertIn('Nothing has been ordered or recorded as eaten.',output)
                self.assertEqual(list(Path(work).iterdir()),[])
                model.assert_not_called()

    def test_unknown_query_recovers_with_chinese_term(self):
        with tempfile.TemporaryDirectory() as work:
            with patch('builtins.input',side_effect=['today','2','xyz123','三明治','1','select','quit']), redirect_stdout(StringIO()) as out:
                self.assertEqual(main(['--profile',str(Path(work)/'f.json'),'--plain']),0)
            self.assertIn('Type another dish or place to search',out.getvalue())
            self.assertIn("This session's idea: sandwich",out.getvalue())


if __name__ == '__main__':
    unittest.main()

class QueryTests(unittest.TestCase):
    def test_invented_and_negated_positive_spans_are_rejected(self):
        from src.query_parser import validate_spans
        for query, spans in [('pizza',[{'quote':'sushi','kind':'want'}]),('no pizza',[{'quote':'pizza','kind':'want'}]),('no pizza',[{'quote':'no pizza','kind':'want'}]),('no pizza',[{'quote':'no pizza','kind':'avoid'},{'quote':'pizza','kind':'want'}])]:
            with self.subTest(query=query,spans=spans), self.assertRaises(ValidationError):
                validate_spans({'spans':spans},query)
        value={'spans':[{'quote':'sandwich','kind':'want'},{'quote':'no egg','kind':'avoid'}]}
        self.assertEqual(validate_spans(value,'sandwich but no egg'),value)

    def test_query_transport_sends_only_query_and_rejects_remote_weights(self):
        from src.query_parser import parse_query
        from src.extraction import ExtractionError
        from unittest.mock import MagicMock
        bodies=[]
        def response(req,timeout):
            bodies.append(json.loads(req.data))
            value={'model_info':{'architecture':'gemma'}} if req.full_url.endswith('show') else {'done':True,'response':json.dumps({'spans':[{'quote':'pizza','kind':'want'}]})}
            context=MagicMock();context.__enter__.return_value.read.return_value=json.dumps(value).encode();return context
        with patch('src.query_parser.build_opener') as opener:
            opener.return_value.open.side_effect=response
            self.assertEqual(parse_query('I fancy pizza','gemma3:4b')['spans'][0]['quote'],'pizza')
        self.assertEqual(set(bodies[1]),{'model','system','prompt','format','stream','keep_alive','options'})
        self.assertNotIn('memory',json.dumps(bodies).lower())
        with patch('src.query_parser.build_opener') as opener:
            context=opener.return_value.open.return_value.__enter__.return_value
            context.read.return_value=b'{"remote_host":"example.com","model_info":{"a":1}}'
            with self.assertRaises(ExtractionError):
                parse_query('pizza','gemma3:4b')
