"""Retained postcard drafts with explicit local formats and share boundaries."""
from datetime import date
from pathlib import Path
from uuid import uuid4
from ..domain.share import APP_URL,validate_share
from ..services.share_render import render_text
from ..services.export import export_file,export_bundle,FORMATS,RendererUnavailable
from .prompts import ask,choose,BackRequested,CancelRequested
from .navigation import form_fields,discard_draft,short_text


def postcard_flow(screen,directory,selected=None,synthetic=False,draft=None):
    draft={} if draft is None else draft
    fields=[('sender','Your name or nickname',short_text(80)),
            ('recipient','Your friend’s name or nickname',short_text(80)),
            ('message','What would you like to say?',short_text(1000))]
    screen.say(screen.t('\nUntil our next meal'),'title')
    screen.paragraph(screen.t('A small note for your friend. Write it here, then send the file yourself whenever you feel like it.'))
    state='fields';start=0;stem='postcard-'+uuid4().hex[:12]
    def card():
        return validate_share({'schema_version':2,**{k:draft[k] for k in ('sender','recipient','message')},
            'dish':draft.get('dish'),'theme':draft.get('theme','table'),'language':screen.language,
            'created_on':date.today().isoformat(),'app_url':APP_URL if draft.get('link') else None})
    def preview():
        screen.say(screen.t('\nPostcard / Preview'),'title')
        screen.divider()
        screen.paragraph(render_text(card()))
        screen.divider()
        screen.say(screen.t('Only the names, message and optional dish shown above will be shared.'))
    while True:
        try:
            if state=='fields':
                if not form_fields(screen,fields,draft,start):return
                state='dish' if selected else 'preview'
            if state=='dish':
                include=choose(screen,screen.t('Include this food idea: ')+selected['name']+screen.t('? yes / no'),
                               {'yes':True,'no':False},'yes' if draft.get('dish') else 'no')
                draft['dish']=selected['name'] if include else None;state='preview'
            if state=='preview':
                preview()
                screen.say(screen.t('1 Export / 2 Edit note / 3 Style / 0 Back / h Home'))
                result=choose(screen,screen.t('Export this note locally? yes / no'),
                              {'1':'export','2':'edit','3':'theme','yes':'export','no':'stop','theme':'theme','edit':'edit'},'no')
                if result=='stop':return
                if result=='edit':state='fields';start=len(fields)-1;continue
                if result=='theme':state='theme';continue
                if synthetic:
                    screen.say(screen.t('Demo records stay in memory. This note will be exported only to the path you choose.'))
                state='format'
            if state=='theme':
                draft['theme']=choose(screen,screen.t('1 Cafeteria table / 2 Takeout receipt / 3 Next lunch invitation / 0 Preview'),
                                      {'1':'table','2':'receipt','3':'invitation','table':'table','receipt':'receipt','invitation':'invitation'},draft.get('theme','table'))
                state='preview';continue
            if state=='format':
                screen.say(screen.t('1 Share folder: HTML + text + lunchbox JSON / 2 HTML / 3 Text / 4 Lunchbox JSON / 5 PNG'))
                old_format=draft.get('format')
                draft['format']=choose(screen,screen.t('Choose format / 0 Preview / h Home'),
                    {'1':'bundle','2':'html','3':'text','4':'json','5':'png','bundle':'bundle','html':'html','text':'text','json':'json','png':'png'},draft.get('format','bundle'))
                if draft['format']!=old_format:draft.pop('path',None)
                state='link'
            if state=='link':
                screen.say(screen.t('The link opens the public project quick-start, not a web ordering app.'))
                draft['link']=choose(screen,screen.t('Include the link to try Plate Memory? yes / no'),{'yes':True,'no':False},'yes' if draft.get('link') else 'no')
                preview();state='destination'
            if state=='destination':
                format=draft['format'];default=directory/stem
                if format!='bundle':default=default.with_suffix(FORMATS[format])
                screen.say(screen.t('Postcard / Save file — /back: preview · /home: table, keep draft'))
                path=Path(ask(screen,screen.t('Save path'),draft.get('path',default))).expanduser()
                draft['path']=str(path)
                if format=='bundle' and path.exists():
                    screen.say(screen.t('This folder already exists. Choose a new folder to keep its files intact.'),'warn');continue
                state='replace' if path.exists() else 'write';replace=False
            if state=='replace':
                screen.say(screen.t('/back: choose another path · /home: table, keep draft'))
                if not choose(screen,screen.t('Replace the existing file? yes / no'),{'yes':True,'no':False},'no'):
                    screen.say(screen.t('Existing file kept. Your note draft is still available this session.'));return
                replace=True;state='write'
            if state=='write':
                try:
                    files=export_bundle(path,card()) if format=='bundle' else export_file(path,card(),format,replace)
                except RendererUnavailable as exc:
                    screen.say(screen.t(str(exc)),'warn');state='format';continue
                except (OSError,ValueError) as exc:
                    screen.say(screen.t('Could not save: ')+screen.t(str(exc)),'warn');state='destination';continue
                screen.say(screen.t('Saved locally. Nothing was sent.'),'ok')
                for file in files:screen.paragraph(str(file))
                if format=='bundle':screen.say(screen.t('Open postcard.html to view; import lunchbox.json in Lunchbox.'))
                draft.clear();return
        except BackRequested:
            if state in ('dish','preview'):state='fields';start=len(fields)-1
            elif state in ('theme','format','destination'):state='preview'
            elif state=='link':state='format'
            elif state=='replace':state='destination'
        except CancelRequested:
            if discard_draft(screen,draft):return
