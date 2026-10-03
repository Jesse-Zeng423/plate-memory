"""Cancellable, validated prompts for new companion flows."""
from ..food_adapter import ValidationError


class FlowCancelled(Exception):
    pass


class BackRequested(FlowCancelled):
    pass


class CancelRequested(FlowCancelled):
    pass


class HomeRequested(Exception):
    """Return to the table without nested flows swallowing the request."""


def ask(screen, label, default=None, *, optional=False, convert=None):
    while True:
        raw = screen.ask(label, default)
        if raw.lower() in ('/back', 'back'):
            raise BackRequested
        if raw.lower() == '/cancel':
            raise CancelRequested
        if raw.lower() in ('/home', 'home'):
            raise HomeRequested
        if raw.lower() == '/skip' or (optional and not raw):
            if optional:
                return None
            screen.say(screen.t('This field is needed for this action. /back returns without saving.'), 'warn')
            continue
        try:
            if not raw:
                raise ValidationError('Enter a value, or /back to return.')
            return convert(raw) if convert else raw
        except (ValidationError, ValueError) as exc:
            screen.say(screen.t(str(exc)), 'warn')


def choose(screen, label, choices, default=None):
    def validate(raw):
        value = raw.lower().lstrip('/')
        if 'yes' in choices and 'no' in choices:
            value={'1':'yes','2':'no','是':'yes','否':'no','保存':'yes','不保存':'no'}.get(value,value)
        if value == '0' and value not in choices:
            raise BackRequested
        if value == 'h' and value not in choices:
            raise HomeRequested
        if value not in choices:
            raise ValidationError('Choose ' + ', '.join(choices) + ', or /back.')
        return choices[value]
    return ask(screen, label, default, convert=validate)
