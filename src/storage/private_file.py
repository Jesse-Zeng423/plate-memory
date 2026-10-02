"""Atomic owner-only writes for small local companion artifacts."""
import os
from pathlib import Path
import tempfile


def write_private(path, text):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd, temporary=tempfile.mkstemp(dir=path.parent,prefix='.plate-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            stream.write(text)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
