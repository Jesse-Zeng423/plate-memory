"""Build-time only: bounded official FNDDS zip → new attributed name snapshot.

No user queries/profiles, model calls, API keys or runtime downloads. Download
separately from the URL printed in SOURCE, then supply --archive and new --output.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.catalog.schema import validate_pack
SOURCE='https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_survey_food_json_2024-10-31.zip'
# Explicit product-scope selection of published category labels; all variants in
# these categories are retained, never merged by ingredient/recipe inference.
CATEGORIES=['Meat mixed dishes','Pasta mixed dishes, excludes macaroni and cheese','Poultry mixed dishes','Rice mixed dishes','Pizza','Stir-fry and soy-based sauce mixtures','Deli and cured meat sandwiches','Burgers','Other Mexican mixed dishes','Burritos and tacos','Soups, broth-based','Egg/breakfast sandwiches','Fried rice and lo/chow mein','Egg rolls, dumplings, sushi','Bean, pea, legume dishes','Chicken fillet sandwiches','Meat and BBQ sandwiches','Seafood sandwiches','Pasta, noodles, cooked grains','Macaroni and cheese','Ramen and Asian broth-based soups','Cheese sandwiches','Vegetable sandwiches/burgers','Lettuce and lettuce salads','Soups, cream-based','Coleslaw, non-lettuce salads','Eggs and omelets','Rice']
# Editorial Chinese lookup hints apply ONLY to an explicit word in the published
# name, not to assumed ingredients. Original sourced labels are retained intact.
HINTS={'pizza':['披萨','披薩'],'sandwich':['三明治'],'egg':['鸡蛋','雞蛋'],'burger':['汉堡','漢堡'],'soup':['汤','湯'],'salad':['沙拉'],'noodle':['面条','麵條'],'rice':['米饭','米飯'],'dumpling':['饺子','餃子'],'curry':['咖喱','咖哩'],'pasta':['意面'],'burrito':['墨西哥卷饼'],'taco':['塔可'],'chicken':['鸡肉','雞肉'],'fish':['鱼','魚']}

EXTENDED_CATEGORIES=['Chicken, whole pieces','Chicken patties, nuggets and tenders','Fish','Shellfish','Seafood mixed dishes','Turkey, duck, other poultry','Beef, excludes ground','Pork','Soy and meat-alternative products','Beans, peas, legumes','Vegetable dishes','Other vegetables and combinations','Broccoli','Spinach','Carrots','Corn','String beans','Other dark green vegetables','Other red and orange vegetables','Fried vegetables','Mashed potatoes and white potato mixtures','White potatoes, baked or boiled','French fries and other fried white potatoes','Yeast breads','Rolls and buns','Bagels and English muffins','Biscuits, muffins, quick breads','Pancakes, waffles, French toast','Oatmeal','Grits and other cooked cereals','Yogurt, regular','Yogurt, Greek','Plant-based yogurt','Cheese','Apples','Bananas','Citrus fruits','Blueberries and other berries','Strawberries','Grapes','Melons','Peaches and nectarines','Pears','Pineapple','Mango and papaya','Other fruits and fruit salads','Dried fruits','Nuts and seeds','Ice cream and frozen dairy desserts','Coffee','Tea','Plant-based milk','Milk, whole','Milk, reduced fat','Milk, lowfat','Milk, nonfat']
RAW_FRUIT_CATEGORIES={'Apples','Bananas','Citrus fruits','Blueberries and other berries','Strawberries','Grapes','Melons','Peaches and nectarines','Pears','Pineapple','Mango and papaya','Other fruits and fruit salads'}
EXTENDED_HINTS={'bread':['面包'],'bagel':['贝果'],'oatmeal':['燕麦粥'],'yogurt':['酸奶'],'potato':['土豆'],'potatoes':['土豆'],'fries':['薯条'],'tofu':['豆腐'],'broccoli':['西兰花'],'spinach':['菠菜'],'apple':['苹果'],'banana':['香蕉'],'orange':['橙子'],'strawberry':['草莓'],'strawberries':['草莓'],'coffee':['咖啡'],'tea':['茶'],'cheese':['奶酪'],'bean':['豆类'],'beans':['豆类'],'ice cream':['冰淇淋'],'salmon':['三文鱼'],'beef':['牛肉'],'pork':['猪肉']}


def build(archive,output,extended=False):
    categories=CATEGORIES+EXTENDED_CATEGORIES if extended else CATEGORIES
    lookup_hints=dict(HINTS,**EXTENDED_HINTS) if extended else HINTS
    if output.exists():raise ValueError('Use a new output directory; snapshots are never overwritten.')
    with archive.open('rb') as stream:raw=stream.read(10_000_001)
    if len(raw)>10_000_000:raise ValueError('Archive exceeds bounded source size.')
    with zipfile.ZipFile(archive) as zipped:
        member=zipped.getinfo('surveyDownload.json')
        if member.file_size>80_000_000:raise ValueError('Source JSON too large.')
        rows=json.loads(zipped.read(member))['SurveyFoods']
    if not isinstance(rows,list) or not 1<=len(rows)<=20000:raise ValueError('Invalid source record count.')
    items=[]
    old=json.loads((ROOT/'data/catalog/v1/dishes.json').read_text(encoding='utf-8'))
    for item in old['items']:
        value=dict(item,id='wikidata:'+item['id'],kind='dish',category=None)
        value['search_terms']=[t for t in item['search_terms'] if t not in ('egg','eggs','鸡蛋','雞蛋')]
        value['source']=dict(item['source'],provider='wikidata',license='CC0-1.0')
        items.append(value)
    for row in rows:
        category=row['wweiaFoodCategory']['wweiaFoodCategoryDescription']
        if category not in categories:continue
        name=row['description'];qid=row['fdcId']
        is_raw=bool(re.search(r'\braw\b',name,re.I))
        # Keep exactly one raw egg reference so egg means an ingredient rather
        # than silently equating it with a particular cooked dish.
        if is_raw and name!='Egg, whole, raw' and not (extended and category in RAW_FRUIT_CATEGORIES):continue
        aliases=['egg','eggs','鸡蛋','雞蛋'] if name=='Egg, whole, raw' else []
        hints=[]
        for word,terms in lookup_hints.items():
            if re.search(r'\b'+word+r'(?:s)?\b',name,re.I):hints.extend(terms)
        items.append({'id':'usda:'+str(qid),'name':name,'names':{'en':name},'aliases':aliases,'search_terms':sorted(set(hints)),'source':{'provider':'usda','url':'https://fdc.nal.usda.gov/food-details/'+str(qid)+'/nutrients','revision':'FNDDS 2021-2023 / 2024-10-31','license':'CC0-1.0'},'kind':'ingredient' if is_raw and category not in RAW_FRUIT_CATEGORIES else 'reference_food','category':category})
    pack=validate_pack({'schema_version':2,'items':items})
    data=(json.dumps(pack,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    manifest={'schema_version':2,'file':'dishes.json','count':len(items),'sha256':hashlib.sha256(data).hexdigest(),'license':'CC0-1.0','retrieved_at':datetime.now(timezone.utc).isoformat(),'source_archive':{'url':SOURCE,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'source_records':len(rows),'selected_categories':categories},'field_provenance':{'wikidata_names_aliases':'Wikidata v1 snapshot, per-record revision retained','usda_name_category':'FNDDS published description and WWEIA category','search_terms':'Project-authored lookup hints, MIT; not sourced translations or ingredient evidence','egg_alias':'Editorial English/Chinese alias for the exact Egg, whole, raw reference'},'coverage':('Expanded meals, sides, fruit, breakfast and drinks' if extended else 'Selected prepared-food references')+' plus 13 Wikidata concepts. No restaurant listings, nutrients, availability or worldwide completeness.'}
    output.mkdir(parents=True)
    (output/'dishes.json').write_bytes(data)
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_records':len(rows),'catalog_records':len(items),'shipped_bytes':len(data)},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--extended',action='store_true',help='Expanded meals/sides/breakfast/fruit/drinks; create a new snapshot.')
    args=parser.parse_args();build(args.archive,args.output,args.extended)
