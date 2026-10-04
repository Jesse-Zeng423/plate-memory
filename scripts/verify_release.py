#!/usr/bin/env python3
"""Fresh release archive verification using synthetic normal-mode inputs only."""
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import subprocess
import sys
import tempfile
import zipfile


def verify(archive):
    archive=Path(archive).resolve()
    with tempfile.TemporaryDirectory(prefix='plate-release-') as work:
        folder=Path(work)
        with zipfile.ZipFile(archive) as package:
            names=package.namelist()
            for name in names:
                parts=PurePosixPath(name).parts
                if name.startswith('/') or '..' in parts or any(p in ('.git','private','local','__pycache__') for p in parts):
                    raise ValueError('Unsafe or private release content: '+name)
            package.extractall(folder)
        roots=[p for p in folder.iterdir() if p.is_dir()]
        if len(roots)!=1:raise ValueError('Expected one release root.')
        root=roots[0];outside=folder/'unrelated';outside.mkdir()
        def run(args,**kwargs):
            result=subprocess.run([sys.executable,'-B',*args],cwd=outside,text=True,capture_output=True,timeout=45,**kwargs)
            if result.returncode:raise RuntimeError(result.stderr+'\n'+result.stdout[-4000:])
            return result.stdout
        version=run([str(root/'plate-memory.py'),'--version']).strip()
        run([str(root/'scripts/verify_project.py')])
        # This is the distribution's default real launcher, not --demo.
        transcript=run([str(root/'plate-memory.py'),'--language','en','--plain'],input='0\n')
        if 'Synthetic demo' in transcript or 'Demo records' in transcript:raise ValueError('Default launcher entered demo mode.')
        if (root/'private').exists():raise ValueError('Opening and closing unexpectedly wrote private records.')
        metadata=json.loads(run([str(root/'scripts/run_friend_ready_smoke.py')]))
        if len(metadata)!=2 or not all(r['app_sockets_forbidden'] and r['exit_code']==0 for r in metadata):
            raise ValueError('Incomplete normal-mode export journeys.')
        print(json.dumps({'version':version,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
              'private_files_in_package':0,'default_mode':'normal','fresh_launch':'pass',
              'bilingual_normal_mode_export':'pass','synthetic_inputs_only':True},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive',type=Path)
    verify(parser.parse_args().archive)
