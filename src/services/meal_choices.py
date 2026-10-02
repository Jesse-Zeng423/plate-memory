"""Deterministic discovery of saved facts; no implicit dietary personalization."""
import unicodedata
from copy import deepcopy

from ..domain.meals import validate_meal
from ..food_adapter import ValidationError, build_report, validate_profile


def normalized(text):
    return unicodedata.normalize('NFKC', text).casefold().strip()


def shortlist(rows, route, query='', limit=3):
    if route not in ('delivery', 'cafeteria'):
        raise ValidationError('Choose delivery or cafeteria.')
    if len(query) > 160:
        raise ValidationError('Use a short dish or place keyword (up to 160 characters).')
    tokens = normalized(query).split()
    matches = []
    for meal, revision in rows:
        validate_meal(meal)
        if meal['route'] != route:
            continue
        name = normalized(meal['name'])
        # Matching only name/place prevents a hidden ingredient note from appearing
        # to establish ingredient suitability before explicit guard review.
        text = name + ' ' + normalized(meal['venue'])
        if not all(token in text for token in tokens):
            continue
        score = sum(token in name for token in tokens)
        matches.append((score, meal, revision))
    matches.sort(key=lambda item: (-item[0], normalized(item[1]['name']), item[1]['id']))
    return [(meal, revision) for _, meal, revision in matches[:limit]]


def guard_reminders(profile, meal_date):
    """Keep risk/permission reminders visible without claiming a menu was checked."""
    if profile is None:
        return []
    validate_profile(profile)
    report = build_report(profile, {'candidates': []}, meal_date, 'saved-choice-discovery', None)
    return [decision for decision in report['decisions']
            if decision['guard_verdict'] in ('ESCALATE', 'VERIFY_EXTERNAL')
            or decision['memory_action'] == 'ASK']


def recorded_menu_profile(profile):
    """Recorded restaurant text requires current preparation verification.

    This is an ephemeral review context, never a write to the user's profile.
    """
    copied = deepcopy(validate_profile(profile))
    for fact in copied['memories']:
        fact['external_required'] = True
    return copied
