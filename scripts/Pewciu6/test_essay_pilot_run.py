"""Tests for the bounded essay pilot launcher. Fake backends and clocks only: no model calls."""

import contextlib
import io
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import essay_pilot_run as runner  # noqa: E402
import essay_route  # noqa: E402
from test_essay_route import ESSAY_NAMED, ESSAY_NUMBERED, essay_text, write_rows  # noqa: E402


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def completion(case_id, text, finish="stop"):
    return {"id": case_id, "raw_response": {"choices": [{"message": {"content": text}, "finish_reason": finish}]},
            "usage": None, "latency_seconds": 0.0, "error": None}


class FakeBackend:
    """Deterministic stub: records every call, optionally advances the fake clock."""

    def __init__(self, clock=None, seconds_per_call=0.0, fail_ids=(), raise_ids=()):
        self.clock = clock
        self.seconds_per_call = seconds_per_call
        self.fail_ids = set(fail_ids)
        self.raise_ids = set(raise_ids)
        self.calls = []

    def __call__(self, case, config):
        self.calls.append((case["id"], config["max_output_tokens"], config["timeout_seconds"]))
        if self.clock is not None:
            self.clock.now += self.seconds_per_call
        if case["id"] in self.raise_ids:
            raise ConnectionError("stub connection refused")
        if case["id"] in self.fail_ids:
            return {"id": case["id"], "raw_response": None, "usage": None, "latency_seconds": 0.0,
                    "error": {"type": "http", "status": 500, "message": "stub"}}
        if case["id"].endswith(essay_route.PLAN_SUFFIX):
            return completion(case["id"], "- Temat nr 1\n- Teza: PLAN-SECRET " + case["id"])
        return completion(case["id"], essay_text(100))


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "input.jsonl"
        write_rows(self.source, [{"id": "a", "prompt": ESSAY_NAMED}, {"id": "c", "prompt": ESSAY_NUMBERED}])
        config = self.root / "base.json"
        config.write_text(json.dumps({"name": "stub", "base_url": "http://127.0.0.1:9/v1", "model": "m",
                                      "timeout_seconds": 420}))
        self.run_dir = self.root / "private" / "run1"
        with contextlib.redirect_stdout(io.StringIO()):
            code = essay_route.main(["build", "--input", str(self.source), "--out-dir", str(self.run_dir),
                                     "--mode", "both", "--base-config", str(config)])
        self.assertEqual(code, 0)
        self.manifest = self.run_dir / "manifest.json"
        self.saved = {name: getattr(runner, name) for name in
                      ("MAX_CALLS", "MAX_REQUESTED_TOKENS", "PER_CALL_TIMEOUT", "OVERRUN_GRACE", "MIN_CALL_SECONDS")}

    def tearDown(self):
        for name, value in self.saved.items():
            setattr(runner, name, value)
        self.tmp.cleanup()

    def run_main(self, backend, clock=time.monotonic, *extra):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return runner.main(["--manifest", str(self.manifest), "--source", str(self.source), *extra],
                               backend=backend, clock=clock)

    def record(self):
        return json.loads((self.run_dir / "run_manifest.json").read_text())

    def rows(self, name):
        return [json.loads(line) for line in (self.run_dir / name).read_text().splitlines()]

    def test_complete_run_within_bounds(self):
        clock = FakeClock()
        backend = FakeBackend(clock, seconds_per_call=60)
        self.assertEqual(self.run_main(backend, clock), 0)
        self.assertEqual([c[0] for c in backend.calls],
                         ["a", "c", "a__plan", "c__plan", "a", "c"])  # deterministic order
        self.assertEqual([c[1] for c in backend.calls], [1536, 1536, 512, 512, 1536, 1536])
        self.assertTrue(all(c[2] == 420 for c in backend.calls))
        record = self.record()
        self.assertEqual(record["status"], "complete")
        self.assertEqual(record["calls_sent"], 6)
        self.assertEqual(record["tokens_reserved"], 7168)
        self.assertEqual(record["unsent"], {})
        self.assertEqual(record["bounds"]["max_wall_seconds"], 1800)
        self.assertEqual(record["bounds"]["retries"], 0)
        # The write stage embeds the plan; it stays in the private dir and never in the handoff.
        self.assertIn("PLAN-SECRET a__plan", (self.run_dir / "write.input.jsonl").read_text())
        for name in ("answers.single.jsonl", "answers.write.jsonl"):
            answers = self.rows(name)
            self.assertEqual([a["id"] for a in answers], ["a", "c"])
            self.assertEqual(set(answers[0]), {"id", "stage", "answer", "error_type"})
            self.assertNotIn("PLAN-SECRET", (self.run_dir / name).read_text())
        self.assertFalse((self.run_dir / "answers.plan.jsonl").exists())

    def test_global_deadline_stops_run_and_caps_timeout(self):
        clock = FakeClock()
        backend = FakeBackend(clock, seconds_per_call=400)
        self.assertEqual(self.run_main(backend, clock), 1)
        # After 4 calls 1600 s are gone: call 5 gets min(420, 200) and overshoots the deadline.
        self.assertEqual([c[2] for c in backend.calls], [420, 420, 420, 420, 200])
        record = self.record()
        self.assertEqual(record["status"], "stopped")
        self.assertEqual(record["stop_reason"], "deadline")
        self.assertEqual(record["calls_sent"], 5)
        self.assertEqual(record["unsent"], {"write": ["c"]})
        self.assertEqual(len(self.rows("write.output.jsonl")), 1)

    def test_deadline_reached_before_a_call_sends_nothing_more(self):
        clock = FakeClock()
        backend = FakeBackend(clock, seconds_per_call=445)
        self.assertEqual(self.run_main(backend, clock), 1)
        # 4 x 445 = 1780 s; 20 s left >= MIN_CALL_SECONDS so call 5 runs with timeout 20.
        self.assertEqual(backend.calls[-1][2], 20)
        record = self.record()
        self.assertEqual(record["stop_reason"], "deadline")
        self.assertLessEqual(record["calls_sent"], 5)

    def test_six_timeouts_cannot_exceed_thirty_minutes(self):
        clock = FakeClock()

        def slow(case, config):  # every call consumes its full timeout, as a hung server would
            clock.now += config["timeout_seconds"]
            return {"id": case["id"], "raw_response": None, "usage": None, "latency_seconds": None,
                    "error": {"type": "TimeoutError", "message": "stub timeout"}}

        self.assertEqual(self.run_main(slow, clock), 1)
        record = self.record()
        self.assertLessEqual(sum(c["timeout_seconds"] for c in record["calls"]), 1800)
        self.assertLessEqual(record["elapsed_seconds"], 1800)
        self.assertEqual(record["stop_reason"], "deadline")
        self.assertEqual(record["failed_calls"], [f"{c['stage']}:{c['id']}" for c in record["calls"]])

    def test_overrunning_call_is_abandoned_and_run_stops(self):
        runner.PER_CALL_TIMEOUT, runner.OVERRUN_GRACE, runner.MIN_CALL_SECONDS = 0.05, 0.05, 0.0
        release = threading.Event()

        def hung(case, config):
            release.wait(5)
            return completion(case["id"], "late")

        try:
            self.assertEqual(self.run_main(hung), 1)
        finally:
            release.set()
        record = self.record()
        self.assertEqual(record["stop_reason"], "call_overran")
        self.assertEqual(record["calls_sent"], 1)
        self.assertEqual(record["calls"][0]["error_type"], "orchestrator_timeout")
        self.assertEqual(record["unsent"], {"single": ["c"], "plan": ["a__plan", "c__plan"], "write": ["a", "c"]})
        self.assertEqual(self.rows("single.output.jsonl")[0]["error"]["type"], "orchestrator_timeout")

    def test_no_retries_and_failed_plan_fallback(self):
        clock = FakeClock()
        backend = FakeBackend(clock, fail_ids={"a", "a__plan"}, raise_ids={"c__plan"})
        self.assertEqual(self.run_main(backend, clock), 0)
        ids = [c[0] for c in backend.calls]
        self.assertEqual(ids, ["a", "c", "a__plan", "c__plan", "a", "c"])  # each id exactly once per stage
        record = self.record()
        self.assertEqual(record["failed_calls"], ["single:a", "plan:a__plan", "plan:c__plan", "write:a"])
        self.assertEqual(record["plan_fallback_reasons"], {"a": "failed_plan:http", "c": "failed_plan:ConnectionError"})
        self.assertNotIn("PLAN:", (self.run_dir / "write.input.jsonl").read_text())
        single = self.rows("answers.single.jsonl")
        self.assertEqual(single[0], {"id": "a", "stage": "single", "answer": "", "error_type": "http"})

    def test_token_ledger_stops_deterministically(self):
        runner.MAX_REQUESTED_TOKENS = 3072 + 512  # a lowered launch-record bound
        backend = FakeBackend()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = runner.main(["--manifest", str(self.manifest), "--source", str(self.source)], backend=backend)
        self.assertEqual(code, 2)  # the plan exceeds the lowered bound: refused before any call
        self.assertEqual(backend.calls, [])
        run = runner.Run(self.manifest, self.source, backend=backend)
        runner.MAX_REQUESTED_TOKENS = 7168
        run.validate()
        runner.MAX_REQUESTED_TOKENS = 3072 + 512
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run.execute(), 1)
        self.assertEqual(self.record()["stop_reason"], "token_limit")
        self.assertEqual([c[0] for c in backend.calls], ["a", "c", "a__plan"])

    def test_call_ledger_stops_deterministically(self):
        backend = FakeBackend()
        run = runner.Run(self.manifest, self.source, backend=backend)
        run.validate()
        runner.MAX_CALLS = 3
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run.execute(), 1)
        self.assertEqual(self.record()["stop_reason"], "call_limit")
        self.assertEqual(len(backend.calls), 3)

    def test_rerun_in_same_dir_refused(self):
        self.assertEqual(self.run_main(FakeBackend()), 0)
        backend = FakeBackend()
        self.assertEqual(self.run_main(backend), 2)
        self.assertEqual(backend.calls, [])

    def test_check_mode_sends_nothing(self):
        backend = FakeBackend()
        self.assertEqual(self.run_main(backend, time.monotonic, "--check"), 0)
        self.assertEqual(backend.calls, [])
        self.assertFalse((self.run_dir / "run_manifest.json").exists())

    def test_non_private_or_tampered_run_refused(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["stages"]["write"]["calls"] = 3
        self.manifest.write_text(json.dumps(manifest))
        backend = FakeBackend()
        self.assertEqual(self.run_main(backend), 2)
        public = self.root / "public"
        public.mkdir()
        (public / "manifest.json").write_text(json.dumps(manifest))
        with contextlib.redirect_stderr(io.StringIO()):
            code = runner.main(["--manifest", str(public / "manifest.json"), "--source", str(self.source)],
                               backend=backend)
        self.assertEqual(code, 2)
        self.assertEqual(backend.calls, [])


if __name__ == "__main__":
    unittest.main()
