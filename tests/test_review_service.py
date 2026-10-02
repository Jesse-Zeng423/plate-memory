"""Regression boundaries for the shared review operation and moved launch path."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.paths import ROOT
from src.profile_store import load_profile
from src.services.review import review_demo, review_menu


class ReviewServiceTests(unittest.TestCase):
    def test_public_demo_reports_remain_identical(self):
        for scenario in ('allergy', 'weekend', 'stale', 'weekday'):
            with self.subTest(scenario=scenario):
                expected = json.loads((ROOT / f'examples/{scenario}.expected.json').read_text())
                self.assertEqual(review_demo(scenario).report, expected)

    def test_unresolved_permissions_never_invoke_extraction(self):
        profile = deepcopy(load_profile(ROOT / 'examples/profile.json'))
        for fact in profile['memories']:
            fact['permission'] = 'UNKNOWN'
        with patch('src.services.review.local_extract') as extract:
            result = review_menu(profile, 'rice', date(2026, 10, 2))
        extract.assert_not_called()
        self.assertEqual(result.report['extraction_mode'], 'permission-withheld-no-inference')
        self.assertTrue(all(d['memory'] == '[withheld]' for d in result.report['decisions']))

    def test_absolute_terminal_launch_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as work:
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'src/terminal.py'), '--demo', '--no-color'],
                                    input='demo\nweekend\nquit\n', text=True, capture_output=True, cwd=work)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Synthetic canned demo; no AI ran.', result.stdout)
        self.assertIn('Preference does not apply on this meal date', result.stdout)


if __name__ == '__main__':
    unittest.main()
