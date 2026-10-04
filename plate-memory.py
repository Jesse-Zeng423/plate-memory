#!/usr/bin/env python3
"""Launch the local app from any working directory, without installing packages."""
import sys

if sys.version_info < (3, 10):
    print('Plate Memory needs Python 3.10 or newer. Your files have not been changed.', file=sys.stderr)
    raise SystemExit(2)

from src.terminal import main

if __name__ == '__main__':
    raise SystemExit(main())
