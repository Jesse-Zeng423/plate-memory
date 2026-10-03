"""Conservative text matching, separate from ingredient/preference interpretation."""
from functools import lru_cache
import re
import unicodedata

NEGATION=r'\b(no|not|without|avoid|free|under|less)\b|不要|不吃|不含|过敏|過敏|以内|以內'


def normalized(value):
    return unicodedata.normalize('NFKC',value).casefold().strip()


@lru_cache(maxsize=16384)
def words(value):
    parts=re.findall(r'[\w]+',normalized(value))
    # Only common English plurals; don't stem arbitrary food names.
    plurals={'burgers':'burger','sandwiches':'sandwich','eggs':'egg','noodles':'noodle','tacos':'taco','burritos':'burrito','dumplings':'dumpling','salads':'salad','soups':'soup'}
    return tuple(plurals.get(p,p) for p in parts)


def contains(term,query):
    terms=words(term)
    return all(any(q in t for t in terms) if any('\u3400'<=c<='\u9fff' for c in q) else q in terms for q in words(query))
