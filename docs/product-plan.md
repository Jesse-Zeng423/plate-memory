# Product plan v2: that bro from high school

Status: revised product and data direction, October 2, 2026. Stage 0 refactor is
implemented. Stages 1–5 below are planned work, not shipped features. This revision
makes direct local search the default and moves dataset work ahead of new UI flows.

## Purpose and voice

Built for two friends who shared a high-school cafeteria and now attend different
universities. The product brings a little of that everyday friendship into choosing
a meal, noticing how it felt, and deciding what to share with each other.

Official positioning supplied by the user: **that bro who ate with you everyday
back when highschool.** Edited English for product copy: **That bro who ate with
you every day back in high school.** Chinese: **高中时每天陪你吃饭的那个兄弟。**

Keep **给你留了个座 / Saved you a seat** as the welcome line and Plate Memory as
the project name. This is a personal gift with useful meal support. Actual friend messages are
written by the sender, attributed to them, and displayed verbatim. No synthesized
voice, invented shared memory, or model impersonation of the friend.

Only known background belongs in public copy. Real dietary records, body-comfort
reports, university details and actual private letters belong in local private
storage; public demonstrations use labeled synthetic examples.

## Existing product

Already implemented: pasted-menu extraction through local Ollama; source-grounded
food matching; deterministic memory applicability; scope/date/freshness/permission
checks; allergy escalation; readable dish rows and raw explanations; guided local
profile editing; confirmation/revocation; private revisions; grounded extraction
cache; explicit offline synthetic demonstrations; scripted CLI/JSON interface.

Not yet implemented: proactive meal recommendations, positive preference ranking,
a meal catalog, energy/equipment choices, friend packs, after-meal journaling,
postcard export, cafeteria decoration or a new onboarding flow.

## Four equal destinations, one everyday primary action

The cafeteria corner is the home scene, not a fifth destination or a compulsory
activity. It contains four consistently ordered destinations:

| Destination | Purpose | Entry/exit contract |
| --- | --- | --- |
| 今天吃什么 / A meal for today | Primary daily action: say what you want and retrieve local options | Start here directly; return to the table from every step |
| 离线饭盒 / From your friend | Read a letter, browse shared dishes, import a text-only gift | Independent of recording meals or creating a dietary profile |
| 吃得还好吗 / How was that meal? | Optional taste, fullness and body-comfort journal | Enter independently or after a chosen meal; each field can be skipped |
| 下周再一起吃 / Until our next meal | Compose a postcard or an invitation to eat together | Preview and explicitly export a file; sender shares it themselves |

Below the four destinations: preferences, appearance/privacy settings, sample demo
and quit. Technical details belong inside a completed review, not as a top-level
peer of the main product features. Existing typed commands remain as shortcuts.
Only implemented routes become interactive; do not show buttons that pretend to
work. During staged delivery, keep shipped functionality discoverable.

```text
                    食堂一角 / Saved you a seat
                      [two places at a table]

   1 今天吃什么                  2 离线饭盒
     Choose this meal              A letter and familiar dishes
   3 吃得还好吗                  4 下周再一起吃
     A moment to notice            Something you choose to share

          Preferences    Appearance & privacy    Demo    Quit
```

## First visit

1. Welcome to the table. Optional alias and optional friend-pack import.
2. Offer a short free-text meal prompt or "Explore a sample" immediately. No menu
   import, catalog construction or mandatory multi-question setup before search.
3. Offer dietary setup without blocking the rest of the app. Skipped setup means
   no personalized constraints are known; it must never imply none exist.
4. Ask for each preference's meaning and permission when it is actually added.
   A sender's gift must never become the receiver's approved dietary profile.

Profile-less browsing requires explicit implementation in stage 2. The current
v1 engine profile still requires at least one memory; do not fake an empty profile
with an invented preference just to satisfy that schema.

## Main daily flow

```text
A meal for today → "What sounds good?" (or "Help me choose")
  Examples: "想吃面，只有微波炉" / "有什么鸡蛋能做的" / "biryani"
                               ↓
       exact names and aliases + optional local candidate extraction
                               ↓
             local dish index → checked recipe variants
                               ↓
       show understood constraints; ask only a material missing question
                               ↓
       applicable confirmed preferences → deterministic candidate ranking
                               ↓
      up to three options with source, match reasons and missing information
                               ↓
          choose / refine / inspect / optionally add an actual menu
                               ↓
           optional meal log → optional check-in → table
```

The default action retrieves a locally packaged knowledge snapshot. The user never
needs to assemble that database or import a restaurant menu before searching.
"I have a menu" remains a secondary action for checking a specific real-world
choice. "I already ate" goes directly to the optional journal. Exact-name lookup
can work without model inference; free-text queries use the installed open-weight
model only for bounded candidate extraction and matching. Personal policy still
comes from explicit metadata and the guard.

For an ambiguous name, show a short variant choice. For a missing dish, acknowledge
the local coverage gap and offer a nearby category, another query, or a private
user note. Never silently make up an authoritative recipe. The proposed curated
starter pack and data sources are detailed in `data-plan.md`.

The energy choices are "almost none", "about ten minutes", and "up for cooking".
Energy describes effort, not a medical measurement. Available equipment must be
known before claiming a recipe is feasible; otherwise show the equipment required
and ask the user to confirm it. No hidden assumption that someone has a stove.

| Step | Can skip? | Result of skipping |
| --- | --- | --- |
| Greeting, friend's message, decoration | Yes | Continue immediately |
| Alias and friend-pack import | Yes | Use a neutral local session |
| Meal date | Accept visible "today" default | Date remains editable |
| Free-text query or "Help me choose" | One starting action is needed | No menu import required; return home if cancelled |
| Model-parsed constraints | Can correct or skip | Unconfirmed interpretation never silently becomes a saved preference |
| Energy, time, budget | Yes | No claim of matching an unspecified limit |
| Equipment | May leave unknown | Show required equipment; feasibility remains unconfirmed |
| Remembered dietary profile | Yes, after stage 2 | Browse unpersonalized options with that status visible |
| Permission to use a memory | Answer later allowed | Withhold that memory, never silently allow it |
| Stale/uncertain preference question | Answer later allowed | Keep unresolved; do not convert ASK to USE |
| Allergy/preparation verification | May leave unresolved | Preserve review-needed status on affected results |
| Selection or meal logging | Yes | A recommendation is not evidence the user ate it |
| Taste/fullness/body-comfort check-in | Each field optional | Missing stays missing; never impute "comfortable" |
| Postcard | Yes | Nothing exported or transmitted |

Ask one meaningful question per step; show back/skip/cancel wherever applicable.
Keep earlier answers when going back within an unfinished flow. Recompute results
when context changes. Confirmation uses the actual confirmation date; permission
and confirmation remain separate actions. A declined question should not reappear
repeatedly during the same meal flow.

## Feature details

### Text-only offline lunchbox

A bounded, versioned local document with sender label, letter and optional recipe
cards. Import parses data only: no executable content, archive extraction, remote
fetching or active terminal escape sequences. Preview before saving. Importing a
recipe does not mark it nutritionally suitable or authorize a dietary preference.
Only user-written text appears as the friend's message. Remembered cafeteria meals
must be supplied by the people involved; all shipped examples are synthetic.

### Local discovery and low-energy meal choices

A broader dish-name/alias/cuisine index supplies discovery; typical ingredient
relationships remain reference information, not evidence of a particular serving.
Separate concrete recipe variants support actionable cooking recommendations.
Runtime search is local; public sources are processed during development into
versioned distributable packs. See `data-plan.md`.

A small curated offline recipe catalog with ingredients, steps, equipment, estimated prep
time and provenance. Model extraction remains limited to grounded candidates.
Food adapter and fixed ranking rules provide explanations. Positive likes will
need a versioned preference representation; existing avoid-records must retain
their meaning during migration. Unknown prices and missing nutrition stay unknown.
User-supplied prices show their dates. No generated precision about calories,
restaurant quality or suitability for digestive symptoms.

### Optional after-meal journal

Store actual selected/entered meal, timestamp, optional taste/fullness/body comfort
and optional user note. Keep observation records separate from approved memories.
Trends describe recorded events and missing coverage; they cannot assert causation,
diagnose, or automatically create exclusions. A separate explicit user action can
turn an observation into a preference. Deletion must account for related records
and private revisions; do not promise deletion while keeping an undisclosed copy.

### Until our next meal

Previewable plain-text postcard first: one meal, one message, optional invitation.
Use explicit inclusion, not a dump of the journal. Exclude body-comfort fields,
profile metadata and complete history by default. Export does not send anything
or reveal whether the other friend is online. A future imported reply is also
an attributed local document, never live presence.

### Cafeteria corner

Two places at a table, a bowl, a noticeboard and text from a real friend. Warm amber,
peach and leaf accents, configurable decoration density and a plain-output mode.
Decorations may unlock through collecting dishes or writing a note, not through
food scores or uninterrupted streaks. No punishment for absence. Narrow terminal,
non-color output, Unicode width and reduced motion need explicit presentation
checks. Do not rely on emoji width for column alignment.

## Architecture after stage 0

```text
src/terminal.py                 Stable launch arguments and error boundary
src/cli.py                      Scripted input/output and JSON interface
src/ui/screen.py                Safe terminal output and prompts
src/ui/forms.py                 Preference forms
src/ui/review_view.py           Human-readable menu review
src/ui/session.py               Current navigation and interaction
src/services/review.py          Shared validated review operation
src/paths.py, file_io.py        Source-relative paths and bounded reads
src/demo.py                     Fingerprint-bound synthetic fixtures
src/profile_store.py           Private profile persistence and revisions
src/food_cache.py               Grounded food phrases only
src/food_adapter.py             Food-specific facts → neutral guard inputs
src/extraction.py               Local model, candidate extraction only
src/guard_decision.py           Unchanged generic decision engine
```

UI imports application services; services never import UI or an entry point.
Storage never imports CLI. Both entry points use the same review service.
New features will get services and small UI flows when implemented, rather than
empty scaffolds for every planned module. New local data types have independent
schema versions: friend pack, meal context/catalog, journal and postcard.
The profile-v1 schema, historical fixtures and generic engine fingerprint are
preserved by this refactor. Do not merge all private data into one profile JSON.

## Delivery stages and acceptance

0. **Structure — implemented this iteration.** Extract UI responsibilities and
   review service; decouple file reads from CLI; preserve old launch commands,
   canned reports, profile storage and guard behavior. Regression checks pass.
1. **Public data and local retrieval.** Define the dish/recipe/provenance schemas,
   build a bounded CC0 source subset plus original checked recipe cards, package
   the first version with the app, and implement name/alias/ingredient lookup.
   Target 100–200 dish concepts and 30–50 practical variants only if each clears
   the data review; these are goals, not current inventory or a coverage claim.
   Check real mixed-language query examples and package/license completeness.
2. **A welcoming table and a complete meal flow.** Build the cafeteria home,
   text-only lunchbox and direct query entry. Support profile-less browsing,
   optional energy/equipment constraints, explainable candidates and same-flow
   confirmation/recalculation. Original pasted-menu review becomes an optional
   detail action. Model extraction gets its own query schema and prompt; preserve
   the existing menu-extraction prompt. A new preference meaning needs explicit
   schema versioning and migration before use.
3. **How was that meal?** Optional private journal and simple factual history;
   cancellation, missing fields, edits/deletion and permission boundaries work.
4. **Until our next meal.** Select contents, preview, export a text postcard, then
   return home. Private symptom/permission/history data do not leak into exports.
5. **Polish and handover.** Decor density, narrow terminal/keyboard flow, synthetic
   end-to-end demonstration and real Harold trial. Write actual feedback only
   after that trial; update the English challenge draft from verified outcomes.

Each stage is a reviewable checkpoint with a runnable entry point and a clear list
of shipped versus remaining features. Deadline tradeoffs favor one complete meal
flow and a real friend-authored message; do not claim unfinished routes work.
