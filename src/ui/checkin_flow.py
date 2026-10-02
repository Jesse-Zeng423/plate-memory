"""Optional after-meal observations; no diagnosis or automatic preference update."""
from copy import deepcopy
from ..domain.checkin import empty_checkin,validate_checkin,OPTIONS
from ..food_adapter import parse_date
from .prompts import ask,choose,FlowCancelled


def show_checkin(screen,item,index=None):
    screen.paragraph((str(index)+'. ' if index else '')+item['date']+' · '+item['dish'])
    for key in ('route','taste','fullness','comfort','note'):
        if item[key] is not None:screen.paragraph(key+': '+item[key])


def checkin_form(screen,existing=None,selected=None):
    item=deepcopy(existing) if existing else empty_checkin()
    screen.paragraph('Only save a meal you actually ate. Every feeling is optional; /skip leaves it blank, /back leaves without saving.')
    item['dish']=ask(screen,'What did you eat?',item['dish'] or (selected['name'] if selected else None))
    item['date']=ask(screen,'Date YYYY-MM-DD',item['date'],convert=lambda raw:parse_date(raw).isoformat())
    raw=ask(screen,'delivery / cafeteria (optional)',item['route'],optional=True)
    item['route']=raw
    for key,options in OPTIONS.items():
        item[key]=ask(screen,key+' — '+' / '.join(options)+' (optional)',item[key],optional=True)
    item['note']=ask(screen,'Anything else? (optional)',item['note'],optional=True)
    validate_checkin(item)
    show_checkin(screen,item)
    if choose(screen,'Save as an actual meal? yes / no',{'yes':True,'no':False},'no'):
        return item
    return None


def checkin_flow(screen,store,selected=None):
    while True:
        screen.say('\nHow was your meal?', 'title')
        screen.paragraph('A little space to remember how eating felt. You can skip this completely.')
        try:
            action=choose(screen,'log / history / edit / delete / back',{'log':'log','history':'history','edit':'edit','delete':'delete'})
            if action=='log':
                item=checkin_form(screen,selected=selected)
                if item:store.save(item);screen.say('Saved just to your meal journal.', 'ok')
                continue
            rows=sorted(store.list(),key=lambda row:(row[0]['date'],row[0]['id']),reverse=True)
            if not rows:screen.say('No meals recorded yet. Nothing to catch up on.');continue
            screen.say(str(len(rows))+' meals you chose to record. This may not be every meal.')
            for index,(item,_) in enumerate(rows[:10],1):show_checkin(screen,item,index)
            if action=='history':continue
            index=choose(screen,'Record number / back',{str(i):i-1 for i in range(1,min(len(rows),10)+1)})
            item,revision=rows[index]
            if action=='edit':
                changed=checkin_form(screen,item)
                if changed:store.save(changed,revision)
            elif choose(screen,'Delete this local journal record? yes / no',{'yes':True,'no':False},'no'):
                store.delete(item['id'],revision)
                screen.say('Removed from this journal. Existing exports or backups may still contain it.')
        except FlowCancelled:return
