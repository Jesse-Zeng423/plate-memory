"""Terminal output, safe text and basic prompts."""
import os
import re
import shutil
import sys
import textwrap


def safe_text(value):
    # Untrusted menu/model/profile text must not issue terminal control commands.
    return re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', '', str(value))


class Screen:
    def __init__(self, color=True):
        self.color = color and sys.stdout.isatty() and 'NO_COLOR' not in os.environ

    def say(self, text='', tone=None):
        colors = {'title': '1;36', 'warn': '33', 'error': '31', 'ok': '32'}
        clean = safe_text(text)
        if self.color and tone in colors:
            clean = '\033[' + colors[tone] + 'm' + clean + '\033[0m'
        print(clean)

    def paragraph(self, text):
        width = max(24, min(88, shutil.get_terminal_size((88, 24)).columns - 2))
        self.say(textwrap.fill(safe_text(text), width))

    def ask(self, label, default=None):
        suffix = f' [{safe_text(default)}]' if default is not None else ''
        result = input(safe_text(label) + suffix + ': ').strip()
        return result or (str(default) if default is not None else '')
