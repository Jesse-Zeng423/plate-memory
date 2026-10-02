"""A minimal deliberate sharing boundary; never accepts a profile or journal."""
from ..food_adapter import ValidationError
from ..storage.private_file import write_private

FIELDS={'schema_version','sender','recipient','message','dish'}


def validate_postcard(value):
    if not isinstance(value,dict) or set(value)!=FIELDS or type(value['schema_version']) is not int or value['schema_version']!=1:
        raise ValidationError('Invalid postcard fields.')
    for key,maximum in [('sender',80),('recipient',80),('message',1000),('dish',160)]:
        text=value[key]
        if key=='dish' and text is None:continue
        if not isinstance(text,str) or not text.strip() or len(text)>maximum or any(ord(c)<32 or 127<=ord(c)<=159 for c in text):
            raise ValidationError('Invalid postcard '+key+'.')
    return value


def render_postcard(value):
    validate_postcard(value)
    lines=['Until our next meal', '', 'From '+value['sender']+' to '+value['recipient'], '', value['message']]
    if value['dish']:lines+=['','A dish for next time: '+value['dish']]
    return '\n'.join(lines)+'\n'


def export_postcard(path,value):
    write_private(path,render_postcard(value))
