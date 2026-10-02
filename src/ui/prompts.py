"""Cancellable, validated prompts for new companion flows."""
from ..food_adapter import ValidationError


class FlowCancelled(Exception):
    pass


def ask(screen, label, default=None, *, optional=False, convert=None):
    while True:
        raw = screen.ask(label, default)
        if raw.lower() in ('/back', '/cancel', 'back'):
            raise FlowCancelled
        if raw.lower() == '/skip' or (optional and not raw):
            if optional:
                return None
            screen.say('This field is needed for this action. /back returns without saving.', 'warn')
            continue
        try:
            if not raw:
                raise ValidationError('Enter a value, or /back to return.')
            return convert(raw) if convert else raw
        except (ValidationError, ValueError) as exc:
            screen.say(str(exc), 'warn')


def choose(screen, label, choices, default=None):
    def validate(raw):
        value = raw.lower().lstrip('/')
        if value not in choices:
            raise ValidationError('Choose ' + ', '.join(choices) + ', or /back.')
        return choices[value]
    return ask(screen, label, default, convert=validate)
