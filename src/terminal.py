"""Guided terminal interface. No UI dependency or cloud service required."""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import re
import shutil
import sys
import textwrap
from uuid import uuid4

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = 'src'

from .cli import ROOT, load_demo, read_text
from .extraction import ExtractionError, local_extract, model_name
from .food_adapter import (ValidationError, build_report, menu_lines, parse_date,
                           targets, validate_profile)
from .json_contract import JsonContractError
from .profile_store import load_profile, save_profile, update_record


def safe_text(value):
    # Untrusted menu/model/profile text must not issue terminal control commands.
    return re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', '', str(value))


class Screen:
    def __init__(self, color=True):
        self.color = color and sys.stdout.isatty() and 'NO_COLOR' not in os.environ

    def say(self, text='', tone=None):
        colors = {'title': '1;36', 'warn': '33', 'error': '31', 'ok': '32'}
        clean = safe_text(text)
        if self.color and tone in colors:
            clean = '\033[' + colors[tone] + 'm' + clean + '\033[0m'
        print(clean)

    def paragraph(self, text):
        width = max(24, min(88, shutil.get_terminal_size((88, 24)).columns - 2))
        self.say(textwrap.fill(safe_text(text), width))

    def ask(self, label, default=None):
        suffix = f' [{safe_text(default)}]' if default is not None else ''
        result = input(safe_text(label) + suffix + ': ').strip()
        return result or (str(default) if default is not None else '')


def headline(decision):
    if decision['reason_code'] == 'PERMISSION_REVOKED':
        return 'Not used: permission revoked'
    if decision['kind'] == 'withheld':
        return 'Ask for permission before using this record'
    if decision['guard_verdict'] == 'ESCALATE':
        return 'Allergy: confirm ingredients and cross-contact with the preparer'
    if decision['guard_verdict'] == 'VERIFY_EXTERNAL':
        return 'Check current preparation with the preparer'
    if decision['memory_action'] == 'ASK':
        return 'Ask your friend before applying this preference'
    if decision['memory_action'] == 'USE':
        return 'Preference applies: request a change or choose another dish'
    if 'WEEKDAY_OUT_OF_SCOPE' in decision['observations']:
        return 'Preference does not apply on this meal date'
    if 'SUPERSEDED' in decision['reason_code']:
        return 'An updated record replaces this preference'
    return 'No relevant ingredient detected; this is not clearance'


def show_report(screen, report, lines):
    screen.say('\nMenu review', 'title')
    screen.say(f"{report['friend']} | Meal date {report['meal_date']}")
    mode = report['extraction_mode']
    screen.say('Synthetic canned demo; no AI ran.' if mode == 'canned-demo' else
               ('Validated cached extraction: ' + report['model'] if mode == 'local-ollama-cached-extraction' else
               ('Local model: ' + report['model'] if report['model'] else 'Permission withheld; no AI ran.')))
    screen.paragraph(report['notice'])
    # Persistent allergy warning even when no ingredient was detected.
    for d in report['decisions']:
        if d['guard_verdict'] == 'ESCALATE':
            screen.say('\n! ' + headline(d), 'warn')
            screen.paragraph(d['memory'])
    for line in lines:
        screen.say('\n' + line['line_id'], 'title')
        screen.paragraph(line['text'])
        relevant = [d for d in report['decisions'] if any(c['line_id'] == line['line_id'] for c in d['candidates'])]
        if not relevant:
            screen.paragraph('No matching note detected for this line. Missing ingredients and cross-contact are not checked.')
        for d in relevant:
            screen.paragraph(headline(d) + ': ' + d['memory'])
    screen.say('\nNotes for this meal', 'title')
    for d in report['decisions']:
        screen.paragraph(d['memory_id'] + ' | ' + headline(d))
    screen.say('Use preferences to confirm, edit or revoke a note; details shows the rule trace.')


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


class Session:
    def __init__(self, screen, path, model, demo=False):
        self.screen, self.path, self.model = screen, path, model
        self.profile = load_profile(ROOT / 'examples/profile.json') if demo else (load_profile(path) if path.exists() else None)
        self.synthetic = demo
        self.meal_date = date.today()
        self.last = None
        self.lines = []

    def commit(self, profile):
        validate_profile(profile)
        if self.synthetic:
            self.screen.say('Updated synthetic session only. No real profile was saved.')
        else:
            save_profile(self.path, profile)
            self.screen.say('Saved locally with a private revision history.', 'ok')
        self.profile = profile
        if self.last:
            self.last = None
            self.screen.say('Previous review cleared. Review the menu again with the updated notes.')

    def preferences(self):
        if self.profile:
            self.screen.say('\nLocal notes (including records withheld from reviews)', 'title')
            for i, f in enumerate(self.profile['memories'], 1):
                self.screen.paragraph(f"{i}. {f['text']} | {f['permission']} | confirmed {f['confirmed_on'] or 'unknown'}")
        choice = self.screen.ask('add / edit / confirm / revoke / allow / back', 'back').lower()
        if choice == 'back':
            return
        if choice == 'add':
            friend = self.profile['friend'] if self.profile else self.screen.ask('Friend name or alias', 'Harold')
            new = deepcopy(self.profile) if self.profile else {'schema_version':1, 'friend':friend, 'memories':[]}
            new['memories'].append(record_form(self.screen))
        elif choice in ('edit', 'confirm', 'revoke', 'allow') and self.profile:
            try:
                index = int(self.screen.ask('Note number')) - 1
            except ValueError as exc:
                raise ValidationError('Enter a note number from the list.') from exc
            if not 0 <= index < len(self.profile['memories']):
                raise ValidationError('Note number is outside the list.')
            fact = self.profile['memories'][index]
            if choice == 'edit':
                new = deepcopy(self.profile)
                new['memories'][index] = record_form(self.screen, fact)
            else:
                if choice == 'confirm':
                    self.screen.say('Confirm only after your friend says this still applies. Date uses today, not the meal date.')
                if choice == 'allow':
                    self.screen.say('Allow only after your friend explicitly permits use of this note.')
                if self.screen.ask('Apply this change? yes/no', 'no').lower() != 'yes':
                    return
                new = update_record(self.profile, fact['id'], choice)
        else:
            raise ValidationError('Choose add first, or use one of the listed actions.')
        validate_profile(new)
        if choice in ('add', 'edit'):
            if self.screen.ask('Save this note? yes/no', 'no').lower() != 'yes':
                return
        self.commit(new)

    def review(self, demo=False):
        self.last = None
        if demo:
            self.screen.say('Opening an independent synthetic example; your real profile is unchanged.')
            scenario = self.screen.ask('Scenario: weekday / weekend / stale / allergy', 'weekend')
            if scenario not in ('weekday', 'weekend', 'stale', 'allergy'):
                raise ValidationError('Choose one of the four listed scenarios.')
            profile = load_profile(ROOT / 'examples/profile.json')
            menu = read_text(ROOT / f'examples/{scenario}.txt')
            scenarios = json.loads(read_text(ROOT / 'examples/scenarios.json'))
            # Fixture dates are read below; no artificial claims about current preferences.
            fixture = next(s for s in scenarios if s['name'] == scenario)
            meal = parse_date(fixture['date'])
            lines = menu_lines(menu)
            extraction = load_demo(ROOT / f'examples/{scenario}.extraction.json', menu, targets(profile), lines)
            mode, model = 'canned-demo', None
        else:
            if self.synthetic:
                raise ValidationError('Demo sessions do not use real menus. Restart without --demo to create a real profile.')
            if not self.profile:
                raise ValidationError('Add an actual friend-authored note in preferences first, or choose demo.')
            profile, meal = self.profile, self.meal_date
            self.screen.say('Paste one dish per line (up to 16). Finish with a line containing /done. /cancel cancels.')
            chunks = []
            while True:
                line = input()
                if line == '/cancel':
                    return
                if line == '/done':
                    break
                chunks.append(line)
                if len('\n'.join(chunks)) > 12000 or sum(bool(c.strip()) for c in chunks) > 16:
                    raise ValidationError('Menu too long. Review at most 16 short dish lines at a time.')
            lines = menu_lines('\n'.join(chunks))
            allowed = targets(profile)
            if allowed:
                self.screen.say('Local extraction started. The first line can take longer while weights load; Ctrl+C cancels this review.')
                cached = []
                def progress(n, total, msg):
                    cached.append(msg.startswith('Using validated'))
                    self.screen.say(f'  {n}/{total}  {msg}')
                extraction = local_extract(lines, allowed, self.model,
                    progress=progress,
                    cache_path=self.path.parent / 'food-cache')
                mode, model = ('local-ollama-cached-extraction' if any(cached) else 'local-ollama'), self.model
            else:
                extraction, mode, model = {'candidates':[]}, 'permission-withheld-no-inference', None
        self.last = build_report(profile, extraction, meal, mode, model)
        self.lines = lines
        show_report(self.screen, self.last, lines)

    def run(self):
        self.screen.say('\n╭─ Plate Memory ───────────────────────────╮', 'title')
        self.screen.say('│  Plan a meal with someone you know.      │', 'title')
        self.screen.say('╰─────────────────────────────────────────╯', 'title')
        self.screen.paragraph('A menu, a friend, and notes you can trust. Local food extraction; explicit rules decide when a note applies.')
        if self.synthetic:
            self.screen.say('Synthetic demo session. These are not Harold\'s preferences.', 'warn')
        while True:
            self.screen.say('\n' + (self.profile['friend'] if self.profile else 'No profile yet: add actual preferences or try demo') + ' | ' + self.meal_date.isoformat(), 'title')
            self.screen.say('review  Paste a menu       preferences  Manage notes\ndemo    Try a sample      date         Change meal date\ndetails View rule trace   quit         Exit')
            try:
                command = self.screen.ask('Choose', 'demo' if not self.profile or self.synthetic else 'review').lower().lstrip('/')
                if command == 'quit':
                    return 0
                if command == 'review':
                    self.review()
                elif command == 'demo':
                    self.review(demo=True)
                elif command == 'preferences':
                    self.preferences()
                elif command == 'date':
                    self.meal_date = parse_date(self.screen.ask('Meal date YYYY-MM-DD', self.meal_date))
                    self.last = None
                elif command == 'details':
                    if not self.last:
                        self.screen.say('Review a menu first. Changing notes or date clears the old report.')
                    else:
                        self.screen.say(json.dumps(self.last, ensure_ascii=False, indent=2))
                else:
                    self.screen.say('Choose a command listed above.', 'warn')
            except KeyboardInterrupt:
                self.screen.say('\nCurrent action cancelled. No partial review is shown.', 'warn')
            except (ValidationError, ExtractionError, JsonContractError, OSError, UnicodeError, json.JSONDecodeError) as exc:
                self.screen.say(str(exc), 'error')


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
