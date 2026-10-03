"""Terminal output, safe text and basic prompts."""
import os
import re
import shutil
import sys
from .._vendor.wcwidth import wrap, wcswidth
from .i18n import translate


def safe_text(value):
    # Untrusted menu/model/profile text must not issue terminal control commands.
    return re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', '', str(value))


class Screen:
    def __init__(self, color=True, decor=True, language="en"):
        self.language = language
        self.decor = decor
        self.color = color and sys.stdout.isatty() and 'NO_COLOR' not in os.environ

    def t(self,text):
        return translate(text,self.language)

    @property
    def columns(self):
        return max(12,min(88,shutil.get_terminal_size((88,24)).columns-2))

    def say(self, text='', tone=None):
        colors = {'title':'1;33','accent':'36','warn':'33','error':'31','ok':'32'}
        clean = safe_text(text)
        if self.decor and tone=='title':
            icons={'How are you doing today?':'🍽️','Takeout ideas':'🛵',
                   'A walk and something to eat':'🚶','A corner of the cafeteria':'🎒',
                   'How was your meal?':'📝','Until our next meal':'💌',
                   'Postcard / Preview':'💌','Your usuals':'📍','Browse a food family':'🍱'}
            icons.update({self.t(k):v for k,v in list(icons.items())})
            title=clean.strip()
            if title in icons:clean=('\n' if clean.startswith('\n') else '')+icons[title]+'  '+title
        rendered=[]
        for line in clean.split('\n'):
            rendered.extend(wrap(line,self.columns,replace_whitespace=False) or [''])
        clean='\n'.join(rendered)
        if self.color and tone in colors:
            clean='\033['+colors[tone]+'m'+clean+'\033[0m'
        print(clean)

    def paragraph(self, text):
        self.say(text)

    def ask(self, label, default=None):
        suffix=f' [{safe_text(default)}]' if default is not None else ''
        self.say(safe_text(label)+suffix)
        result=input('› ' if self.decor else '> ').strip()
        return result or (str(default) if default is not None else '')
