"""Companion gifts and journals never silently become preference memories."""
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.paths import ROOT
from src.food_adapter import ValidationError
from src.json_contract import JsonContractError
from src.services.friend_pack import load_friend_pack,save_friend_pack
from src.domain.friend_pack import validate_friend_pack
from src.terminal import main
from src.ui.lunchbox_flow import preview_pack
from src.ui.screen import Screen


class LunchboxTests(unittest.TestCase):
    def test_import_preview_confirm_restart_is_private_and_separate(self):
        fixture=ROOT/'examples/friend-pack-v1.json'
        with tempfile.TemporaryDirectory() as work:
            profile=Path(work)/'friend.json'
            with patch('builtins.input',side_effect=['lunchbox','import',str(fixture),'yes','back','quit']), redirect_stdout(StringIO()):
                self.assertEqual(main(['--profile',str(profile),'--plain']),0)
            path=Path(work)/'friend-lunchbox.json'
            self.assertEqual(load_friend_pack(path),load_friend_pack(fixture))
            self.assertEqual(path.stat().st_mode&0o777,0o600)
            self.assertFalse(profile.exists())
            with patch('builtins.input',side_effect=['lunchbox','back','quit']), redirect_stdout(StringIO()) as out:
                main(['--profile',str(profile),'--plain'])
            self.assertIn('Different campuses',out.getvalue())

    def test_cancel_and_demo_do_not_write_and_controls_are_sanitized(self):
        with tempfile.TemporaryDirectory() as work:
            for args,answers in [([],['lunchbox','import',str(ROOT/'examples/friend-pack-v1.json'),'no','back','quit']),(['--demo'],['lunchbox','back','quit'])]:
                with patch('builtins.input',side_effect=answers),redirect_stdout(StringIO()):
                    main(['--profile',str(Path(work)/'f.json'),'--plain',*args])
                self.assertEqual(list(Path(work).iterdir()),[])
        pack=load_friend_pack(ROOT/'examples/friend-pack-v1.json');pack['messages']=['Hi\x1b[2Jthere']
        with redirect_stdout(StringIO()) as out:
            preview_pack(Screen(False),pack)
        self.assertNotIn('\x1b',out.getvalue())

    def test_invalid_duplicate_and_unknown_fields_are_rejected(self):
        pack=load_friend_pack(ROOT/'examples/friend-pack-v1.json')
        for key,value in [('messages',[]),('schema_version',2),('memories',[])]:
            changed=deepcopy(pack);changed[key]=value
            with self.assertRaises(ValidationError):validate_friend_pack(changed)
        with tempfile.TemporaryDirectory() as work:
            path=Path(work)/'bad.json';path.write_text('{"sender":"a","sender":"b"}')
            with self.assertRaises(JsonContractError):load_friend_pack(path)
