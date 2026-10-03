"""In-memory form navigation. This module never persists a draft."""
from .prompts import ask, choose, BackRequested, CancelRequested


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


def form_fields(screen, fields, draft, start=0):
    """Fill (key, label, converter) fields; back edits the preceding field.

    The caller owns draft, including when /home interrupts the form. Returning
    False means back from the first field or confirmed discard, never a save.
    """
    index = start
    screen.say('/back: previous field · /home: table, keep draft · /cancel: discard draft')
    while index < len(fields):
        key, label, convert = fields[index]
        try:
            draft[key] = ask(screen, label, draft.get(key), convert=convert)
            index += 1
        except BackRequested:
            if index == 0:
                screen.say('Back at the table. Your draft is kept for this session.')
                return False
            index -= 1
        except CancelRequested:
            if discard_draft(screen, draft):
                return False
    return True
