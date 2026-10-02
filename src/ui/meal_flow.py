"""Two-route meal discovery. Selection is a plan, never a consumption record."""
from ..food_adapter import ValidationError
from ..services.meal_choices import shortlist
from .prompts import FlowCancelled, ask, choose
from .saved_flow import add_choice, show_choice


def choose_meal(screen, store, review=None, reminders=()):
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
            rows = shortlist(store.list(), route, query)
            screen.say('\n' + ('Takeout ideas' if route == 'delivery' else 'A walk and something to eat'), 'title')
            screen.paragraph('Saved references only. Check current availability and price. Dietary notes have not been checked in this list; review a menu before relying on a choice.')
            if not rows:
                screen.say('No saved matches yet. Type another dish or place to search, add a choice, change route, or /back.')
                action = ask(screen, 'New keyword / add / route / back', optional=True)
                action = (action or '').lower()
                if action == 'add':
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
            for index, (meal, _) in enumerate(rows, 1):
                show_choice(screen, meal, index)
            action = ask(screen, 'Number / refine / route / add / back').lower()
            if action == 'refine':
                query = ask(screen, 'Dish or place keyword (optional)', query or None, optional=True, convert=keyword) or ''
            elif action == 'route':
                route = None
            elif action == 'add':
                try:
                    add_choice(screen, store, route)
                except FlowCancelled:
                    pass
            elif action.isdigit() and 1 <= int(action) <= len(rows):
                meal = rows[int(action) - 1][0]
                show_choice(screen, meal)
                try:
                    decision = choose(screen, 'select / review / back', {'select':'select','review':'review'})
                except FlowCancelled:
                    continue
                if decision == 'review':
                    if review:
                        review(meal)
                    continue
                screen.say('An idea for this meal, saved for this session. You can change your mind.', 'ok')
                screen.say('Nothing has been ordered or recorded as eaten.')
                return meal
            else:
                screen.say('Choose a shown number, refine, route, add, or /back.', 'warn')
        except FlowCancelled:
            return None
        except ValidationError as exc:
            screen.say(str(exc), 'warn')
            return None
