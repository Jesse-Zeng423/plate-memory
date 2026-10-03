"""Two-route meal discovery. Selection is a plan, never a consumption record."""
from ..food_adapter import ValidationError
from ..extraction import ExtractionError
from ..services.search import discover
from .prompts import FlowCancelled, ask, choose
from .saved_flow import add_choice, show_choice


def choose_meal(screen, store, review=None, reminders=(), catalog=None, query_parser=None, edit_notes=None):
    route = None
    query = ''
    offset = 0
    category = None
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
                offset=0;category=None
                screen.say('1  Too tired. Let\'s look at takeout.\n2  Up for a walk. Let\'s look at the cafeteria.')
                route = choose(screen, '1 / 2 / back', {'1':'delivery','2':'cafeteria','delivery':'delivery','cafeteria':'cafeteria'})
                query = ask(screen, "Anything you’re craving? (Enter to browse)", optional=True, convert=keyword) or ''
            saved, ideas = discover(store, route, query, catalog, offset, category)
            rows = saved + ideas
            screen.say('More options: next / previous / categories / route / add / notes / ai')
            screen.say('\n' + ('Takeout ideas' if route == 'delivery' else 'A walk and something to eat'), 'title')
            if saved:
                screen.paragraph('Your saved places. Check today’s price and ingredients before deciding.')
            if not saved and ideas:
                screen.say('No saved matches yet. Here are a few things you could look for.')
            if ideas:
                screen.paragraph('Food ideas, not live listings. Ingredients, availability and price are unknown. These ideas have not been personalized.')
            if category:
                screen.paragraph('Category: '+category+' (a reference category, not current stock)')
            if offset:
                screen.say('More food ideas — type previous to go back.')
            if not rows:
                screen.say('No saved matches yet. Type another dish or place to search, or add one you know.')
                if catalog is not None:
                    screen.paragraph('Try a simple food name, like sandwich or 汤. For a sentence, type ai. The starter catalog is still small.')
                action = ask(screen, 'Food keyword / back to table', optional=True)
                action = (action or '').lower()
                if action=='next':
                    screen.say('No more matches on this page. Try previous or a new food name.')
                elif action=='previous':
                    offset=max(0,offset-3)
                elif action=='categories' and catalog:
                    chosen_category=category_flow(screen,catalog)
                    if chosen_category is not None:
                        category=chosen_category;offset=0;query=''
                elif action == 'ai':
                    query = query_flow(screen, query_parser, query);offset=0;category=None
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
                    query = keyword(action); offset=0;category=None
                else:
                    query = '';offset=0;category=None
                continue
            for index, (kind, meal) in enumerate(rows, 1):
                if kind == 'saved':
                    screen.say('Your saved choice', 'title')
                    show_choice(screen, meal, index)
                else:
                    show_idea(screen, meal, index)
            action = ask(screen, 'Number / food keyword / back to table').lower()
            if action=='next' and catalog:
                offset += 3
            elif action=='previous':
                offset=max(0,offset-3)
            elif action=='categories' and catalog:
                chosen_category=category_flow(screen,catalog)
                if chosen_category is not None:
                    category=chosen_category;offset=0;query=''
            elif action == 'ai':
                query = query_flow(screen, query_parser, query);offset=0;category=None
            elif action == 'notes' and edit_notes:
                edit_notes()
            elif action == 'refine':
                try:
                    query = ask(screen, "Anything you’re craving? (Enter to browse; /back: food ideas)", query or None, optional=True, convert=keyword) or ''
                except FlowCancelled:
                    continue
                offset=0;category=None
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
                    show_idea(screen, meal, detail=True)
                try:
                    if meal.get('kind')=='ingredient':
                        decision=choose(screen,'dishes (prepared egg ideas) / check / back',{'dishes':'dishes','check':'review','review':'review'})
                    else:
                        decision = choose(screen, 'pick / check ingredients / back', {'pick':'select','select':'select','check':'review','review':'review','check ingredients':'review'})
                except FlowCancelled:
                    continue
                if decision=='dishes':
                    category='Eggs and omelets';query='';offset=0
                    continue
                if decision == 'review':
                    if kind == 'idea':
                        screen.say('Use review at the table and paste the actual menu to check dietary notes. A dish name cannot establish ingredients.')
                    elif review:
                        review(meal)
                    continue
                screen.say('Sounds good. Keep this idea for today; you can always change your mind.', 'ok')
                screen.say('Nothing has been ordered or recorded as eaten.')
                return meal
            else:
                query = keyword(action);offset=0;category=None
        except FlowCancelled:
            return None
        except ValidationError as exc:
            screen.say(str(exc), 'warn')
            continue


def show_idea(screen, item, index=None, detail=False):
    prefix = str(index) + '. ' if index is not None else ''
    chinese = item['names'].get('zh-hans', item['names'].get('zh', ''))
    screen.say(prefix + item['name'] + (' · ' + chinese if chinese else '') + (' [ingredient reference]' if item.get('kind')=='ingredient' else ' [food idea]') + (' [suggested match]' if item.get('match_kind')=='suggested' else ''), 'title')
    if detail:
        if item.get('kind')=='ingredient':
            screen.paragraph('An ingredient reference, not a prepared meal. Search omelette or an egg sandwich for a dish idea.')
        if item.get('match_kind')=='suggested':
            screen.paragraph('This spelling match is a suggestion. Pick only if it is the food you meant.')
        screen.paragraph('Look for this on your menu. The recipe can vary; check the ingredients if needed.')
        screen.paragraph('Source: ' + item['source']['url'] + ' (revision ' + str(item['source']['revision']) + ')')


def query_flow(screen, parser, previous):
    screen.say('/back: food ideas · /home: table')
    try:
        return _query_flow(screen, parser, previous)
    except FlowCancelled:
        return previous


def _query_flow(screen, parser, previous):
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


def category_flow(screen,catalog):
    screen.say('Browse a food family', 'title')
    categories=catalog.categories()
    if not categories:
        screen.say('No categories in this catalog.');return None
    for i,name in enumerate(categories,1):screen.paragraph(str(i)+'. '+name)
    try:
        return choose(screen,'Category number / back',{str(i):name for i,name in enumerate(categories,1)})
    except FlowCancelled:return None
