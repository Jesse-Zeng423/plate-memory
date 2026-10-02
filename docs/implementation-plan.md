# Implementation plan v1 — takeout and campus cafeteria

October 2, 2026. This is the executable roadmap for the latest user requirements.
Positioning: **That bro who ate with you every day back in high school.**
Cooking instructions, kitchen equipment and meal preparation are out of scope.
Status at the start of this iteration: shared review service/refactor complete;
steps 1–6 now have runnable checkpoints recorded in `build-status.md`.
Step 2’s starter coverage and verified-menu personalization boundary are documented
below; expanded coverage remains future work.

## Product flow and dependencies

Home is a warm cafeteria corner. The completed product has four destinations:
today's meal, a text-only lunchbox from a friend, optional meal check-ins and a
postcard for the next shared meal. Ship only functioning routes at each checkpoint.
Saved choices and the original menu-review commands remain visible alongside
the four completed primary destinations.

```text
Today → too tired / up for a walk
           ↓              ↓
        delivery        cafeteria
                 ↓
    optional food/place keyword (later: natural-language query)
                 ↓
    at most three actual saved choices / later public dish ideas
                 ↓
  choose / refine / inspect a menu / add a saved choice / back
                 ↓
  selected plan only → optional explicit meal record in step 4
```

A route is needed to filter the current choice. Cancel always returns home.
Food/place keywords are optional. Saving a place, setting up a dietary profile,
recording a meal, symptoms and sharing are optional. An unresolved permission or
preference can be skipped, but stays unresolved. Missing prices, walk times,
current stock, opening hours and ingredients stay unknown.

The app does not claim to order delivery, locate nearby cafeterias or know today's
menu. It compares saved references and public dish ideas, and makes that status
visible. A selected plan is never automatically marked as eaten.

## Code structure

Existing unchanged contracts:
- `guard_decision.py`: neutral deterministic applicability engine, exact upstream copy.
- `food_adapter.py`, `extraction.py`: existing source-grounded menu extraction/review.
- `services/review.py`: shared original CLI and terminal review operation.
- `profile_store.py`: existing profile-v1 validation and private revisions.

Step 1 additions:
- `domain/meals.py`: saved-meal schema and validation; CAD prices stored as integer
  cents, explicit date for known price, optional last-seen date and walk time.
- `storage/meal_store.py`: versioned private SQLite store, bounded records,
  transactions and revision checks for edit/delete; an in-memory store in demo.
- `services/meal_choices.py`: deterministic route/keyword shortlist from saved
  facts; never guesses constraints or applies dietary preferences without guard.
- `ui/prompts.py`: cancellable prompts and a distinct cancellation exception.
- `ui/home.py`: warm ASCII table, active routes and optional decoration settings.
- `ui/meal_flow.py`: two-route selection, browse/refine/back, explicit selection.
- `ui/saved_flow.py`: add/edit/delete saved meals with preview and explicit save.
- `examples/saved-meals-v1.json`: unmistakably synthetic reference choices.
- `ui/session.py`: composes the flows, owns session-only selected plan and database.
- `terminal.py`: preserves launch arguments and adds a plain/decor control if needed.

Future modules are created when their step is implemented, not empty placeholders:
- Step 2: `catalog/{schema,index}.py`, `services/search.py`, public pack manifest.
- Step 3: `domain/friend_pack.py`, `services/friend_pack.py`, `ui/lunchbox_flow.py`.
- Step 4: `domain/checkin.py`, `storage/journal_store.py`, `ui/checkin_flow.py`.
- Step 5: `services/postcard.py`, `ui/postcard_flow.py` and explicit export schema.

## Implemented step-1 interfaces

```python
validate_meal(value: dict) -> dict
parse_price(text: str) -> int  # exact CAD cents

MealStore(path=None)  # None gives an isolated in-memory database
MealStore.list() -> list[tuple[dict, int]]  # meal + revision
MealStore.save(meal, expected_revision=None) -> int
MealStore.delete(meal_id, expected_revision) -> None
MealStore.close() -> None

shortlist(rows, route, query="", limit=3) -> list[tuple[dict, int]]
guard_reminders(profile, meal_date) -> list[dict]
recorded_menu_profile(profile) -> dict  # ephemeral verification context

choose_meal(screen, store, review=None, reminders=()) -> dict | None
manage_choices(screen, store) -> None
```

`Session` owns the store and selected idea. The launcher closes the store on normal
exit, Ctrl+D and errors. A demo store is seeded lazily from the synthetic fixture;
first real browsing does not create a database until a choice is saved. Store
revision checks prevent a second window from silently clobbering an edit.

## Private saved-meal contract v1

Store next to the selected profile as `<profile-stem>-meals.sqlite3`. Profiles in
separate paths do not accidentally share saved meals. Default file remains inside
ignored `private/`; files are owner-only on POSIX, not encrypted. Demo uses memory
only and cannot write a real saved-meal file.

A meal contains: stable ID, name, venue (may be unknown), route (`delivery` or
`cafeteria`), price in CAD cents + recorded date (both present or both absent),
optional last-seen date, optional walk minutes for cafeteria only, and optional
menu text transcribed by the user. A revision number is storage metadata.

Venue and dish names do not prove availability. Menu text is historical input;
when used for guard review the result labels it as recorded information. No
synthetic sample becomes a real profile record. No ratings/health observations
silently affect ranking. Save, edit and delete use explicit user actions; stored
meal updates do not change profile permissions or confirmation dates.

SQLite user_version guards schema compatibility; unknown future versions fail
without trying to rewrite them. Updates compare expected revision. Deletes remove
the app record; do not claim to erase OS backups or forensic traces. No cloud sync.

## Step-by-step delivery

### 1. Two routes, personal saved choices, welcoming home

Implement schemas/store first, then shortlist service, then prompts/UI and session
wiring. Keep old menu review accessible, with guard interpretation unchanged.
Empty first run allows adding a choice or browsing a synthetic demo, without
forcing a profile or fabricating restaurants. First shortlist is a literal
food/place lookup, clearly not yet free-form AI search or dietary clearance.

Acceptance: choose each route; a no-match prompt accepts the next free-text term
without requiring a `refine` command; create/edit/delete a choice; restart and retrieve
it; show historic price date and unknown availability; back/cancel does not save;
selection does not record consumption; demo never touches real data. Concurrency
conflicts reject stale edits. Four original reports and guard fingerprint pass.

### 2. Local public dish discovery and guard-aware candidates

Build a bounded attributed Wikidata CC0 dish/alias/cuisine subset; ship checked
counts, sources and hashes. No recipe instructions. Public ideas and known personal
places are separate result types. Exact/alias search first; local Gemma gets a
new source-span-constrained query parser only for free text. Validate negation,
ambiguous variants, candidate IDs and explicit session constraints. Unknown facts
cannot become hard filters or confirmed memories. Search sends no private profile
or journal to the model. No runtime external API.

Personalization always consults guard. Catalog-typical ingredients are reference
facts, not the user's restaurant recipe; unknown preparation cannot be presented
as safe. Provide same-flow preference confirmation and recomputation. If the user
has no profile, discovery is explicitly unpersonalized. Model failure offers an
explicit literal-search path. Keep the original extraction prompt/fixtures intact.

Acceptance: English/Chinese aliases, both routes, no-hit recovery, negation,
revoked/stale preferences, unknown actual ingredients, offline synthetic run.

### 3. Text lunchbox and cafeteria corner

Implement bounded versioned friend-pack JSON, text previews and explicit import.
Preserve attribution; all sender text is user-authored. Gift contents are messages
and remembered/shared dishes, not recipe instructions or authorized preferences.
Imported control characters are sanitized at display. No executable archive or
implicit URL fetch. Decorations respect terminal width, no-color/plain modes.

Acceptance: safe import/reject malformed/duplicate fields, genuine sender labels,
no dietary permission side effects, fully isolated synthetic demonstration.

### 4. Optional after-meal check-in

Explicitly log an actual meal; optional taste, fullness, comfort and free text.
Keep check-ins separate from meal selections and preference memory. Skipped fields
stay null. Offer browse/edit/delete with honest local retention behavior; report
only observed counts, not causal diagnoses or guessed missing meals.

Acceptance: skip any field/whole flow, no accidental meal log, no automatic
preference creation, restart/history and deletion paths, private schema version.

### 5. Until our next meal and final flow polish

Build a postcard from explicitly chosen fields with preview then local export.
Exclude symptom, permission and full-history data by default. User sends the file
using existing chat tools. Add back/skip consistency, narrow-terminal checks and
a complete synthetic demo. Collect actual Harold feedback before filling article
trial claims. No automatic DEV publication.

## Execution rules

Each step ends in a runnable checkpoint with docs explaining what is shipped and
what remains. Required local checks: unittest, pytest, package verification and
mock dry run. Model smoke tests only when changed model integration warrants it,
using synthetic public inputs with separate evidence versions. No modification of
frozen research or historical checkpoints. Update `build-status.md` as the resume
point. An old automation prompt must be updated before resuming background work.

## Step 2 implementation clarification

Checkpoint ships 13 sourced concepts rather than the provisional 100–200 target.
Cuisine/ingredient facts stay absent pending verification. Literal/alias discovery
and optional confirmed local query spans are implemented. Guard-aware notes and
actual-menu review provide confirmation/recomputation; personalized ranking awaits
actual menu facts. No catalog result implies an ingredient or preference clearance.
These conservative boundaries are deliberate, and described in README/build status.

### 6. Final user-facing copy and low-friction walkthrough

Walk the entire app from the perspective of a hungry friend. Keep the primary meal
route prominent, optional steps skippable and each next action clear. Use short,
warm language; move technical detail to inspectable detail views. Retain essential
ingredient/allergy uncertainty at the decision point without repeating paragraphs.
Check empty account, demo, cancellation, narrow terminal and unsupported queries.
Acceptance: a first-time user can pick a food idea without profile setup, import,
logging, AI setup or knowing command names; optional destinations stay parallel.

Step 6 is implemented and validated; see README for the shortest first-run path
and build-status for tests, synthetic terminal evidence and remaining limits.
