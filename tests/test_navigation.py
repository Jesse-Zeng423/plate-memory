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
                       'yes', '/back', '/back', 'Revised note', 'yes', str(path)]
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
            self.assertIn('From Me to Bro', out.getvalue())
            self.assertEqual(list(Path(work).iterdir()), [])

    def test_overwrite_back_and_save_failure_allow_new_destination(self):
        with tempfile.TemporaryDirectory() as work:
            existing = Path(work) / 'existing.txt'
            existing.write_text('original')
            target = Path(work) / 'new.txt'
            answers = ['Me', 'Bro', 'Hello', 'yes', str(existing), '/back', str(target)]
            with patch('builtins.input', side_effect=answers), redirect_stdout(StringIO()):
                postcard_flow(Screen(False), Path(work))
            self.assertEqual(existing.read_text(), 'original')
            self.assertIn('Hello', target.read_text())
            from src.services.postcard import export_postcard
            attempts = []
            def fail_once(path, card):
                attempts.append(path)
                if len(attempts) == 1:
                    raise PermissionError('Synthetic denied destination')
                export_postcard(path, card)
            recovered = Path(work) / 'recovered.txt'
            answers = ['Me', 'Bro', 'Hello', 'yes', str(Path(work)/'denied.txt'), str(recovered)]
            with patch('builtins.input', side_effect=answers), patch('src.ui.postcard_flow.export_postcard', side_effect=fail_once), redirect_stdout(StringIO()):
                postcard_flow(Screen(False), Path(work))
            self.assertIn('Hello', recovered.read_text())
            self.assertFalse((Path(work)/'denied.txt').exists())

    def test_query_interpretation_back_preserves_previous_keyword(self):
        from src.ui.meal_flow import query_flow
        parsed = {'spans': [{'kind': 'want', 'quote': 'pizza'}]}
        with patch('builtins.input', side_effect=['I want pizza', '/back']), redirect_stdout(StringIO()):
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
