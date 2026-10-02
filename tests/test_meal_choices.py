"""Saved-choice persistence, permission boundaries and real terminal flow checks."""
from contextlib import redirect_stdout, closing
from copy import deepcopy
from datetime import date
from io import StringIO
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.domain.meals import empty_meal, parse_price, validate_meal
from src.food_adapter import ValidationError, build_report
from src.paths import ROOT
from src.services.meal_choices import guard_reminders, shortlist, recorded_menu_profile
from src.storage.meal_store import MealStore
from src.terminal import main
from src.ui.meal_flow import choose_meal
from src.ui.screen import Screen

SAMPLES = json.loads((ROOT/'examples/saved-meals-v1.json').read_text())['meals']


def sample(route='delivery'):
    return deepcopy(next(m for m in SAMPLES if m['route'] == route))


class SavedMealTests(unittest.TestCase):
    def test_money_is_exact_and_unknown_metadata_stays_unknown(self):
        self.assertEqual(parse_price('12.34'), 1234)
        for text in ('NaN', 'Infinity', '-1', '0.001', '10001', 'x'):
            with self.subTest(text=text), self.assertRaises(ValidationError):
                parse_price(text)
        meal = sample()
        meal['price_date'] = None
        with self.assertRaises(ValidationError):
            validate_meal(meal)
        meal['price_cents'] = None
        validate_meal(meal)
        meal['walk_minutes'] = 5
        with self.assertRaises(ValidationError):
            validate_meal(meal)

    def test_private_store_survives_restart_and_rejects_stale_edits_and_deletes(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work)/'saved.sqlite3'
            first, second = MealStore(path), MealStore(path)
            try:
                self.assertEqual(first.list(), [])
                self.assertFalse(path.exists())
                meal = sample()
                first.save(meal)
                old, revision = second.list()[0]
                changed = deepcopy(meal)
                changed['name'] = 'Different bowl'
                first.save(changed, expected_revision=revision)
                with self.assertRaisesRegex(ValidationError, 'changed elsewhere'):
                    second.save(old, expected_revision=revision)
                with self.assertRaises(ValidationError):
                    second.delete(old['id'], revision)
                self.assertEqual(second.list()[0][0]['name'], 'Different bowl')
                second.delete(old['id'], revision+1)
                self.assertEqual(first.list(), [])
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            finally:
                first.close(); second.close()
            reopened = MealStore(path)
            try:
                self.assertEqual(reopened.list(), [])
            finally:
                reopened.close()

    def test_unknown_future_schema_and_unrelated_database_are_not_rewritten(self):
        for future in (False, True):
            with self.subTest(future=future), tempfile.TemporaryDirectory() as work:
                path = Path(work)/'saved.sqlite3'
                with closing(sqlite3.connect(path)) as db, db:
                    db.execute('CREATE TABLE untouched (value TEXT)')
                    db.execute("INSERT INTO untouched VALUES ('original')")
                    if future:
                        db.execute('PRAGMA user_version = 99')
                store = MealStore(path)
                try:
                    with self.assertRaises(ValidationError):
                        store.list()
                finally:
                    store.close()
                with closing(sqlite3.connect(path)) as db, db:
                    self.assertEqual(db.execute('SELECT value FROM untouched').fetchone()[0], 'original')
                    self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 99 if future else 0)

    def test_route_filter_and_stable_keyword_order(self):
        rows = [(m,1) for m in SAMPLES]
        self.assertTrue(all(m['route']=='delivery' for m,_ in shortlist(rows,'delivery')))
        self.assertEqual(shortlist(rows,'cafeteria','rice')[0][0]['id'], 'sample-cafeteria-rice')
        self.assertEqual(shortlist(rows,'delivery','absent'), [])
        self.assertEqual(shortlist(rows,'delivery'), shortlist(list(reversed(rows)),'delivery'))
        chinese = empty_meal('cafeteria'); chinese.update(name='鸡肉饭', venue='北食堂')
        self.assertEqual(shortlist([(chinese,1)], 'cafeteria', '鸡肉')[0][0]['name'], '鸡肉饭')

    def test_permission_precedence_survives_discovery_without_extraction(self):
        profile = json.loads((ROOT/'examples/profile.json').read_text())
        decisions = guard_reminders(profile, date(2026,10,3))
        self.assertTrue(any(d['guard_verdict']=='ESCALATE' for d in decisions))
        profile['memories'][0]['permission'] = 'REVOKED'
        self.assertFalse(any(d['memory_id']=='peanut-allergy' for d in guard_reminders(profile,date(2026,10,3))))
        self.assertEqual(guard_reminders(None,date(2026,10,3)), [])

    def test_recorded_menu_requires_external_check_without_mutating_profile(self):
        profile = json.loads((ROOT/'examples/profile.json').read_text())
        before = deepcopy(profile)
        context = recorded_menu_profile(profile)
        extraction = {'candidates':[{'memory_id':'cilantro','line_id':'L1','quote':'cilantro rice','match':'matched'}]}
        report = build_report(context,extraction,date(2026,10,2),'test',None)
        self.assertEqual(report['decisions'][3]['guard_verdict'],'VERIFY_EXTERNAL')
        self.assertEqual(report['decisions'][0]['guard_verdict'],'ESCALATE')
        self.assertEqual(profile,before)
        profile['memories'][3]['permission'] = 'REVOKED'
        report = build_report(recorded_menu_profile(profile),{'candidates':[]},date(2026,10,2),'test',None)
        self.assertEqual(report['decisions'][3]['reason_code'],'PERMISSION_REVOKED')


class MealFlowTests(unittest.TestCase):
    def test_demo_both_routes_have_no_real_writes_or_model_calls(self):
        for route in ('1','2'):
            with self.subTest(route=route), tempfile.TemporaryDirectory() as work:
                path=Path(work)/'friend.json'
                with patch('builtins.input', side_effect=['today',route,'','1','select','quit']), patch('src.services.review.local_extract') as model, redirect_stdout(StringIO()) as out:
                    self.assertEqual(main(['--profile',str(path),'--demo','--plain']),0)
                self.assertIn('Nothing has been ordered or recorded as eaten.',out.getvalue())
                self.assertIn('Allergy: confirm',out.getvalue())
                self.assertEqual(list(Path(work).iterdir()), [])
                model.assert_not_called()

    def test_empty_real_session_and_cancel_do_not_create_database(self):
        with tempfile.TemporaryDirectory() as work:
            with patch('builtins.input',side_effect=['today','2','','back','quit']), redirect_stdout(StringIO()) as out:
                main(['--profile',str(Path(work)/'friend.json'),'--plain'])
            self.assertIn('No saved matches yet',out.getvalue())
            self.assertEqual(list(Path(work).iterdir()), [])

    def test_explicit_add_persists_without_a_dietary_profile(self):
        answers=['usuals','add','delivery','My noodle bowl','My place','','','', 'yes','back','today','1','noodle','1','select','quit']
        with tempfile.TemporaryDirectory() as work:
            profile=Path(work)/'friend.json'
            with patch('builtins.input',side_effect=answers), redirect_stdout(StringIO()) as out:
                self.assertEqual(main(['--profile',str(profile),'--plain']),0)
            self.assertFalse(profile.exists())
            store=MealStore(profile.with_name('friend-meals.sqlite3'))
            try:
                meal,_=store.list()[0]
                self.assertEqual(meal['name'],'My noodle bowl')
                self.assertIsNone(meal['price_cents'])
                self.assertIsNone(meal['last_seen'])
            finally:
                store.close()
            self.assertIn('This session\'s idea: My noodle bowl',out.getvalue())

    def test_cancelled_form_does_not_persist(self):
        with tempfile.TemporaryDirectory() as work:
            with patch('builtins.input',side_effect=['usuals','add','delivery','/back','back','quit']), redirect_stdout(StringIO()):
                main(['--profile',str(Path(work)/'friend.json'),'--plain'])
            self.assertEqual(list(Path(work).iterdir()), [])

    def test_back_from_candidate_returns_to_list_and_route_can_change(self):
        store=MealStore()
        try:
            for meal in SAMPLES:
                store.save(meal)
            with patch('builtins.input',side_effect=['1','','1','back','route','2','','1','select']), redirect_stdout(StringIO()):
                chosen=choose_meal(Screen(False),store)
            self.assertEqual(chosen['route'],'cafeteria')
        finally:
            store.close()

    def test_absolute_launch_has_warm_home_and_plain_mode(self):
        with tempfile.TemporaryDirectory() as work:
            result=subprocess.run([sys.executable,'-B',str(ROOT/'src/terminal.py'),'--demo','--plain'],input='today\n2\n\nback\nquit\n',cwd=work,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Saved you a seat.', result.stdout)
        self.assertNotIn('\x1b', result.stdout)
        self.assertNotIn('.-----.', result.stdout)
        self.assertIn('Your walk estimate: 8 min',result.stdout)


if __name__ == '__main__':
    unittest.main()
