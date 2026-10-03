"""Explicit presentation translation; never translates input, model or stored text."""
import json
import re
from pathlib import Path

ZH=json.loads(Path(__file__).with_name('zh.json').read_text(encoding='utf-8'))


def translate(text,language):
    if language!='zh' or not isinstance(text,str):return text
    trimmed=text.strip()
    if trimmed not in ZH:
        match=re.fullmatch(r'Use up to (\d+) characters, without control characters\.',trimmed)
        if match:return '请用最多 '+match[1]+' 字，不要包含控制字符。'
        return text
    before=text[:len(text)-len(text.lstrip())]
    after=text[len(text.rstrip()):]
    return before+ZH[trimmed]+after
