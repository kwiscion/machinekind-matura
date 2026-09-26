"""Synthetic tests for essay_wave_run.py (fake backend and clock; no model or network calls)."""

import json
import tempfile
import time
import unittest
from pathlib import Path

import essay_wave_run as w

FIXTURE = {"id": "t1", "prompt": "Wybierz jeden z podanych tematów i napisz wypracowanie. Wypracowanie powinno liczyć "
           "co najmniej 300 słów.\n\nTemat 1. Oceń coś (1500–1600).\n\nTemat 2. Przedstaw coś innego."}


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def fake_backend(clock, text="Temat nr 1\nTeza: x.", step=10, error=None):
    calls = []

    def call(prompt, cap, timeout):
        calls.append((prompt, cap, timeout))
        clock.t += step
        if error:
            return {"error": error}
        if "Temat: N" in prompt:
            return {"text": "Temat: 2", "eval_count": 3}
        return {"text": text, "eval_count": 50}

    call.calls = calls
    return call


class WaveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.source = root / "fx.jsonl"
        self.source.write_text(json.dumps(FIXTURE, ensure_ascii=False) + "\n", encoding="utf-8")
        self.dir = root / "wave"
        self.dir.mkdir()
        ledger = {"envelope": dict(w.ENVELOPE), "wave_start": None, "deadline": None, "families": [], "entries": []}
        w.write_json_atomic(self.dir / "ledger.json", ledger)
        self.clock = Clock()

    def tearDown(self):
        self.tmp.cleanup()

    def wave(self, **kw):
        wave = w.Wave(self.dir, clock=self.clock)
        wave.backend = fake_backend(self.clock, **kw)
        return wave

    def items(self):
        return w.load_items(self.source, ["t1"])

    def test_all_families_and_dependencies(self):
        wave = self.wave()
        m = w.run_batch(wave, "b1", ["A", "B", "C", "D"], self.items(), 1, self.source)
        self.assertEqual(m["status"], "complete")
        self.assertEqual(m["attempted"], 7)
        rows = w.read_jsonl(self.dir / "batches/b1/answers.jsonl")
        self.assertEqual([r["family"] for r in rows], ["A", "B", "C", "D"])
        self.assertEqual(rows[3]["topic"], 2)
        critic_prompt = wave.backend.calls[3][0]
        self.assertIn("Temat nr 1\nTeza: x.", critic_prompt)
        ledger = wave.load()
        self.assertEqual(ledger["deadline"], 1000.0 + 5400)
        self.assertEqual(w.Wave.totals(ledger), (9 + 7, 7168 + 2048 * 4 + 768 + 1024 + 128))

    def test_batch_id_not_reusable(self):
        wave = self.wave()
        w.run_batch(wave, "b1", ["A"], self.items(), 1, self.source)
        with self.assertRaises(FileExistsError):
            w.run_batch(wave, "b1", ["B"], self.items(), 1, self.source)

    def test_no_duplicate_call_across_batches(self):
        wave = self.wave()
        w.run_batch(wave, "b1", ["A"], self.items(), 1, self.source)
        m = w.run_batch(wave, "b2", ["A"], self.items(), 1, self.source)
        self.assertEqual(m["stop_reason"], "duplicate_call:A|t1|final")
        self.assertEqual(m["attempted"], 0)

    def test_call_limit_counts_prior(self):
        ledger = json.loads((self.dir / "ledger.json").read_text())
        ledger["envelope"]["max_calls"] = 10
        w.write_json_atomic(self.dir / "ledger.json", ledger)
        wave = self.wave()
        m = w.run_batch(wave, "b1", ["B"], self.items(), 1, self.source)
        self.assertEqual(m["stop_reason"], "call_limit")
        self.assertEqual(m["attempted"], 1)
        self.assertEqual(m["unsent"], [{"family": "B", "item": "t1", "stage": "final", "reason": "call_limit"}])

    def test_token_and_family_limits(self):
        ledger = json.loads((self.dir / "ledger.json").read_text())
        ledger["envelope"]["max_tokens"] = 7168 + 2048 + 100
        w.write_json_atomic(self.dir / "ledger.json", ledger)
        m = w.run_batch(self.wave(), "b1", ["A", "D"], self.items(), 1, self.source)
        self.assertEqual(m["stop_reason"], "token_limit")
        ledger = json.loads((self.dir / "ledger.json").read_text())
        ledger["envelope"].update(max_tokens=10**6, max_families=1)
        w.write_json_atomic(self.dir / "ledger.json", ledger)
        m = w.run_batch(self.wave(), "b2", ["D"], self.items(), 1, self.source)
        self.assertEqual(m["stop_reason"], "family_limit")

    def test_deadline_and_per_call_timeout(self):
        wave = self.wave(step=5390)
        m = w.run_batch(wave, "b1", ["A", "B"], self.items(), 1, self.source)
        self.assertEqual(m["stop_reason"], "deadline")
        self.assertEqual(wave.backend.calls[0][2], 420)

    def test_timeout_shrinks_near_deadline(self):
        wave = self.wave(step=5300)
        w.run_batch(wave, "b1", ["A", "B"], self.items(), 1, self.source)
        self.assertAlmostEqual(wave.backend.calls[1][2], 100.0)

    def test_failed_dependency_unsent_no_fallback(self):
        wave = self.wave(error="truncated")
        m = w.run_batch(wave, "b1", ["B", "C"], self.items(), 1, self.source)
        self.assertEqual(m["attempted"], 1)
        reasons = sorted(u["reason"] for u in m["unsent"])
        self.assertEqual(reasons, ["failed_facts:truncated", "no_A_draft", "no_A_draft"])

    def test_transport_error_stops_batch(self):
        wave = self.wave(error="URLError")
        m = w.run_batch(wave, "b1", ["A", "B"], self.items(), 1, self.source)
        self.assertEqual(m["stop_reason"], "transport_error:URLError")
        self.assertEqual(m["attempted"], 1)
        self.assertEqual(len(m["unsent"]), 2)

    def test_grounded_variants_count_as_their_family(self):
        orig = w.retrieve
        w.retrieve = lambda info, topic: [{"chunk_id": "c1", "source_id": "s", "title": "T", "locator": "L",
                                           "text": "1500 – X – coś.", "score": 1.0}]
        try:
            wave = self.wave()
            m = w.run_batch(wave, "b1", ["A", "B3", "C3"], self.items(), 1, self.source)
        finally:
            w.retrieve = orig
        self.assertEqual(m["status"], "complete")
        self.assertEqual(m["attempted"], 5)
        self.assertEqual(wave.load()["families"], ["A", "B", "C"])
        prompts = [c[0] for c in wave.backend.calls]
        self.assertIn("[1] T – L: 1500 – X – coś.", prompts[1])
        self.assertIn("WYCIĄGI", prompts[3])
        self.assertIn("Temat nr 1\nTeza: x.", prompts[3])
        self.assertIn("nie podawaj numerów wyciągów", prompts[4])
        rows = (self.dir / "batches/b1/retrieval.jsonl").read_text().splitlines()
        self.assertEqual(len(rows), 2)

    def test_overrun_stops(self):
        def slow(prompt, cap, timeout):
            time.sleep(0.3)
            return {"text": "x"}
        orig = w.GRACE_S
        w.GRACE_S = 0
        try:
            result, overran = w.call_with_timeout(slow, "p", 1, 0.05)
        finally:
            w.GRACE_S = orig
        self.assertTrue(overran)
        self.assertEqual(result["error"], "call_overran")

    def test_selection_parse(self):
        self.assertEqual(w.parse_selection("Temat: 2", [1, 2]), 2)
        self.assertEqual(w.parse_selection("Temat nr 1", [1, 2]), 1)
        self.assertIsNone(w.parse_selection("Temat: 3", [1, 2]))
        self.assertIsNone(w.parse_selection("nie wiem", [1, 2]))


if __name__ == "__main__":
    unittest.main()
