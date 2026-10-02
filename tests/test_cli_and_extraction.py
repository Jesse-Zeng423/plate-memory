from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError

from src import cli
from src.extraction import ExtractionError, NoRedirect, local_extract, model_name
from src.food_adapter import ValidationError, menu_lines, targets
from src.json_contract import JsonContractError, loads

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "examples/profile.json").read_text())


class CliTests(unittest.TestCase):
    def args(self):
        return ["--menu", str(ROOT / "examples/weekend.txt"), "--date", "2026-10-03",
                "--offline", "--demo-extraction", str(ROOT / "examples/weekend.extraction.json"), "--json"]

    def test_absolute_cli_and_default_profile_from_unrelated_cwd(self):
        with tempfile.TemporaryDirectory() as work:
            result = subprocess.run([sys.executable, "-B", str(ROOT / "src/cli.py"), *self.args()],
                                    cwd=work, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["extraction_mode"], "canned-demo")

    def test_stdin_and_fixture(self):
        args = self.args()[2:] + ["--stdin"]
        with patch("sys.stdin", StringIO((ROOT / "examples/weekend.txt").read_text())), redirect_stdout(StringIO()) as out:
            self.assertEqual(cli.main(args), 0)
        self.assertEqual(json.loads(out.getvalue())["meal_date"], "2026-10-03")

    def test_fingerprint_rejects_changed_menu(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "menu.txt"
            path.write_text("different menu")
            args = self.args()
            args[1] = str(path)
            with redirect_stderr(StringIO()) as err:
                self.assertEqual(cli.main(args), 2)
            self.assertIn("fingerprints", err.getvalue())

    def test_fingerprint_rejects_changed_profile_targets(self):
        with tempfile.TemporaryDirectory() as work:
            p = deepcopy(PROFILE)
            p["memories"][0]["terms"] = ["different concept"]
            path = Path(work) / "profile.json"
            path.write_text(json.dumps(p))
            with redirect_stderr(StringIO()) as err:
                self.assertEqual(cli.main(self.args() + ["--profile", str(path)]), 2)
            self.assertIn("fingerprints", err.getvalue())

    def test_demo_requires_explicit_pair(self):
        for args in (["--menu", "absent", "--offline"], ["--menu", "absent", "--demo-extraction", "absent"]):
            with redirect_stderr(StringIO()):
                self.assertEqual(cli.main(args), 2)

    def test_live_failure_never_falls_back(self):
        with patch("src.cli.local_extract", side_effect=ExtractionError("unavailable")), redirect_stdout(StringIO()) as out, redirect_stderr(StringIO()) as err:
            self.assertEqual(cli.main(["--menu", str(ROOT / "examples/weekend.txt")]), 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("unavailable", err.getvalue())

    def test_no_permitted_memories_skips_model_and_reports_asks(self):
        with tempfile.TemporaryDirectory() as work:
            p = deepcopy(PROFILE)
            p["memories"] = [p["memories"][1]]
            p["memories"][0]["permission"] = "UNKNOWN"
            path = Path(work) / "profile.json"
            path.write_text(json.dumps(p))
            with patch("src.cli.local_extract") as live, redirect_stdout(StringIO()) as out:
                self.assertEqual(cli.main(["--profile", str(path), "--menu", str(ROOT / "examples/weekend.txt"), "--json"]), 0)
            live.assert_not_called()
            report = json.loads(out.getvalue())
            self.assertEqual(report["extraction_mode"], "permission-withheld-no-inference")
            self.assertEqual(report["decisions"][0]["memory_action"], "ASK")

    def test_invalid_date_and_menu_source_are_cli_errors(self):
        for args in (["--menu", "x", "--date", "2026-99-99"],
                     ["--menu", "x", "--stdin"], []):
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as exc:
                cli.parser().parse_args(args)
            self.assertEqual(exc.exception.code, 2)

    def test_timeout_bounds(self):
        with redirect_stderr(StringIO()):
            self.assertEqual(cli.main(["--menu", "absent", "--timeout", "0"]), 2)


def response(value):
    item = Mock()
    item.__enter__ = Mock(return_value=item)
    item.__exit__ = Mock(return_value=False)
    item.read.return_value = json.dumps(value).encode()
    return item



class ExtractionTests(unittest.TestCase):
    def run_extraction(self):
        return local_extract(menu_lines("chicken with coriander leaves"), targets(PROFILE), "gemma3:4b", 1)

    def successful_responses(self, foods=()):
        return [response({"model_info": {"architecture": "gemma3"}}),
                response({"done": True, "done_reason": "stop", "response": json.dumps({"foods": list(foods)})})]

    def test_transport_is_loopback_no_proxy_no_policy_metadata(self):
        with patch("src.extraction.build_opener") as builder:
            opener = builder.return_value
            opener.open.side_effect = self.successful_responses()
            self.assertEqual(self.run_extraction(), {"candidates": []})
            self.assertEqual(opener.open.call_count, 2)
            for call in opener.open.call_args_list[1:]:
                request = call.args[0]
                self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/generate")
                payload = json.loads(request.data)
                prompt = payload["prompt"]
                self.assertIn("chicken with coriander leaves", prompt)
                for forbidden in ("memory_id", "confirmed_on", "valid_for_days", "friend", "permission", "risk", "weekdays", "peanuts"):
                    self.assertNotIn(forbidden, prompt)
                self.assertEqual(payload["options"]["temperature"], 0)
                self.assertFalse(payload["stream"])
            self.assertEqual(builder.call_args.args[0].proxies, {})

    def test_disguised_remote_alias_rejected_before_generation(self):
        with patch("src.extraction.build_opener") as builder:
            builder.return_value.open.return_value = response({"remote_host": "https://example.org"})
            with self.assertRaises(ExtractionError):
                self.run_extraction()
            self.assertEqual(builder.return_value.open.call_count, 1)

    def test_missing_local_model_metadata_rejected(self):
        with patch("src.extraction.build_opener") as builder:
            builder.return_value.open.return_value = response({})
            with self.assertRaises(ExtractionError):
                self.run_extraction()
            self.assertEqual(builder.return_value.open.call_count, 1)

    def test_redirect_rejected(self):
        with self.assertRaises(ExtractionError):
            NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://example.org")

    def test_unavailable_model_reports_clear_error(self):
        with patch("src.extraction.build_opener") as builder:
            builder.return_value.open.side_effect = URLError("offline")
            with self.assertRaisesRegex(ExtractionError, "local Ollama"):
                self.run_extraction()

    def test_output_policy_injection_or_invalid_json_rejected(self):
        for raw in ('{"foods":[],"guard_verdict":"PASS"}', 'broken', '{"foods":"chicken"}'):
            with patch("src.extraction.build_opener") as builder:
                builder.return_value.open.side_effect = [response({"model_info": {"architecture": "gemma3"}}),
                                                        response({"done": True, "response": raw})]
                with self.assertRaises(ExtractionError):
                    self.run_extraction()

    def test_model_pair_gets_original_evidence_and_host_ids(self):
        with patch("src.extraction.build_opener") as builder:
            builder.return_value.open.side_effect = self.successful_responses(("chicken", "coriander leaves"))
            output = self.run_extraction()
        self.assertEqual([c["memory_id"] for c in output["candidates"]], ["weekday-vegetarian", "cilantro"])
        self.assertEqual(output["candidates"][0]["quote"], "chicken with coriander leaves")

    def test_negated_mention_becomes_uncertain(self):
        with patch("src.extraction.build_opener") as builder:
            builder.return_value.open.side_effect = self.successful_responses(("chicken", "cilantro"))
            output = local_extract(menu_lines("chicken without cilantro"), targets(PROFILE), "gemma3:4b")
        self.assertEqual(output["candidates"][1]["match"], "uncertain")

    def test_model_cannot_invent_quote_or_context_id(self):
        for raw in ('{"foods":["invented"]}', '{"foods":["chicken"],"line_id":"L99"}'):
            with patch("src.extraction.build_opener") as builder:
                builder.return_value.open.side_effect = [response({"model_info": {"architecture": "gemma3"}}),
                                                        response({"done": True, "response": raw})]
                with self.assertRaises(ExtractionError):
                    self.run_extraction()

    def test_model_cannot_supply_a_matrix_or_duplicate_json_keys(self):
        for raw in ('{"candidates":[]}', '{"foods":[],"foods":[]}', '{"foods":["chicken","chicken"]}'):
            with patch("src.extraction.build_opener") as builder:
                builder.return_value.open.side_effect = [response({"model_info": {"architecture": "gemma3"}}),
                                                        response({"done": True, "response": raw})]
                with self.assertRaises(ExtractionError):
                    self.run_extraction()

    def test_pair_count_and_context_bounds_prevent_silent_truncation(self):
        for lines, allowed in ((menu_lines("\n".join(["rice"] * 17)), targets(PROFILE)),
                               (menu_lines("rice " * 1200), targets(PROFILE))):
            with patch("src.extraction.build_opener") as builder:
                builder.return_value.open.return_value = response({"model_info": {"architecture": "gemma3"}})
                with self.assertRaises(ExtractionError):
                    local_extract(lines, allowed, "gemma3:4b")
                self.assertEqual(builder.return_value.open.call_count, 1)

    def test_no_allowed_terms_never_contacts_model(self):
        with patch("src.extraction.build_opener") as builder:
            self.assertEqual(local_extract(menu_lines("rice"), [], "gemma3:4b"), {"candidates": []})
            builder.assert_not_called()

    def test_truncated_output_rejected(self):
        with patch("src.extraction.build_opener") as builder:
            builder.return_value.open.side_effect = [response({"model_info": {"architecture": "gemma3"}}),
                                                    response({"done": True, "done_reason": "length", "response": '{"match":"matched"}'})]
            with self.assertRaises(ExtractionError):
                self.run_extraction()

    def test_cloud_models_and_bad_model_names_rejected(self):
        for name in ("gemma3:cloud", "https://example.org/model", "", "model name"):
            with self.assertRaises(ValidationError):
                model_name(name)

    def test_duplicate_json_fields_cannot_override_permission_or_verdict(self):
        for raw in ('{"permission":"REVOKED","permission":"ALLOWED"}',
                    '{"candidates":[],"candidates":[]}', '{"n":NaN}'):
            with self.assertRaises(JsonContractError):
                loads(raw)


if __name__ == "__main__":
    unittest.main()
