"""Validate friend-authored metadata and map it to the unchanged upstream guard."""

from __future__ import annotations

from datetime import date
import re
from typing import Any

from .guard_decision import decide

MAX_MENU_CHARS = 12000
MAX_MEMORIES = 24
FACT_FIELDS = {"id", "text", "kind", "terms", "permission", "weekdays",
               "confirmed_on", "valid_for_days", "superseded_by", "external_required"}


class ValidationError(ValueError):
    """Invalid local profile or untrusted extraction."""


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def parse_date(value: Any) -> date:
    if not isinstance(value, str):
        raise ValidationError("Dates must be YYYY-MM-DD strings.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("Dates must be YYYY-MM-DD strings.") from exc
    if parsed.isoformat() != value:
        raise ValidationError("Dates must be YYYY-MM-DD strings.")
    return parsed


def validate_profile(value: Any) -> dict:
    if not isinstance(value, dict) or set(value) != {"schema_version", "friend", "memories"}:
        raise ValidationError("Profile needs exactly schema_version, friend, memories.")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValidationError("Only profile schema_version 1 is supported.")
    if not nonempty(value["friend"]) or len(value["friend"]) > 120:
        raise ValidationError("friend must be a short nonempty label.")
    facts = value["memories"]
    if not isinstance(facts, list) or not 1 <= len(facts) <= MAX_MEMORIES:
        raise ValidationError(f"memories must contain 1–{MAX_MEMORIES} entries.")
    ids = set()
    for fact in facts:
        if not isinstance(fact, dict) or set(fact) != FACT_FIELDS:
            raise ValidationError(f"Each memory needs exactly {sorted(FACT_FIELDS)}.")
        if not nonempty(fact["id"]) or len(fact["id"]) > 60 or fact["id"] in ids:
            raise ValidationError("Memory ids must be unique nonempty strings, at most 60 chars.")
        ids.add(fact["id"])
        if not nonempty(fact["text"]) or len(fact["text"]) > 500:
            raise ValidationError("Memory text must be nonempty and at most 500 chars.")
        if fact["kind"] not in ("allergy", "preference"):
            raise ValidationError("kind must be allergy or preference.")
        if fact["permission"] not in ("ALLOWED", "REVOKED", "UNKNOWN"):
            raise ValidationError("permission must be ALLOWED, REVOKED or UNKNOWN.")
        if not isinstance(fact["terms"], list) or not 1 <= len(fact["terms"]) <= 16:
            raise ValidationError("terms needs 1–16 matching concepts.")
        if any(not nonempty(t) or len(t) > 80 for t in fact["terms"]):
            raise ValidationError("Each term must be nonempty and at most 80 chars.")
        days = fact["weekdays"]
        if (not isinstance(days, list) or len(days) != len(set(map(str, days)))
                or any(type(d) is not int or not 0 <= d <= 6 for d in days)):
            raise ValidationError("weekdays must be unique integers 0=Monday through 6=Sunday; [] means every day.")
        if fact["confirmed_on"] is not None:
            parse_date(fact["confirmed_on"])
        if type(fact["valid_for_days"]) is not int or not 1 <= fact["valid_for_days"] <= 3650:
            raise ValidationError("valid_for_days must be an integer from 1 to 3650.")
        if type(fact["external_required"]) is not bool:
            raise ValidationError("external_required must be boolean.")
        if fact["superseded_by"] is not None and not nonempty(fact["superseded_by"]):
            raise ValidationError("superseded_by must be null or a memory id.")
    # A replacement must exist and be usable. Do not invent a supersession bridge.
    by_id = {f["id"]: f for f in facts}
    for fact in facts:
        successor = fact["superseded_by"]
        if successor is not None:
            if successor not in by_id or successor == fact["id"]:
                raise ValidationError("superseded_by must identify a different existing memory.")
            if by_id[successor]["permission"] != "ALLOWED":
                raise ValidationError("Superseding memory must have ALLOWED permission.")
        seen = {fact["id"]}
        while successor is not None:
            if successor in seen:
                raise ValidationError("Supersession cycles are not allowed.")
            seen.add(successor)
            successor = by_id[successor]["superseded_by"]
    return value


def menu_lines(menu: str) -> list[dict]:
    if not nonempty(menu) or len(menu) > MAX_MENU_CHARS:
        raise ValidationError(f"Menu must contain 1–{MAX_MENU_CHARS} characters.")
    lines = [{"line_id": f"L{i+1}", "text": line.strip()}
             for i, line in enumerate(menu.splitlines()) if line.strip()]
    if len(lines) > 80:
        raise ValidationError("Menu has more than 80 nonempty lines.")
    return lines


def targets(profile: dict) -> list[dict]:
    # No memory text, date, permission, risk or scope metadata crosses the model boundary.
    return [{"memory_id": f["id"], "terms": f["terms"]}
            for f in profile["memories"] if f["permission"] == "ALLOWED"]


# Food vocabulary belongs to this adapter, never to the applicability engine.
# This small table is an explicit product choice, not an exhaustive ingredient ontology.
FOOD_ALIASES = {
    "meat": ("meat", "beef", "pork", "lamb", "chicken", "turkey", "duck", "bacon", "ham", "steak", "sausage"),
    "poultry": ("poultry", "chicken", "turkey", "duck", "goose"),
    "fish": ("fish", "salmon", "tuna", "cod", "trout", "anchovy", "anchovies"),
    "seafood": ("seafood", "fish", "salmon", "tuna", "shrimp", "prawn", "crab", "lobster", "mussel", "oyster", "scallop"),
    "peanuts": ("peanuts", "peanut", "groundnut", "groundnuts"),
    "spicy food": ("spicy", "chilli", "chili", "chilli oil", "chili oil", "hot sauce", "sriracha", "jalapeño", "jalapeno"),
    "chilli heat": ("spicy", "chilli", "chili", "hot sauce", "sriracha", "jalapeño", "jalapeno"),
    "cilantro": ("cilantro", "coriander leaves"),
    "coriander leaves": ("cilantro", "coriander leaves"),
}


def candidates_from_foods(value: Any, line: dict, allowed: list[dict]) -> list[dict]:
    """Ground extracted food spans and map them to local targets without AI policy."""
    if not isinstance(value, dict) or set(value) != {"foods"}:
        raise ValidationError("Model output must contain exactly a foods array.")
    foods = value["foods"]
    if not isinstance(foods, list) or len(foods) > 32:
        raise ValidationError("Model foods must be an array with at most 32 source phrases.")
    for food in foods:
        if not nonempty(food) or len(food) > 200 or food not in line["text"]:
            raise ValidationError("Each extracted food must occur verbatim in its original menu line.")
    if len(set(foods)) != len(foods):
        raise ValidationError("Duplicate extracted food phrases are not allowed.")
    candidates = []
    for target in allowed:
        matches = []
        for term in target["terms"]:
            for alias in FOOD_ALIASES.get(term.casefold(), (term.casefold(),)):
                pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
                if any(re.search(pattern, food.casefold()) for food in foods):
                    matches.append(alias)
        if not matches:
            continue
        # A mention in a negated or '-free' phrase is a clue requiring confirmation.
        text = line["text"].casefold()
        negated = any(re.search(r"(?:\bno\s+|\bwithout\s+|\bfree from\s+)" + re.escape(a) + r"\b|\b" + re.escape(a) + r"[ -]free\b", text)
                      for a in matches)
        candidates.append({"memory_id": target["memory_id"], "line_id": line["line_id"],
                           "quote": line["text"], "match": "uncertain" if negated else "matched"})
    return candidates


def validate_candidates(value: Any, lines: list[dict], allowed: list[dict]) -> dict:
    if not isinstance(value, dict) or set(value) != {"candidates"}:
        raise ValidationError("Extraction needs exactly the candidates field.")
    candidates = value["candidates"]
    if not isinstance(candidates, list) or len(candidates) > len(lines) * len(allowed):
        raise ValidationError("Invalid candidate count.")
    ids = {t["memory_id"] for t in allowed}
    line_map = {line["line_id"]: line["text"] for line in lines}
    seen = set()
    for c in candidates:
        if not isinstance(c, dict) or set(c) != {"memory_id", "line_id", "quote", "match"}:
            raise ValidationError("Candidate fields must be memory_id, line_id, quote, match only.")
        if not isinstance(c["memory_id"], str) or c["memory_id"] not in ids:
            raise ValidationError("Candidate references an unknown or unpermitted memory.")
        if not isinstance(c["line_id"], str) or c["line_id"] not in line_map:
            raise ValidationError("Candidate references an unknown menu line.")
        if c["match"] not in ("matched", "uncertain"):
            raise ValidationError("match must be matched or uncertain, never a guard verdict.")
        if not nonempty(c["quote"]) or c["quote"] not in line_map[c["line_id"]]:
            raise ValidationError("Candidate quote must occur verbatim in the referenced menu line.")
        key = (c["memory_id"], c["line_id"])
        if key in seen:
            raise ValidationError("Duplicate memory/line candidate.")
        seen.add(key)
    return value


def audit_fact(fact: dict, candidates: list[dict], meal_date: date) -> dict:
    matched = [c for c in candidates if c["memory_id"] == fact["id"]]
    observations = []
    permission = fact["permission"]
    evidence = [{"id": "source", "kind": "MEMORY_SOURCE", "decisive": False,
                 "text": fact["text"] if permission == "ALLOWED" else "Local record withheld."}]
    evidence.append({"id": "permission", "kind": "PERMISSION", "decisive": True,
                     "text": f"Local profile permission: {permission}."})
    days = fact["weekdays"]
    out_of_scope = bool(days) and meal_date.weekday() not in days
    confirmed = parse_date(fact["confirmed_on"]) if fact["confirmed_on"] else None
    stale = confirmed is None or not 0 <= (meal_date - confirmed).days <= fact["valid_for_days"]
    if out_of_scope:
        observations.append("WEEKDAY_OUT_OF_SCOPE")
    if stale:
        observations.append("CONFIRMATION_MISSING_OR_STALE")
    if any(c["match"] == "uncertain" for c in matched):
        observations.append("EXTRACTION_UNCERTAIN")
    if not matched:
        observations.append("NO_MATCH_DETECTED_NOT_CLEARANCE")
    if permission == "UNKNOWN":
        relationship = "UNKNOWN"
        scope_reason = "Permission is unresolved; no matching terms were sent to the model."
    elif fact["superseded_by"]:
        relationship = "SUPERSEDED"
        scope_reason = f"Local profile explicitly replaces this record with {fact['superseded_by']}."
    elif out_of_scope:
        relationship = "NO_BRIDGE"
        scope_reason = f"Meal date {meal_date} has weekday {meal_date.weekday()}, outside declared {days}."
    elif not matched:
        relationship = "NO_BRIDGE"
        scope_reason = "No candidate was detected; this is not evidence that ingredients are absent."
    else:
        relationship = "DIRECT"
        scope_reason = f"Declared day scope covers {meal_date}; menu candidates are present."
    evidence.append({"id": "scope", "kind": "APPLICABILITY", "decisive": True,
                     "text": scope_reason})
    if fact["external_required"]:
        evidence_status = "EXTERNAL_REQUIRED"
    elif stale or any(c["match"] == "uncertain" for c in matched):
        evidence_status = "USER_RESOLVABLE"
    else:
        evidence_status = "SUFFICIENT"
    payload = {"current_task": f"Review menu for meal date {meal_date}.",
               "candidate_memory": fact["text"] if permission == "ALLOWED" else "Withheld record",
               "proposed_memory_action": "USE", "permission": permission,
               "relationship": relationship, "evidence_status": evidence_status,
               "robust_action_available": False,
               "risk": "HIGH" if fact["kind"] == "allergy" else "LOW", "evidence": evidence}
    decision = decide(payload)
    if permission != "ALLOWED":
        matched = []
        observations = ["PERMISSION_WITHHELD"]
    if decision["guard_verdict"] == "ESCALATE":
        advice = "Allergy review required: confirm ingredients and cross-contact with the preparer; do not treat extraction as clearance."
    elif decision["reason_code"] == "PERMISSION_REVOKED":
        advice = "Permission revoked; do not use or disclose this memory."
    elif permission == "UNKNOWN":
        advice = "Ask the friend for permission before using this record."
    elif decision["guard_verdict"] == "VERIFY_EXTERNAL":
        advice = "Confirm current ingredients or preparation with the preparer before using this record."
    elif decision["memory_action"] == "ASK":
        advice = "Ask the friend whether this preference still applies; confirm uncertain menu wording if needed."
    elif decision["memory_action"] == "USE":
        advice = "This preference applies on the meal date; avoid the listed candidates or request a change."
    elif out_of_scope:
        advice = "This weekday-only preference does not apply on the meal date."
    elif fact["superseded_by"]:
        advice = "Use the separate decision for the replacement record."
    else:
        advice = "No candidate detected for this preference; ingredients may still be missing from the menu."
    return {"memory_id": fact["id"],
            "memory": fact["text"] if permission == "ALLOWED" else "[withheld]",
            "kind": fact["kind"] if permission == "ALLOWED" else "withheld",
            "candidates": matched, "observations": observations,
            **decision, "advice": advice}


def build_report(profile: dict, extraction: dict, meal_date: date, mode: str, model: str | None) -> dict:
    return {"schema_version": 1, "friend": profile["friend"], "meal_date": meal_date.isoformat(),
            "extraction_mode": mode, "model": model,
            "notice": "Decision support only. No dish is certified safe. Extraction may omit ingredients or misread menus; cross-contact is not assessed.",
            "decisions": [audit_fact(f, extraction["candidates"], meal_date) for f in profile["memories"]]}
