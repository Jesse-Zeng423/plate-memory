#!/usr/bin/env python3
"""Synthetic real-terminal walkthroughs, with app sockets forbidden and temp stores."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import sys
import tempfile
import termios
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def run(language):
    master,slave=pty.openpty()
    fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',36,40,0,0))
    process=None
    try:
        with tempfile.TemporaryDirectory(prefix='plate-synthetic-') as work:
            folder=Path(work)
            answers=['1' if language=='zh' else '2',
                '1','2','披萨' if language=='zh' else 'pizza','1','1',
                '2','2','Synthetic Jesse','Synthetic Bro',
                '合成示例：给你留了个座。' if language=='zh' else 'Synthetic: a seat saved for you.',
                '','yes','3',str(folder/'gift.json'),'yes','0',
                '3','1','','','no','','yes','2','0',
                '4','Synthetic Jesse','Synthetic Bro',
                '合成示例：下次，再一起吃。🥣' if language=='zh' else 'Synthetic: lunch next week? 🥣',
                'yes','3','2','yes','1','yes',str(folder/'share'),'0']
            code=("import sys,socket;sys.path.insert(0,"+repr(str(ROOT))+ ");from src.terminal import main;"
                  "socket.socket=lambda *a,**k:(_ for _ in ()).throw(AssertionError('No app network sockets'));"
                  "sys.exit(main(['--no-color','--profile',"+
                  repr(str(folder/'f.json'))+"]))")
            process=subprocess.Popen([sys.executable,'-B','-c',code],cwd=work,stdin=slave,stdout=slave,stderr=slave)
            os.close(slave);slave=None
            os.write(master,('\n'.join(answers)+'\n').encode())
            output=bytearray();deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                if select.select([master],[],[],.2)[0]:
                    try:chunk=os.read(master,65536)
                    except OSError:break
                    if not chunk:break
                    output.extend(chunk)
                    if len(output)>512000:raise RuntimeError('Unexpectedly large terminal output.')
                elif process.poll() is not None:break
            process.wait(timeout=1)
            if process.returncode!=0:raise RuntimeError(output.decode(errors='replace'))
            if (folder/'f.json').exists():raise RuntimeError('Journey unexpectedly created a dietary profile.')
            files={p.name for p in (folder/'share').iterdir()}
            if files!={'postcard.html','postcard.txt','lunchbox.json','manifest.json'}:raise RuntimeError('Incomplete export.')
            from src.services.friend_pack import load_friend_pack
            pack=load_friend_pack(folder/'share/lunchbox.json')
            if not pack['messages'][0].startswith(('Synthetic:','合成示例')):raise RuntimeError('Missing synthetic label.')
            capture=output.decode().replace('\r\n','\n').replace(work,'<synthetic temporary folder>')
            return capture,{'language':language,'columns':40,'exit_code':0,'app_sockets_forbidden':True,
                            'dietary_profile_created':False,'share_files':sorted(files),'synthetic':True}
    finally:
        if process and process.poll() is None:process.kill();process.wait()
        if slave is not None:os.close(slave)
        os.close(master)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Explicit evidence directory; otherwise no evidence files.')
    args=parser.parse_args();results=[]
    for language in ('en','zh'):
        capture,result=run(language);results.append(result)
        if args.output:
            args.output.mkdir(parents=True,exist_ok=True)
            (args.output/('friend-ready-'+language+'.txt')).write_text('SYNTHETIC real-terminal walkthrough\n'+capture)
    if args.output:(args.output/'friend-ready-smoke.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
