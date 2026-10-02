"""Preview chosen fields, then explicit local export. Nothing is sent."""
from pathlib import Path
from uuid import uuid4
from ..services.postcard import render_postcard,export_postcard
from .prompts import ask,choose,FlowCancelled


def postcard_flow(screen,directory,selected=None,synthetic=False):
    try:
        screen.say('\nUntil our next meal', 'title')
        screen.paragraph('A small note for your friend. Write it here, then send the file yourself whenever you feel like it.')
        card={'schema_version':1,'sender':ask(screen,'Your name or nickname'),'recipient':ask(screen,'Your friend’s name or nickname'),'message':ask(screen,'What would you like to say?'),'dish':None}
        if selected and choose(screen,'Include this food idea: '+selected['name']+'? yes / no',{'yes':True,'no':False},'no'):
            card['dish']=selected['name']
        screen.say('\nPreview', 'title');screen.paragraph(render_postcard(card))
        screen.say('This file contains only the names, message and optional dish shown above.')
        if not choose(screen,'Export this note locally? yes / no',{'yes':True,'no':False},'no'):return
        if synthetic:
            screen.say('Synthetic preview only. No file exported.');return
        default=directory/('postcard-'+uuid4().hex[:12]+'.txt')
        path=Path(ask(screen,'Save path',default)).expanduser()
        if path.exists() and not choose(screen,'Replace the existing file? yes / no',{'yes':True,'no':False},'no'):return
        export_postcard(path,card)
        screen.paragraph('Saved to '+str(path)+'. Nothing was sent. You can share this file in your own chat.')
    except FlowCancelled:return
