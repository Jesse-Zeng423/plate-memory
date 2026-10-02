#!/usr/bin/env python3
"""Deterministic decision support for structured memory-applicability audits."""

from __future__ import annotations

import json
import sys
from typing import Any


__version__ = "1.1.0"

PERMISSIONS = {"ALLOWED", "REVOKED", "UNKNOWN"}
RELATIONSHIPS = {"DIRECT", "EXPLICIT_TRANSFER", "NO_BRIDGE", "SUPERSEDED", "CONFLICTING", "UNKNOWN"}
EVIDENCE_STATUSES = {"SUFFICIENT", "USER_RESOLVABLE", "EXTERNAL_REQUIRED", "UNKNOWN"}
RISKS = {"LOW", "MEDIUM", "HIGH"}
MEMORY_ACTIONS = {"USE", "IGNORE", "ASK"}
EVIDENCE_KINDS = {"MEMORY_SOURCE", "APPLICABILITY", "PERMISSION", "CURRENT_EXTERNAL", "USER_STATEMENT"}
REQUIRED_FIELDS = {
    "current_task",
    "candidate_memory",
    "proposed_memory_action",
    "permission",
    "relationship",
    "evidence_status",
    "robust_action_available",
    "risk",
    "evidence",
}
OPTIONAL_FIELDS = {"robust_action"}
# Presence/type checks only: these do not verify the evidence text or its age.
CLAIM_SUPPORT = {
    "permission": {"REVOKED": {"PERMISSION", "USER_STATEMENT"}},
    "relationship": {
        "DIRECT": {"APPLICABILITY", "USER_STATEMENT"},
        "EXPLICIT_TRANSFER": {"APPLICABILITY", "USER_STATEMENT"},
        "SUPERSEDED": {"APPLICABILITY", "USER_STATEMENT", "CURRENT_EXTERNAL"},
    },
}
BOUNDARY = "Research-informed decision-support prototype; not production validated; no autonomous execution or high-risk approval."


class InputValidationError(ValueError):
    """Raised when a guard input violates the closed input contract."""

    code = "INPUT_VALIDATION_ERROR"


class SemanticConsistencyError(InputValidationError):
    """Raised when classifications lack the required decisive evidence kinds."""

    code = "SEMANTIC_CONSISTENCY_ERROR"


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_enum(payload: dict[str, Any], field: str, allowed: set[str], errors: list[str]) -> None:
    value = payload.get(field)
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{field} must be one of {sorted(allowed)}; got {value!r}")


def validate_input(payload: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        raise InputValidationError("input must be a single JSON object")
    keys = set(payload)
    missing = sorted(REQUIRED_FIELDS - keys)
    unknown = sorted(keys - REQUIRED_FIELDS - OPTIONAL_FIELDS)
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
    if unknown:
        errors.append(f"unknown fields: {', '.join(unknown)}")
    if not _nonempty_string(payload.get("current_task")):
        errors.append("current_task must be a non-empty string")
    if not _nonempty_string(payload.get("candidate_memory")):
        errors.append("candidate_memory must be a non-empty string")
    _validate_enum(payload, "proposed_memory_action", MEMORY_ACTIONS, errors)
    _validate_enum(payload, "permission", PERMISSIONS, errors)
    _validate_enum(payload, "relationship", RELATIONSHIPS, errors)
    _validate_enum(payload, "evidence_status", EVIDENCE_STATUSES, errors)
    _validate_enum(payload, "risk", RISKS, errors)
    if not isinstance(payload.get("robust_action_available"), bool):
        errors.append("robust_action_available must be a boolean")
    robust_action = payload.get("robust_action")
    if payload.get("robust_action_available") is True and not _nonempty_string(robust_action):
        errors.append("robust_action must be a non-empty string when robust_action_available is true")
    if payload.get("robust_action_available") is False and robust_action is not None:
        errors.append("robust_action must be absent or null when robust_action_available is false")

    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must be a non-empty array")
    else:
        seen: set[str] = set()
        required_evidence = {"id", "text", "kind", "decisive"}
        for index, item in enumerate(evidence):
            prefix = f"evidence[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            item_keys = set(item)
            if item_keys != required_evidence:
                errors.append(f"{prefix} fields must be exactly {sorted(required_evidence)}")
            evidence_id = item.get("id")
            if not _nonempty_string(evidence_id):
                errors.append(f"{prefix}.id must be a non-empty string")
            elif evidence_id in seen:
                errors.append(f"duplicate evidence id: {evidence_id}")
            else:
                seen.add(evidence_id)
            if not _nonempty_string(item.get("text")):
                errors.append(f"{prefix}.text must be a non-empty string")
            if not isinstance(item.get("kind"), str) or item.get("kind") not in EVIDENCE_KINDS:
                errors.append(f"{prefix}.kind must be one of {sorted(EVIDENCE_KINDS)}")
            if not isinstance(item.get("decisive"), bool):
                errors.append(f"{prefix}.decisive must be a boolean")
            if item.get("kind") == "MEMORY_SOURCE" and item.get("decisive") is True:
                errors.append(f"{prefix}: MEMORY_SOURCE cannot be decisive applicability evidence")
    if errors:
        raise InputValidationError("; ".join(errors))
    return payload


def validate_consistency(payload: dict[str, Any]) -> dict[str, Any]:
    """Check a structurally valid payload and report all support violations."""
    decisive_kinds = {item["kind"] for item in payload["evidence"] if item["decisive"]}
    errors: list[str] = []
    for field, claims in CLAIM_SUPPORT.items():
        value = payload[field]
        required_kinds = claims.get(value)
        if required_kinds is not None and not decisive_kinds.intersection(required_kinds):
            errors.append(
                f"{field}={value} requires decisive evidence of kind "
                + " or ".join(sorted(required_kinds))
            )
    if payload["evidence_status"] == "EXTERNAL_REQUIRED" and "CURRENT_EXTERNAL" in decisive_kinds:
        errors.append(
            "evidence_status=EXTERNAL_REQUIRED cannot include decisive CURRENT_EXTERNAL; "
            "reclassify the already-verified fact or narrow the unresolved claim"
        )
    if errors:
        raise SemanticConsistencyError("; ".join(errors))
    return payload


def _decisive_evidence(payload: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"id": item["id"], "kind": item["kind"], "text": item["text"]}
        for item in payload["evidence"]
        if item["decisive"]
    ]


def _aligned_verdict(proposed: str, recommended: str) -> str:
    return "PASS" if proposed == recommended else "REVISE"


def decide(value: Any) -> dict[str, Any]:
    payload = validate_input(value)
    validate_consistency(payload)
    proposed = payload["proposed_memory_action"]
    permission = payload["permission"]
    relationship = payload["relationship"]
    evidence_status = payload["evidence_status"]
    robust = payload["robust_action_available"]
    risk = payload["risk"]
    decisive_kinds = {item["kind"] for item in payload["evidence"] if item["decisive"]}

    if permission == "REVOKED":
        verdict, action, state, source, reason = _aligned_verdict(proposed, "IGNORE"), "IGNORE", "CLEAR_INAPPLICABLE", "USER", "PERMISSION_REVOKED"
        next_step = "Do not rely on the candidate memory; continue only with permission-safe information."
        if risk == "HIGH":
            next_step += " The underlying high-risk task still requires qualified human review."
    elif risk == "HIGH":
        verdict, action, state, source, reason = "ESCALATE", "IGNORE", "UNCERTAIN", "HUMAN_REVIEW", "HIGH_RISK_HUMAN_REVIEW_REQUIRED"
        next_step = "Pause memory-grounded action and escalate to a qualified human decision-maker."
    elif evidence_status == "EXTERNAL_REQUIRED":
        verdict, action, state, source, reason = "VERIFY_EXTERNAL", "IGNORE", "UNCERTAIN", "EXTERNAL_EVIDENCE", "EXTERNAL_VERIFICATION_REQUIRED"
        next_step = "Verify current or third-party facts externally before relying on the memory; do not ask the user to guess."
    elif relationship == "NO_BRIDGE":
        verdict, action, state, source, reason = _aligned_verdict(proposed, "IGNORE"), "IGNORE", "CLEAR_INAPPLICABLE", "SUPPLIED_EVIDENCE", "NO_BRIDGE"
        next_step = "Continue without relying on the candidate memory unless explicit transfer evidence is supplied."
    elif relationship == "SUPERSEDED":
        verdict, action, state, source, reason = _aligned_verdict(proposed, "IGNORE"), "IGNORE", "CLEAR_INAPPLICABLE", "SUPPLIED_EVIDENCE", "SUPERSEDED"
        next_step = "Use the newer supplied evidence and do not rely on the superseded memory."
    elif risk == "MEDIUM" and not decisive_kinds.intersection({"PERMISSION", "USER_STATEMENT"}):
        verdict, action, state, source, reason = "ASK_USER", "ASK", "UNCERTAIN", "USER", "MEDIUM_RISK_CONFIRMATION_REQUIRED"
        next_step = "Obtain explicit user or permission confirmation before relying on memory for this medium-risk action."
    elif relationship in {"DIRECT", "EXPLICIT_TRANSFER"} and permission == "ALLOWED" and evidence_status == "SUFFICIENT":
        verdict, action, state, source = _aligned_verdict(proposed, "USE"), "USE", "CLEAR_APPLICABLE", "SUPPLIED_EVIDENCE"
        reason = relationship
        next_step = "The recommendation may rely on the candidate memory within the evidenced scope and permission."
    elif relationship == "CONFLICTING" and not robust:
        verdict, action, state, source, reason = "ASK_USER", "ASK", "UNCERTAIN", "USER", "CONFLICTING_EVIDENCE"
        next_step = "Ask one targeted question to resolve the competing current evidence before relying on memory."
    elif evidence_status == "USER_RESOLVABLE" and not robust:
        verdict, action, state, source, reason = "ASK_USER", "ASK", "UNCERTAIN", "USER", "USER_RESOLVABLE_UNCERTAINTY"
        next_step = "Ask one targeted question whose answer would change the memory or task action."
    elif robust:
        verdict, action, state, source, reason = _aligned_verdict(proposed, "IGNORE"), "IGNORE", "UNCERTAIN", "NONE", "ROBUST_ACTION_AVAILABLE"
        next_step = f"Take the robust action without relying on the disputed memory: {payload['robust_action']}"
    else:
        verdict, action, state, source, reason = "ASK_USER", "ASK", "UNCERTAIN", "USER", "EVIDENCE_GAP"
        next_step = "Request only the missing applicability or permission information that could change the action."

    return {
        "boundary": BOUNDARY,
        "decisive_evidence": _decisive_evidence(payload),
        "guard_verdict": verdict,
        "memory_action": action,
        "memory_state": state,
        "next_step": next_step,
        "reason_code": reason,
        "resolution_source": source,
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = decide(payload)
    except (json.JSONDecodeError, InputValidationError) as error:
        message = {"details": str(error), "error": getattr(error, "code", "INPUT_VALIDATION_ERROR")}
        print(json.dumps(message, ensure_ascii=False, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
