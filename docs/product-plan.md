# Product plan: that bro from high school

Current implementation: four destinations, bilingual startup, 3,535-record offline
reference catalog, retained draft navigation and visual local exports. The
first-checkpoint descriptions below are historical sequencing; current behavior
and friend instructions are in [start-here.md](start-here.md).

Positioning: **That bro who ate with you every day back in high school.**
Welcome: **给你留了个座 / Saved you a seat.** Project name: Plate Memory.

The friend mainly gets takeout or eats at a university cafeteria. Cooking,
kitchen equipment and meal preparation are outside this version. This document
supersedes the cooking-oriented flow in earlier Git revisions. Code structure and
exact delivery order live in [implementation-plan.md](implementation-plan.md).

## Product structure

The home scene is a small cafeteria corner with two places at a table. The complete
product has four destinations in a consistent order:

1. **今天吃什么 / Today's meal:** the daily primary action.
2. **离线饭盒 / From your friend:** real user-written text and remembered/shared dishes.
3. **吃得还好吗 / How was that meal?:** optional private after-meal observations.
4. **下周再一起吃 / Until our next meal:** explicitly selected postcard content.

Preferences, saved choices, appearance, demo and technical details support those
flows. Only implemented routes are interactive. The first checkpoint exposes
Today's meal, Your usuals and all original menu-review commands; the other three
companion destinations remain planned.

## Short daily flow

```text
How are you doing today?
  Too tired → delivery
  Up for a walk → cafeteria
              ↓
   Optional dish/place keyword
              ↓
   Up to three saved choices
   Later: also public dish ideas from a local catalog
              ↓
   Select / refine / change route / add / review a menu / back
              ↓
   Session-only idea (not ordered, not recorded as eaten)
              ↓
   Later: optional actual-meal log, check-in and postcard
```

The first checkpoint searches literal dish/place keywords. Free-form AI search and
public catalog discovery come in step 2; they are not implied by the current input.
Exact-name discovery does not require a dietary profile. Current availability,
opening hours, delivery fees and prices are unknown unless the user supplies them;
historical values keep their dates and are not current provider facts.

## Questions and skip behavior

- Choosing delivery or cafeteria is needed to filter a meal flow. Back returns home.
- Dish/place keyword, price, last-seen date, venue, cafeteria walk time and recorded
  menu description are optional. Unknown fields remain unknown.
- A saved choice needs a name and route. If price is supplied, its observation date
  is needed; the user can instead omit the price. Save is explicit.
- A selected idea is not a meal log. Recording consumption requires another explicit
  action when that feature is built.
- Dietary setup can be skipped for discovery. It cannot be skipped into an implicit
  claim of dietary suitability. Saved-choice browsing does not apply preferences.
- Baseline guard risk/permission reminders stay visible during browsing. Menu review
  is explicit; a historical recorded menu additionally requires verification of
  current preparation. Context changes clear prior reports.
- Unknown permission, old preferences and uncertain ingredients can be answered
  later but cannot become confirmed by skipping. Allergy escalation remains visible.
- Future check-in fields are independently optional. Missing data is not "comfortable".
- Letters, decoration, journals and postcards never block choosing a meal.

## Local information boundaries

Personal saved meals contain the user's own places and dishes. Price and walk-time
are recorded facts with missing/uncertain status, not generated estimates. This is
more useful to the first daily loop than a huge recipe collection.

The later public catalog contains dish names, aliases, cuisine and cautiously
attributed typical-ingredient information. It supplies ideas to look for, not a
claim a cafeteria or restaurant currently offers them. See [data-plan.md](data-plan.md).
Model extraction stays local and returns candidate information only. Confirmed
context and the generic guard govern later personalization and fixed-rule ranking.

A friend pack contains authentic sender text; imported text never impersonates a
live friend or creates dietary permission. No audio is planned. Personal journal
observations stay separate from approved preference memories. Postcard export
includes only previewed fields, excluding symptoms and full histories by default.
No external APIs, automatic messaging, cloud sync or DEV publication.

## Visual direction

Warm amber headings, leaf-green completion messages and an accent for the two-bowl
ASCII table. Function labels remain readable without color. The `--plain` option
removes decoration and colors; `--no-color` retains artwork. Avoid emoji-dependent
column alignment and mandatory animation. Returning after an absence never incurs
a penalty or a broken-streak warning.

A genuine high-school memory, a sender's note and details of the recipient's life
must come from the people involved. All committed personal examples remain clearly
synthetic. Actual Harold trial feedback is still pending.

## Shipped and next

- Stage 0: separate CLI, terminal UI, services and persistence — complete.
- Step 1: two-route personal saved-choice flow and warm home — implemented; see
  build status for validation.
- Step 2: local public dish data, aliases/free-text retrieval and guard-aware choices.
- Step 3: text lunchbox and expanded cafeteria corner.
- Step 4: optional meal journal.
- Step 5: preview/export postcard and final usability handover.
