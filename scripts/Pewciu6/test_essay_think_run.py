"""Tests for the #80 paired native-thinking wave runner. No model calls.

  cd scripts/Pewciu6 && python3 -m unittest test_essay_think_run -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import contract_synthetic as cs  # noqa: E402
import essay_contract as ec  # noqa: E402
import essay_route as er  # noqa: E402
import essay_think_run as tr  # noqa: E402
import essay_wave_run as wr  # noqa: E402

EVIDENCE = [{"chunk_id": "c1", "source_id": "s1", "title": "Kazimierz III Wielki", "locator": "§1",
             "text": "Kazimierz III Wielki panował w latach 1333–1370.", "score": 1.0}]


def item() -> dict:
    row = {r["id"]: r for r in er.read_jsonl(tr.FIXTURES)}[cs.ITEM]
    info = er.detect_essay(row["prompt"])
    task = ec.parse_task(info["body"])
    return {"item": cs.ITEM, "topic": 1, "full_task": info["body"], "draft_prompt": ec.writer_prompt(task, 1),
            "evidence": EVIDENCE}


def ollama(content: str, thinking: str = "", done: str = "stop", n: int = 900) -> dict:
    return {"message": {"role": "assistant", "content": content, "thinking": thinking}, "done_reason": done,
            "eval_count": n, "prompt_eval_count": 1200, "model": tr.MODEL}


class Accounting(unittest.TestCase):
    def test_bounds_match_declaration(self):
        self.assertEqual(tr.MAX_CALLS, 24)
        self.assertEqual(tr.MAX_TOKENS, 294_912)
        self.assertEqual(tr.ARMS["T"], {"name": "K-think", "think": True, "cap": 20480})
        self.assertEqual(tr.ARMS["N"], {"name": "K-nothink", "think": False, "cap": 4096})

    def test_eval_count_is_recorded_as_is_without_split(self):
        out = tr.interpret(ollama(cs.as_json(cs.essay(3)), thinking="myślę " * 500, n=5321), True)
        self.assertEqual(out["eval_count"], 5321)
        self.assertIsNone(out.get("error"))
        for k in out:
            self.assertNotIn("final_tokens", k)
            self.assertNotIn("thinking_tokens", k)

    def test_truncated_is_a_failure_even_with_content(self):
        out = tr.interpret(ollama(cs.as_json(cs.essay(3)), thinking="x", done="length"), True)
        self.assertEqual(out["error"], "truncated")

    def test_thinking_is_never_the_essay(self):
        out = tr.interpret(ollama("", thinking=cs.essay(3)), True)
        self.assertEqual(out["error"], "empty_final_after_thinking")
        self.assertEqual(out["text"], "")
        chk = tr.stage_check(out, ec.parse_task(item()["full_task"]), 1)
        self.assertIsNone(chk)

    def test_thinking_when_off_is_flagged(self):
        self.assertEqual(tr.interpret(ollama("x", thinking="y"), False)["error"], "unexpected_thinking_when_off")

    def test_review_fixes(self):
        """Independent pre-launch review findings 4, 5, 7, 8."""
        self.assertEqual(tr.interpret(ollama("x", done=None), True)["error"], "done_reason:None")
        self.assertTrue(tr.interpret(ollama(cs.as_json(cs.essay(3))), True)["thinking_absent_when_on"])
        self.assertFalse(tr.interpret(ollama(cs.as_json(cs.essay(3))), False)["thinking_absent_when_on"])
        task = ec.parse_task(item()["full_task"])
        self.assertNotIn(tr.TRUNCATED_NOTE, tr.review_prompt(task, 1, "x", ["call_error:unexpected_thinking_when_off"], []))
        self.assertIn(tr.TRUNCATED_NOTE, tr.review_prompt(task, 1, "x", ["call_error:truncated"], []))
        rec = {}

        def send(stage, prompt):
            if stage == "review":
                raise wr.StopWave("deadline")
            return tr.interpret(ollama(cs.as_json(cs.essay(3)), "t"), True)
        with self.assertRaises(wr.StopWave):
            tr.run_arm(send, "T", item(), rec)
        self.assertIsNotNone(rec["draft_answer"])  # the completed draft survives a mid-item stop

    def test_unsent_review_is_recorded(self):
        def send(stage, prompt):
            if stage == "review":
                return {"error": "context_guard_unsent:x", "unsent": True, "text": ""}
            return tr.interpret(ollama(cs.as_json(cs.essay(3)), "t"), True)
        rec = tr.run_arm(send, "T", item())
        self.assertEqual(rec["final_status"], "failed")
        self.assertEqual(rec["unsent"][0]["stage"], "review")

    def test_context_guard(self):
        self.assertTrue(tr.prompt_fits("a" * 20000, 20480)[0])
        self.assertFalse(tr.prompt_fits("a" * 30000, 20480)[0])


class TwoStages(unittest.TestCase):
    def run_arm(self, outputs, arm="T"):
        outs, calls = iter(outputs), []

        def send(stage, prompt):
            calls.append((stage, prompt))
            return tr.interpret(next(outs), tr.ARMS[arm]["think"])
        return tr.run_arm(send, arm, item()), calls

    def test_exactly_two_calls_and_review_always_runs(self):
        good = cs.as_json(cs.essay(3))
        review = json.dumps({"uwagi": "Brak błędów.", "topic_id": 1, "body": cs.essay(4)}, ensure_ascii=False)
        rec, calls = self.run_arm([ollama(good, "t"), ollama(review, "t")])
        self.assertEqual([c[0] for c in calls], ["draft", "review"])
        self.assertIn("WYCIĄGI", calls[1][1])
        self.assertIn("Kazimierz III Wielki panował", calls[1][1])
        self.assertEqual(rec["draft_status"], "ok")
        self.assertEqual(rec["final_status"], "ok")
        self.assertEqual(rec["review"]["extras"], {"uwagi": "Brak błędów."})
        self.assertNotIn("Brak błędów", rec["final_answer"])
        self.assertIsNotNone(rec["draft"]["pre_cleanup_body"])
        self.assertIsNotNone(rec["draft"]["post_cleanup_text"])

    def test_review_repairs_mechanical_failure(self):
        review = json.dumps({"uwagi": "x", "topic_id": 1, "body": cs.essay(3)}, ensure_ascii=False)
        rec, calls = self.run_arm([ollama(cs.CASES["underlength"]), ollama(review)], arm="N")
        self.assertEqual(rec["draft_status"], "failed")
        self.assertIn("minimum", calls[1][1])  # the mechanical failure is named in the review prompt
        self.assertEqual(rec["final_status"], "ok")

    def test_truncated_draft_still_reviewed_but_counts_failed(self):
        partial = cs.as_json(cs.essay(3))[:900]
        review = json.dumps({"uwagi": "x", "topic_id": 1, "body": cs.essay(3)}, ensure_ascii=False)
        rec, calls = self.run_arm([ollama(partial, "t", done="length"), ollama(review)])
        self.assertEqual(rec["draft_status"], "failed")
        self.assertIn(tr.TRUNCATED_NOTE, calls[1][1])
        self.assertEqual(len(calls), 2)

    def test_empty_draft_leaves_review_unsent(self):
        rec, calls = self.run_arm([ollama("", thinking="t" * 10, done="length")])
        self.assertEqual(len(calls), 1)
        self.assertEqual(rec["final_status"], "failed")
        self.assertTrue(rec["unsent"][0]["reason"].startswith("no_draft_text"))

    def test_truncated_final_is_failure(self):
        good = cs.as_json(cs.essay(3))
        review = json.dumps({"uwagi": "x", "topic_id": 1, "body": cs.essay(4)}, ensure_ascii=False)
        rec, _ = self.run_arm([ollama(good), ollama(review, done="length")])
        self.assertEqual(rec["final_status"], "failed")
        self.assertIsNone(rec["final_answer"])

    def test_uwagi_outside_review_is_still_rejected(self):
        raw = json.dumps({"topic_id": 1, "body": cs.essay(3), "uwagi": cs.UNIA}, ensure_ascii=False)
        self.assertFalse(ec.parse_output(raw)["ok"])
        self.assertTrue(ec.parse_output(raw, allow_keys=("uwagi",))["ok"])


class Selection(unittest.TestCase):
    def test_six_items_two_per_era_deterministic(self):
        rows = er.read_jsonl(tr.FIXTURES)
        a, b = tr.select_items(rows), tr.select_items(list(reversed(rows)))
        self.assertEqual(a, b)
        self.assertEqual(len(a), 6)
        self.assertEqual([x["era"] for x in a], ["medieval"] * 2 + ["early_modern"] * 2 + ["modern_1795_plus"] * 2)
        self.assertEqual(len({x["item"] for x in a}), 6)

    def test_order_pairs_every_item(self):
        items = [{"item": f"i{n}"} for n in range(6)]
        plan = tr.order(items)
        self.assertEqual(len(plan), 12)
        self.assertEqual([a for _, a in plan[:4]], ["T", "N", "N", "T"])


class Ledger(unittest.TestCase):
    def test_ledger_blocks_25th_call_and_token_overrun(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "private" / "w"
            d.mkdir(parents=True)
            now = time.time()
            env = {"max_calls": tr.MAX_CALLS, "max_tokens": tr.MAX_TOKENS, "max_families": 2, "wall_seconds": 3600,
                   "per_call_max_s": 420, "retries": 0, "prior_calls": 0, "prior_tokens": 0}
            wr.write_json_atomic(d / "ledger.json", {"envelope": env, "entries": [], "families": [],
                                                     "wave_start": now, "deadline": now + 3600})
            wave = wr.Wave(d)
            for n in range(6):
                for arm in "TN":
                    for stage in tr.STAGES:
                        wave.reserve("b", arm, f"i{n}", stage, tr.ARMS[arm]["cap"], "p")
            self.assertEqual(wr.Wave.totals(wave.load()), (24, 294_912))
            with self.assertRaises(wr.StopWave):
                wave.reserve("b", "N", "i9", "draft", 1, "p")
            with self.assertRaises(wr.StopWave):
                wave.reserve("b", "X", "i0", "draft", 1, "p")


if __name__ == "__main__":
    unittest.main()
