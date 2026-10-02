# Generic engine, one food adapter

`src/guard_decision.py` is the domain-neutral engine copied verbatim from the
public MIT project at the commit and fingerprint in `provenance.json`.
It imports no food adapter, model client, network client or profile reader.
Its API is `decide(payload) -> decision`; stdin/stdout JSON is also supported.
There is no hard-coded ingredient, dish, menu, friend or diet concept in it.

## Neutral input contract

| Concept | Engine field | Meaning |
| --- | --- | --- |
| Context | `current_task` | Current task description |
| Memory item | `candidate_memory` | One candidate record |
| Scope relationship | `relationship` | DIRECT, EXPLICIT_TRANSFER, NO_BRIDGE, SUPERSEDED, CONFLICTING, UNKNOWN |
| Permission | `permission` | ALLOWED, REVOKED, UNKNOWN |
| Evidence status | `evidence_status` | SUFFICIENT, USER_RESOLVABLE, EXTERNAL_REQUIRED, UNKNOWN |
| Risk | `risk` | LOW, MEDIUM, HIGH |
| Proposed action | `proposed_memory_action` | USE, IGNORE, ASK |
| Robust alternative | `robust_action_available`, optional `robust_action` | Whether an action can avoid relying on disputed memory |
| Evidence | `evidence` | Typed evidence with id, text, kind and decisive flag |

The engine rejects unknown keys, invalid enums, provenance-only evidence marked
decisive, and missing required support kinds. It does not authenticate evidence
or independently verify its truth. An adapter is responsible for correctly
deriving these neutral fields from available metadata.

## Output contract

`guard_verdict`, `memory_action`, `memory_state`, `reason_code`,
`resolution_source`, `decisive_evidence`, `next_step`, `boundary`.
All fields are domain neutral. `PASS` means a proposed **memory action** agrees
with the guard recommendation; it does not mean the underlying task is safe.

Precedence remains the upstream implementation: revoked permission; high risk;
external verification; no scope bridge or supersession; medium-risk permission
confirmation; evidenced direct/explicit transfer; resolvable uncertainty;
robust alternative; remaining evidence gap. No stage can be bypassed by model output.

## The only implemented adapter

`src/food_adapter.py` validates local friend metadata and the meal date, derives
weekday applicability and freshness, assigns HIGH risk to allergy records, then
calls `decide`. `src/extraction.py` separately asks local Ollama to extract source
food phrases, one menu line per request. The closed model output is only
`{"foods": ["exact source phrase", ...]}`. Every phrase must occur verbatim in the
original line; invalid or duplicate phrases reject the report.

The food adapter then uses an explicit, limited `FOOD_ALIASES` table to map
source phrases to permitted targets. For example, duck is a candidate for poultry.
A term outside that table uses literal word-boundary matching. Negated mentions
such as cilantro-free become uncertain candidates. This vocabulary matching is
food-specific; it is not the memory applicability decision.

The model never supplies scope, permission, risk, age, evidence classifications,
guard verdicts or actions. It receives only menu text, no profile terms, record IDs,
friend name or policy metadata. The adapter attaches the exact original line as a
quote and returns candidate records with memory_id, line_id, quote and
matched/uncertain. Canned fixtures use this same post-adapter candidate contract.

No-match is always qualified as incomplete detection. Allergy escalation does
not depend on the model finding an ingredient. Revocation has higher precedence
than risk: the record is withheld, while the generic underlying high-risk
boundary remains in the engine's next step.

Future adapters can derive the same neutral payload from another domain.
No second adapter is implemented or claimed here. Future DEV rounds still require
new projects during their own windows and credited reuse; reuse alone does not
establish eligibility.
