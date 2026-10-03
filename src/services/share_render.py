"""Offline escaped HTML, text and importable lunchbox renderings."""
from html import escape
import base64
import json
from string import Template
from ..paths import ROOT
from ..domain.share import validate_share
from ..domain.friend_pack import validate_friend_pack


def labels(card):
    if card['language']=='zh':
        return {'table':'两份饭，一张桌','title':'下次，还坐一起。','from':'来自','to':'给','dish':'下次想一起吃：',
                'footer':'大学不在一起，饭桌上还是有你的位置。',
                'app':'给兄弟留个座 · Plate Memory','hint':'打开项目里的启动说明，在自己电脑上用。',
                'idea':'下次一起吃的想法；不是已吃过的记录。'}
    return {'table':'two trays, one table','title':'Same table, soon.','from':'From','to':'To','dish':'For our next meal:',
            'footer':'Different campuses. Still a place for you at the table.',
            'app':'Save your bro a seat · Plate Memory','hint':'Open the project quick-start. Runs on your own computer.',
            'idea':'A food idea for next time; not a record of a meal eaten.'}


def render_text(card):
    validate_share(card);t=labels(card)
    lines=[t['title'],card['created_on'],'',t['from']+' '+card['sender']+' / '+t['to']+' '+card['recipient'],'',card['message']]
    if card['dish']:lines+=['',t['dish']+' '+card['dish']]
    if card['app_url']:lines+=['',t['app'],card['app_url'],t['hint']]
    return '\n'.join(lines)+'\n'


def render_html(card):
    validate_share(card);t=labels(card)
    app=''
    if card['app_url']:
        app='<a class="app" href="'+escape(card['app_url'],quote=True)+'">'+escape(t['app'])+'</a><p class="url">'+escape(card['app_url'])+'</p>'
    dish='<p class="dish">'+escape(t['dish'])+' '+escape(card['dish'])+'</p>' if card['dish'] else ''
    illustration='data:image/png;base64,'+base64.b64encode((ROOT/'assets/postcards/friends-crayon.png').read_bytes()).decode('ascii')
    template=Template((ROOT/'assets/postcards/card.html').read_text(encoding='utf-8'))
    return template.substitute(language=card['language'],theme=card['theme'],title=escape(t['title']),
        date=card['created_on'],sender=escape(card['sender']),recipient=escape(card['recipient']),
        from_label=t['from'],to_label=t['to'],message=escape(card['message']),dish=dish,
        illustration=illustration,illustration_label='两个兄弟坐在一起吃饭的蜡笔画' if card['language']=='zh' else 'Crayon drawing of two friends sharing a meal',app=app)


def render_friend_pack(card):
    validate_share(card);t=labels(card)
    messages=[card['message']]
    if card['app_url']:messages.append(t['app']+'\n'+card['app_url'])
    pack={'schema_version':1,'sender':card['sender'],'recipient':card['recipient'],
          'messages':messages,'shared_dishes':[]}
    if card['dish']:pack['shared_dishes']=[{'name':card['dish'],'note':t['idea']}]
    return json.dumps(validate_friend_pack(pack),ensure_ascii=False,indent=2)+'\n'
