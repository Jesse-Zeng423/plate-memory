from contextlib import redirect_stdout
from copy import deepcopy
from datetime import date
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.cli import ROOT
from src.extraction import local_extract
from src.food_adapter import ValidationError, build_report, menu_lines, targets
from src.food_cache import key, read_cache, write_cache
from src.profile_store import load_profile, save_profile, update_record
from src.terminal import Screen, Session, headline, main, safe_text

PROFILE = json.loads((ROOT / 'examples/profile.json').read_text())


class ProfileTests(unittest.TestCase):
    def test_private_revisions_are_preserved_and_current_is_valid(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / 'friend.json'
            first = save_profile(path, PROFILE)
            changed = update_record(PROFILE, 'old-spice', 'confirm', date(2026,10,4))
            second = save_profile(path, changed)
            self.assertNotEqual(first, second)
            self.assertEqual(load_profile(first), PROFILE)
            self.assertEqual(load_profile(path), changed)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_confirm_does_not_restore_revoked_or_unknown_permission(self):
        for permission in ('REVOKED', 'UNKNOWN'):
            p = deepcopy(PROFILE)
            p['memories'][2]['permission'] = permission
            with self.assertRaisesRegex(ValidationError, 'does not grant'):
                update_record(p, 'old-spice', 'confirm')
        revoked = update_record(PROFILE, 'old-spice', 'revoke')
        allowed = update_record(revoked, 'old-spice', 'allow')
        self.assertEqual(allowed['memories'][2]['confirmed_on'], '2023-06-01')

    def test_confirmation_changes_applicability_but_not_risk(self):
        extraction = {'candidates':[{'memory_id':'old-spice','line_id':'L1','quote':'spicy noodles','match':'matched'}]}
        before = build_report(PROFILE, extraction, date(2026,10,4), 'test', None)
        p = update_record(PROFILE, 'old-spice', 'confirm', date(2026,10,4))
        after = build_report(p, extraction, date(2026,10,4), 'test', None)
        self.assertEqual(before['decisions'][2]['memory_action'], 'ASK')
        self.assertEqual(after['decisions'][2]['memory_action'], 'USE')
        p = update_record(p, 'peanut-allergy', 'confirm', date(2026,10,4))
        self.assertEqual(build_report(p, extraction, date(2026,10,4), 'test', None)['decisions'][0]['guard_verdict'], 'ESCALATE')


class CacheTests(unittest.TestCase):
    def test_cache_rematches_profile_and_does_not_contact_model(self):
        lines = menu_lines('chicken with cilantro')
        with tempfile.TemporaryDirectory() as work:
            write_cache(work, lines, 'gemma3:4b', [{'foods':['chicken','cilantro']}])
            with patch('src.extraction.build_opener') as network:
                result = local_extract(lines, targets(PROFILE), 'gemma3:4b', cache_path=work)
                changed = deepcopy(PROFILE)
                changed['memories'][3]['permission'] = 'REVOKED'
                new = local_extract(lines, targets(changed), 'gemma3:4b', cache_path=work)
                network.assert_not_called()
            self.assertIn('cilantro', [c['memory_id'] for c in result['candidates']])
            self.assertNotIn('cilantro', [c['memory_id'] for c in new['candidates']])
            weekday = build_report(PROFILE,result,date(2026,10,2),'local-ollama','gemma3:4b')
            weekend = build_report(PROFILE,result,date(2026,10,3),'local-ollama','gemma3:4b')
            self.assertEqual(weekday['decisions'][1]['memory_action'], 'USE')
            self.assertEqual(weekend['decisions'][1]['memory_action'], 'IGNORE')
            raw = next(Path(work).glob('*.json')).read_text()
            for forbidden in ('guard_verdict','confirmed_on','friend','memory_id','permission'):
                self.assertNotIn(forbidden,raw)

    def test_cache_source_and_model_keys_and_grounding(self):
        lines = menu_lines('rice')
        with tempfile.TemporaryDirectory() as work:
            write_cache(work,lines,'gemma3:4b',[{'foods':['rice']}])
            self.assertIsNone(read_cache(work,menu_lines('chicken'),'gemma3:4b'))
            self.assertIsNone(read_cache(work,lines,'other:4b'))
            path = Path(work) / (key(lines,'gemma3:4b')+'.json')
            path.write_text(json.dumps({'key':key(lines,'gemma3:4b'),'foods':[{'foods':['invented']}]}))
            with self.assertRaises(ValidationError):
                read_cache(work,lines,'gemma3:4b')

    def test_cache_fingerprint_cannot_be_bypassed(self):
        lines = menu_lines('rice')
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / (key(lines,'gemma3:4b')+'.json')
            path.write_text('{"key":"wrong","foods":[{"foods":[]}]}')
            with self.assertRaisesRegex(ValidationError,'fingerprint'):
                local_extract(lines,targets(PROFILE),'gemma3:4b',cache_path=work)


class TerminalTests(unittest.TestCase):
    def test_terminal_control_sequences_are_removed(self):
        self.assertEqual(safe_text('\x1b[2Jrice\x07\x9b31m'), '[2Jrice31m')

    def test_allergy_is_never_presented_as_ignored_or_safe(self):
        report = build_report(PROFILE,{'candidates':[]},date(2026,10,3),'canned-demo',None)
        self.assertIn('Allergy: confirm', headline(report['decisions'][0]))
        self.assertNotIn('ignore', headline(report['decisions'][0]).lower())

    def test_canned_demo_runs_without_model_or_profile_writes(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / 'friend.json'
            for scenario in ('allergy','weekend','stale','weekday'):
                with patch('builtins.input',side_effect=['demo',scenario,'details','quit']), patch('src.terminal.local_extract') as live, redirect_stdout(StringIO()) as out:
                    self.assertEqual(main(['--profile',str(path),'--no-color']),0)
                self.assertIn('Synthetic canned demo; no AI ran.',out.getvalue())
                self.assertIn('Allergy: confirm',out.getvalue())
                live.assert_not_called()
                self.assertFalse(path.exists())

    def test_no_profile_review_gives_next_step(self):
        with tempfile.TemporaryDirectory() as work:
            with patch('builtins.input',side_effect=['review','quit']), redirect_stdout(StringIO()) as out:
                main(['--profile',str(Path(work)/'absent.json'),'--no-color'])
            self.assertIn('Add an actual friend-authored note',out.getvalue())

    def test_add_record_requires_explicit_save(self):
        answers = ['preferences','add','Harold','Dislikes cilantro','preference','cilantro','all','ALLOWED','unknown','180','no','yes','quit']
        with tempfile.TemporaryDirectory() as work:
            path = Path(work)/'friend.json'
            with patch('builtins.input',side_effect=answers), redirect_stdout(StringIO()):
                main(['--profile',str(path),'--no-color'])
            p = load_profile(path)
            self.assertEqual(p['friend'],'Harold')
            self.assertIsNone(p['memories'][0]['confirmed_on'])

    def test_profile_change_invalidates_report(self):
        with tempfile.TemporaryDirectory() as work:
            session = Session(Screen(False),Path(work)/'friend.json','gemma3:4b',True)
            session.last = {'old':'report'}
            with redirect_stdout(StringIO()):
                session.commit(update_record(PROFILE,'old-spice','confirm'))
            self.assertIsNone(session.last)
            self.assertFalse(session.path.exists())

    def test_failed_review_clears_previous_trace(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work)/'friend.json'
            save_profile(path, PROFILE)
            session = Session(Screen(False), path, 'gemma3:4b')
            session.last = {'old': 'report'}
            with patch('builtins.input', side_effect=['rice','/done']), patch('src.terminal.local_extract', side_effect=ValidationError('bad cache')), redirect_stdout(StringIO()):
                with self.assertRaises(ValidationError):
                    session.review()
            self.assertIsNone(session.last)

    def test_cancel_menu_produces_no_report(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work)/'friend.json'
            save_profile(path,PROFILE)
            session = Session(Screen(False),path,'gemma3:4b')
            with patch('builtins.input',side_effect=['rice','/cancel']), patch('src.terminal.local_extract') as live, redirect_stdout(StringIO()):
                session.review()
            self.assertIsNone(session.last)
            live.assert_not_called()


if __name__ == '__main__':
    unittest.main()
