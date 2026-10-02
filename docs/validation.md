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

GitHub Actions across Python 3.10, 3.12 and 3.14: pending first push/run.

## Still requires a human

Harold's actual dietary preferences, a real meal-planning problem and usability
trial feedback have not been provided. All committed profiles/menus are synthetic.
DEV draft follows the official template; publication/submission has not occurred.

## Boundaries

Passing these checks does not estimate real-world extraction accuracy or establish
medical safety. Source phrases can be omitted, vocabulary mappings are incomplete,
menus can hide ingredients, and cross-contact is not assessed. The generic guard
validates structure/precedence, not the truth of manually supplied metadata.
