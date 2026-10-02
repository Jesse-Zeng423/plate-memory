# Adapted MIT upstream test suite; see docs/provenance.json.
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src/guard_decision.py"
SPEC = importlib.util.spec_from_file_location("guard_decision", SCRIPT)
assert SPEC and SPEC.loader
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def case(**updates):
    value = {
        "current_task": "Choose a training option",
        "candidate_memory": "The user trained at the downtown pool",
        "proposed_memory_action": "USE",
        "permission": "ALLOWED",
        "relationship": "DIRECT",
        "evidence_status": "SUFFICIENT",
        "robust_action_available": False,
        "risk": "LOW",
        "evidence": [
            {"id": "SOURCE", "text": "Old record", "kind": "MEMORY_SOURCE", "decisive": False},
            {"id": "CURRENT", "text": "Current boundary evidence", "kind": "USER_STATEMENT", "decisive": True},
        ],
    }
    value.update(updates)
    return value


class GuardDecisionTests(unittest.TestCase):
    def assert_decision(self, payload, verdict, state, action):
        result = GUARD.decide(payload)
        self.assertEqual((result["guard_verdict"], result["memory_state"], result["memory_action"]), (verdict, state, action))

    def test_direct(self):
        self.assert_decision(case(), "PASS", "CLEAR_APPLICABLE", "USE")

    def test_explicit_transfer(self):
        self.assert_decision(case(relationship="EXPLICIT_TRANSFER", proposed_memory_action="IGNORE"), "REVISE", "CLEAR_APPLICABLE", "USE")

    def test_no_bridge(self):
        self.assert_decision(case(relationship="NO_BRIDGE"), "REVISE", "CLEAR_INAPPLICABLE", "IGNORE")

    def test_superseded(self):
        result = GUARD.decide(case(relationship="SUPERSEDED"))
        self.assertEqual(result["reason_code"], "SUPERSEDED")
        self.assertEqual([item["id"] for item in result["decisive_evidence"]], ["CURRENT"])
        self.assertEqual(result["memory_action"], "IGNORE")

    def test_permission_revoked_has_priority(self):
        result = GUARD.decide(case(permission="REVOKED", risk="HIGH", evidence_status="EXTERNAL_REQUIRED"))
        self.assertEqual(result["reason_code"], "PERMISSION_REVOKED")
        self.assertEqual(result["memory_action"], "IGNORE")

    def test_user_resolvable(self):
        self.assert_decision(case(relationship="UNKNOWN", evidence_status="USER_RESOLVABLE"), "ASK_USER", "UNCERTAIN", "ASK")

    def test_external_required(self):
        result = GUARD.decide(case(relationship="UNKNOWN", evidence_status="EXTERNAL_REQUIRED", proposed_memory_action="ASK"))
        self.assertEqual(result["guard_verdict"], "VERIFY_EXTERNAL")
        self.assertEqual(result["resolution_source"], "EXTERNAL_EVIDENCE")

    def test_robust_action(self):
        result = GUARD.decide(case(
            relationship="UNKNOWN",
            evidence_status="USER_RESOLVABLE",
            proposed_memory_action="IGNORE",
            robust_action_available=True,
            robust_action="Choose the reversible option",
        ))
        self.assertEqual(result["guard_verdict"], "PASS")
        self.assertEqual(result["reason_code"], "ROBUST_ACTION_AVAILABLE")

    def test_high_risk(self):
        self.assert_decision(case(risk="HIGH"), "ESCALATE", "UNCERTAIN", "IGNORE")

    def test_evidence_gap(self):
        self.assert_decision(case(permission="UNKNOWN", relationship="CONFLICTING", evidence_status="UNKNOWN"), "ASK_USER", "UNCERTAIN", "ASK")

    def test_invalid_enum_and_decisive_provenance(self):
        with self.assertRaises(GUARD.InputValidationError):
            GUARD.decide(case(permission="INVALID"))
        invalid = case()
        invalid["evidence"][0]["decisive"] = True
        with self.assertRaises(GUARD.InputValidationError):
            GUARD.decide(invalid)

    def test_repeatable_cli_output(self):
        encoded = json.dumps(case(), sort_keys=True).encode()
        command = [sys.executable, "-B", str(SCRIPT)]
        first = subprocess.run(command, input=encoded, capture_output=True, check=True).stdout
        second = subprocess.run(command, input=encoded, capture_output=True, check=True).stdout
        self.assertEqual(first, second)


class ValidationAndPrecedenceTests(unittest.TestCase):
    def cli(self, raw):
        return subprocess.run([sys.executable, "-B", str(SCRIPT)], input=raw, text=True, capture_output=True)

    def test_wrong_enum_types_are_validation_errors(self):
        for field in ("permission", "relationship", "evidence_status", "risk", "proposed_memory_action"):
            for value in ([], {}, None, 7, True):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(GUARD.InputValidationError):
                        GUARD.decide(case(**{field: value}))
        for value in ([], {}, None):
            payload = case()
            payload["evidence"][1]["kind"] = value
            with self.assertRaises(GUARD.InputValidationError):
                GUARD.decide(payload)

    def test_cli_validation_error_contract(self):
        for raw in ('{', '[]', '{}', json.dumps(case(permission=[]))):
            with self.subTest(raw=raw):
                result = self.cli(raw)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertEqual(json.loads(result.stderr)["error"], "INPUT_VALIDATION_ERROR")
                self.assertNotIn("Traceback", result.stderr)

    def test_closed_contract_and_evidence_constraints(self):
        payloads = [case(extra="unexpected"), case(robust_action_available=1), case(evidence=[])]
        missing = case()
        del missing["permission"]
        payloads.append(missing)
        duplicate = case()
        duplicate["evidence"][1]["id"] = "SOURCE"
        payloads.append(duplicate)
        extra = case()
        extra["evidence"][1]["extra"] = "unexpected"
        payloads.append(extra)
        for payload in payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(GUARD.InputValidationError):
                    GUARD.decide(payload)

    def test_robust_action_requires_explicit_nonempty_action(self):
        for updates in ({"robust_action_available": True}, {"robust_action_available": True, "robust_action": " "}, {"robust_action": "Do something"}):
            with self.assertRaises(GUARD.InputValidationError):
                GUARD.decide(case(**updates))

    def test_high_risk_precedes_external_and_robust(self):
        result = GUARD.decide(case(risk="HIGH", evidence_status="EXTERNAL_REQUIRED", robust_action_available=True, robust_action="Prepare an outline"))
        self.assertEqual(result["guard_verdict"], "ESCALATE")

    def test_external_required_precedes_supersession_and_robust(self):
        result = GUARD.decide(case(evidence_status="EXTERNAL_REQUIRED", relationship="SUPERSEDED", robust_action_available=True, robust_action="Prepare an outline"))
        self.assertEqual(result["guard_verdict"], "VERIFY_EXTERNAL")

    def test_unknown_permission_never_allows_use(self):
        for relationship in ("DIRECT", "EXPLICIT_TRANSFER"):
            result = GUARD.decide(case(permission="UNKNOWN", relationship=relationship))
            self.assertEqual(result["memory_action"], "ASK")

    def test_no_bridge_precedes_robust_action(self):
        result = GUARD.decide(case(relationship="NO_BRIDGE", robust_action_available=True, robust_action="Prepare an outline"))
        self.assertEqual(result["reason_code"], "NO_BRIDGE")

    def test_all_examples_execute_and_match_expected_results(self):
        process = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/run_mock_dry_run.py")], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout.count("PASS "), 4)

    def test_pass_only_binds_memory_action(self):
        result = GUARD.decide(case(relationship="NO_BRIDGE", proposed_memory_action="IGNORE"))
        self.assertEqual(result["guard_verdict"], "PASS")
        self.assertEqual(result["memory_action"], "IGNORE")
        self.assertIn("no autonomous execution", result["boundary"])

if __name__ == "__main__":
    unittest.main()
