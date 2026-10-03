"""Explicit add/edit/delete of private saved meal references."""
from copy import deepcopy
from datetime import date

from ..domain.meals import empty_meal, parse_price, validate_meal, FIELDS
from ..food_adapter import ValidationError, parse_date, menu_lines
from .prompts import FlowCancelled, ask, choose, BackRequested, CancelRequested
from .navigation import Field, form_fields, discard_draft, short_text


def observed_date(value):
    parsed = parse_date(value)
    if parsed > date.today():
        raise ValidationError('Use the date you actually observed it, not a future date.')
    return parsed.isoformat()


def show_choice(screen, meal, number=None):
    prefix = f'{number}. ' if number is not None else ''
    screen.paragraph(prefix + meal['name'] + screen.t(' | ') + (meal['venue'] or 'Place not recorded'))
    if meal['price_cents'] is None:
        screen.say(screen.t('   Price unknown'))
    else:
        cents = meal['price_cents']
        screen.say(f"   CAD {cents // 100}.{cents % 100:02d} recorded {meal['price_date']} (check current price)")
    if meal['route'] == 'cafeteria':
        screen.say(f"   Your walk estimate: {meal['walk_minutes']} min" if meal['walk_minutes'] else screen.t('   Walk time unknown'))
    screen.say(screen.t('   Last seen: ') + (meal['last_seen'] or 'not recorded') + screen.t('; current availability unknown'))


def meal_form(screen, previous=None, route=None, draft=None, back_target='saved choices'):
    draft = {} if draft is None else draft
    if not draft:
        draft.update(deepcopy(previous) if previous else empty_meal(route or 'delivery'))
    def route_value(raw):
        value={'1':'delivery','2':'cafeteria','外卖':'delivery','食堂':'cafeteria'}.get(raw,raw)
        if value not in meal_routes():raise ValidationError('Choose delivery or cafeteria.')
        return value
    def price_default(d):
        price=d.get('price_cents')
        return None if price is None else f'{price//100}.{price%100:02d}'
    def walk(value):
        minutes = int(value)
        if not 1 <= minutes <= 180:raise ValidationError('Enter 1–180 minutes, or /skip.')
        return minutes
    def menu_description(value):
        if len(value) > 4000 or len(menu_lines(value)) > 16:
            raise ValidationError('Keep the description within 4000 characters and 16 lines.')
        return value
    fields=[Field('route',screen.t('delivery / cafeteria'),route_value),
            Field('name',screen.t('Dish name'),short_text(160)),
            Field('venue',screen.t('Place (optional)'),short_text(160),True),
            Field('price_cents',screen.t('CAD price (optional)'),parse_price,True,default=price_default),
            Field('price_date',screen.t('Date that price was recorded YYYY-MM-DD'),observed_date,
                  active=lambda d:d.get('price_cents') is not None),
            Field('last_seen',screen.t('Last actually seen YYYY-MM-DD (optional)'),observed_date,True),
            Field('walk_minutes',screen.t('Your walking time in minutes (optional)'),walk,True,
                  active=lambda d:d['route']=='cafeteria'),
            Field('menu_text',screen.t('Recorded menu description (optional)'),menu_description,True)]
    screen.say(screen.t('\nSave something you could choose again.'), 'title')
    screen.say(screen.t('/skip clears optional information; nothing is saved until you confirm.'))
    start=0
    while True:
        if not form_fields(screen,fields,draft,start,back_target=back_target):return None
        meal={k:draft[k] for k in FIELDS}
        meal['venue']=meal['venue'] or '';meal['menu_text']=meal['menu_text'] or ''
        if meal['price_cents'] is None:meal['price_date']=None
        if meal['route']!='cafeteria':meal['walk_minutes']=None
        validate_meal(meal)
        show_choice(screen,meal)
        screen.say(screen.t('Menu description: ')+(meal['menu_text'] or 'not recorded'))
        screen.say(screen.t('/back: edit last answer · /home: table, keep draft · /cancel: discard draft'))
        try:
            if choose(screen,screen.t('Save this choice? yes/no'),{'yes':True,'no':False},'no'):return meal
            return None
        except BackRequested:start=len(fields)-1
        except CancelRequested:
            if discard_draft(screen,draft):return None
            start = len(fields)


def meal_routes():
    return {'delivery':'delivery', 'cafeteria':'cafeteria'}


def add_choice(screen, store, route=None, draft=None):
    meal = meal_form(screen, route=route, draft=draft,
                     back_target='food ideas' if route else 'saved choices')
    if meal is not None:
        store.save(meal)
        if draft is not None:draft.clear()
        screen.say(screen.t('Saved. It will be here next time you need an idea.'), 'ok')
    return meal


def manage_choices(screen, store, drafts=None):
    drafts={} if drafts is None else drafts
    while True:
        action = None
        try:
            rows = store.list()
            screen.say(screen.t('\nYour usuals'), 'title')
            if not rows:
                screen.say(screen.t('No choices saved yet. Add a dish and a place; the rest can wait.'))
            for index, (meal, _) in enumerate(rows, 1):
                screen.say(meal['route'], 'accent')
                show_choice(screen, meal, index)
            action = choose(screen, screen.t('1 Add / 2 Edit / 3 Delete / 0 Back to table / h Home'), {'1':'add','2':'edit','3':'delete','add':'add','edit':'edit','delete':'delete'})
            if action == 'add':
                try:
                    add_choice(screen, store, draft=drafts.setdefault('new',{}))
                except FlowCancelled:
                    pass
                continue
            if not rows:
                screen.say(screen.t('Add a choice first.'), 'warn')
                continue
            def number(raw):
                index = int(raw) - 1
                if not 0 <= index < len(rows):
                    raise ValidationError('Choose a number from the list.')
                return index
            meal, revision = rows[ask(screen, screen.t('Choice number'), convert=number)]
            if action == 'edit':
                try:
                    draft=drafts.setdefault(meal['id'],{})
                    if draft and draft.get('_revision')!=revision:
                        screen.say(screen.t('This choice changed while you were editing. Discard the old draft to start again.'), 'warn')
                        if not discard_draft(screen,draft):continue
                    if not draft:draft.update(deepcopy(meal));draft['_revision']=revision
                    updated = meal_form(screen, meal, draft=draft)
                except FlowCancelled:
                    continue
                if updated:
                    store.save(updated, expected_revision=revision)
                    draft.clear()
                    screen.say(screen.t('Updated your saved choice.'), 'ok')
            elif choose(screen, screen.t('Delete this saved choice? yes/no'), {'yes':True,'no':False}, 'no'):
                store.delete(meal['id'], revision)
                screen.say(screen.t('Removed this saved choice.'), 'ok')
        except FlowCancelled:
            if action is None:return
            continue
        except ValidationError as exc:
            screen.say(str(exc), 'warn')
            return
