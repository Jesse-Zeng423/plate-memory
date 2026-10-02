"""A text gift never authorizes dietary preferences or carries executable content."""
from ..food_adapter import ValidationError


def bounded(value, size):
    if not isinstance(value,str) or not value.strip() or len(value)>size:
        raise ValidationError('Friend-pack text is empty or too long.')
    return value


def validate_friend_pack(pack):
    if not isinstance(pack,dict) or set(pack)!={'schema_version','sender','recipient','messages','shared_dishes'} or type(pack['schema_version']) is not int or pack['schema_version']!=1:
        raise ValidationError('Unknown friend-pack fields or version.')
    for key in ('sender','recipient'):
        bounded(pack[key],80)
    if not isinstance(pack['messages'],list) or not 1<=len(pack['messages'])<=8:
        raise ValidationError('A lunchbox needs 1–8 messages.')
    for message in pack['messages']:
        bounded(message,1000)
    if not isinstance(pack['shared_dishes'],list) or len(pack['shared_dishes'])>12:
        raise ValidationError('Keep at most 12 shared dishes.')
    for dish in pack['shared_dishes']:
        if not isinstance(dish,dict) or set(dish)!={'name','note'}:
            raise ValidationError('Invalid shared dish.')
        bounded(dish['name'],160); bounded(dish['note'],600)
    return pack
