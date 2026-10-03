"""A quiet corner for friend-authored messages with preview-before-import."""
from pathlib import Path
from ..services.friend_pack import load_friend_pack, save_friend_pack
from .prompts import ask, choose, FlowCancelled, BackRequested, CancelRequested
from .navigation import Field, form_fields, discard_draft, short_text
from ..domain.friend_pack import validate_friend_pack


def preview_pack(screen,pack):
    screen.say('\nA corner of the cafeteria', 'title')
    if screen.decor:
        screen.say('   +----------------------+\n   |  a little lunchbox   |\n   +----------------------+', 'accent')
    screen.paragraph('From ' + pack['sender'] + ' to ' + pack['recipient'] + ' (sender label supplied in the file)')
    for message in pack['messages']:
        screen.paragraph(message)
    for dish in pack['shared_dishes']:
        screen.paragraph(dish['name'] + ' — ' + dish['note'])
    screen.paragraph('These words are a gift. Shared dishes are memories; dietary notes are managed separately.')


def write_lunchbox(screen,draft):
    fields = [Field('sender','Your name or nickname',short_text(80)),
              Field('recipient','Your friend’s name or nickname',short_text(80)),
              Field('message','A little message for your friend',short_text(1000)),
              Field('dish','A shared dish? (Enter to skip)',short_text(160),True),
              Field('note','What do you remember about it?',short_text(600),active=lambda d:bool(d.get('dish')))]
    start = 0
    while True:
        if not form_fields(screen,fields,draft,start,back_target='your lunchbox'):
            return None
        pack = {'schema_version':1,'sender':draft['sender'],'recipient':draft['recipient'],
                'messages':[draft['message']], 'shared_dishes':[]}
        if draft.get('dish'):
            pack['shared_dishes'] = [{'name':draft['dish'],'note':draft['note']}]
        validate_friend_pack(pack)
        preview_pack(screen,pack)
        screen.say('/back: edit last answer · /home: table, keep draft · /cancel: discard draft')
        try:
            if choose(screen,'Keep these words? yes/no',{'yes':True,'no':False},'no'):
                return pack
            return None
        except BackRequested:
            start = len(fields)-1
        except CancelRequested:
            if discard_draft(screen,draft):return None
            start = len(fields)


def export_lunchbox(screen,current,synthetic):
    preview_pack(screen,current)
    if synthetic:
        screen.say('Synthetic preview only. No file exported.');return
    state = 'path'
    path = None
    while True:
        try:
            if state == 'path':
                screen.say('/back: lunchbox · /home: table')
                path=Path(ask(screen,'Save lunchbox JSON path',path)).expanduser()
                state='replace' if path.exists() else 'confirm'
            if state == 'replace':
                screen.say('/back: choose another path · /home: table')
                if not choose(screen,'Replace this existing file? yes/no',{'yes':True,'no':False},'no'):return
                state='confirm'
            if state == 'confirm':
                preview_pack(screen,current)
                screen.say('/back: choose another path · /home: table')
                if not choose(screen,'Export exactly these words? yes/no',{'yes':True,'no':False},'no'):return
                try:
                    save_friend_pack(path,current)
                except OSError as exc:
                    screen.say('Could not save: '+str(exc),'warn');state='path';continue
                screen.say('Saved to '+str(path)+'. Send this file yourself; your friend can open it in lunchbox.')
                return
        except BackRequested:
            if state == 'path':return
            state='path'
        except CancelRequested:return


def import_lunchbox(screen,save):
    path = None
    while True:
        screen.say('/back: lunchbox · /home: table')
        try:
            path=Path(ask(screen,'Local friend-pack JSON path',path)).expanduser()
        except FlowCancelled:return None
        try:
            pack=load_friend_pack(path)
        except (OSError,ValueError) as exc:
            screen.say('Could not open: '+str(exc),'warn');continue
        preview_pack(screen,pack)
        screen.say('/back: choose another file · /home: table')
        try:
            if choose(screen,'Keep this lunchbox locally? yes/no',{'yes':True,'no':False},'no'):
                save(pack)
                screen.say('Lunchbox saved locally. No dietary note was created.', 'ok')
                return pack
            return None
        except BackRequested:continue
        except CancelRequested:return None


def lunchbox_flow(screen,current,save,synthetic=False,draft=None):
    draft = {} if draft is None else draft
    while True:
        if current:
            preview_pack(screen,current)
        else:
            screen.paragraph('Your lunchbox is waiting for a note from a friend. Open a local JSON pack, or write one here.')
        screen.say('1 Open file · 2 Write · 3 Export · 0 Back to table')
        try:
            action=choose(screen,'Choose',{'1':'import','2':'write','3':'export','0':'back',
                          'import':'import','open':'import','open file':'import','write':'write','export':'export'})
            if action == 'back':return
            if action == 'write':
                pack=write_lunchbox(screen,draft)
                if pack:
                    save(pack);current=pack;draft.clear()
            elif action == 'export':
                if not current:
                    screen.say('Write a note first, then export it.');continue
                export_lunchbox(screen,current,synthetic)
            elif synthetic:
                screen.say('Demo keeps its synthetic lunchbox in memory. Import real words after restarting without --demo.')
            else:
                imported=import_lunchbox(screen,save)
                if imported:current=imported
        except FlowCancelled:return
