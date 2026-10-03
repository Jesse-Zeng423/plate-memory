"""Optional after-meal observations; no diagnosis or automatic preference update."""
from copy import deepcopy
from datetime import date
from ..domain.checkin import empty_checkin,validate_checkin,OPTIONS,FIELDS
from ..food_adapter import parse_date,ValidationError
from .prompts import ask,choose,FlowCancelled,BackRequested,CancelRequested
from .navigation import Field,form_fields,discard_draft,short_text


def show_checkin(screen,item,index=None):
    screen.paragraph((str(index)+screen.t('. ') if index else '')+item['date']+screen.t(' · ')+item['dish'])
    for key in ('route','taste','fullness','comfort','note'):
        if item[key] is not None:screen.paragraph(screen.t(key)+screen.t(': ')+(item[key] if key=='note' else screen.t(item[key])))


def checkin_form(screen,existing=None,selected=None,draft=None):
    draft = {} if draft is None else draft
    if not draft:
        draft.update(deepcopy(existing) if existing else empty_checkin())
        if not draft['dish'] and selected:
            draft['dish'] = selected['name']
        draft['_feelings'] = 'yes' if existing and any(existing[k] for k in ('route',*OPTIONS)) else 'no'
    def observed(raw):
        parsed = parse_date(raw)
        if parsed > date.today():
            raise ValidationError('Record an actual meal today or earlier.')
        return parsed.isoformat()
    def allowed(options):
        def convert(raw):
            aliases={'是':'yes','否':'no','1':'yes','2':'no','外卖':'delivery','食堂':'cafeteria','喜欢':'enjoyed','一般':'okay','不喜欢':'disappointing','还饿':'still hungry','刚好':'satisfied','太饱':'too full','舒服':'comfortable','不确定':'unsure','不舒服':'uncomfortable'}
            raw=aliases.get(raw,raw)
            if raw not in options:
                raise ValidationError('Choose one of the listed words, or /skip for an optional field.')
            return raw
        return convert
    feelings = lambda d: d['_feelings'] == 'yes'
    fields = [Field('dish',screen.t('What did you eat?'),short_text(160)),
              Field('date',screen.t('Date YYYY-MM-DD'),observed),
              Field('_feelings',screen.t('Add how it felt? yes / no'),allowed(('yes','no'))),
              Field('route',screen.t('delivery / cafeteria (optional)'),allowed(('delivery','cafeteria')),True,feelings)]
    fields += [Field(k,screen.t(k)+screen.t(' — ')+screen.t(' / '.join(options))+screen.t(' (optional)'),allowed(options),True,feelings)
               for k,options in OPTIONS.items()]
    fields += [Field('note',screen.t('Anything to remember? (Enter to skip)'),short_text(1000),True)]
    screen.paragraph(screen.t('Only save a meal you actually ate. Feelings are optional. /skip clears an optional answer.'))
    start = 0
    while True:
        if not form_fields(screen,fields,draft,start,back_target='your meal journal'):
            return None
        item = {k:draft[k] for k in FIELDS}
        if not feelings(draft):
            for k in ('route',*OPTIONS):
                item[k] = None
        validate_checkin(item)
        show_checkin(screen,item)
        screen.say(screen.t('/back: edit last answer · /home: table, keep draft · /cancel: discard draft'))
        try:
            if choose(screen,screen.t('Save as an actual meal? yes / no'),{'yes':True,'no':False},'no'):
                return item
            return None
        except BackRequested:
            start = len(fields)-1
        except CancelRequested:
            if discard_draft(screen,draft):
                return None
            start = len(fields)


def checkin_flow(screen,store,selected=None,drafts=None):
    drafts = {} if drafts is None else drafts
    while True:
        screen.say(screen.t('\nHow was your meal?'), 'title')
        screen.paragraph(screen.t('A little space to remember how eating felt. You can skip this completely.'))
        screen.say(screen.t('1 Log · 2 History · 3 Edit · 4 Delete · 0 Back to table · h Home'))
        action = None
        try:
            action=choose(screen,screen.t('Choose'),{'1':'log','2':'history','3':'edit','4':'delete','log':'log','history':'history','edit':'edit','delete':'delete'})
            if action=='log':
                draft = drafts.setdefault('new',{})
                item=checkin_form(screen,selected=selected,draft=draft)
                if item:
                    store.save(item);draft.clear()
                    screen.say(screen.t('Saved just to your meal journal.'), 'ok')
                continue
            rows=sorted(store.list(),key=lambda row:(row[0]['date'],row[0]['id']),reverse=True)
            if not rows:screen.say(screen.t('No meals recorded yet. Nothing to catch up on.'));continue
            screen.say(str(len(rows))+screen.t(' meals you chose to record. This may not be every meal.'))
            for index,(item,_) in enumerate(rows[:10],1):show_checkin(screen,item,index)
            if action=='history':continue
            index=choose(screen,screen.t('Record number / 0 back to journal / h home'),{str(i):i-1 for i in range(1,min(len(rows),10)+1)})
            item,revision=rows[index]
            if action=='edit':
                draft = drafts.setdefault(item['id'],{})
                # Keep the revision with the draft, so resumed edits cannot overwrite newer data.
                if draft and draft.get('_revision') != revision:
                    screen.say(screen.t('This record changed while you were editing. The old draft cannot overwrite it.'), 'warn')
                    if not discard_draft(screen,draft):
                        continue
                if not draft:
                    draft.update(deepcopy(item));draft['_feelings']='yes' if any(item[k] for k in ('route',*OPTIONS)) else 'no'
                    draft['_revision']=revision
                changed=checkin_form(screen,item,draft=draft)
                if changed:
                    store.save(changed,revision);draft.clear()
            elif choose(screen,screen.t('Delete this local journal record? yes / no'),{'yes':True,'no':False},'no'):
                store.delete(item['id'],revision)
                screen.say(screen.t('Removed from this journal. Existing exports or backups may still contain it.'))
        except FlowCancelled:
            if action is None:return
            continue
