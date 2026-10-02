# Plate Memory

- New Hacktoberfest project; keep actual commit timestamps. Deadline: 2026-10-05 02:59 EDT.
- `src/guard_decision.py` is a verbatim MIT upstream copy. Check `docs/provenance.json`; adapt in `src/food_adapter.py`.
- Model output is untrusted candidate extraction only. Permission, scope, freshness, risk and guard verdicts come from Python and validated local metadata.
- Never send revoked or unknown-permission memory text/terms to the model. No cloud models, tools, API keys or remote inference endpoints.
- Only synthetic profiles/menus may be committed. Real profiles belong in ignored `private/`.
- Harold is Jesse's friend and roommate from high school, and a big foodie. His specific preferences and trial feedback are not supplied; never invent them.
- No formal guard skill is created or installed. No DEV publishing without final user instruction and completed factual placeholders.
- Active CLI lives in `src/`; defaults resolve from project root. Explicit absolute paths remain absolute.
- Run `python3 -m unittest discover -s tests -v`, `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider`, `python3 scripts/verify_project.py` and `python3 scripts/run_mock_dry_run.py` before handoff. Routine tests never call a model.
- Real model smoke tests use only synthetic public fixtures and are separately documented. Do not modify the original research repo or its frozen artifacts.

## Companion implementation

- Product: That bro who ate with you every day back in high school.
- Primary routes: too tired => delivery; up for a walk => campus cafeteria. No cooking workflow.
- Follow docs/implementation-plan.md and update docs/build-status.md at runnable checkpoints.
- Saved choices are historical references, not live stock/prices or dietary clearance.
- Selection is not consumption; future check-ins never silently become preference memories.
- Synthetic companion demos use an in-memory store. Private meal databases stay ignored.
