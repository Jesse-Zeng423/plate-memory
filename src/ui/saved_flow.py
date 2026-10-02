"""Explicit add/edit/delete of private saved meal references."""
from copy import deepcopy
from datetime import date

from ..domain.meals import empty_meal, parse_price, validate_meal
from ..food_adapter import ValidationError, parse_date, menu_lines
from .prompts import FlowCancelled, ask, choose


def observed_date(value):
    parsed = parse_date(value)
    if parsed > date.today():
        raise ValidationError('Use the date you actually observed it, not a future date.')
    return parsed.isoformat()


def show_choice(screen, meal, number=None):
    prefix = f'{number}. ' if number is not None else ''
    screen.paragraph(prefix + meal['name'] + ' | ' + (meal['venue'] or 'Place not recorded'))
    if meal['price_cents'] is None:
        screen.say('   Price unknown')
    else:
        cents = meal['price_cents']
        screen.say(f"   CAD {cents // 100}.{cents % 100:02d} recorded {meal['price_date']} (check current price)")
    if meal['route'] == 'cafeteria':
        screen.say(f"   Your walk estimate: {meal['walk_minutes']} min" if meal['walk_minutes'] else '   Walk time unknown')
    screen.say('   Last seen: ' + (meal['last_seen'] or 'not recorded') + '; current availability unknown')


def meal_form(screen, previous=None, route=None):
    meal = deepcopy(previous) if previous else empty_meal(route or 'delivery')
    screen.say('\nSave something you could choose again.', 'title')
    screen.say('/skip leaves optional information unknown; /back leaves this form without saving.')
    meal['route'] = choose(screen, 'delivery / cafeteria', meal_routes(), meal['route'])
    def short_text(value):
        if len(value) > 160 or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value):
            raise ValidationError('Use one short line, up to 160 characters.')
        return value
    meal['name'] = ask(screen, 'Dish name', meal['name'] or None, convert=short_text)
    meal['venue'] = ask(screen, 'Place (optional)', meal['venue'] or None, optional=True, convert=short_text) or ''
    old_price = None if meal['price_cents'] is None else f"{meal['price_cents'] / 100:.2f}"
    meal['price_cents'] = ask(screen, 'CAD price (optional)', old_price, optional=True, convert=parse_price)
    meal['price_date'] = (ask(screen, 'Date that price was recorded YYYY-MM-DD', meal['price_date'], convert=observed_date)
                          if meal['price_cents'] is not None else None)
    meal['last_seen'] = ask(screen, 'Last actually seen YYYY-MM-DD (optional)', meal['last_seen'], optional=True, convert=observed_date)
    def walk(value):
        minutes = int(value)
        if not 1 <= minutes <= 180:
            raise ValidationError('Enter 1–180 minutes, or /skip.')
        return minutes
    meal['walk_minutes'] = (ask(screen, 'Your walking time in minutes (optional)', meal['walk_minutes'], optional=True, convert=walk)
                             if meal['route'] == 'cafeteria' else None)
    def menu_description(value):
        if len(value) > 4000 or len(menu_lines(value)) > 16:
            raise ValidationError('Keep the description within 4000 characters and 16 lines.')
        return value
    meal['menu_text'] = ask(screen, 'Recorded menu description (optional)', meal['menu_text'] or None, optional=True, convert=menu_description) or ''
    validate_meal(meal)
    show_choice(screen, meal)
    screen.say('Menu description: ' + (meal['menu_text'] or 'not recorded'))
    if choose(screen, 'Save this choice? yes/no', {'yes':True, 'no':False}, 'no'):
        return meal
    return None


def meal_routes():
    return {'delivery':'delivery', 'cafeteria':'cafeteria'}


def add_choice(screen, store, route=None):
    meal = meal_form(screen, route=route)
    if meal is not None:
        store.save(meal)
        screen.say('Saved. It will be here next time you need an idea.', 'ok')
    return meal


def manage_choices(screen, store):
    while True:
        try:
            rows = store.list()
            screen.say('\nYour usuals', 'title')
            if not rows:
                screen.say('No choices saved yet. Add a dish and a place; the rest can wait.')
            for index, (meal, _) in enumerate(rows, 1):
                screen.say(meal['route'], 'accent')
                show_choice(screen, meal, index)
            action = choose(screen, 'add / edit / delete / back', {'add':'add','edit':'edit','delete':'delete'})
            if action == 'add':
                try:
                    add_choice(screen, store)
                except FlowCancelled:
                    pass
                continue
            if not rows:
                screen.say('Add a choice first.', 'warn')
                continue
            def number(raw):
                index = int(raw) - 1
                if not 0 <= index < len(rows):
                    raise ValidationError('Choose a number from the list.')
                return index
            meal, revision = rows[ask(screen, 'Choice number', convert=number)]
            if action == 'edit':
                try:
                    updated = meal_form(screen, meal)
                except FlowCancelled:
                    continue
                if updated:
                    store.save(updated, expected_revision=revision)
                    screen.say('Updated your saved choice.', 'ok')
            elif choose(screen, 'Delete this saved choice? yes/no', {'yes':True,'no':False}, 'no'):
                store.delete(meal['id'], revision)
                screen.say('Removed this saved choice.', 'ok')
        except FlowCancelled:
            return
        except ValidationError as exc:
            screen.say(str(exc), 'warn')
            return
