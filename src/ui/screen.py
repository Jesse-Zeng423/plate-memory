"""Terminal output, safe text and basic prompts."""
import os
import re
import shutil
import sys
import textwrap
import unicodedata


def safe_text(value):
    # Untrusted menu/model/profile text must not issue terminal control commands.
    return re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', '', str(value))


class Screen:
    def __init__(self, color=True, decor=True):
        self.decor = decor
        self.color = color and sys.stdout.isatty() and 'NO_COLOR' not in os.environ

    def say(self, text='', tone=None):
        colors = {'title': '1;33', 'accent': '35', 'warn': '33', 'error': '31', 'ok': '32'}
        clean = safe_text(text)
        width = max(12, min(88, shutil.get_terminal_size((88, 24)).columns - 2))
        rendered = []
        for line in clean.split('\n'):
            for part in (textwrap.wrap(line, width, replace_whitespace=False) or ['']):
                chunk = ''; cells = 0
                for char in part:
                    size = 0 if unicodedata.combining(char) else (2 if unicodedata.east_asian_width(char) in ('W', 'F') else 1)
                    if cells + size > width:
                        rendered.append(chunk); chunk = ''; cells = 0
                    chunk += char; cells += size
                rendered.append(chunk)
        clean = '\n'.join(rendered)
        if self.color and tone in colors:
            clean = '\033[' + colors[tone] + 'm' + clean + '\033[0m'
        print(clean)

    def paragraph(self, text):
        width = max(12, min(88, shutil.get_terminal_size((88, 24)).columns - 2))
        self.say(textwrap.fill(safe_text(text), width))

    def ask(self, label, default=None):
        suffix = f' [{safe_text(default)}]' if default is not None else ''
        result = input(safe_text(label) + suffix + ': ').strip()
        return result or (str(default) if default is not None else '')
