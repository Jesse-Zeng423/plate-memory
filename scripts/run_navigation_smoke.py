#!/usr/bin/env python3
"""Replay synthetic navigation in a real 40-column Unix pseudo-terminal."""
import argparse
import fcntl
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

ROOT = Path(__file__).resolve().parents[1]
ANSWERS = [
    '2','2','Demo Jesse','/home','2','2','','Demo Bro','Remember lunch?',
    'Soup','At school','/back','/back','/skip','yes','3','0',
    '3','1','Synthetic soup','','yes','cafeteria','enjoyed','satisfied',
    'comfortable','','/back','A good lunch','yes','2','0',
    'usuals','1','delivery','Synthetic noodles','','','','','/back',
    'Recorded synthetic noodle description','yes','0',
    '1','2','pizza','0','/back','1','','1','back','h','quit',
]


def run():
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH',35,40,0,0))
    proc = None
    try:
        with tempfile.TemporaryDirectory() as work:
            proc = subprocess.Popen(
                [sys.executable,'-B',str(ROOT/'src/terminal.py'),'--demo','--plain',
                 '--profile',str(Path(work)/'f.json')],
                cwd=work,stdin=slave,stdout=slave,stderr=slave)
            os.close(slave);slave=None
            os.write(master, ('\n'.join(ANSWERS)+'\n').encode())
            output = bytearray()
            deadline = time.monotonic()+15
            while time.monotonic()<deadline:
                if select.select([master],[],[],.2)[0]:
                    try:chunk=os.read(master,65536)
                    except OSError:break
                    if not chunk:break
                    output.extend(chunk)
                    if len(output)>512000:raise RuntimeError('Unexpectedly large terminal output.')
                elif proc.poll() is not None:break
            if proc.poll() is None:
                proc.wait(timeout=1)
            if proc.returncode!=0:raise RuntimeError('Terminal replay failed.')
            if list(Path(work).iterdir()):raise RuntimeError('Demo wrote real files.')
            capture=output.decode().replace('\r\n','\n')
            flat=' '.join(capture.split())
            for expected in ['Remember lunch?','Saved just to your meal journal.',
                             'A good lunch','Saved. It will be here next time','Takeout ideas',
                             '0 Back to food ideas']:
                if expected not in flat:raise RuntimeError('Missing terminal checkpoint: '+expected)
            return 'SYNTHETIC demo; 40-column pseudo-terminal; unrelated cwd; exit 0; no files written.\n'+capture
    finally:
        if proc and proc.poll() is None:proc.kill();proc.wait()
        if slave is not None:os.close(slave)
        os.close(master)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Explicit transcript destination; otherwise no output file.')
    args=parser.parse_args()
    capture=run()
    if args.output:args.output.write_text(capture)
    print('PASS synthetic lunchbox/journal/saved-choice/meal navigation; no demo files.')
