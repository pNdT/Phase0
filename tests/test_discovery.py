import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from phase0.core import AppError, FIELDS, Store, blank_profile, validate_response


def output(updates=None, reply="Who will use this?"):
    facts = blank_profile()
    facts.update(updates or {})
    return json.dumps({"reply": reply, "updates": facts})


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        # These tests isolate extraction/persistence. Domain gates have separate integration tests.
        self.input_gate = patch('phase0.core.scope.input_decision', return_value='allow')
        self.output_gate = patch('phase0.core.scope.output_allowed', return_value=True)
        self.planner_gate = patch('phase0.core.planner.should_plan', return_value=False)
        self.input_gate.start()
        self.output_gate.start()
        self.planner_gate.start()
        self.addCleanup(self.input_gate.stop)
        self.addCleanup(self.output_gate.stop)
        self.addCleanup(self.planner_gate.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "test.sqlite3")
        self.project = self.store.create("Dog matcher")

    def tearDown(self):
        self.tmp.cleanup()

    def test_unsubstantiated_updates_are_skipped(self):
        raw = output({"budget": {"value": "USD 0/month", "evidence": "My budget is zero"}})
        _, accepted, rejected = validate_response(raw, "I want dog matching")
        self.assertEqual(accepted, {})
        self.assertEqual(rejected, ["budget"])

    def test_assistant_claims_are_not_evidence(self):
        raw = output({"platform": {"value": "web", "evidence": "web app"}})
        _, accepted, _ = validate_response(raw, "Actually I have not decided")
        self.assertFalse(accepted)

    def test_missing_evidence_skips_only_unsupported_fact(self):
        raw = output({"monetization": {"value": "undecided", "evidence": None},
                      "platform": {"value": "web", "evidence": "web app"}})
        _, accepted, rejected = validate_response(raw, "I want a web app")
        self.assertEqual(set(accepted), {"platform"})
        self.assertEqual(rejected, ["monetization"])

    @patch("phase0.core.local_models", return_value=["test:local"])
    @patch("phase0.core.ollama_request")
    def test_grounded_correction_and_persistence(self, request, models):
        request.return_value = {"message": {"content": output({"platform": {"value": "web", "evidence": "web app"}})}}
        self.store.chat(self.project["id"], "A web app for dogs", "test:local")
        request.return_value = {"message": {"content": output({"platform": {"value": "mobile", "evidence": "mobile app instead"}})}}
        self.store.chat(self.project["id"], "Make it a mobile app instead", "test:local")
        restored = Store(self.store.path).get(self.project["id"])
        self.assertEqual(restored["profile"]["platform"]["value"], "mobile")
        self.assertEqual(len(restored["messages"]), 4)
        self.assertIsNone(restored["profile"]["budget"]["value"])

    @patch("phase0.core.local_models", return_value=["test:local"])
    @patch("phase0.core.ollama_request", return_value={"message": {"content": "not JSON"}})
    def test_invalid_inference_does_not_commit(self, request, models):
        with self.assertRaises(AppError):
            self.store.chat(self.project["id"], "Build an app", "test:local")
        self.assertEqual(self.store.get(self.project["id"])["messages"], [])
        self.assertEqual(self.store.get(self.project["id"])["profile"], blank_profile())

    @patch("phase0.core.local_models", return_value=["test:local"])
    def test_cloud_or_unknown_models_are_rejected(self, models):
        with self.assertRaises(AppError):
            self.store.chat(self.project["id"], "Build an app", "remote:cloud")

    def test_schema_missing_fields_is_rejected(self):
        with self.assertRaises(AppError):
            validate_response(json.dumps({"reply": "Hello", "updates": {}}), "Hello")

    def test_projects_remain_separate(self):
        second = self.store.create("Another idea")
        self.assertNotEqual(self.project["id"], second["id"])
        self.assertEqual(len(self.store.list()), 2)

    @patch("phase0.core.local_models", return_value=["test:local"])
    @patch("phase0.core.ollama_request")
    def test_repair_accepts_only_grounded_requested_fields(self, request, models):
        request.side_effect = [
            {"message": {"content": output({"budget": {"value": "100", "evidence": "wrong quote"}})}},
            {"message": {"content": output({"budget": {"value": "100", "evidence": "budget 100"},
                                            "platform": {"value": "web", "evidence": "web"}})}}]
        result = self.store.chat(self.project["id"], "web, budget 100", "test:local")
        self.assertEqual(result["profile"]["budget"]["value"], "100")
        self.assertIsNone(result["profile"]["platform"]["value"])
        self.assertEqual(result["rejected_updates"], [])

    @patch("phase0.core.local_models", return_value=["test:local"])
    @patch("phase0.core.ollama_request")
    def test_failed_repair_preserves_valid_first_response(self, request, models):
        request.side_effect = [
            {"message": {"content": output({"budget": {"value": "100", "evidence": "invented"},
                                            "platform": {"value": "web", "evidence": "web"}})}},
            AppError("offline")]
        result = self.store.chat(self.project["id"], "web", "test:local")
        self.assertEqual(result["profile"]["platform"]["value"], "web")
        self.assertIsNone(result["profile"]["budget"]["value"])
        self.assertEqual(result["rejected_updates"], ["budget"])


if __name__ == "__main__":
    unittest.main()
