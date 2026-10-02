"""Saved places and dishes are historical references, not live availability."""
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from ..food_adapter import ValidationError, menu_lines, parse_date

FIELDS = {'id', 'name', 'venue', 'route', 'price_cents', 'price_date',
          'last_seen', 'walk_minutes', 'menu_text'}
MAX_MEALS = 300


def validate_meal(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValidationError('Saved meal fields do not match schema v1.')
    for field, maximum, required in (('id', 60, True), ('name', 160, True),
                                     ('venue', 160, False), ('menu_text', 4000, False)):
        text = value[field]
        if not isinstance(text, str) or len(text) > maximum or (required and not text.strip()):
            raise ValidationError(f'{field} must be text up to {maximum} characters' + (' and cannot be empty.' if required else '.'))
        if field != 'menu_text' and any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in text):
            raise ValidationError(f'{field} must be a single line without control characters.')
    if value['route'] not in ('delivery', 'cafeteria'):
        raise ValidationError('Choose delivery or cafeteria.')
    price = value['price_cents']
    if price is not None and (type(price) is not int or not 0 <= price <= 1000000):
        raise ValidationError('Price must be whole CAD cents between 0 and 1000000.')
    if (price is None) != (value['price_date'] is None):
        raise ValidationError('A known price needs the date it was recorded.')
    for key in ('price_date', 'last_seen'):
        if value[key] is not None and parse_date(value[key]) > date.today():
            raise ValidationError(f'{key} cannot be a future observation.')
    walk = value['walk_minutes']
    if walk is not None and (type(walk) is not int or not 1 <= walk <= 180 or value['route'] != 'cafeteria'):
        raise ValidationError('Walk time is 1–180 minutes and belongs to cafeteria choices only.')
    if value['menu_text'] and len(menu_lines(value['menu_text'])) > 16:
        raise ValidationError('Save at most 16 short menu lines.')
    return value


def empty_meal(route='delivery'):
    return {'id': 'meal-' + uuid4().hex, 'name': '', 'venue': '', 'route': route,
            'price_cents': None, 'price_date': None, 'last_seen': None,
            'walk_minutes': None, 'menu_text': ''}


def parse_price(text):
    try:
        price = Decimal(text)
        if not price.is_finite() or not 0 <= price <= 10000 or price * 100 != (price * 100).to_integral_value():
            raise ValueError
        return int(price * 100)
    except (InvalidOperation, ValueError, OverflowError):
        raise ValidationError('Enter a CAD amount with at most two decimal places, or skip.') from None
