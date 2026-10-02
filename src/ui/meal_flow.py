"""Two-route meal discovery. Selection is a plan, never a consumption record."""
from ..food_adapter import ValidationError
from ..extraction import ExtractionError
from ..services.search import discover
from .prompts import FlowCancelled, ask, choose
from .saved_flow import add_choice, show_choice


def choose_meal(screen, store, review=None, reminders=(), catalog=None, query_parser=None, edit_notes=None):
    route = None
    query = ''
    def keyword(raw):
        if len(raw) > 160:
            raise ValidationError('Use up to 160 characters.')
        return raw
    screen.say('\nHow are you doing today?', 'title')
    for reminder in reminders:
        screen.paragraph('A note to keep in mind: ' + reminder)
    while True:
        try:
            if route is None:
                screen.say('1  Too tired. Let\'s look at takeout.\n2  Up for a walk. Let\'s look at the cafeteria.')
                route = choose(screen, '1 / 2 / back', {'1':'delivery','2':'cafeteria','delivery':'delivery','cafeteria':'cafeteria'})
                query = ask(screen, 'Dish or place keyword (optional)', optional=True, convert=keyword) or ''
            saved, ideas = discover(store, route, query, catalog)
            rows = saved + ideas
            screen.say('Type a new keyword anytime; ai parses a sentence locally; notes opens dietary notes.')
            screen.say('\n' + ('Takeout ideas' if route == 'delivery' else 'A walk and something to eat'), 'title')
            screen.paragraph('Saved references only. Check current availability and price. Dietary notes have not been checked in this list; review a menu before relying on a choice.')
            if not saved and ideas:
                screen.say('No saved matches yet.' + (' Here are some food ideas to look for.' if ideas else ''))
            if ideas:
                screen.paragraph('Food ideas from the offline catalog. These are not confirmed cafeteria or takeout listings. Ingredients, availability and price are unknown; these ideas have not been personalized.')
            if not rows:
                screen.say('No saved matches yet. Type another dish or place to search, add a choice, change route, or /back.')
                action = ask(screen, 'New keyword / ai / notes / add / route / back', optional=True)
                action = (action or '').lower()
                if action == 'ai':
                    query = query_flow(screen, query_parser, query)
                elif action == 'notes' and edit_notes:
                    edit_notes()
                elif action == 'add':
                    try:
                        add_choice(screen, store, route)
                    except FlowCancelled:
                        pass
                elif action == 'route':
                    route = None
                elif action:
                    query = keyword(action)
                else:
                    query = ''
                continue
            for index, (kind, meal) in enumerate(rows, 1):
                if kind == 'saved':
                    screen.say('Your saved choice', 'title')
                    show_choice(screen, meal, index)
                else:
                    show_idea(screen, meal, index)
            action = ask(screen, 'Number / keyword / ai / notes / refine / route / add / back').lower()
            if action == 'ai':
                query = query_flow(screen, query_parser, query)
            elif action == 'notes' and edit_notes:
                edit_notes()
            elif action == 'refine':
                query = ask(screen, 'Dish or place keyword (optional)', query or None, optional=True, convert=keyword) or ''
            elif action == 'route':
                route = None
            elif action == 'add':
                try:
                    add_choice(screen, store, route)
                except FlowCancelled:
                    pass
            elif action.isdigit() and 1 <= int(action) <= len(rows):
                kind, meal = rows[int(action) - 1]
                if kind == 'saved':
                    show_choice(screen, meal)
                else:
                    show_idea(screen, meal)
                try:
                    decision = choose(screen, 'select / review / back', {'select':'select','review':'review'})
                except FlowCancelled:
                    continue
                if decision == 'review':
                    if kind == 'idea':
                        screen.say('Use review at the table and paste the actual menu to check dietary notes. A dish name cannot establish ingredients.')
                    elif review:
                        review(meal)
                    continue
                screen.say('An idea for this meal, saved for this session. You can change your mind.', 'ok')
                screen.say('Nothing has been ordered or recorded as eaten.')
                return meal
            else:
                query = keyword(action)
        except FlowCancelled:
            return None
        except ValidationError as exc:
            screen.say(str(exc), 'warn')
            return None


def show_idea(screen, item, index=None):
    prefix = str(index) + '. ' if index is not None else ''
    chinese = item['names'].get('zh-hans', item['names'].get('zh', ''))
    screen.say(prefix + item['name'] + (' · ' + chinese if chinese else '') + ' [food idea]', 'title')
    screen.say('Something to look for on the menu. Variants and preparation differ.')
    screen.say('Source: ' + item['source']['url'] + ' (revision ' + str(item['source']['revision']) + ')')


def query_flow(screen, parser, previous):
    if parser is None:
        screen.say('Local AI sentence parsing is unavailable in this demo. Use a dish keyword.')
        return previous
    raw = ask(screen, 'What sounds good? (up to 160 characters)')
    try:
        value = parser(raw)
    except (ExtractionError, ValidationError) as exc:
        screen.say(str(exc), 'warn')
        return ask(screen, 'Literal dish keyword / back', optional=True) or ''
    wants = [s['quote'] for s in value['spans'] if s['kind'] == 'want']
    for span in value['spans']:
        screen.paragraph(span['kind'] + ': ' + span['quote'])
    screen.paragraph('Only a dish keyword will be searched. Avoidances and budgets are unverified until you check an actual menu and price. Nothing is saved as a preference.')
    if not wants:
        return ask(screen, 'Literal dish keyword / back', optional=True) or ''
    for index, want in enumerate(wants, 1):
        screen.say(str(index) + '. ' + want)
    selected = choose(screen, 'Confirm a food phrase by number / back', {str(i):w for i,w in enumerate(wants,1)})
    return selected
