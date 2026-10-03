"""Broader references remain named source records, never inferred clearance."""
import unittest
from src.catalog.index import Catalog
from src.paths import ROOT


class ExpandedCatalogTests(unittest.TestCase):
    def test_v3_preserves_every_v2_source_record_and_expands_useful_queries(self):
        old=Catalog(ROOT/'data/catalog/v2');new=Catalog()
        ids={i['id'] for i in new.items}
        self.assertEqual(len(new.items),3535)
        self.assertTrue({i['id'] for i in old.items}<=ids)
        for query in ('bagel','oatmeal','yogurt','apple','banana','broccoli','coffee','tea','tofu','fish','ice cream','贝果','燕麦粥','酸奶','苹果','香蕉','西兰花','咖啡','豆腐','薯条'):
            with self.subTest(query=query):self.assertTrue(new.search(query))
        for query in ('no egg','without peanuts','不要鸡蛋','pizza under 5 dollars'):
            self.assertEqual(new.search(query),[])
        self.assertEqual(new.search('egg')[0]['kind'],'ingredient')
        self.assertTrue(all(i['source']['license']=='CC0-1.0' for i in new.items))
        self.assertTrue(all('nutrients' not in i for i in new.items))
