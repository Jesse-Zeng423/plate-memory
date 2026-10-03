"""Synthetic navigation journeys; no model or private profile involved."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.ui.screen import Screen
from src.ui.postcard_flow import postcard_flow
from src.ui.prompts import HomeRequested
from src.terminal import main


class NavigationTests(unittest.TestCase):
    def test_fields_and_destination_back_retain_note(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / 'note.txt'
            answers = ['Me', 'Bro', '/back', 'Other bro', 'First note',
                       'yes','3','no', '/back', '/back', 'Revised note', 'yes','3','no', str(path)]
            with patch('builtins.input', side_effect=answers), redirect_stdout(StringIO()):
                postcard_flow(Screen(False), Path(work))
            self.assertIn('Other bro', path.read_text())
            self.assertIn('Revised note', path.read_text())
            self.assertNotIn('First note', path.read_text())

    def test_home_resumes_and_discard_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as work:
            draft = {}
            with patch('builtins.input', side_effect=['Me', '/home']), redirect_stdout(StringIO()):
                with self.assertRaises(HomeRequested):
                    postcard_flow(Screen(False), Path(work), draft=draft)
            self.assertEqual(draft, {'sender': 'Me'})
            answers = ['', 'Bro', '/cancel', 'no', 'Hello', '/cancel', 'yes']
            with patch('builtins.input', side_effect=answers), redirect_stdout(StringIO()):
                postcard_flow(Screen(False), Path(work), draft=draft)
            self.assertEqual(draft, {})
            self.assertEqual(list(Path(work).iterdir()), [])

    def test_session_keeps_draft_across_home_without_writing(self):
        with tempfile.TemporaryDirectory() as work:
            answers = ['postcard', 'Me', '/home', 'postcard', '', 'Bro', 'Hello', 'no', 'quit']
            with patch('builtins.input', side_effect=answers), redirect_stdout(StringIO()) as out:
                self.assertEqual(main(['--profile', str(Path(work) / 'f.json'), '--plain']), 0)
            self.assertIn('From Me / To Bro', out.getvalue())
            self.assertEqual(list(Path(work).iterdir()), [])

    def test_overwrite_back_and_save_failure_allow_new_destination(self):
        with tempfile.TemporaryDirectory() as work:
            existing = Path(work) / 'existing.txt'
            existing.write_text('original')
            target = Path(work) / 'new.txt'
            answers = ['Me', 'Bro', 'Hello', 'yes','3','no', str(existing), '/back', str(target)]
            with patch('builtins.input', side_effect=answers), redirect_stdout(StringIO()):
                postcard_flow(Screen(False), Path(work))
            self.assertEqual(existing.read_text(), 'original')
            self.assertIn('Hello', target.read_text())
            from src.services.export import export_file
            attempts = []
            def fail_once(path, card, format, replace=False):
                attempts.append(path)
                if len(attempts) == 1:
                    raise PermissionError('Synthetic denied destination')
                return export_file(path, card, format, replace)
            recovered = Path(work) / 'recovered.txt'
            answers = ['Me', 'Bro', 'Hello', 'yes','3','no', str(Path(work)/'denied.txt'), str(recovered)]
            with patch('builtins.input', side_effect=answers), patch('src.ui.postcard_flow.export_file', side_effect=fail_once), redirect_stdout(StringIO()):
                postcard_flow(Screen(False), Path(work))
            self.assertIn('Hello', recovered.read_text())
            self.assertFalse((Path(work)/'denied.txt').exists())

    def test_query_interpretation_back_preserves_previous_keyword(self):
        from src.ui.meal_flow import query_flow
        parsed = {'spans': [{'kind': 'want', 'quote': 'pizza'}]}
        with patch('builtins.input', side_effect=['I want pizza', '/back', '/back']), redirect_stdout(StringIO()):
            self.assertEqual(query_flow(Screen(False), lambda _: parsed, 'soup'), 'soup')
        with patch('builtins.input', side_effect=['/home']), redirect_stdout(StringIO()):
            with self.assertRaises(HomeRequested):
                query_flow(Screen(False), lambda _: parsed, 'soup')

    def test_cancel_category_and_refine_keep_current_food_list(self):
        from src.catalog.index import Catalog
        from src.storage.meal_store import MealStore
        from src.ui.meal_flow import choose_meal
        store = MealStore()
        answers = ['2', 'pizza', 'categories', '/back', 'refine', '/back', '1', 'pick']
        try:
            with patch('builtins.input', side_effect=answers), redirect_stdout(StringIO()):
                result = choose_meal(Screen(False), store, catalog=Catalog())
            self.assertIn('pizza', result['name'].lower())
        finally:
            store.close()

    def test_checkin_home_resume_and_local_invalid_date(self):
        from src.ui.checkin_flow import checkin_form
        draft = {}
        with tempfile.TemporaryDirectory() as work:
            with patch('builtins.input', side_effect=['Synthetic soup','/home']), redirect_stdout(StringIO()):
                with self.assertRaises(HomeRequested):
                    checkin_form(Screen(False),draft=draft)
            self.assertEqual(draft['dish'],'Synthetic soup')
            answers = ['', '2099-01-01', '', 'no', '', 'yes']
            with patch('builtins.input', side_effect=answers), redirect_stdout(StringIO()) as out:
                item = checkin_form(Screen(False),draft=draft)
            self.assertEqual(item['dish'],'Synthetic soup')
            self.assertNotIn('_feelings',item)
            self.assertIsNone(item['comfort'])
            self.assertIn('today or earlier',out.getvalue())
            self.assertEqual(list(Path(work).iterdir()),[])

    def test_checkin_back_to_feelings_can_skip_the_entire_group(self):
        from src.ui.checkin_flow import checkin_form
        # Exercise the explicit route -> feelings return directly; retained observations stay private.
        draft={'id':'checkin-synthetic','date':'2026-10-02','dish':'Synthetic soup','route':'cafeteria',
               'taste':'enjoyed','fullness':'satisfied','comfort':'uncomfortable','note':None,'_feelings':'yes'}
        with patch('builtins.input',side_effect=['','','yes','/back','no','','yes']),redirect_stdout(StringIO()):
            item=checkin_form(Screen(False),draft=draft)
        self.assertTrue(all(item[k] is None for k in ('route','taste','fullness','comfort')))

    def test_lunchbox_home_resume_back_preview_and_optional_dish_skip(self):
        from src.ui.lunchbox_flow import write_lunchbox
        draft={}
        with patch('builtins.input',side_effect=['Demo me','/home']),redirect_stdout(StringIO()):
            with self.assertRaises(HomeRequested):write_lunchbox(Screen(False),draft)
        answers=['','Demo bro','Hello','Soup','At school','/back','/back','/skip','yes']
        with patch('builtins.input',side_effect=answers),redirect_stdout(StringIO()):
            pack=write_lunchbox(Screen(False),draft)
        self.assertEqual(pack['messages'],['Hello'])
        self.assertEqual(pack['shared_dishes'],[])
        self.assertEqual(pack['sender'],'Demo me')

    def test_lunchbox_import_back_chooses_another_file_and_export_back(self):
        from src.ui.lunchbox_flow import import_lunchbox,export_lunchbox
        from src.paths import ROOT
        from src.services.friend_pack import load_friend_pack
        saved=[]
        fixture=ROOT/'examples/friend-pack-v1.json'
        with patch('builtins.input',side_effect=[str(fixture),'/back',str(fixture),'yes']),redirect_stdout(StringIO()):
            self.assertEqual(import_lunchbox(Screen(False),saved.append),saved[0])
        with tempfile.TemporaryDirectory() as work:
            path=Path(work)/'gift.json'
            with patch('builtins.input',side_effect=[str(path),'/back','/back']),redirect_stdout(StringIO()):
                export_lunchbox(Screen(False),load_friend_pack(fixture),False)
            self.assertEqual(list(Path(work).iterdir()),[])

    def test_food_home_preserves_query_and_back_moves_through_route(self):
        from src.catalog.index import Catalog
        from src.storage.meal_store import MealStore
        from src.ui.meal_flow import choose_meal
        store=MealStore();draft={}
        try:
            with patch('builtins.input',side_effect=['2','pizza','h']),redirect_stdout(StringIO()):
                with self.assertRaises(HomeRequested):choose_meal(Screen(False),store,catalog=Catalog(),draft=draft)
            self.assertEqual((draft['step'],draft['route'],draft['query']),('browse','cafeteria','pizza'))
            # List -> craving -> route -> table. No selection or save.
            with patch('builtins.input',side_effect=['0','/back','0']),redirect_stdout(StringIO()):
                self.assertIsNone(choose_meal(Screen(False),store,catalog=Catalog(),draft=draft))
            with patch('builtins.input',side_effect=['','', '1','pick']),redirect_stdout(StringIO()):
                meal=choose_meal(Screen(False),store,catalog=Catalog(),draft=draft)
            self.assertIn('pizza',meal['name'].lower())
            self.assertEqual(draft,{})
            self.assertEqual(store.list(),[])
        finally:store.close()

    def test_saved_choice_back_clears_inactive_price_date_and_walk(self):
        from src.ui.saved_flow import meal_form
        from src.domain.meals import empty_meal
        draft=empty_meal('cafeteria')
        draft.update(name='Synthetic soup',price_cents=650,price_date='2026-10-02',walk_minutes=15)
        with patch('builtins.input',side_effect=['delivery','','','/skip','','','yes']),redirect_stdout(StringIO()):
            item=meal_form(Screen(False),draft=draft)
        self.assertIsNone(item['price_cents']);self.assertIsNone(item['price_date']);self.assertIsNone(item['walk_minutes'])
        draft={}
        with patch('builtins.input',side_effect=['delivery','Synthetic soup','/home']),redirect_stdout(StringIO()):
            with self.assertRaises(HomeRequested):meal_form(Screen(False),draft=draft)
        answers=['','','/back','Soup revised','Cafe','','','','/back','Menu note','yes']
        with patch('builtins.input',side_effect=answers),redirect_stdout(StringIO()):
            item=meal_form(Screen(False),draft=draft)
        self.assertEqual(item['name'],'Soup revised')
        self.assertEqual(item['menu_text'],'Menu note')

    def test_optional_fields_back_skip_over_inactive_fields(self):
        from src.ui.navigation import Field,form_fields
        draft={}
        fields=[Field('first','First'),Field('hidden','Hidden',active=lambda d:False),Field('last','Last')]
        with patch('builtins.input',side_effect=['one','/back','two','three']),redirect_stdout(StringIO()):
            self.assertTrue(form_fields(Screen(False),fields,draft))
        self.assertEqual(draft,{'first':'two','last':'three'})

    def test_declining_discard_at_preview_keeps_preview_and_draft(self):
        from src.ui.checkin_flow import checkin_form
        from src.ui.lunchbox_flow import write_lunchbox
        from src.ui.saved_flow import meal_form
        cases=[(checkin_form,['Synthetic soup','','no','']),
               (write_lunchbox,['Demo me','Demo bro','Hello','']),
               (meal_form,['delivery','Synthetic soup','','','',''])]
        for form,answers in cases:
            with self.subTest(form=form.__name__),patch('builtins.input',side_effect=answers+['/cancel','no','yes']),redirect_stdout(StringIO()):
                self.assertIsNotNone(form(Screen(False),draft={}))
