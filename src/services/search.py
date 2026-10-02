"""Two explicit result types; discovery never infers dietary suitability."""
from .meal_choices import shortlist


def discover(store, route, query='', catalog=None):
    saved = [('saved', meal) for meal, _ in shortlist(store.list(), route, query)]
    ideas = [('idea', item) for item in catalog.search(query, limit=max(0, 3-len(saved)))] if catalog is not None else []
    return saved, ideas
