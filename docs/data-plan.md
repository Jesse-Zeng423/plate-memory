# Local food discovery: data plan v2

October 2, 2026. Public-data research remains valid; scope now focuses on takeout
and campus cafeterias. Cooking recipes, preparation steps, kitchen equipment and
recipe-variant targets from v1 are removed. A 13-concept names/aliases starter catalog is now shipped.
The personal saved-choice store is the first implemented data layer.

## Three separate records

1. **Private saved choice:** user-provided dish/place, delivery or cafeteria route,
   optional historical CAD price + date, last-seen date, cafeteria walk time and
   transcribed menu text. Versioned private SQLite store; no live availability.
2. **Public dish concept:** ID, checked names/aliases in selected languages, cuisine,
   food family and attributed reference facts. Used to suggest things to look for.
   A catalog name or ingredient is not evidence of a particular restaurant's recipe.
3. **Private memory/journal:** existing explicit preferences and future observations.
   Separate schema and permissions. A symptom or rating never silently changes
   dietary constraints. A dish selection does not imply it was eaten.

## Sources checked during planning

- [Wikidata developer guide](https://www.wikidata.org/wiki/Wikidata:For_developers/en),
  [licensing](https://www.wikidata.org/wiki/Wikidata:Licensing) and
  [download documentation](https://www.wikidata.org/wiki/Wikidata:Database_download):
  structured multilingual data is CC0 and can be used offline. Proposed primary
  source for a bounded dish/alias/cuisine subset; photos have separate licenses.
- [Biryani entry](https://www.wikidata.org/wiki/Q271555): illustrates that cuisine
  and ingredient relationships can represent different variants, some without
  references. Do not treat all listed ingredients as one complete recipe.
- [USDA download data](https://fdc.nal.usda.gov/download-datasets/) and
  [licensing](https://fdc.nal.usda.gov/api-guide/): downloadable CSV/JSON public-domain
  CC0 food composition data. Optional later reference, not a universal dish menu.
  Actual serving nutrients remain unknown without quantities and preparation.
- [RecipeNLG original repository](https://github.com/Glorf/recipenlg/blob/main/README.md):
  authors report 2,231,142 recipes. Redistribution terms were not verified from the
  official download page during the review. Not selected for this app's data pack.

No inspected source establishes coverage of most dishes worldwide. Step 2 aims
at a checked starter subset, provisionally 100–200 concepts, with actual count,
source revision, retrieval date, license and hashes reported at release. Smaller
well-described coverage is acceptable. No recipe instructions need to be collected.

## Retrieval sequence

1. Step 1 uses deterministic route + literal dish/place keyword lookup over saved
   facts. Stable name/ID order breaks ties. Private menu descriptions and subjective
   observations do not silently become preference-ranking features.
2. Step 2 adds checked aliases and cuisine tags from a bundled public pack. Keep
   "your saved place" and "an idea to look for" visibly distinct result types.
3. Free-text queries can use local Gemma to extract candidate phrases and explicit
   current constraints, with a new closed schema and source-span checks. Negation,
   ambiguous variants and invented IDs must be handled before interpretation.
4. Only explicit context and guard-approved memory may affect personalized ranking.
   Unconfirmed parsing stays visible for correction; a current wish is not a new
   permanent preference. Unknown price cannot satisfy a budget filter.
5. Historical menu review uses temporary external-verification context; it does
   not modify the saved dietary profile. Actual current menu text can be supplied
   through the original review entry point. Allergy/permission precedence holds.

No profiles/journals are sent to the candidate model. Runtime does not access
external APIs. Public-source build scripts run separately during development,
never receiving a user's private query. Bundle a bounded versioned snapshot with
the app; do not download all of Wikidata onto the user's laptop. Updates require
an explicit file import, not background cloud queries.

## Future code and acceptance

Step 2 creates `src/catalog/schema.py`, `src/catalog/index.py`,
`src/services/search.py`, a bounded public `data/catalog/v1/` and a manifest with
source/license/hash/count metadata. No empty modules are created ahead of use.
Verify mixed Chinese/English aliases, no-hit recovery, variant ambiguity, negation,
route filtering, revocation and unknown actual ingredients. Runtime must work with
only loopback model access and no external network. Record speed/coverage after
measurement; do not promise unmeasured latency or global completeness.

Current pack intentionally omits cuisine/ingredient facts until they are checked.
Manifest records actual coverage; 100–200 concepts remain a future expansion target.

## Shipped v2 update

Current default is data/catalog/v2: 13 namespaced Wikidata concepts plus 1,590 USDA
reference-food variants, names/categories only. The developer builder reads a
bounded official FNDDS zip; runtime has no fetch. Original v1 data remains intact.
Chinese lookup hints are separately editorial; no claim of full bilingual coverage.
Source/archive hashes, release, count and field provenance are in the manifest.
