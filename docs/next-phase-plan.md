# Preview → friend-ready release: execution plan v2

October 2, 2026. Requested priorities: expand offline food data first; make back/home
behavior explicit; add playful emoji and terminal decoration; mature local export;
make postcards attractive and include a real link to try Plate Memory.

This document is a plan, not a record of implemented features. Current baseline:
13 public concepts, four working routes, plain-text postcards, 116 tests and a
synthetic four-route terminal smoke. Those checks do not establish real usability.
The previous implementation checkpoints remain preserved. Runtime stays local;
model extraction is untrusted and the generic guard stays byte-for-byte unchanged.

## Judge-facing assessment

Official rubric: writing quality is weighted most heavily, followed by relevance,
creativity, technical execution; partner technology is optional.
Source: https://dev.to/challenges/hacktoberfest-weekend-2026-10-01

| Dimension | Current evidence | Main weakness | Next evidence |
|---|---|---|---|
| Writing | Specific friend and separation across campuses; draft exists | Real trial still absent; technical warnings obscure the emotional story | One real handover, actual feedback, clear before/after scene |
| Theme relevance | Food companionship, friend-authored lunchbox, private observations | Daily meal discovery too sparse to rely on | Common takeout/cafeteria queries work without setup |
| Creativity | Generic deterministic memory guard under a food companion | Plain exports do not convey a gift; AI's useful role is easy to miss | A recognizable cafeteria postcard plus real local menu interpretation |
| Technical execution | Tests, provenance, local Gemma smoke, private stores | Navigation cancels too broadly; data incomplete; exports basic | Back-state tests, attributed data pack, inspected share artifacts |
| Open AI at the core | Local open-weight query/menu extraction; Python decides applicability | Basic browsing is mostly literal lookup | Show a natural query/menu interpreted locally, then a memory changing with date/permission under guard |
| Practical adoption | Dependency-free literal mode, separate optional routes | Recipient must understand commands and filesystem paths | Numbered actions, predictable back/home, simple export destination and quick-start link |

Do not optimize for partner integration at the expense of the offline/private
product. No winning probability or invented rubric scores are claimed.

## Data sources checked

| Source | Verified role/license | Decision |
|---|---|---|
| Wikidata | Multilingual structured labels/aliases, CC0 | Primary dish-concept and alias layer; bounded selected snapshot |
| USDA FoodData Central / FNDDS | Downloadable CSV/JSON; FDC data CC0 | Secondary prepared-food/reference layer; ingest public download at build time |
| Health Canada CNF 2026 | Official bilingual food-composition database and downloadable food-name/resources | Candidate Canada-specific reference layer; verify exact redistribution terms before bundling |
| Open Food Facts | Packaged-product data; ODbL database, separate contents/image licenses | Later packaged-snack module; poor fit for this week's takeout/cafeteria priority |
| OpenNutrition | Offline download; official methodology includes AI-inferred values and attribution gaps | Investigate names/provenance if needed; not a primary source of verified nutrient values |

Sources:
- https://www.wikidata.org/wiki/Wikidata:Licensing
- https://www.wikidata.org/wiki/Wikidata:Menu_Challenge
- https://fdc.nal.usda.gov/download-datasets/
- https://fdc.nal.usda.gov/api-guide/ (Licensing)
- https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/nutrient-data/canadian-nutrient-file-about-us.html
- https://open.canada.ca/data/en/dataset/1b6139bd-ed7e-4043-bc28-ff00e10f3109?res_page=1
- https://openfoodfacts.github.io/openfoodfacts-server/api/
- https://www.opennutrition.app/about

The CNF catalog endpoint returned 403 during direct inspection; official search
metadata and Health Canada documentation confirm the resource exists. Licensing
has not been verified here. No inspected source proves worldwide completeness.
No remote API, API key, scraping of private services or automatic background data
refresh is part of the recipient's runtime.

## A. Data and search: first implementation checkpoint

1. Inspect FNDDS download fields and a representative sample. Record actual counts,
   file size, source release and license. Keep original v1 pack unchanged.
2. Introduce catalog v2 with namespaced source IDs, concept kind (dish/ingredient),
   multilingual aliases and per-field provenance. Reference foods and personal
   restaurant choices remain different records. Ingredient search such as egg
   should not pretend an omelette is the same concept as an ingredient.
3. Expand a verified common-dish subset, provisional target 150–300 concepts. Actual
   reported count follows source inspection. Add a broader FNDDS name index where
   it helps discovery, with no blanket automatic cross-source merging.
4. Normalize plural/case/Unicode, add inspected Chinese aliases and bounded fuzzy
   suggestions. Label a guessed match and ask before using it. Cuisine/category
   browsing only uses sourced or explicitly editorial tags. Preserve negation.
5. Rank named matches deterministically; avoid raw record-order browsing. Separate
   exact matches, suggested matches and unknown queries. Show three at a time with
   a clear next-page action. Do not turn typical nutrients into actual meal facts.
6. Unknown query: explain simply, suggest nearby terms, accept another phrase or
   let the friend save their own choice. Never fabricate a restaurant or dish fact.

Modules: `src/catalog/schema.py`, `index.py`, new `sources.py` and `normalize.py`;
`scripts/build_catalog_v2.py`; `data/catalog/v2/`; `services/search.py`.

Gate: inspect sources/manifest; common English/Chinese query walkthrough; distinguish
pizza/sandwich/egg and dish variants; duplicates/alias collisions; no-ingredient and
negation queries; offline operation; corrupt pack rejection; no private profile in
build/model inputs. Measure search speed and shipped size before reporting them.
Freeze a separate public query set before tuning aliases and preserve failures.
Nutrient values, if introduced later, require units/reference basis and unknown
actual portion/preparation labeling. No guessed calorie total or health score.

## B. Navigation: return means one step

Current `FlowCancelled` can discard the whole meal route/form; a query-parser back
can return home unexpectedly. Treat this as a flow bug, not just label wording.

Implement explicit screen states and retained drafts. `back` goes to the named
previous screen, `home` goes to the table, `cancel` discards the current draft,
`skip` applies only to optional fields. Drafts remain in memory until explicit save.
Canceling a populated draft asks keep editing/discard; no file is written.

Every screen names its location and return target. Visible numbered buttons/actions
work alongside words; help does not expose internal alias names. Context-specific
prompts include `0 Back to food ideas`, `h Home`, or `Enter Skip` where relevant.
At input fields, explain reserved navigation syntax so normal food names are safe.
Keep old command aliases working where they do not create ambiguity.

Modules: new `ui/navigation.py`; `prompts.py`; meal/lunchbox/checkin/postcard flows;
Session composes transitions, rather than catching one exception for every depth.

Gate: back from query interpretation, dish detail, each form field, preview and file
picker; return retains route/query/draft; home and discard are distinct; invalid
input retries locally; no accidental save/order/meal log.

## C. Terminal visual identity

Use a small repeatable cafeteria world: 🍽️ meal, 🎒 lunchbox, 📝 check-in, 💌 postcard;
two bowls, a seat saved, receipt-like search cards, warm accents and short messages.
Decoration frames content without filling each screen with art. Show emoji with
words; tone avoids guilt, streak pressure and invented friend quotations.

Add consistent titles, current-screen breadcrumb and action footer. Test emoji
variation selectors/ZWJ and CJK display width; current per-codepoint wrapping is
insufficient for some emoji. Prefer a maintained width helper if required and keep
an ASCII fallback, `--plain`, `--no-color`, NO_COLOR and non-TTY readability.
Do not add a full-screen TUI dependency unless the state-based prompt UI needs it.

Gate: 32/40/80/120-column preview; emoji/plain/no-color; no broken frames, clipped
choices or hidden prompts; copy reviewed from the hungry friend's perspective.

## D. Mature export and a postcard worth sending

First separate a share schema from rendering and destination handling. Postcard v2
contains only explicit sender/recipient/message/optional food, theme ID, schema
version and opt-in public app link. Migration reads v1 without rewriting old files.
Never include journal symptoms, permissions, profile IDs or full histories by default.

1. Render a standalone local HTML card with embedded CSS/SVG and no external fonts,
   scripts, analytics or image calls. Escape all user text and validate links.
2. Offer three coordinated exports: beautiful browser-viewable HTML, plain text,
   and friend-pack JSON that the recipient can import. Distinguish postcard from
   importable lunchbox; do not ask users to guess which file to open.
3. Add a PNG image export after the HTML design is inspected; use a local renderer
   and explicit optional dependency. Core export continues to work without it.
   SVG/HTML is the visual source; avoid AI-generated decorative text assets.
4. Design a cream-paper cafeteria postcard, stamped date, two tray illustrations,
   space for a genuine short note and a restrained emoji/graphic motif. Themes:
   cafeteria table / takeout receipt / next lunch invitation. Use user-authored text.
5. Include `A seat is saved for you — try Plate Memory` with the verified public
   repository quick-start link. Initial link: https://github.com/Jesse-Zeng423/plate-memory
   Do not imply this URL launches a web app. Add a tested recipient quick-start page
   before pointing at a new deep link. HTML link and PNG QR (if implemented) use the
   same allowlisted public URL; no personal data or tracking parameters in the URL.
6. Default to an easy-to-find export folder; ask format/theme before destination.
   Preview → edit or export → show exact files → optional open file/folder/copy path.
   Handle cancellation, collisions, overwrite refusal, Unicode paths, permission
   errors and renderer failure with a useful recovery action. Avoid partial bundles
   with misleading success messages. Export manifest lists successfully created files.

Modules: `domain/share.py`, `services/export.py`, `postcard.py`, local templates under
`assets/postcards/`, `ui/export_flow.py`, `ui/postcard_flow.py`, `docs/start-here.md`.
Keep data schema validation and HTML rendering independent of terminal code.

Gate: inspect real rendered artifacts at phone/card widths and print; long English/
Chinese messages, emoji and hostile HTML input; no external browser requests; correct
link/QR; recipients can follow quick-start and import JSON; collision/permission/
missing-renderer recovery; exported content exactly matches previewed fields.

## E. Final friend handover and submission evidence

Run a new synthetic end-to-end demo across all destinations, then hand the working
release to Harold. Record actual confusion/feedback with permission and improve
those points. Replace article trial placeholders only after real use. Prioritize
one short story + visible result + local-model/guard demonstration over feature count.
No DEV publishing or messaging is authorized by this plan alone.

Each checkpoint: required unittest/pytest/verify/mock checks, targeted UI/artifact
inspection, docs/build-status update. Live model smoke only for changed integration,
synthetic inputs only, separate versioned evidence. Checkpoint completeness is tied
to acceptance evidence; a green test count is not proof of perfection.

Order: A data → B navigation → C terminal design → D postcard/export → E handover.
Do not defer a blocking navigation issue just to inflate the catalog count. Do not
start another checkpoint while its predecessor has unresolved acceptance failures.

## Phase A checkpoint outcome

Implemented v2 with 1,603 source-backed records (13 concepts + 1,590 FNDDS variants),
not 1,603 deduplicated dishes. This replaces the provisional unique-concept count
with explicit variant retention. Frozen public query set, measured size/latency,
source manifest, corruption/negative/paging tests and real synthetic terminal run
are recorded in build-status. Phase B is next; C–E remain unimplemented.

## Phase B checkpoint 1 (partial)

Shared navigation requests and postcard field/preview/destination states are now
implemented; session-only postcard drafts survive home. Nested query/category/refine
cancellation preserves food results. See build-status and navigation-terminal-v1.txt.
B gate remains open for lunchbox/check-in/saved-choice fields, route/list state and
numbered navigation. Do not advance to C yet.

## Phase B outcome

Companion forms and food route states now implement previous-field/previous-screen
returns, Home with session-only drafts, explicit discard, conditional fields and
numbered actions. File preview/destination returns are separated. 135 tests and
synthetic real-terminal replay are recorded in build-status. B is complete within
the companion scope; original dietary-note/menu-review contracts are preserved.
Next checkpoint is C; no visual postcard or HTML/PNG export is claimed yet.

## Latest user adjustment (October 3)

C is implemented and verified. Before D, expand the attributed offline name pack,
add startup English/Simplified Chinese choice and reduce visible copy to actionable
information. Keep ingredients/availability unknown and preserve safety reminders.
Then complete D and E, with actual Harold feedback still supplied by the user.

Expanded pack/language checkpoint: 3,535 name records now ship by default with v1/v2
retained; interactive language selection and --language en/zh are implemented.
142 tests and offline synthetic walkthroughs pass. Proceed with D.

## Final implementation outcome

C, expanded data/language, D exports and the independently executable part of E
are complete. Actual artifact/print inspection and bilingual real-terminal evidence
are in build-status and friend-ready-smoke.json. Earlier steps are historical.
The remaining handover/real reaction belongs to Harold and Jesse; it cannot be
synthesized. Pause automation after final verification and checkpoint save; resume
only for new work or actual trial feedback. No DEV publication is authorized.
