"""Editorial discovery directions; never dietary advice or inferred ingredients."""
import re
from ..catalog.normalize import normalized,contains,NEGATION

# Categories are published FNDDS categories; grouping and prompts are editorial.
FAMILIES=(
 ('warm',('warm','hot','something warm','热的','热乎','暖和'),('Soups, broth-based','Ramen and Asian broth-based soups','Soups, cream-based')),
 ('noodles',('noodle','noodles','pasta','面条','面食'),('Pasta, noodles, cooked grains','Pasta mixed dishes, excludes macaroni and cheese','Ramen and Asian broth-based soups')),
 ('rice',('rice','饭','米饭'),('Rice mixed dishes','Fried rice and lo/chow mein','Rice')),
 ('sandwiches',('sandwich','sandwiches','三明治'),('Cheese sandwiches','Chicken fillet sandwiches','Egg/breakfast sandwiches','Vegetable sandwiches/burgers')),
 ('pizza',('pizza','披萨','比萨'),('Pizza',)),
 ('soup',('soup','soups','汤'),('Soups, broth-based','Ramen and Asian broth-based soups','Soups, cream-based')),
 ('salads',('salad','salads','沙拉'),('Lettuce and lettuce salads','Coleslaw, non-lettuce salads')),
 ('breakfast',('breakfast','早餐'),('Egg/breakfast sandwiches','Oatmeal','Bagels and English muffins','Pancakes, waffles, French toast')),
)


def direction(query):
    query=normalized(query)
    # Refuse to relax exclusions, price/health requirements into casual ideas.
    if re.search(NEGATION,query) or re.search(r'\d|allerg|healthy|safe|gluten|vegan|vegetarian|cheap|budget|便宜|健康|安全|素食',query):return None
    hits=[family for family in FAMILIES if any(contains(query,term) for term in family[1])]
    if len(hits)!=1:return None
    return hits[0]


def related(catalog,item,limit=3,offset=0):
    category=item.get('category')
    family=next((f for f in FAMILIES if category in f[2]),None) or direction(item['name'])
    if family is None:return []
    return family_items(catalog,family,limit=limit,offset=offset,exclude=item['id'])


def family_items(catalog,family,offset=0,limit=3,exclude=None):
    # Interleave categories to avoid three near-identical variants on page one.
    groups=[catalog.search('',limit=100,category=category) for category in family[2]]
    rows=[]
    for index in range(max((len(g) for g in groups),default=0)):
        for group in groups:
            if index<len(group) and group[index]['id']!=exclude:
                rows.append(dict(group[index],discovery_direction=family[0]))
    return rows[offset:offset+limit]


def menu_check(item):
    family=next((f for f in FAMILIES if item.get('category') in f[2]),None) or direction(item['name'])
    key=family[0] if family else None
    return {
        'warm':'Check the bowl size, broth and toppings.',
        'soup':'Check the bowl size, broth and toppings.',
        'noodles':'Check the portion, sauce or broth, and toppings.',
        'rice':'Check what comes with the rice and the portion size.',
        'sandwiches':'Check the filling, bread and whether a side is included.',
        'pizza':'Check slice or whole-pizza size and toppings.',
        'salads':'Check the dressing, toppings and portion size.',
        'breakfast':'Check the serving size and what is included.',
    }.get(key,'Check the portion, ingredients and what is included.')


def food_icon(item):
    family=next((f for f in FAMILIES if item.get('category') in f[2]),None) or direction(item['name'])
    return {'warm':'🥣','soup':'🥣','noodles':'🍜','rice':'🍚','sandwiches':'🥪',
            'pizza':'🍕','salads':'🥗','breakfast':'🍳'}.get(family[0] if family else None,'🍽️')
