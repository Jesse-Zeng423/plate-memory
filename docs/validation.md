# Validation — October 2, 2026

## Completed locally

- `python3 -m unittest discover -s tests -v`: 69 tests passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`:
  69 tests and 43 subtests passed.
- `python3 scripts/verify_project.py`: guard SHA-256 and package/fixture checks passed.
- `python3 scripts/run_mock_dry_run.py`: all four fingerprint-bound canned scenarios
  passed, launched from an unrelated temporary working directory.
- Core fingerprint: `5873ccb197a6fb19b25a82de98471ad2cc64347b6fcb6a39bb7b8eefd3d772cd`.
- Routine checks used no model and no external API.

## Guided terminal upgrade

- `python3 -m unittest discover -s tests -v`: 83 tests passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`:
  83 tests and 43 subtests passed.
- Project verification and all four canned dry-run scenarios passed again.
- New tests cover private immutable revisions, confirmation versus permission,
  cache grounding/fingerprints, fresh matching after permission changes, guard
  recomputation after date changes, cancelled/failed review invalidation, explicit
  save actions, synthetic demo isolation and terminal control filtering.
- A real pseudo-terminal subprocess ran with local Gemma and the public synthetic
  weekend menu: [evidence](terminal-smoke-v1.json), [ANSI transcript](terminal-live-v1.txt).
  The initial review used inference; the repeated menu used the food-span cache.
  Changing Saturday to Friday changed the weekday memory from IGNORE to USE without
  another extraction. Allergy review stayed visible. No real friend profile or
  real trial is represented by this check.
- Terminal-specific color can be disabled with `--no-color` or `NO_COLOR=1`.
  This is a scrolling, guided interface; no browser or full-screen UI is required.

## Stage 0: structure for the companion roadmap

The terminal was split into presentation, forms, report view and session modules;
scripted CLI and terminal now share `services/review.py`. Bounded file reads and
project paths are independent of the CLI. Launch paths and data formats remain
compatible. No new model inference was necessary for this structural change.

- 86 unittest tests passed; pytest passed 86 tests and 47 subtests.
- Four public demo reports exactly match the historical expected JSON fixtures.
- Absolute terminal launch works from an unrelated temporary directory.
- Unresolved permissions still bypass model extraction and redact records.
- Provenance verification and all four mock dry runs passed.
- Companion features are planned in `product-plan.md`, not implied by these tests.

## Companion step 1: takeout and cafeteria

- 98 unittest tests passed; pytest passed 98 tests and 57 subtests.
- Saved-choice checks cover exact money, unknown metadata, route/keyword filtering,
  Chinese literal names, storage restart, conflict-safe edits/deletes, future schema
  rejection and owner-only file permissions.
- Terminal checks cover no-profile empty state, explicit add, cancel without writes,
  both demo routes, back/switch, session selection versus consumption and plain mode.
- Risk reminders preserve permission precedence. Historical-menu review requires
  external verification through an ephemeral profile copy; the original profile is
  unchanged and revoked records remain withheld.
- [Real pseudo-terminal run](companion-smoke-v1.json) exercised the synthetic
  companion flow with [captured output](companion-terminal-v1.txt). No AI calls or
  real-person data were used in this run. It is not a Harold trial.
- Guard fingerprint verification and four original mock scenarios passed.
- Public catalog/free-text query parsing, friend-pack import, journal and postcard
  export are planned follow-ups, not covered as implemented features by these checks.

## Actual local inference

[Final smoke checkpoint](local-smoke-v11.json) records Gemma 3 4B, prompt version
10, and the current source phrase extraction architecture. All four synthetic
menus produced the expected guard verdict/action pairs. Eight generation requests
were made (one per menu line), plus local model metadata checks. The record also
applies the **same** weekend extraction to Friday to demonstrate that the date,
not another model judgment, changes the weekday rule.

The complete CLI was separately exercised with the real local model, not a canned
fixture: [transcript](live-cli-v1.txt), [rendered transcript image](demo.png).
No cloud inference was used. Ollama 0.34.3 ran with `OLLAMA_NO_CLOUD=1`, bound to
127.0.0.1. Downloaded model ID: `a2af6cc3eb7f`, approximately 3.3 GB of weights.
Hardware: 8 GB Apple Silicon Mac. Cold loading and laptop load can change latency;
final smoke scenarios took about 21s, 3.8s, 4.5s and 4.4s in that run.

## Earlier extraction failures, preserved

Versions v1, v3, v4, v5 and v7 asked the small model to match target concepts or
labels more directly. They produced extra candidates, source errors or malformed
pair coverage. The v2 rejection is separately recorded. Diagnostic v6 showed
plain textual concept recognition worked; v8 still showed a false-positive concept
match. Diagnostic v9 correctly extracted source food words. Final v10/v11 use
source phrase extraction with a deterministic, limited food vocabulary adapter.

These old checkpoint files are preserved without rewriting them. In v7/v10,
`generation_calls` counted scenario invocations, not individual HTTP generations;
that historical metadata is inaccurate for request accounting. v11 uses separate
scenario and generation-count fields. v11 completed four scenarios/eight requests.
The earlier experiments are development traces, not a controlled accuracy study.

## Hosted verification

[GitHub Actions run 36969923732](https://github.com/Jesse-Zeng423/plate-memory/actions/runs/36969923732)
passed on Python 3.10, 3.12 and 3.14 for implementation commit `d4c410c`.
All matrix jobs ran unittest, package verification and the canned dry run.
The guided terminal upgrade at `1ab23cb` also passed the full Python matrix:
[GitHub Actions run 37051337645](https://github.com/Jesse-Zeng423/plate-memory/actions/runs/37051337645).
This validates the hosted checks; it does not validate real-world menu accuracy.

## Still requires a human

Harold's actual dietary preferences, a real meal-planning problem and usability
trial feedback have not been provided. All committed profiles/menus are synthetic.
DEV draft follows the official template; publication/submission has not occurred.

## Boundaries

Passing these checks does not estimate real-world extraction accuracy or establish
medical safety. Source phrases can be omitted, vocabulary mappings are incomplete,
menus can hide ingredients, and cross-contact is not assessed. The generic guard
validates structure/precedence, not the truth of manually supplied metadata.
