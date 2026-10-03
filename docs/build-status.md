# Build status

New project started October 2, 2026. First commit: `6d852a2`, at 00:55 EDT.

## Completed

- Unchanged MIT generic guard; neutral API and upstream fingerprint documented.
- Food adapter with source grounding, inspectable vocabulary, permission boundaries,
  meal-date/freshness/risk mapping, and CLI.
- Local-only Ollama integration; final model input contains menu text only.
- Four synthetic canned scenarios, expected JSON/text output, 69 passing tests.
- Provenance verification and mock dry run passed.
- Four real Gemma 3 4B smoke scenarios passed at v11; actual live CLI transcript
  and demo image saved. Earlier failures remain preserved.
- README, MIT, English DEV draft, handover guide and GitHub Actions workflow.

## Terminal UX upgrade — October 2

User chose to keep the product in the terminal instead of building a browser UI.
Implemented guided setup, private revisioned notes, multi-line menu input,
dish-centric explanations, explicit confirm/allow/revoke actions, raw rule trace,
line progress and a private grounded-food cache. 83 unittest tests and 43 pytest
subtests pass, as do provenance verification and all four canned dry runs. The upstream engine and extraction
prompt remain unchanged. No web UI or UI dependency was added.

Real pseudo-terminal smoke with Gemma and public synthetic input passed: the first
review uses local inference, the repeated menu uses the cache, changing the meal
date changes the weekday guard action, and allergy review remains visible.
See `terminal-smoke-v1.json` and `terminal-live-v1.txt`. Public commit `1ab23cb`
also passed CI on Python 3.10/3.12/3.14:
https://github.com/Jesse-Zeng423/plate-memory/actions/runs/37051337645

## Current checkpoint: companion step 1 implemented

Current checkout: `/Users/zz/Downloads/plate-memory`. Public repository:
https://github.com/Jesse-Zeng423/plate-memory

Positioning: "That bro who ate with you every day back in high school."
Latest scope is takeout and campus cafeteria, with only two energy choices:
too tired -> delivery, otherwise -> walk to cafeteria. Cooking, equipment and
preparation instructions were removed from the plan.

Detailed order/contracts: `docs/implementation-plan.md`; current product flow:
`docs/product-plan.md` v3; data plan: `docs/data-plan.md` v2.

Stage 0 shared-service refactor is complete. Step 1 now adds validated saved-meal
records, private SQLite persistence with revision conflict checks, route/keyword
shortlists, add/edit/delete forms, a warm two-bowl home, plain mode and a synthetic
in-memory companion demo. No dietary profile is needed to browse saved choices.
Selections are session-only plans, not orders or meal logs. Historical prices and
unknown availability remain explicit. Baseline guard risk reminders stay visible;
recorded-menu AI review adds temporary external-verification context without
changing profile files. The generic guard and original extraction prompt are intact.

A real pseudo-terminal synthetic run exercised both routes, back/switch, keyword
filtering, selection and no-file demo isolation. Evidence:
`docs/companion-smoke-v1.json`, `docs/companion-terminal-v1.txt`.
Validation passed: 98 unittest tests; 98 pytest tests and 57 subtests; guard/package
verification; four mock scenarios. No model calls were made for this step's tests
or companion demo.

Next step 2: public local dish/alias data and free-text candidate search, with
explicit guard-based personalization. Current search is literal dish/place lookup
only. Then implement text lunchbox, optional meal journal and postcard export.
Those future features and a public catalog are NOT yet shipped. Do not stop
independent work merely because real dietary preferences/feedback are pending.
No background continuation was started in this step. Inspect/update any saved
heartbeat before resuming it; the old prompt references a moved checkout and old scope.

## User input outstanding

Harold is Jesse's friend and roommate from high school and a big foodie.
His actual preferences and reaction after a real handover are pending. The user
has supplied the broader problem of staying connected and caring about everyday
meals after moving to different universities. Private health details should not
be copied into public fixtures or the article without an explicit sharing choice. Do not invent them; see docs/handover.md and marked DEV placeholders.
No DEV publishing or submission has occurred. No formal skill was created.

## Local operations

Ollama installed through Homebrew, which also upgraded its dependencies
(openssl/readline/sqlite/xz) and installed Python/MLX dependencies. A local-only
server was started for this build; weights remain downloaded for future use.
Mac idle/system-sleep assertions are time-limited to October 5, 02:59 EDT.
The original heartbeat was paused after the CLI handoff. The new staged roadmap
is recorded above; do not assume that old automation is active or points at the
current checkout. No reset credits were used.

## Companion step 2 checkpoint — offline dish discovery

Shipped a bounded 13-concept Wikidata CC0 names/aliases snapshot, revision links,
retrieval timestamp, count and SHA-256 manifest. Added project-authored query hints
separately (e.g. egg -> omelette). No cuisine or typical-ingredient assertions are
shipped; unknown facts stay unknown. This is a small starter catalog, not worldwide
coverage. Explicit developer refresh writes a new directory; runtime never fetches.

Empty accounts can search pizza/sandwich/egg and Chinese aliases. Saved places and
public ideas are visibly different. New keywords work at both empty and populated
lists. Local Gemma query spans use a separate closed schema, preserve negation,
reject invented spans and require phrase confirmation; only the user query reaches
the model. Budgets/avoidances remain visible but unverified. No automatic ranking
by preferences: actual-menu review is required for guard-based matching. The notes
command provides confirmation/edit and recomputes guard reminders in the flow.

105 tests and 72 subtests passed; provenance and four mock scenarios passed.
New local Gemma synthetic query smoke: docs/query-smoke-v1.json, two validated
queries including a negated egg phrase. Offline terminal tests forbid socket calls
and verify empty-account selection creates no private files. Next: text lunchbox.

## Companion step 3 — text lunchbox

Added strict bounded friend-pack v1, explicit local file preview/import/confirmation,
owner-only atomic storage and a dedicated cafeteria corner. Sender attribution is
file-supplied, never a verified identity. Imported control characters are removed
on display; no URLs are fetched and no gift becomes a dietary memory. Synthetic
gift text is labeled and demo import never writes real files. 108 tests passed,
plus pytest, provenance verification and all four mock dry runs. Next: check-ins.
User requested final copy/low-friction walkthrough; added as step 6.

## Companion step 4 — optional meal journal

Implemented explicit actual-meal logging with optional route/taste/fullness/comfort/
note, bounded journal schema, separate private SQLite store and revision-checked
edit/delete/history. A selected idea only provides an editable dish-name default;
save requires actual-meal confirmation. Null fields stay null. No preferences or
model inputs are derived from observations. 110 tests and 72 subtests passed,
provenance verification and four mock scenarios passed. Next: local postcard.

## Companion step 5 — until our next meal

Added postcard composition from explicit names/message and opt-in selected dish,
preview then local text export, owner-only file permissions, overwrite refusal
and demo preview without real writes. Export schema excludes journal/symptoms/
permission/history by construction. No message is sent. 112 tests and 72 subtests
passed, provenance and mock scenarios passed. Next: user-facing copy and walkthrough.

## Companion step 6 — current resume point

Four parallel numbered destinations are live. Meal discovery shows at most three
results total, supports ordinary keyword refinement without special commands and
keeps provenance at the selected detail view. Warm, shorter prompts keep the main
meal path free of mandatory profile/AI setup. Journal feelings skip as one group;
lunchbox authoring/export avoids requiring hand-edited JSON. Narrow-terminal output
counts CJK display width and wraps long source links.

116 tests/72 subtests passed; guard/package verification and all four mock reports
passed. Real 40-column pseudo-terminal synthetic walkthrough covers all four
destinations, English keyword refinement, explicit actual-meal record, postcard
preview and no demo files, from a working directory outside the repository. See
docs/companion-terminal-v2.txt and docs/companion-smoke-v2.json. No Harold trial
feedback or DEV publication is claimed.

Remaining product limits: public catalog covers only 13 concepts; cuisine/typical
ingredient enrichment and personalized ranking require better verified data.
Current flow deliberately defers dietary clearance to actual-menu guard review.
Budget/avoidance extraction shows unverified constraints; it cannot prove a restaurant
meets them. Real Harold usability feedback remains the next evidence needed.

## Next-phase planning (not implemented)

Reviewed current source and official challenge rubric; investigated Wikidata,
USDA FNDDS, CNF, Open Food Facts and OpenNutrition. Primary candidates: Wikidata
concept/alias expansion and a bounded USDA prepared-food reference index. CNF
redistribution terms remain unverified; OpenNutrition includes AI-inferred values.
New ordered plan in docs/next-phase-plan.md: data, explicit navigation states,
emoji/terminal identity, visual postcards and export, real friend handover.
Runtime code/data remain at the preceding checkpoint; planned features are not shipped.

## Phase A completed: offline catalog v2 (current resume point)

Shipped 1,603 records: 13 preserved/namespaced Wikidata concepts and 1,590 selected
USDA FNDDS reference foods from a 5,432-record official archive. Raw food references
are excluded except one explicit egg ingredient record. Original variants and source
labels remain distinct. Published categories, original English names, marked editorial
Chinese hints, release/hash/count/field provenance are retained. No nutrient values
or recipe/restaurant ingredient guarantees are included. V1 is unchanged/readable.

Added plural/Unicode normalization, labeled spelling suggestions, category browsing
and three-at-a-time paging across saved/public results without skipping records.
Egg/鸡蛋 leads to an ingredient reference, with an explicit prepared-dishes action;
it cannot be selected as a prepared meal. Unknown/negative queries do not silently
become dietary clearance. Generic guard and model integration are unchanged.

Validation: 121 unittest tests; 121 pytest tests/105 subtests; provenance verification
and four mock scenarios pass. Frozen 28 positive queries/5 negative constraint cases
pass. A new real 40-column pseudo-terminal walkthrough outside the repo exercises
spelling confirmation, ingredient vs dish, pagination and categories with no demo
files. Evidence: docs/catalog-smoke-v2.json and docs/catalog-terminal-v2.txt.

Observed load 29.55 ms; median query 5.81 ms/max 9.71 ms on this build, pack 897,993
bytes. Not a broad accuracy or global-coverage claim. Scope adjustment from the
provisional 150–300 unique-concept target: retain a larger source-backed variant
index instead of incorrectly collapsing variants into invented canonical dishes.
Source count and covered languages remain explicit. Next: phase B navigation
states, back/home/draft retention; then emoji/visual export. Continue from this
checkpoint, do not restart the completed catalog work.

## Phase B checkpoint 1 — postcard drafts and nested search returns

Added distinct back, discard and home requests, plus a reusable in-memory field
navigator. Postcard fields return one field at a time with retained defaults;
preview returns to the message, destination returns to preview, overwrite returns
to destination. Home preserves the session draft, confirmed discard clears it,
and successful export clears it. Drafts are not written to disk. Invalid postcard
text retries its field; a failed save retries the destination with the note intact.
Existing overwrite refusal leaves the target untouched. Optional dish selection
and original text-export schema remain unchanged for the later export checkpoint.

Query interpretation cancellation keeps the preceding keyword; cancelling category
or refine leaves the preceding list intact. Home propagates out of nested companion
prompts to the table. No guard, model or catalog data changes.

Validation: 127 unittest tests; 127 pytest tests/105 subtests; verify_project and
all four mock scenarios pass. New synthetic tests cover previous-field edits,
preview/path returns, home/resume, discard confirmation, overwrite path correction,
save-error recovery and nested search cancellation. Real 40-column pseudo-terminal
walkthrough from an unrelated directory exits 0 with no demo files; captured in
docs/navigation-terminal-v1.txt. Wrapped output made the first transcript assertion
fail; inspecting and normalizing whitespace confirmed the expected message. This
was a capture assertion, not a terminal crash.

Phase B is NOT complete: lunchbox, saved-choice and check-in forms still need the
same previous-field/draft behavior; meal route/list states and numbered navigation
need completion. Narrow input prompts can still exceed the width, to be addressed
in phase C. Next run continues these B acceptance gaps before visual/export work.

## Phase B completed — companion form and route navigation

Migrated lunchbox writing, meal journal and saved-choice forms to shared conditional
field states. Back edits the previous active field; preview returns to the last
active answer. Home retains drafts only in the current Session; confirmed discard
clears them. Declining discard stays at the preview or current field. Drafts are
never written or sent to a model. Successful explicit save clears its draft.
Retained edit drafts carry their original revision, preventing a resumed edit from
overwriting newer stored data; stale drafts require discard before reloading.

Optional feelings, shared dishes, price dates and walk times are projected only
when enabled. Clearing price removes its date; changing to delivery removes the
walk time. Future observation dates and bounded text errors retry in place.
Import preview returns to file selection; export confirmation/overwrite returns
to destination. Failed export permits a different destination. File selection back
returns to the lunchbox, without altering the existing gift. Numbered companion
menus and choice-detail actions expose 0 Back/h Home without reserving these as
navigation in ordinary text fields.

Food navigation now has route, craving and results states. Back returns one level;
Home retains route/query/page/category in memory. Query interpretation returns to
the original sentence, with unchanged text reusing its validated extraction for
this invocation. Confirmed keyword search remains unpersonalized. Original menu
review and dietary-profile contracts are unchanged; no guard changes.

Validation: 135 unittest tests; 135 pytest tests/108 subtests; verify_project and
four mock scenarios pass. Tests cover retained drafts, conditional-field back,
local invalid-date retry, skipping old hidden answers, preview cancellation,
route/query return and no accidental consumption/profile updates. Two pre-existing
journeys now explicitly distinguish Home from Back. A failed new saved-form test
was corrected to press Back at the intended field rather than the price field.

Real 40-column synthetic pseudo-terminal replay covers lunchbox home/resume/edit,
meal-journal preview edit/history, saved-choice preview edit and meal route returns,
exits 0 and creates no real demo files. Reproduce with
`python3 scripts/run_navigation_smoke.py`; evidence in navigation-terminal-v2.txt.
This checks navigation, not real Harold usability or visual polish. The Phase B
companion gate is met. Next: C emoji identity, proper grapheme width and narrow
input prompts; then D visual/export artifacts and E final copy/real trial.
