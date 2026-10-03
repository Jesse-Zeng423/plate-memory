"""Explicit sharing fields; profiles and journals cannot cross this boundary."""
from datetime import date
from ..food_adapter import ValidationError,parse_date
from ..services.postcard import validate_postcard

APP_URL='https://github.com/Jesse-Zeng423/plate-memory#try-it-in-one-minute--no-installation-dependencies'
THEMES=('table','receipt','invitation')
FIELDS={'schema_version','sender','recipient','message','dish','theme','language','created_on','app_url'}


def validate_share(card):
    if not isinstance(card,dict) or set(card)!=FIELDS or type(card['schema_version']) is not int or card['schema_version']!=2:
        raise ValidationError('Invalid share fields.')
    validate_postcard({k:card[k] for k in ('sender','recipient','message','dish')}|{'schema_version':1})
    if card['theme'] not in THEMES or card['language'] not in ('en','zh'):
        raise ValidationError('Invalid share theme or language.')
    parse_date(card['created_on'])
    if card['app_url'] not in (None,APP_URL):raise ValidationError('Only the public project quick-start link may be shared.')
    return card


def upgrade_postcard(card,language='en'):
    """Read v1 without changing its file or inventing recipient preferences."""
    if isinstance(card,dict) and card.get('schema_version')==2:return validate_share(dict(card))
    validate_postcard(card)
    return validate_share(dict(card,schema_version=2,theme='table',language=language,
                               created_on=date.today().isoformat(),app_url=None))
