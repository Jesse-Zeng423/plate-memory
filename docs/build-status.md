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

## Current checkpoint: stage 0 structure complete

Current checkout: `/Users/zz/Downloads/plate-memory` (moved from the earlier
`2026 summer intern` parent). Public repository:
https://github.com/Jesse-Zeng423/plate-memory

User approved the text-only offline lunchbox, low-energy meal choices, optional
after-meal check-ins, future-meal postcards and a warmer cafeteria corner. The
story is two high-school friends attending different universities. See
`docs/product-plan.md` for the agreed flow, skip behavior and staged delivery.

Stage 0 extracts terminal output/forms/report/navigation and a shared review
service. Storage no longer depends on CLI; both entry points use the same review
operation. Generic guard, extraction prompt, profile schema and historical
fixtures are unchanged. Original launch commands remain supported. Validation: 86 unittest tests,
86 pytest tests plus 47 subtests, provenance verification and four mock scenarios
passed. No model calls were made for this refactor.

The revised positioning is "That bro who ate with you every day back in high
school." Direct local food search is the default planned entry; menu import is
optional. The next implementation checkpoint is stage 1: versioned public dish
data, checked recipe variants and local retrieval. Stage 2 combines the cafeteria
home, text-only friend pack and complete meal-selection flow. See `docs/data-plan.md`
and product plan v2. No dataset has been downloaded or packaged in this revision. These features are
not yet shipped. Continue from this plan; lack of real preferences does not block
independent implementation with synthetic examples. No background continuation
was started as part of this stage. Inspect the saved automation before resuming
it, since earlier prompts reference the old checkout path and completed CLI scope.

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
