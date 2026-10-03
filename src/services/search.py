"""Paged result types; discovery never infers dietary suitability."""
from .meal_choices import shortlist


def discover(store,route,query='',catalog=None,offset=0,category=None):
    saved_all=[('saved',meal) for meal,_ in shortlist(store.list(),route,query,limit=300)] if category is None else []
    saved=saved_all[offset:offset+3]
    idea_offset=max(0,offset-len(saved_all))
    ideas=[('idea',item) for item in catalog.search(query,limit=3-len(saved),offset=idea_offset,category=category)] if catalog is not None else []
    return saved,ideas
