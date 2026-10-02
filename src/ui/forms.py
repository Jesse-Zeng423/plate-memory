"""Preference entry prompts; saves remain explicit session actions."""
from uuid import uuid4
from ..food_adapter import ValidationError


def record_form(screen, previous=None):
    old = previous or {}
    screen.say('\nDescribe what your friend actually told you. Nothing is inferred.', 'title')
    text = screen.ask("Food to avoid or change (in your friend's words)", old.get('text'))
    kind = screen.ask('Type: preference or allergy', old.get('kind', 'preference'))
    terms = screen.ask('Words to match, comma separated', ', '.join(old.get('terms', [])))
    days = screen.ask('Days: all, weekdays, weekend, or Mon,Tue,...',
                      ','.join(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i] for i in old.get('weekdays', [])) or 'all')
    names = {'mon':0,'tue':1,'wed':2,'thu':3,'fri':4,'sat':5,'sun':6}
    if days.lower() == 'all':
        weekdays = []
    elif days.lower() == 'weekdays':
        weekdays = list(range(5))
    elif days.lower() == 'weekend':
        weekdays = [5,6]
    else:
        try:
            weekdays = [names[d.strip().lower()] for d in days.split(',')]
        except KeyError as exc:
            raise ValidationError('Use day names such as Mon,Tue or all/weekdays/weekend.') from exc
    permission = screen.ask('Permission: ALLOWED, UNKNOWN or REVOKED', old.get('permission', 'UNKNOWN')).upper()
    confirmed = screen.ask('Last actually confirmed YYYY-MM-DD, or unknown', old.get('confirmed_on') or 'unknown')
    try:
        valid = int(screen.ask('Reconfirm after how many days?', old.get('valid_for_days', 180)))
    except ValueError as exc:
        raise ValidationError('Reconfirmation interval must be a whole number.') from exc
    external = screen.ask('Always check with the preparer? yes/no', 'yes' if old.get('external_required') else 'no').lower()
    if external not in ('yes', 'no'):
        raise ValidationError('Enter yes or no for preparer verification.')
    return {'id': old.get('id', 'note-' + uuid4().hex[:12]), 'text': text, 'kind': kind,
            'terms': [t.strip() for t in terms.split(',')], 'weekdays': weekdays,
            'permission': permission, 'confirmed_on': None if confirmed.lower() == 'unknown' else confirmed,
            'valid_for_days': valid, 'superseded_by': old.get('superseded_by'), 'external_required': external == 'yes'}
