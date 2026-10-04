"""The distribution entry works outside its folder and does not default to demo."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from src.paths import ROOT
from src.version import VERSION

class ReleaseEntryTests(unittest.TestCase):
    def test_version_and_fresh_normal_launcher_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as work:
            version=subprocess.run([sys.executable,str(ROOT/'plate-memory.py'),'--version'],cwd=work,text=True,capture_output=True,check=True)
            self.assertEqual(version.stdout.strip(),'Plate Memory '+VERSION)
            result=subprocess.run([sys.executable,str(ROOT/'plate-memory.py'),'--profile',str(Path(work)/'f.json'),'--language','en','--plain'],cwd=work,text=True,input='0\n',capture_output=True,check=True)
            self.assertIn('Saved you a seat',result.stdout)
            self.assertNotIn('Demo records',result.stdout)
            self.assertEqual(list(Path(work).iterdir()),[])
