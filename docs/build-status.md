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

## Phase C completed — terminal visual identity

Four destinations have matched bowl/lunchbox/journal/postcard emoji, a compact
seat motif and warm title accents. Optional technical actions move to More while
old commands remain accepted. Bundled unmodified MIT wcwidth 0.6.0 provides
Unicode grapheme-aware wrapping, with source/license recorded separately in
terminal-width-provenance.json. No package installation or runtime network needed.
Multiline text stays multiline; labels and defaults now wrap above a short input
marker. Plain mode removes product emoji/art/color; no-color keeps decoration.

137 unittest/pytest tests, width/control checks at 32/40/80/120 columns, verify and
four mocks pass; navigation replay passes. Checked CJK, combining accents, ZWJ
families, flags, skin tones, URL wrapping and long input defaults. Synthetic visual
previews are in terminal-preview-{32,40,80,120}.txt. Actual terminal/font emoji
rendering may differ; no cross-terminal universal rendering claim is made.

Latest user scope adds broader offline data, a startup English/Simplified Chinese
choice and shorter key-information copy before final exports/handover. These are
next, followed by D visual postcard/export and final walkthrough. Harold's trial
and DEV factual placeholders remain outstanding.

## Expanded catalog and bilingual interface checkpoint

Default offline snapshot v3 contains 3,535 records, retaining every v2 source ID
and adding sourced categories for sides, breakfast, fruit, vegetables, drinks and
more cafeteria/takeout references. Names only: no nutrient estimates or dietary
clearance. CC0 FNDDS archive/release/category selection/hash and editorial Chinese
hints are in the new manifest. Builder --extended creates a new snapshot; old
snapshots are not overwritten. Source archive still has 5,432 records. Fruit
references can be selected as ideas; raw egg remains an ingredient reference.

Interactive startup offers Simplified Chinese/English; --language supports scripts
and direct launches, with English default for noninteractive stdin. Session language
can change in More. Explicit translation wraps presentation strings, never user
input, stored notes, model outputs or source names. Common confirmations and journal
choices accept Chinese aliases while storage/guard decisions keep canonical values.
Source labels remain in their published language and are searchable by marked
editorial hints. Decoration/width work applies to both languages.

142 unittest/pytest tests pass, including interactive selection, offline Chinese
meal path, canonical journal fields, untranslated user-authored content and added
catalog coverage. Repository verification, four mocks and the actual navigation replay also pass.
Synthetic bilingual walkthroughs are in language-preview-en/zh.txt. Next: visual postcard/export.

## D/E implementation complete — visual exports and final synthetic handover

Postcard v2 is a strict separate share contract: explicit names/message/optional
food, theme/language/date and opt-in allowlisted public quick-start link. V1 remains
readable and its API/schema unchanged. Standalone HTML embeds original CSS/SVG,
escapes user text and forbids automatic external resources/scripts through CSP.
Three themes and English/Chinese labels are implemented. No journal, health,
permission, profile ID or history fields are accepted. Food included in an imported
lunchbox is explicitly an idea, not evidence of a meal eaten together.

Exports: atomic new folder with HTML/text/importable lunchbox JSON and SHA-256
manifest; single HTML/text/JSON files with explicit replacement; optional PNG from
an isolated installed local Chrome/Chromium, no install/download triggered. New
share folders are never overwritten. Failures remove staging files and keep the
note; missing renderer returns to format selection. Exact created paths are shown.
HTML supports viewing and browser printing offline; the public app link requires
intentional navigation and opens repository instructions, not a hosted app.

Actual local rendering exposed two issues before this gate passed: Chrome stayed
alive after writing a valid PNG, and macOS's minimum desktop viewport clipped a
390px screenshot. The renderer now waits for a complete image, terminates only its
own process group and pins small preview document width. A bounded RGB/RGBA PNG
crop removes only uniform trailing background, preserving all content. Long
Chinese output is complete; templates wrap long names/words and preserve emoji.
Desktop, phone-width and long-message images were visually inspected. Print QA
initially put a hint on page 2; refined print CSS produced one complete inspected
A4 page for the normal synthetic example. Scratch PDF/PNG QA files were removed.

Synthetic examples: examples/postcards/, including actual share bundle, desktop
PNG, phone Chinese PNG and Chinese HTML. These contain no Harold trial facts.
Recipient guide: docs/start-here.md; handover checklist updated to begin with hungry
meal discovery, with local AI and dietary setup optional. DEV draft updated for
current functionality and friend story; real reaction remains explicitly unfilled.
Source links/rule details are secondary actions instead of the default food screen;
Chinese discovery actions also accept Chinese words. Core guard/inference unchanged.

Final evidence: 150 unittest/pytest tests; provenance/four mocks; navigation replay;
new 40-column real-terminal journeys in both languages across meals, authored
lunchbox/export, actual-meal confirmation/history and styled postcard bundle with
app link. Runtime app sockets are forbidden in this smoke; no dietary profile was
created. Synthetic private stores are temporary and removed. Reproduce with
scripts/run_friend_ready_smoke.py; transcripts and metadata in docs/friend-ready-*.

All independently implementable plan items are complete within stated scope.
Remaining human work: actual Harold device/use trial, permitted factual feedback,
and final DEV publication instruction. No real trial, message or DEV submission
has occurred. No new accuracy, nutrient, availability or health claim is made.
Automatic continuation should pause after the saved checks/commit/CI are complete.

Final release checks repeated successfully: 150 unittest tests; 150 pytest tests
and 132 subtests; verify_project; four mock scenarios; navigation replay; English
and Chinese 40-column friend-ready replay with application sockets forbidden.
No new model inference was required for these presentation/export changes.

## Practical follow-up completed — English default and usable discovery

Startup language now lists English first and Enter selects it; Simplified Chinese
remains available as 2 or --language zh. Demo postcard export is explicitly allowed
after format/path confirmation, while profile, meal and preference records remain
in memory. A real synthetic demo journey generated a share folder and local PNG
in ignored private/postcards; actual resulting PNG was visually inspected.

A separate editorial food_ideas service recognizes bounded loose directions such
as something warm/I want noodles/想吃点热的, groups existing sourced categories and
labels nearby matches. Exact lookup remains first. Exclusions, numeric budgets,
health/dietary constraints and ambiguous multi-family requests are not relaxed by
this fallback. Details include source food family, editorial menu checklist and
selectable related references. Related-list Back restores the original search.
Picking gives a route-specific delivery-app/cafeteria-board next step, never an
order, consumption record, live price or dietary clearance. No guard/model change.

Terminal uses food-specific emoji, table separators and a compact menu→plate→bowl
motif. Keyboard n/p/c/a/d shortcuts retain earlier full commands. Narrow-width
checks now include food detail rendering. A real navigation replay caught a return
state regression during implementation; it was fixed before handoff. A stale
smoke expectation was updated for the new Similar ideas option.

154 unittest tests and 154 pytest tests/145 subtests passed; guard fingerprint, four
mocks, actual navigation replay and bilingual 40-column journeys passed. See
practical-review.md for what the tool achieves and the remaining need for actual
Harold trial and dated campus choices. No feedback or nutritional ranking invented.

## Crayon postcard visual revision

User requested a shorter warmer brotherhood card. Replaced the tray diagram with
a bundled wax-crayon illustration of two fictional male friends eating together,
made with built-in image_gen. Exact prompt and asset provenance are in assets/
postcards/. No real likeness, personal preference or trial feedback is implied.
Runtime remains offline: the PNG is embedded as a data URL in standalone HTML.

Card copy is now a short “Same table, soon.” / “下次，还坐一起。” title plus the
author's unmodified note. Repeated footer and instructional paragraph removed;
small signature/date and optional use link retained. Three saved theme values
remain compatible. Desktop/Chinese/phone actual renders checked; examples updated.
User notes are never silently shortened. Existing escaping/privacy/atomic export
contracts preserved. Full release tests and real-terminal replay repeated below.

Crayon checkpoint verified: 154 unittest/pytest tests, 145 subtests, repository
provenance verification, all four mocks and bilingual real-terminal export replay
pass. Actual desktop and 390px Chinese PNGs were visually inspected.

## v1.0.0 release preparation

Normal mode is now the primary README/download path. New plate-memory.py entry,
macOS start.command and portable start.sh launch without package installation and
without depending on shell working directory. --version reports 1.0.0. Unsupported
Python exits before importing app code; Python 3.10+ is required. Existing personal
records are retained; no demo profile is loaded unless --demo is explicitly chosen.

Release tooling archives committed public Git content, not the working/private
tree. Fresh-archive verification rejects private/unsafe paths, checks version and
provenance, launches real normal mode outside its directory, and runs bilingual
normal-mode synthetic export journeys with app sockets forbidden. Release notes
and a download/backup guide are included. Real Harold trial and DEV publication
remain separate human steps, not prerequisites for using this local app.

Pre-package checks pass: 155 unittest/pytest tests, 145 subtests, unchanged guard
fingerprint, all four mocks, navigation and bilingual actual-terminal replay.
Archive verification and public release publication follow after saving this ref.

## v1.0.0 published

Stable release: https://github.com/Jesse-Zeng423/plate-memory/releases/tag/v1.0.0
Source commit: 96ace12a04c68e109846d5aeac65685e9f1160cf. Public API confirms
isDraft=false and isPrerelease=false; ZIP/checksum/verification assets uploaded.
The ZIP is 9,487,996 bytes and its hosted digest matches the locally verified
SHA-256 4e0d2dd3bfb5a21f9f0d2a0ead23170e514bbf3e493640cfcdcc9cc044fe3b12.
Fresh-archive launch/export verification passed. Both actual shell launchers
report Plate Memory 1.0.0. CI run 37166548415 passed on 3.10/3.12/3.14.
Normal use is the default. No existing private records were reset or packaged.
No DEV publication or real Harold trial has occurred.
