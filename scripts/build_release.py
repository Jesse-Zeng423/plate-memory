#!/usr/bin/env python3
"""Archive a committed public Git ref; never package a local/private working tree."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.version import VERSION


def build(output,ref='HEAD'):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    archive=output/('plate-memory-'+VERSION+'.zip')
    if archive.exists():raise FileExistsError('Choose a new output directory; release artifacts are not overwritten.')
    subprocess.run(['git','archive','--format=zip','--prefix=plate-memory-'+VERSION+'/',
                    '--output='+str(archive),ref],cwd=ROOT,check=True)
    checksum=output/'SHA256SUMS.txt'
    checksum.write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    return archive


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ref',default='HEAD')
    args=parser.parse_args();print(build(args.output,args.ref))
