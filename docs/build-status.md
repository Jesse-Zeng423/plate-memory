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
