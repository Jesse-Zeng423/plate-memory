"""Session navigation and interaction; food review lives in an application service."""
from copy import deepcopy
from datetime import date
import json

from ..paths import ROOT
from ..extraction import ExtractionError
from ..food_adapter import ValidationError, parse_date, validate_profile
from ..json_contract import JsonContractError
from ..profile_store import load_profile, save_profile, update_record
from ..services.review import review_demo, review_menu
from .forms import record_form
from .review_view import show_report


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
            result = review_demo(scenario)
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
            def progress(n, total, msg):
                self.screen.say(f'  {n}/{total}  {msg}')
            self.screen.say('Preparing local review. First extraction may take longer while weights load; Ctrl+C cancels.')
            result = review_menu(profile, '\n'.join(chunks), meal, self.model,
                                 cache_path=self.path.parent / 'food-cache', progress=progress)
        self.last = result.report
        self.lines = result.lines
        show_report(self.screen, self.last, self.lines)

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
