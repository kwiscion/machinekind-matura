"""Synthetic CPU tests. No live model, HTTP, SSH or GPU operations."""
import base64
import copy
import fcntl
import sys
import time
from datetime import datetime, timezone
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("reasoning_lab", Path(__file__).with_name("reasoning_lab.py"))
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class FakeTransport:
    def __init__(self, responses=None, change_after=False):
        self.calls = []
        self.responses = list(responses or [])
        self.generated = 0
        self.change_after = change_after

    def __call__(self, base, route, payload, budget):
        budget.remaining()
        self.calls.append((route, copy.deepcopy(payload)))
        if route == "/api/version":
            return {"version": "0.34.4"}
        if route == "/api/tags":
            return {"models": [{"name": lab.MODEL, "digest": "bad" if self.generated and self.change_after else lab.DIGEST}]}
        if route == "/api/show":
            return {"capabilities": ["completion", "vision", "thinking"], "modelfile": "\n".join("FROM /mock/blobs/sha256-" + digest for digest in lab.ASSETS)}
        if route == "/api/ps":
            return {"models": [] if not self.generated else [{"name": lab.MODEL, "digest": lab.DIGEST, "context_length": 32768}]}
        if route == "/api/chat":
            self.generated += 1
            if self.responses:
                response = self.responses.pop(0)
                if isinstance(response, Exception):
                    raise response
                return response
            return response_ok(thinking="private reasoning" if payload["think"] else "")
        raise AssertionError(route)


def response_ok(answer="Odpowiedź", thinking=""):
    return {"model": lab.MODEL, "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": answer, "thinking": thinking},
            "prompt_eval_count": 50, "eval_count": 20}


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.root_patch = patch.object(lab, "PRIVATE_ROOT", self.path / "private")
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.watchdog_patch = patch.object(lab, "verify_server_deadline", return_value={"synthetic": True})
        self.watchdog_patch.start()
        self.addCleanup(self.watchdog_patch.stop)
        self.m = {"run_id": "synthetic-1", "owner": "ljaniec", "host": "synthetic-owned-host",
                  "runtime": "ollama-0.34.4", "base_url": "http://127.0.0.1:11436",
                  "model": lab.MODEL, "model_digest": lab.DIGEST, "context_length": 32768,
                  "assets": lab.ASSETS, "input_sha256": "0" * 64,
                  "deadline_utc": "2099-01-01T00:00:00Z", "deadline_epoch": 4070908800,
                  "hourly_rate_usd": 3.28, "max_calls": 120, "max_requested_tokens": 240000,
                  "max_wall_seconds": 5400, "timeout_seconds": 60, "num_predict": 1024, "readiness_calls": 0, "image_hashes": {}, "dispatch_order": lab.DISPATCH_ORDER}

    def manifest(self, changes=None):
        value = {**self.m, **(changes or {})}
        path = self.path / "manifest.json"
        path.write_text(json.dumps(value))
        return lab.load_manifest(path)

    def panel(self, rows):
        path = self.path / "panel.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.m["input_sha256"] = lab.sha256(path)
        self.m["image_hashes"] = {image: lab.sha256(path.parent / image) for row in rows for image in row.get("images", [])}
        return path, lab.load_panel(path, self.m)

    def task(self, name="baseline", case_id="id-original"):
        family = {"name": name}
        if name == "pf_statementwise":
            family["statements"] = [{"id": "A", "text": "First statement"}, {"id": "B", "text": "Second statement"}]
        return {"case": {"id": case_id, "content": "FULL ORIGINAL SOURCE"},
                "family": family, "readiness": False, "calls": 2 if name in ("critic", "pf_statementwise") else 1}

    def run_tasks(self, tasks, fake, changes=None):
        m = {**self.m, **(changes or {})}
        run = self.path / "private" / "wave"
        with patch.object(lab, "PRIVATE_ROOT", self.path / "private"):
            result = lab.execute(m, tasks, run, fake)
        answers = [json.loads(row) for row in (run / "answers.jsonl").read_text().splitlines()]
        ledger = [json.loads(row) for row in (run / "ledger.jsonl").read_text().splitlines()]
        return result, answers, ledger, run

    def test_manifest_requires_actual_mapping_rate_and_caps(self):
        self.assertEqual(self.manifest()["context_length"], 32768)
        for field, invalid in (("host", "PLACEHOLDER"), ("hourly_rate_usd", 0), ("max_calls", 121),
                               ("max_requested_tokens", 240001), ("max_wall_seconds", 5401),
                               ("num_predict", 4096), ("readiness_calls", 3), ("context_length", 4096)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.manifest({field: invalid})

    def test_endpoint_refuses_remote_credentials_paths_dns(self):
        for url in ("http://example.com", "https://127.0.0.1", "http://localhost", "http://a:b@127.0.0.1", "http://127.0.0.1/v1", "http://127.0.0.1?x=1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.manifest({"base_url": url})

    def test_panel_hash_ids_and_structured_families(self):
        path, tasks = self.panel([{"id": "a", "prompt": "source", "families": [{"name": "baseline"}, {"name": "critic"}]}])
        self.assertEqual(sum(t["calls"] for t in tasks), 3)
        self.m["input_sha256"] = "1" * 64
        with self.assertRaises(ValueError):
            lab.load_panel(path, self.m)
        with self.assertRaises(ValueError):
            self.panel([{"id": "a", "prompt": "source", "families": [{"name": "pf_statementwise"}]}])
        with self.assertRaises(ValueError):
            self.panel([{"id": "a", "prompt": "source", "families": [{"name": "baseline"}]}] * 2)

    def test_readiness_is_counted_and_planned_token_ceiling(self):
        self.m["readiness_calls"] = 1
        self.panel([{"id": "smoke", "prompt": "synthetic", "readiness": True, "readiness_expected_answer": "5", "families": [{"name": "baseline"}]}])
        self.m["max_requested_tokens"] = 1000
        with self.assertRaises(ValueError):
            self.panel([{"id": "smoke", "prompt": "synthetic", "readiness": True, "readiness_expected_answer": "5", "families": [{"name": "baseline"}]}])

    def test_wrong_synthetic_readiness_answer_stops_all_exam_baselines_unsent(self):
        self.m["readiness_calls"] = 1
        _, tasks = self.panel([
            {"id": "exam-first", "prompt": "original source", "families": [{"name": "baseline"}]},
            {"id": "synthetic-readiness", "prompt": "Return only 2+3", "readiness": True,
             "readiness_expected_answer": "5", "families": [{"name": "baseline"}]},
            {"id": "exam-second", "prompt": "original source", "families": [{"name": "baseline"}]},
        ])
        fake = FakeTransport([response_ok("wrong")])
        result, answers, ledger, _ = self.run_tasks(tasks, fake)
        self.assertEqual(fake.generated, 1)
        self.assertEqual(result["reserved_calls"], 1)
        self.assertEqual([(a["id"], a["status"]) for a in answers],
                         [("synthetic-readiness", "failed"), ("exam-first", "unsent"), ("exam-second", "unsent")])
        self.assertIn("synthetic readiness answer mismatch", result["stop_reason"])
        self.assertEqual(answers[0]["usage"][0]["eval_count"], 20)
        with self.assertRaises(ValueError):
            self.panel([{"id": "exam", "prompt": "original source", "readiness_expected_answer": "5", "families": [{"name": "baseline"}]}])

    def test_dispatch_readiness_then_families_preserves_original_id_order(self):
        self.m["readiness_calls"] = 1
        panel, tasks = self.panel([
            {"id": "first", "prompt": "source", "families": [{"name": "thinking"}, {"name": "critic"}, {"name": "baseline"}]},
            {"id": "smoke", "prompt": "synthetic", "readiness": True, "readiness_expected_answer": "5", "families": [{"name": "baseline"}]},
            {"id": "second", "prompt": "source", "families": [{"name": "thinking"}, {"name": "baseline"},
                {"name": "pf_statementwise", "statements": [{"id": "1", "text": "Statement"}]}, {"name": "critic"}]},
        ])
        self.assertEqual([(t["case"]["id"], t["family"]["name"]) for t in tasks],
                         [("smoke", "baseline"), ("first", "baseline"), ("second", "baseline"),
                          ("second", "pf_statementwise"), ("first", "critic"), ("second", "critic"),
                          ("first", "thinking"), ("second", "thinking")])
        with self.assertRaises(ValueError):
            self.manifest({"dispatch_order": list(reversed(lab.DISPATCH_ORDER))})

    def test_native_payload_images_are_same_ordered_bytes_and_explicit_think(self):
        data = [b"\x89PNG\r\n\x1a\nfirst", b"\x89PNG\r\n\x1a\nsecond"]
        for i, body in enumerate(data):
            (self.path / f"{i}.png").write_bytes(body)
        _, tasks = self.panel([{"id": "images", "prompt": "source", "images": ["0.png", "1.png"],
                                "families": [{"name": "baseline"}, {"name": "thinking"}]}])
        for task in tasks:
            payload = lab.payload_for(task, self.m, 0)
            self.assertIs(payload["think"], task["family"]["name"] == "thinking")
            self.assertIs(payload["stream"], False)
            self.assertEqual(payload["options"], {"num_ctx": 32768, "num_predict": 1024})
            encoded = payload["messages"][0]["images"]
            self.assertTrue(all(not image.startswith("data:") for image in encoded))
            self.assertEqual([base64.b64decode(image) for image in encoded], data)

    def test_budget_reserve_persisted_once_without_refund(self):
        ledger_path = self.path / "ledger"
        with ledger_path.open("w") as handle:
            budget = lab.Budget({**self.m, "max_calls": 1}, handle)
            budget.reserve({"id": "a"})
            self.assertEqual(len(ledger_path.read_text().splitlines()), 1)
            with self.assertRaises(lab.StopWave):
                budget.reserve({"id": "b"})
            self.assertEqual(budget.tokens, 1024)

    def test_deadline_and_monotonic_wall_before_reservation(self):
        for changes, mono, utc in (({"deadline_epoch": 10}, 0, 11), ({"max_wall_seconds": 1}, 2, 0)):
            with self.subTest(changes=changes), (self.path / "deadline-ledger").open("w") as handle:
                ticks = iter([0, mono])
                budget = lab.Budget({**self.m, **changes}, handle, clock=lambda: next(ticks), utc=lambda: utc)
                with self.assertRaises(lab.StopWave):
                    budget.reserve({"id": "a"})
                self.assertEqual(budget.calls, 0)

    def test_critic_two_calls_original_source_and_final_only_handoff(self):
        fake = FakeTransport([response_ok("initial"), response_ok("final")])
        result, answers, ledger, run = self.run_tasks([self.task("critic")], fake)
        self.assertEqual(result["reserved_calls"], 2)
        self.assertEqual(answers[0]["id"], "id-original")
        self.assertEqual(answers[0]["answer"], "final")
        requests = [payload for route, payload in fake.calls if route == "/api/chat"]
        self.assertTrue(requests[1]["messages"][0]["content"].startswith("FULL ORIGINAL SOURCE"))
        self.assertIn("initial", requests[1]["messages"][0]["content"])
        self.assertNotIn("private reasoning", (run / "answers.jsonl").read_text())
        self.assertNotIn("payload", answers[0])
        self.assertIn("FULL ORIGINAL SOURCE", (run / "private-envelopes.jsonl").read_text())
        self.assertIsNone(answers[0]["usage"][0]["thinking_tokens"])
        self.assertIsNone(answers[0]["usage"][0]["final_answer_tokens"])
        self.assertEqual(answers[0]["usage"][0]["eval_count"], 20)

    def test_pf_uses_explicit_statement_ids_and_full_source_each_call(self):
        fake = FakeTransport([response_ok("P"), response_ok("F")])
        result, answers, _, _ = self.run_tasks([self.task("pf_statementwise")], fake)
        self.assertEqual(answers[0]["answer"], "A. P\nB. F")
        requests = [payload for route, payload in fake.calls if route == "/api/chat"]
        self.assertTrue(all(p["messages"][0]["content"].startswith("FULL ORIGINAL SOURCE") for p in requests))

    def test_empty_length_transport_and_identity_change_stop_no_retry(self):
        empty = response_ok("")
        length = {**response_ok(), "done_reason": "length"}
        for response, changed in ((empty, False), (length, False), (lab.StopWave("transport"), False), (response_ok(), True)):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as temp:
                old = self.path
                self.path = Path(temp)
                fake = FakeTransport([response], changed)
                result, answers, ledger, _ = self.run_tasks([self.task("baseline", "one"), self.task("thinking", "two")], fake)
                self.path = old
                self.assertEqual(fake.generated, 1)
                self.assertEqual(result["reserved_calls"], 1)
                self.assertEqual([a["status"] for a in answers], ["failed", "unsent"])
                self.assertEqual([a["id"] for a in answers], ["one", "two"])
                self.assertEqual(sum(row["event"] == "reserved" for row in ledger), 1)
                if not isinstance(response, Exception):
                    self.assertEqual(answers[0]["usage"][0]["eval_count"], 20)

    def test_health_no_warmup_and_preflight_failure_preserves_unsent(self):
        fake = FakeTransport()
        fake.change_after = True
        fake.generated = 1
        result, answers, _, _ = self.run_tasks([self.task()], fake)
        self.assertEqual(result["reserved_calls"], 0)
        self.assertEqual(answers[0]["status"], "unsent")
        self.assertNotIn("/api/chat", [route for route, _ in fake.calls])

    def test_no_overwrite_or_public_raw_directory(self):
        fake = FakeTransport()
        _, _, _, run = self.run_tasks([self.task()], fake)
        with self.assertRaises(FileExistsError):
            lab.execute(self.m, [self.task()], run, fake)
        with self.assertRaises(ValueError):
            lab.execute(self.m, [self.task()], self.path / "public", fake)

    def test_check_mode_has_zero_http(self):
        panel, _ = self.panel([{"id": "check", "prompt": "synthetic", "families": [{"name": "baseline"}]}])
        manifest = self.path / "m.json"
        manifest.write_text(json.dumps(self.m))
        with patch.object(lab, "request_json", side_effect=AssertionError("HTTP forbidden")), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(lab.main(["--panel", str(panel), "--manifest", str(manifest)]), 0)

    def test_thinking_actual_behavior_and_error_truncation_context_guards(self):
        for response in ({**response_ok(), "error": ""}, {**response_ok(), "error": {}},
                         {**response_ok(), "truncated": True}, {**response_ok(), "prompt_eval_count": 32700},
                         response_ok(thinking="unexpected")):
            with self.subTest(response=response), self.assertRaises(lab.StopWave):
                lab.answer_and_usage(response, self.m, False)
        with self.assertRaises(lab.StopWave):
            lab.answer_and_usage(response_ok(), self.m, True)
        answer, usage = lab.answer_and_usage(response_ok(thinking="private actual thinking"), self.m, True)
        self.assertEqual(answer, "Odpowiedź")
        self.assertIsNone(usage["thinking_tokens"])

    def test_image_change_after_panel_declaration_blocks(self):
        image = self.path / "image.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\noriginal")
        panel, _ = self.panel([{"id": "image", "prompt": "source", "images": ["image.png"], "families": [{"name": "baseline"}]}])
        image.write_bytes(b"\x89PNG\r\n\x1a\nchanged")
        with self.assertRaises(ValueError):
            lab.load_panel(panel, self.m)

    def test_cached_image_bytes_bind_even_if_file_changes_during_infer_load(self):
        image = self.path / "image.png"
        original = b"\x89PNG\r\n\x1a\noriginal"
        changed = b"\x89PNG\r\n\x1a\nchanged"
        image.write_bytes(original)
        panel, _ = self.panel([{"id": "image", "prompt": "source", "images": ["image.png"], "families": [{"name": "baseline"}]}])
        original_loader = lab.infer.load_cases
        def swapped_image(path, cap):
            cached = original_loader(path, cap)
            image.write_bytes(changed)
            return cached
        self.m["image_hashes"]["image.png"] = lab.hashlib.sha256(changed).hexdigest()
        with patch.object(lab.infer, "load_cases", side_effect=swapped_image), self.assertRaises(ValueError):
            lab.load_panel(panel, self.m)

    def test_separate_infer_read_cannot_change_hashed_prompt_or_id(self):
        panel, _ = self.panel([{"id": "frozen", "prompt": "frozen prompt", "families": [{"name": "baseline"}]}])
        for case in ({"id": "changed", "content": "frozen prompt"}, {"id": "frozen", "content": "changed prompt"}):
            with self.subTest(case=case), patch.object(lab.infer, "load_cases", return_value=[case]), self.assertRaises(ValueError):
                lab.load_panel(panel, self.m)

    def test_shared_owner_flock_rejects_a_second_wave(self):
        owner = self.path / "private"
        owner.mkdir()
        with (owner / "reasoning-lab-owner.lock").open("a") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fake = FakeTransport()
            with self.assertRaises(BlockingIOError):
                lab.execute(self.m, [self.task()], owner / "different-wave", fake)
            self.assertEqual(fake.calls, [])
            self.assertFalse((owner / "different-wave").exists())

    def test_actual_execution_gate_is_closed_before_files_or_http(self):
        self.watchdog_patch.stop()
        fake = FakeTransport()
        with self.assertRaises(ValueError):
            lab.execute(self.m, [self.task()], self.path / "private" / "blocked", fake)
        self.assertEqual(fake.calls, [])
        self.assertFalse((self.path / "private" / "blocked").exists())
        self.watchdog_patch.start()

    def test_deadline_before_reservation_retains_unsent_not_failed(self):
        fake = FakeTransport()
        # Synthetic preflight advances UTC to the deadline, before the generation reserve.
        utc = [0]
        def transport(base, route, payload, budget):
            result = fake(base, route, payload, budget)
            if route == "/api/ps":
                utc[0] = 2
            return result
        run = self.path / "private" / "expired"
        result = lab.execute({**self.m, "deadline_epoch": 1}, [self.task()], run, transport, utc=lambda: utc[0])
        row = json.loads((run / "answers.jsonl").read_text())
        self.assertEqual(row["status"], "unsent")
        self.assertEqual(row["stages"], [{"stage": 0, "status": "unsent"}])
        self.assertEqual(result["reserved_calls"], 0)
        self.assertEqual(result["failed_families"], 0)

    def test_cpu_timeout_kills_worker_before_it_can_write_late_marker(self):
        marker = self.path / "late-marker"
        original_run = subprocess.run
        def cpu_worker(command, **kwargs):
            return original_run([sys.executable, "-c", "import time,pathlib; time.sleep(.3); pathlib.Path(" + repr(str(marker)) + ").write_text('late')"], **kwargs)
        with (self.path / "timeout-ledger").open("w") as handle:
            budget = lab.Budget({**self.m, "max_wall_seconds": .05}, handle)
            with patch.object(lab.subprocess, "run", side_effect=cpu_worker):
                with self.assertRaises(lab.StopWave):
                    lab.request_json(self.m["base_url"], "/api/chat", {}, budget)
        time.sleep(.35)
        self.assertFalse(marker.exists())

    def test_external_http_process_timeout_bounded_and_no_retry(self):
        with (self.path / "ledger").open("w") as handle:
            budget = lab.Budget(self.m, handle)
            with patch.object(lab.subprocess, "run", side_effect=subprocess.TimeoutExpired("worker", 60)) as run:
                with self.assertRaises(lab.StopWave):
                    lab.request_json(self.m["base_url"], "/api/chat", {}, budget)
                self.assertEqual(run.call_count, 1)
                self.assertLessEqual(run.call_args.kwargs["timeout"], self.m["timeout_seconds"])


if __name__ == "__main__":
    unittest.main()
