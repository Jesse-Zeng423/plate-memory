"""Compose in memory; preview and destination each have a real return target."""
from pathlib import Path
from uuid import uuid4
from ..food_adapter import ValidationError
from ..services.postcard import render_postcard, export_postcard
from .prompts import ask, choose, BackRequested, CancelRequested
from .navigation import form_fields, discard_draft


def _text(maximum):
    def validate(raw):
        if len(raw) > maximum or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in raw):
            raise ValidationError(f'Use up to {maximum} characters, without control characters.')
        return raw
    return validate


def postcard_flow(screen, directory, selected=None, synthetic=False, draft=None):
    draft = {} if draft is None else draft
    fields = [('sender', 'Your name or nickname', _text(80)),
              ('recipient', 'Your friend’s name or nickname', _text(80)),
              ('message', 'What would you like to say?', _text(1000))]
    screen.say(screen.t('\nUntil our next meal'), 'title')
    screen.paragraph(screen.t('A small note for your friend. Write it here, then send the file yourself whenever you feel like it.'))
    state = 'fields'
    start = 0
    default = directory / ('postcard-' + uuid4().hex[:12] + '.txt')
    while True:
        try:
            if state == 'fields':
                if not form_fields(screen, fields, draft, start):
                    return
                state = 'dish' if selected else 'preview'
            if state == 'dish':
                include = choose(screen, screen.t('Include this food idea: ') + selected['name'] + screen.t('? yes / no'),
                                 {'yes': True, 'no': False}, 'yes' if draft.get('dish') else 'no')
                draft['dish'] = selected['name'] if include else None
                state = 'preview'
            if state == 'preview':
                card = {'schema_version': 1, **{k: draft[k] for k in ('sender', 'recipient', 'message')},
                        'dish': draft.get('dish')}
                screen.say(screen.t('\nPostcard / Preview'), 'title')
                screen.paragraph(render_postcard(card))
                screen.say(screen.t('Only the names, message and optional dish shown above will be shared.'))
                screen.say(screen.t('/back: edit note · /home: table, keep draft · /cancel: discard draft'))
                if not choose(screen, screen.t('Export this note locally? yes / no'), {'yes': True, 'no': False}, 'no'):
                    return
                if synthetic:
                    screen.say(screen.t('Synthetic preview only. No file exported.'))
                    draft.clear()
                    return
                state = 'destination'
            if state == 'destination':
                screen.say(screen.t('Postcard / Save file — /back: preview · /home: table, keep draft'))
                path = Path(ask(screen, screen.t('Save path'), draft.get('path', default))).expanduser()
                draft['path'] = str(path)
                state = 'replace' if path.exists() else 'write'
            if state == 'replace':
                screen.say(screen.t('/back: choose another path · /home: table, keep draft'))
                if not choose(screen, screen.t('Replace the existing file? yes / no'), {'yes': True, 'no': False}, 'no'):
                    screen.say(screen.t('Existing file kept. Your note draft is still available this session.'))
                    return
                state = 'write'
            if state == 'write':
                try:
                    export_postcard(Path(draft['path']), card)
                except OSError as exc:
                    screen.say(screen.t('Could not save: ') + str(exc), 'warn')
                    state = 'destination'
                    continue
                screen.paragraph(screen.t('Saved to ') + draft['path'] + screen.t('. Nothing was sent. You can share this file in your own chat.'))
                draft.clear()
                return
        except BackRequested:
            if state in ('dish', 'preview'):
                state, start = 'fields', len(fields) - 1
            elif state == 'destination':
                state = 'preview'
            elif state == 'replace':
                state = 'destination'
        except CancelRequested:
            if discard_draft(screen, draft):
                return
