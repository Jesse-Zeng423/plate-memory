"""Session navigation and interaction; food review lives in an application service."""
from copy import deepcopy
from datetime import date
import json
import sqlite3

from ..paths import ROOT
from ..catalog.index import Catalog
from ..query_parser import parse_query
from ..file_io import read_text
from ..json_contract import loads
from ..storage.meal_store import MealStore
from ..storage.journal_store import JournalStore
from .checkin_flow import checkin_flow
from .home import welcome, home
from .lunchbox_flow import lunchbox_flow
from ..services.friend_pack import load_friend_pack, save_friend_pack
from .meal_flow import choose_meal
from .saved_flow import manage_choices
from ..extraction import ExtractionError
from ..food_adapter import ValidationError, parse_date, validate_profile
from ..json_contract import JsonContractError
from ..profile_store import load_profile, save_profile, update_record
from ..services.review import review_demo, review_menu
from .forms import record_form
from .review_view import show_report, headline
from ..services.meal_choices import guard_reminders, recorded_menu_profile


class Session:
    def __init__(self, screen, path, model, demo=False):
        self.screen, self.path, self.model = screen, path, model
        self.profile = load_profile(ROOT / 'examples/profile.json') if demo else (load_profile(path) if path.exists() else None)
        self.synthetic = demo
        self.meal_date = date.today()
        self.last = None
        self.lines = []
        self.selected_meal = None
        self.meals = MealStore(None if demo else path.with_name(path.stem + '-meals.sqlite3'))
        self.journal = JournalStore(None if demo else path.with_name(path.stem + '-journal.sqlite3'))
        self.demo_meals_loaded = False
        self.catalog = Catalog()
        self.lunchbox_path = path.with_name(path.stem + '-lunchbox.json')
        self.lunchbox = load_friend_pack(ROOT/'examples/friend-pack-v1.json') if demo else (load_friend_pack(self.lunchbox_path) if self.lunchbox_path.exists() else None)

    def meal_store(self):
        if self.synthetic and not self.demo_meals_loaded:
            sample = loads(read_text(ROOT / 'examples/saved-meals-v1.json'))
            if sample.get('synthetic') is not True or sample.get('schema_version') != 1:
                raise ValidationError('Saved-meal demo must be explicitly synthetic schema v1.')
            for meal in sample['meals']:
                self.meals.save(meal)
            self.demo_meals_loaded = True
        return self.meals

    def close(self):
        self.meals.close()
        self.journal.close()

    def review_saved(self, meal):
        self.last = None
        if self.synthetic:
            self.screen.say('This synthetic browser does not run AI. Use demo at the table for a canned guard example.')
            return
        if not self.profile:
            self.screen.say('Add an actual dietary note in preferences first to check it against this choice.')
            return
        if not meal['menu_text']:
            self.screen.say('No menu text saved. Use review at the table to paste the current menu.')
            return
        self.screen.paragraph("Reviewing your recorded menu text. This does not establish today's ingredients or preparation.")
        result = review_menu(recorded_menu_profile(self.profile), meal['menu_text'], self.meal_date, self.model,
                             cache_path=self.path.parent / 'food-cache',
                             progress=lambda n, total, msg: self.screen.say(f'{n}/{total} {msg}'))
        self.last, self.lines = result.report, result.lines
        show_report(self.screen, self.last, self.lines)

    def save_lunchbox(self, pack):
        if not self.synthetic:
            save_friend_pack(self.lunchbox_path, pack)
        self.lunchbox = pack

    def discovery_notes(self):
        self.preferences()
        for decision in guard_reminders(self.profile, self.meal_date):
            self.screen.paragraph('A note to keep in mind: ' + headline(decision))
        self.screen.say('Guard reminders recomputed. Food ideas remain unverified; review the actual menu for preference matching.')

    def commit(self, profile):
        validate_profile(profile)
        if self.synthetic:
            self.screen.say('Updated synthetic session only. No real profile was saved.')
        else:
            save_profile(self.path, profile)
            self.screen.say('Saved locally with a private revision history.', 'ok')
        self.profile = profile
        self.selected_meal = None
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
        welcome(self.screen)
        while True:
            home(self.screen, self.profile, self.meal_date, self.synthetic)
            if self.selected_meal:
                self.screen.paragraph("This session's idea: " + self.selected_meal['name'])
            try:
                command = self.screen.ask('Choose', 'today').lower().lstrip('/')
                command = {'1':'today', '2':'lunchbox', '3':'checkin'}.get(command, command)
                if command == 'quit':
                    return 0
                if command == 'today':
                    self.last = None
                    self.selected_meal = None
                    self.selected_meal = choose_meal(
                        self.screen, self.meal_store(), self.review_saved,
                        reminders=[headline(d) for d in guard_reminders(self.profile, self.meal_date)],
                        catalog=self.catalog,
                        query_parser=None if self.synthetic else lambda q: parse_query(q, self.model),
                        edit_notes=self.discovery_notes)
                    if self.selected_meal:
                        self.last = None
                elif command == 'checkin':
                    checkin_flow(self.screen, self.journal, self.selected_meal)
                elif command == 'lunchbox':
                    lunchbox_flow(self.screen, self.lunchbox, self.save_lunchbox, self.synthetic)
                elif command == 'usuals':
                    self.last = None
                    self.selected_meal = None
                    manage_choices(self.screen, self.meal_store())
                elif command == 'review':
                    self.review()
                elif command == 'demo':
                    self.review(demo=True)
                elif command == 'preferences':
                    self.preferences()
                elif command == 'date':
                    self.meal_date = parse_date(self.screen.ask('Meal date YYYY-MM-DD', self.meal_date))
                    self.last = None
                    self.selected_meal = None
                elif command == 'details':
                    if not self.last:
                        self.screen.say('Review a menu first. Changing notes or date clears the old report.')
                    else:
                        self.screen.say(json.dumps(self.last, ensure_ascii=False, indent=2))
                else:
                    self.screen.say('Choose a command listed above.', 'warn')
            except KeyboardInterrupt:
                self.screen.say('\nCurrent action cancelled. No partial review is shown.', 'warn')
            except (ValidationError, ExtractionError, JsonContractError, OSError, UnicodeError, json.JSONDecodeError, sqlite3.Error) as exc:
                self.screen.say(str(exc), 'error')
