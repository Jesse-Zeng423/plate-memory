# Local food discovery: data plan v1

Decision date: October 2, 2026. Research/design only; the catalog and search described
here are not implemented. Runtime must not call external APIs or look up user
queries on the internet. Public data may be fetched during development, inspected
and shipped as a versioned local pack. Users install the pack with the application.
Updates will be explicit local-file imports, not hidden runtime network requests.

## Product decision

Default input is a short message: "想吃面，只有微波炉", "有什么鸡蛋能做的", or a
particular dish name. Search retrieves local candidates without requiring a pasted
menu. A menu is optional evidence when assessing a specific restaurant offering.

No source reviewed establishes coverage of "most dishes in the world", across
regional variants, languages, complete ingredients, instructions and nutrition.
We will show actual packaged counts and supported languages. Coverage, recipe
quality and knowledge of an actual serving are different properties.

## Sources inspected

| Source | Verified facts | Intended role / decision |
| --- | --- | --- |
| [Wikidata developer guide](https://www.wikidata.org/wiki/Wikidata:For_developers/en), [licensing](https://www.wikidata.org/wiki/Wikidata:Licensing), [downloads](https://www.wikidata.org/wiki/Wikidata:Database_download) | Structured data is CC0, multilingual and downloadable for offline use. Media has separate licenses. | Primary proposed source for a bounded dish-name, alias and cuisine index. Preserve entity IDs, source revisions and relationships; do not bundle photographs. |
| [Biryani example](https://www.wikidata.org/wiki/Q271555) | A dish entity has cuisine and ingredient relationships, several without references; ingredients include variants. | Evidence that a knowledge entry is not a complete single recipe or the composition of a user's actual dish. |
| [USDA downloads](https://fdc.nal.usda.gov/download-datasets/), [licensing](https://fdc.nal.usda.gov/api-guide/) | CSV/JSON downloads; FoodData Central data is public domain/CC0. | Optional later ingredient-composition reference. It is not a universal cuisine or restaurant-recipe catalog. Omit nutrition calculations until amounts and ingredient mappings are reliable. |
| [RecipeNLG original repository](https://github.com/Glorf/recipenlg/blob/main/README.md) | Authors report 2,231,142 recipes aggregated from multiple sources. | Broad recipe collection, not proof of distinct global-dish coverage. The official download page did not expose readable redistribution terms during this check. Dataset redistribution rights remain unverified; do not package a mirror based on its repository's code license. |

This plan chooses Wikidata structured data plus original checked cooking cards.
It does not depend on obtaining new permissions for a scraped recipe collection.
RecipeNLG licensing is marked unverified, not assumed to be prohibited or permitted.
Wikidata ingredient relationships are incomplete and variant-dependent; reference
absence never means an ingredient is absent from an actual meal.

## Three distinct information layers

1. **Dish concepts:** canonical ID, multilingual names and aliases, cuisine labels,
   dish family, optional source-provided typical ingredients, source/version/license.
   These support discovery and variant questions. They cannot certify allergies,
   exact nutrients, price or local availability.
2. **Actionable recipe variants:** original/appropriately licensed instructions,
   specified ingredient quantities, equipment, servings, estimated prep time,
   effort category, author/provenance, review status and parent dish concept.
   Imported reference-only entries do not automatically become cooking suggestions.
   Original cards must be reviewed for feasibility; label untested timings as estimates.
3. **Private context:** actual user-provided menu text, price and date, actual meal,
   pantry/equipment declarations and explicitly approved preferences. These facts
   stay local and separate from the distributable catalog and candidate parser.

Proposed starter target: 100–200 dish concepts and 30–50 practical recipe variants,
with checked English/Chinese names for the selected entries. Curate for student
use and variety across cuisines, without claiming a worldwide coverage percentage.
If review capacity is smaller, ship fewer complete cards and report the real count.
Public catalog facts are attributed source data or original recipe content;
fictional prices, people and trial examples are explicitly synthetic. No real
personal profile is bundled.

## Retrieval and recommendation sequence

1. Normalize the user's text and search exact names/curated aliases locally first.
2. For free-form text, local Gemma may extract candidate dish/ingredient phrases
   and explicitly expressed constraints with their source spans. New prompt/schema
   is separate from the existing menu extractor. Validate field shape, span grounding
   and candidate IDs; ambiguous intent becomes a brief confirmation question.
3. Use a local SQLite index for names, aliases, cuisine and curated ingredient tags.
   Include explicit Chinese alias handling rather than assuming English tokenization
   handles Chinese. Start with lexical retrieval and fixed ranking; embeddings are
   an optional later improvement only if measured retrieval misses justify them.
4. Resolve dish variants and display unknown information. An invented model item
   ID is rejected; a missing catalog result is not filled by an invented recipe.
5. Use confirmed current constraints and guard-approved memories for deterministic
   filtering/ranking. Stable ties preserve reproducible results. The model does not
   receive private history or decide permissions, applicability, risk or ranking.
6. Show at most three choices, reasons, recipe/reference status and required equipment.
   Ask one material missing question when useful; do not block discovery with a
   complete questionnaire. Lack of price means budget fit is unknown.
7. Optionally add actual restaurant menu text or prices to review a real offer.
   No claim of finding nearby restaurants, stock, current deals or completing an order.

Do not transfer a user's negative phrase ("don't want noodles") into a positive
retrieval constraint by stripping negation. Parse failures offer direct keyword
search/manual choices explicitly, never pretend an AI extraction succeeded.
A session-only statement must not silently become a permanent memory.

## Evidence boundary for the guard

Track provenance independently for `catalog_reference`, `recipe_variant` and
`user_menu` evidence. A typical ingredient may prompt a question about a real dish,
but must not masquerade as text actually extracted from that menu. Do not combine
reference ingredients from different variants into a supposedly complete recipe.

The food adapter maps these contexts to existing neutral evidence/risk fields.
External ingredient verification remains required when the actual preparation is
unknown and the decision depends on it. High-risk allergy review remains explicit,
including when the catalog has no matching ingredient. New food evidence fields
belong to a versioned food adapter contract, never hard-coded into the generic guard.

No-profile discovery is allowed with an explicit unpersonalized state; do not
fabricate a memory to satisfy the existing profile-v1 validator. Likes versus avoid
rules need an explicit schema version before recommendations use them differently.

## Planned modules and packaging

- `src/catalog/`: schemas, bounded import, aliases and local index; no runtime HTTP.
- `src/services/search.py`: query candidates and source-grounded retrieval.
- `src/services/recommend.py`: confirmed context + guard actions + fixed ranking.
- `src/ui/meal_flow.py`: short prompts, back/skip, disambiguation and result cards.
- `data/catalog/v1/`: reviewed public source subset and original recipe cards.
- `manifests/catalog-v1.json`: source URLs, entity revisions, fetch date, license,
  hashes, actual entry counts, review status and package version.

These paths are planned, not empty modules added now. Public source-fetch/build
scripts remain separate from the runtime app and never take a private user query.
Never download a full global Wikidata dump onto the user's laptop just for this
small catalog. Package a bounded subset after reviewing it. Catalog v2 produces
new artifacts; do not overwrite a shipped v1 snapshot.

## Acceptance for the first data/retrieval stage

- Known dish and alias queries return the intended local concept; ambiguous names
  request a variant; unknown names clearly report coverage limits.
- Ingredient/energy/equipment queries retrieve actionable cards with matching
  declared fields and traceable reasons; missing facts are shown as missing.
- Chinese/English aliases, negation and variant ingredient differences are exercised.
- User preferences, symptom history and personal notes never enter source-building
  requests or the public data pack.
- Runtime works with external internet unavailable and only loopback model access.
- Package validation checks hashes, required fields, source/license metadata,
  actual counts and the absence of executable import content.
- No benchmark or latency claim until measured on the existing 8 GB Mac.
