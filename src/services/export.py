"""Private atomic local exports; PNG uses an optional isolated local browser."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import time
import subprocess
import tempfile
from ..domain.share import validate_share
from .png import crop_background
from .share_render import render_html,render_text,render_friend_pack

FORMATS={'html':'.html','text':'.txt','json':'.json','png':'.png'}


class RendererUnavailable(OSError):
    pass


def chrome_path():
    for candidate in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                      shutil.which('chromium'),shutil.which('chromium-browser'),shutil.which('google-chrome')):
        if candidate and Path(candidate).is_file():return candidate
    raise RendererUnavailable('PNG needs a local Chrome/Chromium installation. HTML, text and JSON still work.')


def render_png(card,viewport=(1000,4000)):
    browser=chrome_path()
    with tempfile.TemporaryDirectory(prefix='plate-render-') as work:
        folder=Path(work);source=folder/'card.html';image=folder/'card.png'
        if any(type(v) is not int for v in viewport) or not 1<=viewport[0]<=2000 or not 1<=viewport[1]<=4000:
            raise ValueError('Invalid image viewport.')
        html=render_html(card)
        # Desktop Chrome enforces a minimum layout width on macOS. Pin the
        # document width for smaller card previews so the screenshot cannot clip.
        html=html.replace('</head>','<style>html{width:'+str(viewport[0])+'px}</style></head>')
        source.write_text(html,encoding='utf-8')
        command=[browser,'--headless','--disable-gpu','--disable-background-networking',
                 '--disable-sync','--no-first-run','--no-default-browser-check',
                 '--host-resolver-rules=MAP * 0.0.0.0, EXCLUDE localhost',
                 '--user-data-dir='+str(folder/'browser'),'--hide-scrollbars',
                 '--window-size='+str(viewport[0])+','+str(viewport[1]),'--screenshot='+str(image),source.as_uri()]
        command.extend(['--disable-breakpad','--disable-crash-reporter','--virtual-time-budget=1000'])
        process=None
        raw=None
        try:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,start_new_session=True)
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                if image.exists():
                    candidate=image.read_bytes()
                    # Chrome on macOS can stay alive after writing. Accept only a
                    # complete PNG, then terminate this isolated renderer group.
                    if candidate.startswith(b'\x89PNG\r\n\x1a\n') and candidate.endswith(b'IEND\xaeB`\x82'):
                        if len(candidate)>10_000_000:raise RendererUnavailable('Invalid local renderer image. Try HTML instead.')
                        raw=candidate
                        break
                if process.poll() is not None:break
                time.sleep(.1)
            if raw is None:raise RendererUnavailable('Local PNG rendering failed. Try HTML instead.')
        except OSError as exc:
            raise RendererUnavailable('Local PNG rendering failed. Try HTML instead.') from exc
        finally:
            if process is not None:
                try:os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.wait()
        try:return crop_background(raw)
        except (ValueError,KeyError,StopIteration) as exc:
            raise RendererUnavailable('Invalid local renderer image. Try HTML instead.') from exc


def content(card,format):
    validate_share(card)
    if format=='html':return render_html(card).encode('utf-8')
    if format=='text':return render_text(card).encode('utf-8')
    if format=='json':return render_friend_pack(card).encode('utf-8')
    if format=='png':return render_png(card)
    raise ValueError('Unknown export format.')


def export_file(path,card,format,replace=False):
    path=Path(path)
    if path.suffix.lower()!=FORMATS[format]:raise ValueError('Use the '+FORMATS[format]+' extension for this format.')
    raw=content(card,format)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,temporary=tempfile.mkstemp(dir=path.parent,prefix='.plate-export-')
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw)
        if replace:os.replace(temporary,path)
        else:os.link(temporary,path)  # A concurrently created target is never overwritten.
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    return [path]


def export_bundle(path,card):
    """One new folder contains HTML/text/import JSON plus a file manifest."""
    path=Path(path);validate_share(card)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    path.mkdir(mode=0o700)  # Reserve a new destination; never delete an older bundle.
    stage=None
    try:
        stage=Path(tempfile.mkdtemp(dir=path.parent,prefix='.plate-bundle-'))
        manifest={'schema_version':1,'files':[]}
        for name,format in [('postcard.html','html'),('postcard.txt','text'),('lunchbox.json','json')]:
            raw=content(card,format);target=stage/name
            with target.open('xb') as stream:stream.write(raw)
            target.chmod(0o600)
            manifest['files'].append({'name':name,'sha256':hashlib.sha256(raw).hexdigest()})
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        (stage/'manifest.json').chmod(0o600)
        os.replace(stage,path);stage=None
        return [path/e['name'] for e in manifest['files']]+[path/'manifest.json']
    except BaseException:
        # Only our empty reservation is removable; never remove unrelated contents.
        try:path.rmdir()
        except OSError:pass
        raise
    finally:
        if stage is not None:shutil.rmtree(stage)
