"""A quiet corner for friend-authored messages with preview-before-import."""
from pathlib import Path
from ..services.friend_pack import load_friend_pack, save_friend_pack
from .prompts import ask, FlowCancelled


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


def lunchbox_flow(screen,current,save,synthetic=False):
    while True:
        if current:
            preview_pack(screen,current)
        else:
            screen.paragraph('Your lunchbox is waiting for a note from a friend. Import a local text-only JSON pack, or come back later.')
        try:
            action=ask(screen,'open file / write / export / back')
            if action == 'write':
                pack = {'schema_version':1, 'sender':ask(screen,'Your name or nickname'), 'recipient':ask(screen,'Your friend’s name or nickname'), 'messages':[ask(screen,'A little message for your friend')], 'shared_dishes':[]}
                dish = ask(screen,'A shared dish? (Enter to skip)',optional=True)
                if dish:
                    pack['shared_dishes'].append({'name':dish,'note':ask(screen,'What do you remember about it?')})
                preview_pack(screen,pack)
                if ask(screen,'Keep these words? yes/no','no')=='yes':
                    save(pack); current=pack
                continue
            if action == 'export':
                if not current:
                    screen.say('Write a note first, then export it.'); continue
                preview_pack(screen,current)
                if synthetic:
                    screen.say('Synthetic preview only. No file exported.'); continue
                path=Path(ask(screen,'Save lunchbox JSON path')).expanduser()
                if path.exists() and ask(screen,'Replace this existing file? yes/no','no')!='yes':continue
                if ask(screen,'Export exactly these words? yes/no','no')=='yes':
                    save_friend_pack(path,current);screen.say('Saved. Send this file yourself; your friend can open it in lunchbox.')
                continue
            if action not in ('import','open','open file'):
                screen.say('Choose open file, write, export, or /back.'); continue
            if synthetic:
                screen.say('Demo keeps its synthetic lunchbox in memory. Import real words after restarting without --demo.'); continue
            pack=load_friend_pack(Path(ask(screen,'Local friend-pack JSON path')).expanduser())
            preview_pack(screen,pack)
            if ask(screen,'Keep this lunchbox locally? yes/no','no')=='yes':
                save(pack);current=pack
                screen.say('Lunchbox saved locally. No dietary note was created.', 'ok')
        except FlowCancelled:
            return
