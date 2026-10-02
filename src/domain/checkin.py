"""An explicit observation, separate from plans and preference memories."""
from datetime import date
from uuid import uuid4
from ..food_adapter import ValidationError,parse_date

MAX_CHECKINS=1000
FIELDS={'id','date','dish','route','taste','fullness','comfort','note'}
OPTIONS={'taste':('enjoyed','okay','disappointing'),'fullness':('still hungry','satisfied','too full'),'comfort':('comfortable','unsure','uncomfortable')}


def validate_checkin(value):
    if not isinstance(value,dict) or set(value)!=FIELDS:
        raise ValidationError('Unknown meal journal fields.')
    for key,maximum in [('id',60),('dish',160),('note',1000)]:
        text=value[key]
        if key=='note' and text is None:continue
        if not isinstance(text,str) or not text.strip() or len(text)>maximum or any(ord(c)<32 or 127<=ord(c)<=159 for c in text):
            raise ValidationError('Invalid journal '+key+'.')
    if parse_date(value['date'])>date.today():
        raise ValidationError('Record an actual meal today or earlier.')
    if value['route'] is not None and value['route'] not in ('delivery','cafeteria'):
        raise ValidationError('Invalid meal route.')
    for key,options in OPTIONS.items():
        if value[key] is not None and value[key] not in options:
            raise ValidationError('Invalid journal '+key+'.')
    return value


def empty_checkin():
    return {'id':'checkin-'+uuid4().hex,'date':date.today().isoformat(),'dish':'','route':None,'taste':None,'fullness':None,'comfort':None,'note':None}
