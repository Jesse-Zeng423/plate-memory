"""Stable entry point: python3 -m src.terminal or an absolute script path."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = 'src'

from .paths import ROOT
from .extraction import model_name
from .food_adapter import ValidationError
from .json_contract import JsonContractError
from .ui.screen import Screen, safe_text
from .ui.session import Session
# Preserve the existing presentation import surface for callers.
from .ui.review_view import headline, show_report
from .ui.forms import record_form


def main(argv=None):
    parser = argparse.ArgumentParser(description='Guided local terminal menu review.')
    parser.add_argument('--profile', type=Path, default=ROOT / 'private/friend.json')
    parser.add_argument('--model', type=model_name, default='gemma3:4b')
    parser.add_argument('--demo', action='store_true', help='Synthetic in-memory session, no real profile writes.')
    parser.add_argument('--no-color', action='store_true')
    args = parser.parse_args(argv)
    try:
        return Session(Screen(not args.no_color), args.profile, args.model, args.demo).run()
    except (EOFError, KeyboardInterrupt):
        print('\nPlate Memory closed.')
        return 0
    except (ValidationError, JsonContractError, OSError, UnicodeError) as exc:
        print('Plate Memory: ' + safe_text(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
