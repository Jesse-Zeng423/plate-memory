from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest

from src.food_adapter import (ValidationError, audit_fact, build_report, menu_lines,
                              parse_date, targets, validate_candidates, validate_profile, candidates_from_foods)

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "examples/profile.json").read_text())


def fact(identifier="weekday-vegetarian", **updates):
    value = deepcopy(next(f for f in PROFILE["memories"] if f["id"] == identifier))
    value.update(updates)
    return value


def candidate(identifier="weekday-vegetarian", match="matched"):
    return {"memory_id": identifier, "line_id": "L1", "quote": "chicken", "match": match}


class FoodAdapterTests(unittest.TestCase):
    def test_weekend_scope(self):
        result = audit_fact(fact(), [candidate()], date(2026, 10, 3))
        self.assertEqual((result["memory_action"], result["reason_code"]), ("IGNORE", "NO_BRIDGE"))

    def test_weekday_scope(self):
        result = audit_fact(fact(), [candidate()], date(2026, 10, 2))
        self.assertEqual((result["memory_action"], result["guard_verdict"]), ("USE", "PASS"))

    def test_stale_note_asks(self):
        result = audit_fact(fact("old-spice"), [candidate("old-spice")], date(2026, 10, 3))
        self.assertEqual((result["guard_verdict"], result["memory_action"]), ("ASK_USER", "ASK"))

    def test_allergy_always_escalates_without_detection_or_in_scope(self):
        for scope in ([], [0]):
            result = audit_fact(fact("peanut-allergy", weekdays=scope), [], date(2026, 10, 3))
            self.assertEqual(result["guard_verdict"], "ESCALATE")
            self.assertIn("not treat extraction as clearance", result["advice"])

    def test_revocation_precedes_risk_and_redacts(self):
        result = audit_fact(fact("peanut-allergy", permission="REVOKED"), [], date(2026, 10, 3))
        self.assertEqual(result["reason_code"], "PERMISSION_REVOKED")
        self.assertEqual(result["memory"], "[withheld]")
        self.assertNotIn("Never eat peanuts", json.dumps(result))

    def test_unknown_permission_asks_and_excludes_model_target(self):
        p = deepcopy(PROFILE)
        p["memories"] = [fact(permission="UNKNOWN")]
        self.assertEqual(targets(p), [])
        result = audit_fact(p["memories"][0], [], date(2026, 10, 2))
        self.assertEqual(result["guard_verdict"], "ASK_USER")

    def test_future_confirmation_is_not_current(self):
        result = audit_fact(fact(confirmed_on="2026-10-04"), [candidate()], date(2026, 10, 2))
        self.assertEqual(result["memory_action"], "ASK")

    def test_freshness_boundary(self):
        result = audit_fact(fact(confirmed_on="2026-10-01", valid_for_days=1), [candidate()], date(2026, 10, 2))
        self.assertEqual(result["memory_action"], "USE")
        result = audit_fact(fact(confirmed_on="2026-09-30", valid_for_days=1), [candidate()], date(2026, 10, 2))
        self.assertEqual(result["memory_action"], "ASK")

    def test_uncertain_match_does_not_use_memory(self):
        result = audit_fact(fact(), [candidate(match="uncertain")], date(2026, 10, 2))
        self.assertEqual(result["memory_action"], "ASK")

    def test_external_check_precedes_out_of_scope(self):
        result = audit_fact(fact(external_required=True), [], date(2026, 10, 3))
        self.assertEqual(result["guard_verdict"], "VERIFY_EXTERNAL")

    def test_supersession_is_explicit(self):
        result = audit_fact(fact(superseded_by="old-spice"), [candidate()], date(2026, 10, 2))
        self.assertEqual(result["reason_code"], "SUPERSEDED")

    def test_deterministic_for_identical_inputs(self):
        arguments = (PROFILE, {"candidates": []}, date(2026, 10, 3), "test", None)
        self.assertEqual(build_report(*arguments), build_report(*arguments))

    def test_no_match_is_not_clearance(self):
        result = audit_fact(fact(), [], date(2026, 10, 2))
        self.assertIn("not evidence", result["decisive_evidence"][-1]["text"])

    def test_closed_profile_schema(self):
        p = deepcopy(PROFILE)
        p["guard_verdict"] = "PASS"
        with self.assertRaises(ValidationError):
            validate_profile(p)

    def test_invalid_metadata(self):
        for updates in ({"weekdays": [True]}, {"weekdays": [7]}, {"weekdays": [0,0]},
                        {"valid_for_days": True}, {"permission": "yes"},
                        {"confirmed_on": "2026-13-01"}, {"terms": []}, {"external_required": 1}):
            with self.subTest(updates=updates):
                p = deepcopy(PROFILE)
                p["memories"][0].update(updates)
                with self.assertRaises(ValidationError):
                    validate_profile(p)

    def test_supersession_references_and_cycles(self):
        for successor in ("absent", "weekday-vegetarian"):
            p = deepcopy(PROFILE)
            p["memories"][1]["superseded_by"] = successor
            with self.assertRaises(ValidationError):
                validate_profile(p)
        p = deepcopy(PROFILE)
        p["memories"][0]["superseded_by"] = p["memories"][1]["id"]
        p["memories"][1]["superseded_by"] = p["memories"][0]["id"]
        with self.assertRaises(ValidationError):
            validate_profile(p)

    def test_extraction_can_never_supply_policy(self):
        c = candidate()
        c["risk"] = "LOW"
        with self.assertRaises(ValidationError):
            validate_candidates({"candidates": [c]}, menu_lines("chicken"), targets(PROFILE))

    def test_extraction_rejects_fabricated_quote_ids_and_duplicates(self):
        for update in ({"quote": "invented"}, {"memory_id": "alien"}, {"line_id": "L2"}, {"match": "PASS"}):
            c = candidate()
            c.update(update)
            with self.assertRaises(ValidationError):
                validate_candidates({"candidates": [c]}, menu_lines("chicken"), targets(PROFILE))
        with self.assertRaises(ValidationError):
            validate_candidates({"candidates": [candidate(), candidate()]}, menu_lines("chicken"), targets(PROFILE))

    def test_targets_omit_all_policy_and_memory_text(self):
        p = deepcopy(PROFILE)
        p["memories"][0]["permission"] = "REVOKED"
        t = targets(p)
        self.assertNotIn("peanut-allergy", json.dumps(t))
        for item in t:
            self.assertEqual(set(item), {"memory_id", "terms"})

    def test_input_bounds_and_date_shape(self):
        for menu in ("", "a" * 12001, "\n".join(["a"] * 81)):
            with self.assertRaises(ValidationError):
                menu_lines(menu)
        with self.assertRaises(ValidationError):
            parse_date("20261002")

    def test_grounded_food_category_mapping_and_word_boundaries(self):
        line = menu_lines("Roast duck with champignon mushrooms")[0]
        cs = candidates_from_foods({"foods": ["duck", "champignon mushrooms"]}, line, targets(PROFILE))
        self.assertEqual([c["memory_id"] for c in cs], ["weekday-vegetarian"])
        cs = candidates_from_foods({"foods": ["champignon mushrooms"]}, line,
                                   [{"memory_id": "ham-note", "terms": ["ham"]}])
        self.assertEqual(cs, [])

    def test_extracted_food_must_be_grounded_and_unique(self):
        line = menu_lines("chicken rice")[0]
        for foods in (["cilantro"], ["chicken", "chicken"], [True]):
            with self.assertRaises(ValidationError):
                candidates_from_foods({"foods": foods}, line, targets(PROFILE))

    def test_literal_custom_term_and_negated_food(self):
        line = menu_lines("basil pesto — cilantro-free")[0]
        cs = candidates_from_foods({"foods": ["basil", "cilantro"]}, line,
                                   [{"memory_id": "basil-note", "terms": ["basil"]},
                                    {"memory_id": "cilantro-note", "terms": ["cilantro"]}])
        self.assertEqual([c["match"] for c in cs], ["matched", "uncertain"])


if __name__ == "__main__":
    unittest.main()
