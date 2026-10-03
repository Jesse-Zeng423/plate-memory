"""Language affects presentation, never user text or stored decision fields."""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.terminal import main
from src.ui.screen import Screen
from src.ui.lunchbox_flow import write_lunchbox
from src.ui.checkin_flow import checkin_form


class LanguageTests(unittest.TestCase):
    def test_interactive_startup_asks_and_accepts_both_languages(self):
        for language,expected in [('1','给你留了个座'),('2','Saved you a seat')]:
            with tempfile.TemporaryDirectory() as work,patch('sys.stdin.isatty',return_value=True),patch('builtins.input',side_effect=[language,'0']),redirect_stdout(StringIO()) as out:
                self.assertEqual(main(['--demo','--plain','--profile',str(Path(work)/'f.json')]),0)
                self.assertIn('简体中文 / English',out.getvalue())
                self.assertIn(expected,out.getvalue())
                self.assertEqual(list(Path(work).iterdir()),[])

    def test_chinese_discovery_is_offline_and_has_simple_number_actions(self):
        with tempfile.TemporaryDirectory() as work,patch('builtins.input',side_effect=['1','2','三明治','1','1','0']),patch('socket.socket',side_effect=AssertionError('No runtime network')),redirect_stdout(StringIO()) as out:
            self.assertEqual(main(['--language','zh','--plain','--profile',str(Path(work)/'f.json')]),0)
            text=out.getvalue()
            for phrase in ('找点好吃的','今天怎么样','太累了','三明治','还没有下单或记为吃过'):
                self.assertIn(phrase,text)
            self.assertEqual(list(Path(work).iterdir()),[])

    def test_user_authored_message_is_preserved_verbatim(self):
        with patch('builtins.input',side_effect=['Choose','Until our next meal','What did you eat?','','是']),redirect_stdout(StringIO()):
            pack=write_lunchbox(Screen(False,language='zh'),{})
        self.assertEqual(pack['sender'],'Choose')
        self.assertEqual(pack['recipient'],'Until our next meal')
        self.assertEqual(pack['messages'],['What did you eat?'])

    def test_chinese_journal_choices_store_canonical_values_only(self):
        answers=['合成示例：一碗汤','','是','食堂','喜欢','刚好','舒服','','是']
        with patch('builtins.input',side_effect=answers),redirect_stdout(StringIO()):
            item=checkin_form(Screen(False,language='zh'))
        self.assertEqual((item['route'],item['taste'],item['fullness'],item['comfort']),('cafeteria','enjoyed','satisfied','comfortable'))
        self.assertEqual(item['dish'],'合成示例：一碗汤')
