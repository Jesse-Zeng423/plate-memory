"""Two-route meal discovery. Selection is a plan, never a consumption record."""
from ..food_adapter import ValidationError
from ..extraction import ExtractionError
from ..services.search import discover
from .prompts import FlowCancelled, BackRequested, CancelRequested, HomeRequested, ask, choose
from .navigation import discard_draft
from .saved_flow import add_choice, show_choice


def choose_meal(screen, store, review=None, reminders=(), catalog=None, query_parser=None, edit_notes=None, draft=None, saved_drafts=None):
    draft = {} if draft is None else draft
    saved_drafts = {} if saved_drafts is None else saved_drafts
    route = draft.get('route')
    query = draft.get('query','')
    offset = draft.get('offset',0)
    category = draft.get('category')
    step = draft.get('step','route')
    def keyword(raw):
        if len(raw) > 160:
            raise ValidationError('Use up to 160 characters.')
        return raw
    screen.say(screen.t('\nHow are you doing today?'), 'title')
    for reminder in reminders:
        screen.paragraph(screen.t('A note to keep in mind: ') + screen.t(reminder))
    while True:
        draft.update(route=route,query=query,offset=offset,category=category,step=step)
        try:
            if step == 'route':
                offset=0;category=None
                screen.say(screen.t('1  Too tired. Let\'s look at takeout.\n2  Up for a walk. Let\'s look at the cafeteria.'))
                route = choose(screen, screen.t('1 / 2 / 0 Back to table / h Home'), {'1':'delivery','2':'cafeteria','delivery':'delivery','cafeteria':'cafeteria'},route)
                step='query'
                draft.update(route=route,step=step)
            if step == 'query':
                query = ask(screen, screen.t("Anything you’re craving? (Enter to browse; /back: route; /home: table)"),query or None, optional=True, convert=keyword) or ''
                step='browse'
                offset=0;category=None
            draft.update(route=route,query=query,offset=offset,category=category,step=step)
            saved, ideas = discover(store, route, query, catalog, offset, category)
            rows = saved + ideas
            screen.say(screen.t('next: more ideas · categories · add a place · describe'))
            screen.say('\n' + (screen.t('Takeout ideas') if route == 'delivery' else screen.t('A walk and something to eat')), 'title')
            if saved:
                screen.paragraph(screen.t('Your saved places. Check today’s price and ingredients before deciding.'))
            if not saved and ideas:
                screen.say(screen.t('A few things you could look for today.'))
            if ideas:
                screen.paragraph(screen.t('Food ideas, not live listings. Ingredients, availability and price are unknown. Check dietary notes against an actual menu.'))
            if category:
                screen.paragraph(screen.t('Category: ')+category+screen.t(' (a reference category, not current stock)'))
            if offset:
                screen.say(screen.t('More food ideas — type previous to go back.'))
            if not rows:
                screen.say(screen.t('No saved matches yet. Type another dish or place to search, or add one you know.'))
                if catalog is not None:
                    screen.paragraph(screen.t('Try sandwich or 汤, or type ai to describe what sounds good.'))
                action = ask(screen, screen.t('Food keyword / 0 Back to craving / h Home'), optional=True)
                action = list_action((action or '').lower())
                if action == '0':raise BackRequested
                if action == 'h':
                    raise HomeRequested
                if action=='next':
                    screen.say(screen.t('No more matches on this page. Try previous or a new food name.'))
                elif action=='previous':
                    offset=max(0,offset-3)
                elif action=='categories' and catalog:
                    chosen_category=category_flow(screen,catalog)
                    if chosen_category is not None:
                        category=chosen_category;offset=0;query=''
                elif action == 'ai':
                    query = query_flow(screen, query_parser, query, draft.setdefault('sentence',{}));offset=0;category=None
                elif action == 'notes' and edit_notes:
                    edit_notes()
                elif action == 'add':
                    try:
                        add_choice(screen, store, route, draft=saved_drafts.setdefault('new',{}))
                    except FlowCancelled:
                        pass
                elif action == 'route':
                    step = 'route'
                elif action:
                    query = keyword(action); offset=0;category=None
                else:
                    query = '';offset=0;category=None
                continue
            for index, (kind, meal) in enumerate(rows, 1):
                if kind == 'saved':
                    screen.say(screen.t('Your saved choice'), 'title')
                    show_choice(screen, meal, index)
                else:
                    show_idea(screen, meal, index)
            action = list_action(ask(screen, screen.t('Number / food keyword / 0 Back to craving / h Home')).lower())
            if action == '0':raise BackRequested
            if action == 'h':
                raise HomeRequested
            if action=='next' and catalog:
                offset += 3
            elif action=='previous':
                offset=max(0,offset-3)
            elif action=='categories' and catalog:
                chosen_category=category_flow(screen,catalog)
                if chosen_category is not None:
                    category=chosen_category;offset=0;query=''
            elif action == 'ai':
                query = query_flow(screen, query_parser, query, draft.setdefault('sentence',{}));offset=0;category=None
            elif action == 'notes' and edit_notes:
                edit_notes()
            elif action == 'refine':
                try:
                    query = ask(screen, screen.t("Anything you’re craving? (Enter to browse; /back: food ideas)"), query or None, optional=True, convert=keyword) or ''
                except FlowCancelled:
                    continue
                offset=0;category=None
            elif action == 'route':
                step = 'route'
            elif action == 'add':
                try:
                    add_choice(screen, store, route, draft=saved_drafts.setdefault('new',{}))
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
                        decision=choose(screen,screen.t('1 Prepared dishes / 2 Check / 3 Source / 0 Back / h Home'),{'1':'dishes','2':'review','3':'source','source':'source','dishes':'dishes','check':'review','review':'review'})
                    else:
                        decision = choose(screen, screen.t('1 Pick / 2 Check ingredients / 3 Source / 0 Back / h Home'), {'1':'select','2':'review','3':'source','source':'source','pick':'select','select':'select','check':'review','review':'review','check ingredients':'review'})
                except FlowCancelled:
                    continue
                if decision=='source':
                    if kind=='idea':screen.paragraph(screen.t('Source: ')+meal['source']['url']+screen.t(' (revision ')+str(meal['source']['revision'])+screen.t(')'))
                    else:screen.say(screen.t('This is a choice you saved yourself.'))
                    continue
                if decision=='dishes':
                    category='Eggs and omelets';query='';offset=0
                    continue
                if decision == 'review':
                    if kind == 'idea':
                        screen.say(screen.t('Use review at the table and paste the actual menu to check dietary notes. A dish name cannot establish ingredients.'))
                    elif review:
                        review(meal)
                    continue
                screen.say(screen.t('Sounds good. Keep this idea for today; you can always change your mind.'), 'ok')
                screen.say(screen.t('Nothing has been ordered or recorded as eaten.'))
                draft.clear()
                return meal
            else:
                query = keyword(action);offset=0;category=None
        except BackRequested:
            if step == 'route':return None
            step = 'route' if step == 'query' else 'query'
        except CancelRequested:
            if discard_draft(screen,draft):return None
        except ValidationError as exc:
            screen.say(str(exc), 'warn')
            continue


def list_action(raw):
    return {'下一页':'next','上一页':'previous','分类':'categories','换路线':'route','收藏':'add',
            '描述':'ai','描述想吃什么':'ai','describe':'ai','add a place':'add','饮食提醒':'notes'}.get(raw,raw)


def show_idea(screen, item, index=None, detail=False):
    prefix = str(index) + '. ' if index is not None else ''
    chinese = item['names'].get('zh-hans', item['names'].get('zh', ''))
    screen.say(prefix + item['name'] + (screen.t(' · ') + chinese if chinese else '') + (screen.t(' [ingredient reference]') if item.get('kind')=='ingredient' else screen.t(' [food idea]')) + (screen.t(' [suggested match]') if item.get('match_kind')=='suggested' else ''), 'title')
    if detail:
        if item.get('kind')=='ingredient':
            screen.paragraph(screen.t('An ingredient reference, not a prepared meal. Search omelette or an egg sandwich for a dish idea.'))
        if item.get('match_kind')=='suggested':
            screen.paragraph(screen.t('This spelling match is a suggestion. Pick only if it is the food you meant.'))
        screen.paragraph(screen.t('Look for this on your menu. The recipe can vary; check the ingredients if needed.'))


def query_flow(screen, parser, previous, draft=None):
    if parser is None:
        screen.say(screen.t('Local AI sentence parsing is unavailable in this demo. Use a dish keyword.'))
        return previous
    draft = {} if draft is None else draft
    state='sentence'
    cached_raw=None
    value=None
    while True:
        try:
            if state=='sentence':
                screen.say(screen.t('Food ideas / Describe a craving — /back: food ideas · /home: table'))
                raw=ask(screen,screen.t('What sounds good? (up to 160 characters)'),draft.get('raw'))
                if len(raw)>160:
                    screen.say(screen.t('Use up to 160 characters.'),'warn');continue
                draft['raw']=raw
                try:
                    if raw!=cached_raw:
                        value=parser(raw);cached_raw=raw
                    state='interpretation'
                except (ExtractionError,ValidationError) as exc:
                    screen.say(screen.t('Let’s use a food name for now. You can still browse.'),'warn');state='literal'
            if state=='interpretation':
                wants=[s['quote'] for s in value['spans'] if s['kind']=='want']
                for span in value['spans']:
                    screen.paragraph(span['kind']+screen.t(': ')+span['quote'])
                screen.paragraph(screen.t('Only a dish keyword will be searched. Avoidances and budgets are unverified until you check an actual menu and price. Nothing is saved as a preference.'))
                if not wants:
                    state='literal'
                else:
                    for index,want in enumerate(wants,1):screen.say(str(index)+screen.t('. ')+want)
                    screen.say(screen.t('/back: edit your sentence · /home: table'))
                    selected=choose(screen,screen.t('Confirm a food phrase by number / 0 Back / h Home'),
                                    {str(i):w for i,w in enumerate(wants,1)})
                    draft.clear()
                    return selected
            if state=='literal':
                screen.say(screen.t('/back: edit your sentence · /home: table'))
                result=ask(screen,screen.t('Literal dish keyword'),optional=True) or ''
                draft.clear()
                return result
        except BackRequested:
            if state=='sentence':return previous
            state='sentence'
        except CancelRequested:
            if discard_draft(screen,draft):return previous


def category_flow(screen,catalog):
    screen.say(screen.t('Browse a food family'), 'title')
    categories=catalog.categories()
    if not categories:
        screen.say(screen.t('No categories in this catalog.'));return None
    for i,name in enumerate(categories,1):screen.paragraph(str(i)+screen.t('. ')+name)
    try:
        return choose(screen,screen.t('Category number / back'),{str(i):name for i,name in enumerate(categories,1)})
    except FlowCancelled:return None
