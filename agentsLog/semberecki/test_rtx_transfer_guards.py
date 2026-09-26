#!/usr/bin/env python3
"""CPU-only controlled-failure tests for the corrected RTX transfer wrapper (#88).

Exercises the declared guards with mocked runner/service boundaries — no model
calls, no network (api_ps and infer.* are patched), no GPU, $0. The historical
private wrapper and raw results are not touched.
"""

import json
import shutil
import sys
import tempfile
import unittest
from datetime import time as dtime
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rtx_transfer_run as w  # noqa: E402

DIGEST = "4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c"
CONFIG = {"model": "gemma4:12b-it-q4_K_M", "timeout_seconds": 420}


def ok_result(cid):
    return {"id": cid, "error": None, "latency_seconds": 0.5,
            "raw_response": {"choices": [{"message": {"content": "x"},
                                          "finish_reason": "stop"}]},
            "usage": {"prompt_tokens": 1000, "completion_tokens": 50}}


def err_result(cid, etype, status=None):
    return {"id": cid, "error": {"type": etype, "message": "boom", "status": status},
            "latency_seconds": 0.5, "usage": {}}


def ps(digest=DIGEST, context_length=32768):
    return {"models": [{"digest": digest, "context_length": context_length}]}


class GuardUnitTests(unittest.TestCase):
    def test_repo_root_detection_from_committed_path(self):
        root = w.find_repo_root()  # starts at this file, walks up
        self.assertTrue((root / "infer.py").exists())
        self.assertTrue((root / ".git").exists())
        # the historical parents[3] bug resolved ABOVE the repo; the fix must
        # resolve to the minimal repo root (an ancestor of this file)
        self.assertIn(root, Path(__file__).resolve().parents)

    def test_find_repo_root_custom_start(self):
        root = w.find_repo_root(Path(__file__).resolve())
        self.assertTrue((root / "infer.py").exists())

    def test_classify_error(self):
        self.assertEqual(w.classify_result_error({"type": "TimeoutError"}), "infrastructure")
        self.assertEqual(w.classify_result_error({"type": "URLError"}), "infrastructure")
        self.assertEqual(w.classify_result_error({"type": "http", "status": 404}), "provider_4xx")
        self.assertEqual(w.classify_result_error({"type": "http", "status": 503}), "provider_5xx")
        self.assertEqual(w.classify_result_error({"type": "SomethingElse"}), "other")

    def test_assert_served_identity_ok(self):
        actual = w.assert_served_identity(ps())
        self.assertEqual(actual, {"digest": DIGEST, "context_length": 32768,
                                  "context_validated": True})

    def test_assert_served_digest_mismatch(self):
        with self.assertRaises(w.GuardFailure) as cm:
            w.assert_served_identity(ps(digest="deadbeef"))
        self.assertIn("digest", str(cm.exception))

    def test_assert_served_context_mismatch(self):
        with self.assertRaises(w.GuardFailure) as cm:
            w.assert_served_identity(ps(context_length=4096))
        self.assertIn("context_length", str(cm.exception))

    def test_assert_no_loaded_model(self):
        with self.assertRaises(w.GuardFailure):
            w.assert_served_identity({"models": []})

    def test_assert_missing_context_fails_closed(self):
        with self.assertRaises(w.GuardFailure) as cm:
            w.assert_served_identity(ps(context_length=None))
        self.assertIn("non-integer", str(cm.exception))

    def test_assert_absent_context_field_fails_closed(self):
        with self.assertRaises(w.GuardFailure):
            w.assert_served_identity({"models": [{"digest": DIGEST}]})

    def test_assert_bool_context_fails_closed(self):
        with self.assertRaises(w.GuardFailure):
            w.assert_served_identity(ps(context_length=True))

    def test_assert_noninteger_context_fails_closed(self):
        with self.assertRaises(w.GuardFailure):
            w.assert_served_identity(ps(context_length="32768"))

    def test_ambiguous_loaded_snapshot_fails_closed(self):
        two_same = {"models": [{"digest": DIGEST, "context_length": 32768},
                               {"digest": DIGEST, "context_length": 32768}]}
        with self.assertRaises(w.GuardFailure) as cm:
            w.assert_served_identity(two_same)
        self.assertIn("unambiguous", str(cm.exception))

    def test_expected_model_found_unambiguously_among_others(self):
        mixed = {"models": [{"digest": "other-model", "context_length": 8192},
                            {"digest": DIGEST, "context_length": 32768}]}
        actual = w.assert_served_identity(mixed)
        self.assertEqual(actual["context_length"], 32768)
        self.assertTrue(actual["context_validated"])

    def test_no_matching_model_among_multiple_fails_closed(self):
        mixed = {"models": [{"digest": "other-a", "context_length": 8192},
                            {"digest": "other-b", "context_length": 8192}]}
        with self.assertRaises(w.GuardFailure):
            w.assert_served_identity(mixed)


class MainLoopGuardTests(unittest.TestCase):
    """Run main() with patched boundaries; assert first-declared-failure stops."""

    def setUp(self):
        base = w.REPO / "agentsLog/semberecki/private"  # git-ignored; create for clean checkouts
        base.mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="rtx-guard-test-", dir=base))
        self.input = self.tmp / "input.jsonl"
        self.output = self.tmp / "out.jsonl"
        self.manifest = self.tmp / "manifest.json"
        cases = [{"id": f"case-{i}"} for i in range(5)]
        self.input.write_text("".join(json.dumps(c) + "\n" for c in cases), encoding="utf-8")
        self.cases = cases

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, run_case_side_effect, api_ps_value=None):
        with mock.patch.object(w, "INPUT", self.input), \
             mock.patch.object(w, "OUTPUT", self.output), \
             mock.patch.object(w, "MANIFEST", self.manifest), \
             mock.patch.object(w, "INPUT_EXPECTED_SHA", w.sha256_file(self.input)), \
             mock.patch.object(w, "WARSAW_STOP", dtime(23, 59)), \
             mock.patch.object(w.infer, "load_config", return_value=dict(CONFIG)), \
             mock.patch.object(w.infer, "load_cases", return_value=list(self.cases)), \
             mock.patch.object(w.infer, "run_case", side_effect=run_case_side_effect), \
             mock.patch.object(w, "api_ps", return_value=api_ps_value or ps()):
            code = w.main()
        self.manifest_data = json.loads(self.manifest.read_text(encoding="utf-8"))
        return code, self.manifest_data

    def test_first_infra_error_stops(self):
        calls = [ok_result("case-0"), err_result("case-1", "TimeoutError")]
        # case-1 infra error must stop the run immediately (was 2-consecutive)
        def seq(case, config=None):
            return calls[self.cases.index(case)]
        code, m = self.run_main(seq)
        self.assertEqual(m["dispatched"], 2)
        self.assertEqual(m["stop_reason"], "declared_failure:infrastructure")
        self.assertEqual(m["unsent_ids"], ["case-2", "case-3", "case-4"])
        self.assertEqual(code, 1)

    def test_provider_http4xx_stops(self):
        def seq(case, config=None):
            if case["id"] == "case-0":
                return ok_result("case-0")
            return err_result(case["id"], "http", status=404)
        code, m = self.run_main(seq)
        self.assertEqual(m["stop_reason"], "declared_failure:provider_4xx")
        self.assertEqual(m["dispatched"], 2)

    def test_served_digest_mismatch_stops(self):
        code, m = self.run_main(lambda case, config=None: ok_result(case["id"]),
                                api_ps_value=ps(digest="deadbeef"))
        self.assertEqual(m["stop_reason"], "served_identity_mismatch")
        self.assertEqual(m["dispatched"], 1)
        self.assertEqual(m["unsent_ids"], ["case-1", "case-2", "case-3", "case-4"])

    def test_served_context_mismatch_stops(self):
        code, m = self.run_main(lambda case, config=None: ok_result(case["id"]),
                                api_ps_value=ps(context_length=4096))
        self.assertEqual(m["stop_reason"], "served_identity_mismatch")

    def test_served_context_missing_fails_closed(self):
        code, m = self.run_main(lambda case, config=None: ok_result(case["id"]),
                                api_ps_value=ps(context_length=None))
        self.assertEqual(m["stop_reason"], "served_identity_mismatch")
        self.assertEqual(m["dispatched"], 1)

    def test_served_ambiguous_snapshot_fails_closed(self):
        two_same = {"models": [{"digest": DIGEST, "context_length": 32768},
                               {"digest": DIGEST, "context_length": 32768}]}
        code, m = self.run_main(lambda case, config=None: ok_result(case["id"]),
                                api_ps_value=two_same)
        self.assertEqual(m["stop_reason"], "served_identity_mismatch")
        self.assertEqual(m["dispatched"], 1)

    def test_context_overflow_stops(self):
        def seq(case, config=None):
            r = ok_result(case["id"])
            if case["id"] == "case-1":
                r["usage"]["prompt_tokens"] = w.CONTEXT_LIMIT  # > limit - 1024
            return r
        code, m = self.run_main(seq)
        self.assertEqual(m["stop_reason"], "context_overflow_risk")
        self.assertEqual(m["dispatched"], 2)
        self.assertEqual(m["unsent_ids"], ["case-2", "case-3", "case-4"])

    def test_timestamp_ordering_and_provenance(self):
        code, m = self.run_main(lambda case, config=None: ok_result(case["id"]))
        self.assertEqual(m["stop_reason"], "all_cases_dispatched")
        self.assertEqual(m["dispatched"], 5)
        self.assertEqual(code, 0)
        for row in m["results_meta"]:
            self.assertLessEqual(row["request_started_utc"], row["response_completed_utc"])
            self.assertNotIn("dispatch_utc", row)  # renamed per #88 finding 3
        # manifest distinguishes enforced checks from manual-retained evidence
        self.assertIn("enforced_runtime_checks", m["provenance"])
        self.assertIn("manual_retained_evidence", m["provenance"])
        # served identity asserted, not hardcoded
        self.assertEqual(m["served_assertion"]["context_length"], 32768)
        self.assertTrue(m["served_assertion"]["context_validated"])
        self.assertNotIn("context_preserved", m)


if __name__ == "__main__":
    unittest.main(verbosity=2)
