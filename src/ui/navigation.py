"""In-memory form navigation. This module never persists a draft."""
from dataclasses import dataclass
from .prompts import ask, choose, BackRequested, CancelRequested


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    convert: object = None
    optional: bool = False
    active: object = None
    default: object = None


def short_text(maximum):
    from ..food_adapter import ValidationError
    def validate(raw):
        if len(raw) > maximum or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in raw):
            raise ValidationError(f'Use up to {maximum} characters, without control characters.')
        return raw
    return validate


def discard_draft(screen, draft):
    """A populated draft is discarded only after an explicit yes."""
    if not draft:
        return True
    try:
        discard = choose(screen, 'Discard this draft? yes / no (keep editing)',
                         {'yes': True, 'no': False}, 'no')
    except (BackRequested, CancelRequested):
        return False
    if discard:
        draft.clear()
    return discard


def form_fields(screen, fields, draft, start=0, back_target='the table'):
    """Fill (key, label, converter) fields; back edits the preceding field.

    The caller owns draft, including when /home interrupts the form. Returning
    False means back from the first field or confirmed discard, never a save.
    """
    fields = [f if isinstance(f, Field) else Field(*f) for f in fields]
    def active(index):
        return fields[index].active is None or fields[index].active(draft)
    index = start
    while 0 <= index < len(fields) and not active(index):
        index -= 1
    index = max(0, index)
    screen.say('/back: previous field · /home: table, keep draft · /cancel: discard draft')
    while index < len(fields):
        field = fields[index]
        if not active(index):
            index += 1
            continue
        try:
            default = field.default(draft) if field.default else draft.get(field.key)
            draft[field.key] = ask(screen, field.label, default, optional=field.optional, convert=field.convert)
            index += 1
        except BackRequested:
            previous = index - 1
            while previous >= 0 and not active(previous):
                previous -= 1
            if previous < 0:
                screen.say('Back to ' + back_target + '. Your draft is kept for this session.')
                return False
            index = previous
        except CancelRequested:
            if discard_draft(screen, draft):
                return False
    return True
