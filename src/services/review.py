"""Menu review orchestration, shared independently of terminal interaction.

Progress is optional output. It must never supply permission, context or verdicts.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

from ..demo import load_demo
from ..extraction import local_extract
from ..file_io import read_text
from ..food_adapter import (ValidationError, build_report, menu_lines, parse_date,
                            targets, validate_profile)
from ..json_contract import loads
from ..paths import ROOT
from ..profile_store import load_profile


@dataclass(frozen=True)
class ReviewResult:
    report: dict
    lines: list[dict]


def review_menu(profile: dict, menu: str, meal_date: date, model: str = 'gemma3:4b',
                *, cache_path: Path | None = None, progress: Callable | None = None,
                timeout: float = 180, demo_path: Path | None = None,
                extractor: Callable | None = None) -> ReviewResult:
    """Validate input, extract candidates, and run the deterministic food adapter.

    Explicit demo_path selects a fingerprint-bound fixture, never a fallback.
    The optional extractor permits isolated tests and scripted callers.
    No profile or report is persisted by this operation.
    """
    validate_profile(profile)
    if not isinstance(meal_date, date):
        raise ValidationError('Meal date must be a date.')
    lines = menu_lines(menu)
    allowed = targets(profile)
    if demo_path is not None:
        extraction = load_demo(demo_path, menu, allowed, lines)
        mode, used_model = 'canned-demo', None
    elif not allowed:
        extraction = {'candidates': []}
        mode, used_model = 'permission-withheld-no-inference', None
    else:
        cached = False
        def emit(done, total, message):
            nonlocal cached
            cached = cached or message.startswith('Using validated')
            if progress:
                progress(done, total, message)
        extraction = (extractor or local_extract)(lines, allowed, model, timeout,
                                                  progress=emit, cache_path=cache_path)
        mode = 'local-ollama-cached-extraction' if cached else 'local-ollama'
        used_model = model
    return ReviewResult(build_report(profile, extraction, meal_date, mode, used_model), lines)


def review_demo(scenario: str) -> ReviewResult:
    """Load a fixed public scenario without changing a real session profile."""
    if scenario not in ('weekday', 'weekend', 'stale', 'allergy'):
        raise ValidationError('Choose one of the four listed scenarios.')
    fixtures = loads(read_text(ROOT / 'examples/scenarios.json'))
    fixture = next(item for item in fixtures if item['name'] == scenario)
    return review_menu(load_profile(ROOT / 'examples/profile.json'),
                       read_text(ROOT / 'examples' / fixture['menu']),
                       parse_date(fixture['date']),
                       demo_path=ROOT / 'examples' / fixture['extraction'])
