"""Loose cravings are labeled browsing directions, never clearance or price claims."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.catalog.index import Catalog
from src.services.food_ideas import direction,related,menu_check
from src.services.search import discover
from src.terminal import main

class EmptyChoices:
    def list(self):return []

class FoodIdeaTests(unittest.TestCase):
    def test_loose_cravings_are_bounded_and_constraints_not_relaxed(self):
        c=Catalog()
        for query in ('something warm','I want noodles','I feel like rice','想吃点热的','想吃三明治'):
            with self.subTest(query=query):
                saved,ideas=discover(EmptyChoices(),'delivery',query,c)
                self.assertFalse(saved);self.assertEqual(len(ideas),3)
                self.assertTrue(all(i['discovery_direction'] for _,i in ideas))
                self.assertTrue(all(i['source'] for _,i in ideas))
        for query in ('no soup','warm but without egg','healthy noodles','vegan rice','pizza under 5 dollars','不要鸡蛋','健康的饭','soup and pizza'):
            with self.subTest(query=query):self.assertIsNone(direction(query))
        _,ideas=discover(EmptyChoices(),'delivery','pizza',c)
        self.assertTrue(all('discovery_direction' not in i for _,i in ideas))

    def test_related_foods_keep_sources_and_exclude_original(self):
        c=Catalog();pizza=c.search('pizza')[0];rows=related(c,pizza)
        self.assertEqual(len(rows),3)
        self.assertTrue(all(i['id']!=pizza['id'] and i['source'] for i in rows))
        self.assertIn('toppings',menu_check(pizza))
        next_page=related(c,pizza,offset=3)
        self.assertFalse({i['id'] for i in rows}&{i['id'] for i in next_page})

    def test_real_flow_loose_craving_related_back_and_selection_is_not_consumption(self):
        with tempfile.TemporaryDirectory() as work:
            answers=['1','1','something warm','1','4','0','1','1','0']
            with patch('builtins.input',side_effect=answers),patch('socket.socket',side_effect=AssertionError('No network')),redirect_stdout(StringIO()) as out:
                self.assertEqual(main(['--language','en','--plain','--profile',str(Path(work)/'f.json')]),0)
            text=out.getvalue()
            for phrase in ('nearby food ideas','Food family:','On the menu:','More ideas like:','Nothing has been ordered'):
                self.assertIn(phrase,text)
            self.assertEqual(list(Path(work).iterdir()),[])
