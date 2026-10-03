"""Sharing privacy, escaping, atomic collisions and actionable renderer failure."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.domain.share import APP_URL,upgrade_postcard,validate_share
from src.services.share_render import render_html,render_text,render_friend_pack
from src.services.export import export_bundle,export_file,RendererUnavailable
from src.services.friend_pack import load_friend_pack
from src.food_adapter import ValidationError

CARD=upgrade_postcard({'schema_version':1,'sender':'Synthetic Jesse','recipient':'Synthetic Bro',
                      'message':'A synthetic note: a seat saved for you.','dish':'Soup'})


class ExportTests(unittest.TestCase):
    def test_html_escapes_user_text_and_link_is_allowlisted(self):
        card=dict(CARD,message='<script>alert(1)</script> & "hi"',app_url=APP_URL)
        html=render_html(card)
        self.assertNotIn('<script>',html);self.assertIn('&lt;script&gt;',html)
        self.assertIn(APP_URL,html);self.assertIn("default-src 'none'",html)
        self.assertIn('src="data:image/png;base64,',html)
        self.assertNotIn('<svg',html)
        self.assertNotIn('class="hint"',html)
        for bad in ('https://evil.example','javascript:alert(1)','https://github.com/Jesse-Zeng423/plate-memory?private=foo'):
            with self.assertRaises(ValidationError):render_html(dict(card,app_url=bad))
        for key in ('comfort','profile','permission','history'):
            with self.assertRaises(ValidationError):validate_share(dict(card,**{key:'private'}))
        self.assertEqual(upgrade_postcard(CARD),CARD)

    def test_bundle_is_private_manifest_matches_and_json_imports(self):
        import hashlib
        with tempfile.TemporaryDirectory() as work:
            folder=Path(work)/'给朋友的明信片'
            files=export_bundle(folder,dict(CARD,language='zh',app_url=APP_URL))
            self.assertEqual(len(files),4)
            pack=load_friend_pack(folder/'lunchbox.json')
            self.assertEqual(pack['messages'][0],CARD['message'])
            self.assertEqual(pack['shared_dishes'][0]['name'],'Soup')
            manifest=json.loads((folder/'manifest.json').read_text())
            for entry in manifest['files']:
                self.assertEqual(hashlib.sha256((folder/entry['name']).read_bytes()).hexdigest(),entry['sha256'])
            self.assertEqual(folder.stat().st_mode&0o777,0o700)
            self.assertTrue(all(f.stat().st_mode&0o777==0o600 for f in files))
            with self.assertRaises(FileExistsError):export_bundle(folder,CARD)
            self.assertEqual(load_friend_pack(folder/'lunchbox.json'),pack)

    def test_no_partial_bundle_or_overwrite_on_failure(self):
        with tempfile.TemporaryDirectory() as work:
            path=Path(work)/'bundle'
            with patch('src.services.export.content',side_effect=[b'ok',OSError('Synthetic denied')]):
                with self.assertRaises(OSError):export_bundle(path,CARD)
            self.assertEqual(list(Path(work).iterdir()),[])
            file=Path(work)/'card.txt';file.write_text('original')
            with self.assertRaises(FileExistsError):export_file(file,CARD,'text')
            self.assertEqual(file.read_text(),'original')
            export_file(file,CARD,'text',replace=True)
            self.assertIn(CARD['message'],file.read_text())
            with patch('src.services.export.chrome_path',side_effect=RendererUnavailable('Synthetic missing renderer')):
                with self.assertRaises(RendererUnavailable):export_file(Path(work)/'card.png',CARD,'png')
            self.assertFalse((Path(work)/'card.png').exists())

    def test_all_themes_languages_and_maximum_messages_keep_content(self):
        for theme in ('table','receipt','invitation'):
            for language in ('en','zh'):
                card=dict(CARD,theme=theme,language=language,message='合成示例🥣'*160)
                self.assertIn(card['message'],render_html(card))
                self.assertIn(card['message'],render_text(card))
                self.assertEqual(json.loads(render_friend_pack(card))['messages'],[card['message']])

    def test_terminal_bundle_theme_link_and_recipient_import(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from src.terminal import main
        with tempfile.TemporaryDirectory() as work:
            profile=Path(work)/'f.json';folder=Path(work)/'gift'
            answers=['4','Synthetic Jesse','Synthetic Bro','Synthetic: lunch next week?',
                     '3','2','yes','1','yes',str(folder),'0']
            with patch('builtins.input',side_effect=answers),patch('socket.socket',side_effect=AssertionError('No runtime network')),redirect_stdout(StringIO()):
                self.assertEqual(main(['--profile',str(profile),'--language','en','--plain']),0)
            self.assertIn('card receipt',(folder/'postcard.html').read_text())
            self.assertIn(APP_URL,(folder/'postcard.html').read_text())
            self.assertFalse(profile.exists())
            answers=['2','1',str(folder/'lunchbox.json'),'yes','0','0']
            with patch('builtins.input',side_effect=answers),redirect_stdout(StringIO()):
                self.assertEqual(main(['--profile',str(profile),'--language','en','--plain']),0)
            self.assertEqual(load_friend_pack(Path(work)/'f-lunchbox.json')['messages'][0],'Synthetic: lunch next week?')

    def test_missing_png_renderer_can_recover_as_html_without_partial_image(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from src.ui.postcard_flow import postcard_flow
        from src.ui.screen import Screen
        with tempfile.TemporaryDirectory() as work:
            image=Path(work)/'card.png';html=Path(work)/'card.html'
            answers=['Synthetic Me','Synthetic Bro','Synthetic hello','yes','5','no',str(image),'2','no',str(html)]
            with patch('builtins.input',side_effect=answers),patch('src.services.export.chrome_path',side_effect=RendererUnavailable('PNG needs a local Chrome/Chromium installation. HTML, text and JSON still work.')),redirect_stdout(StringIO()):
                postcard_flow(Screen(False),Path(work))
            self.assertFalse(image.exists());self.assertTrue(html.exists())
            self.assertEqual(list(Path(work).iterdir()),[html])

    def test_demo_can_explicitly_export_without_creating_profile_or_meal_records(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from src.terminal import main
        with tempfile.TemporaryDirectory() as work:
            folder=Path(work)/'actual-demo-export'
            answers=['4','Synthetic Jesse','Synthetic Bro','Synthetic: saved you a seat.',
                     '1','1','yes',str(folder),'0']
            with patch('builtins.input',side_effect=answers),patch('socket.socket',side_effect=AssertionError('No network')),redirect_stdout(StringIO()) as out:
                self.assertEqual(main(['--demo','--profile',str(Path(work)/'f.json'),'--language','en','--plain']),0)
            self.assertIn('Saved locally',out.getvalue())
            self.assertIn(APP_URL,(folder/'postcard.html').read_text())
            self.assertEqual(list(Path(work).iterdir()),[folder])
            self.assertTrue(load_friend_pack(folder/'lunchbox.json')['messages'][0].startswith('Synthetic:'))
