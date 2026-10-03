"""Widths and controls are checked independently of terminal decoration."""
from contextlib import redirect_stdout
from io import StringIO
import os
import unittest
from unittest.mock import patch
from src.ui.screen import Screen
from src.ui.home import welcome,home
from src._vendor.wcwidth import wcswidth,iter_graphemes


class TerminalVisualTests(unittest.TestCase):
    def test_graphemes_prompts_and_frames_at_supported_widths(self):
        phrase='三明治 👨‍👩‍👦 🇨🇦 👍🏽 🍽️ e\u0301 '
        for columns in (32,40,80,120):
            with self.subTest(columns=columns),patch('src.ui.screen.shutil.get_terminal_size',return_value=os.terminal_size((columns,24))),patch('builtins.input',return_value=''),redirect_stdout(StringIO()) as out:
                screen=Screen(False)
                welcome(screen);home(screen,None,__import__('datetime').date(2026,10,3),True)
                screen.say(phrase*9)
                screen.ask('Your friend’s name or nickname '+phrase,'A very long default name '+phrase)
            for line in out.getvalue().splitlines():
                self.assertLessEqual(wcswidth(line),min(88,columns-2),line)
            # A joined emoji must appear whole, even at a wrap boundary.
            self.assertEqual(out.getvalue().count('👨‍👩‍👦'),11)
            self.assertNotIn('\x1b',out.getvalue())

    def test_plain_decor_and_no_color_are_independent(self):
        with redirect_stdout(StringIO()) as out:
            welcome(Screen(False,False));home(Screen(False,False),None,__import__('datetime').date.today(),False)
        self.assertNotIn('🥣',out.getvalue());self.assertNotIn('🍽️',out.getvalue())
        with patch('sys.stdout.isatty',return_value=True),patch.dict(os.environ,{'NO_COLOR':''}):
            self.assertFalse(Screen().color)
        self.assertEqual(list(iter_graphemes('👨‍👩‍👦🇨🇦👍🏽')),['👨‍👩‍👦','🇨🇦','👍🏽'])
