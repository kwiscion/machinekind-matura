"""Tests for the #80 essay output contract and its bounded repair loop. No model calls.

  python -m unittest scripts.Pewciu6.test_essay_contract -v
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import contract_synthetic as cs  # noqa: E402
import essay_contract as ec  # noqa: E402
import essay_contract_run as cr  # noqa: E402
import essay_route as er  # noqa: E402
import essay_wave_run as wr  # noqa: E402

FIXTURES = HERE.parents[1] / "agentsLog" / "Pewciu6" / "essay" / "dev_fixtures.jsonl"
THREE_TOPICS = """Zadanie 99.
Zadanie zawiera trzy tematy. Wybierz jeden z nich do opracowania. Twoja wypowiedź
powinna liczyć minimum 300 wyrazów.
1. Pierwsza teza o średniowieczu. Zajmij stanowisko wobec powyższej tezy i je uzasadnij,
uwzględniając w swojej argumentacji aspekty: polityczny, społeczno-gospodarczy
i kulturowy.
2. Druga teza o XVII wieku. Zajmij stanowisko, uwzględniając aspekty: militarny i polityczny.
3. Trzecia teza o XX wieku. W pracy wykorzystaj źródło: fragment przemówienia z 1918 roku.

WYPRACOWANIE
na temat nr ……………..
[miejsce na odpowiedź]
"""


def fixtures() -> dict:
    return {row["id"]: row for row in er.read_jsonl(FIXTURES)}


def task_of(item: str = cs.ITEM) -> tuple[dict, dict]:
    info = er.detect_essay(fixtures()[item]["prompt"])
    return ec.parse_task(info["body"]), info


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class TaskAndSelection(unittest.TestCase):
    def test_all_dev_fixtures_parse(self):
        rows = fixtures()
        self.assertGreaterEqual(len(rows), 8)
        for item, row in rows.items():
            task = ec.parse_task(er.detect_essay(row["prompt"])["body"])
            self.assertEqual(sorted(task["topics"]), [1, 2], item)
            self.assertEqual(task["min_words"], 300, item)
            self.assertGreaterEqual(len(task["aspects"][1]), 2, item)

    def test_three_topics_aspects_sources_and_trailer(self):
        task = ec.parse_task(THREE_TOPICS)
        self.assertEqual(sorted(task["topics"]), [1, 2, 3])
        self.assertEqual(task["aspects"][1], ["polityczny", "społeczno-gospodarczy", "kulturowy"])
        self.assertEqual(task["aspects"][2], ["militarny", "polityczny"])
        self.assertTrue(task["sources"][3])
        self.assertNotIn("WYPRACOWANIE", task["topics"][3])
        self.assertNotIn("miejsce na odpowiedź", task["topics"][3])

    def test_writer_sees_only_selected_topic_and_all_requirements(self):
        task = ec.parse_task(THREE_TOPICS)
        for topic in (1, 2, 3):
            prompt = ec.writer_prompt(task, topic)
            self.assertIn(task["topics"][topic], prompt)
            for other in {1, 2, 3} - {topic}:
                self.assertNotIn(task["topics"][other], prompt)
            self.assertIn("minimum 300 wyrazów", prompt)  # global requirement kept
            for aspect in task["aspects"][topic]:
                self.assertIn(aspect, prompt)
        self.assertIn("Wymagane źródła", ec.writer_prompt(task, 3))
        self.assertIn("JEDEN, już wybrany temat nr 1", ec.writer_prompt(task, 1))

    def test_strict_selection(self):
        self.assertEqual(ec.parse_selection("Temat: 2", [1, 2, 3]), (2, "ok"))
        self.assertEqual(ec.parse_selection("**Temat nr 3**", [1, 2, 3]), (3, "ok"))
        self.assertEqual(ec.parse_selection("Temat: 1\nTemat: 2", [1, 2, 3])[0], None)
        self.assertEqual(ec.parse_selection("Temat: 4", [1, 2, 3]), (None, "not_permitted:4"))
        self.assertEqual(ec.parse_selection("Wybieram drugi, bo znam więcej faktów", [1, 2])[0], None)
        self.assertEqual(ec.parse_selection("", [1, 2])[0], None)

    def test_deterministic_policies(self):
        task = ec.parse_task(THREE_TOPICS)
        self.assertEqual(ec.select_deterministic(task, "first"), 1)
        self.assertEqual(ec.select_deterministic(task, "fixed:3"), 3)
        self.assertEqual(ec.select_deterministic(task, "most-aspects"), 1)
        with self.assertRaises(ValueError):
            ec.select_deterministic(task, "fixed:4")


class WordCounter(unittest.TestCase):
    def test_body_only_counting(self):
        self.assertEqual(ec.count_words("Ala ma kota – i psa."), 5)  # a dash is not a word
        self.assertEqual(ec.count_words("W 1569 roku unia polsko-litewska."), 5)
        self.assertEqual(ec.count_words("Temat nr 1\n\n## Wstęp\n\n**Aspekt polityczny:**\n\nAla ma kota.\n\nLiczba słów: 3"), 3)


class SyntheticMalformedOutputs(unittest.TestCase):
    def setUp(self):
        self.task, _ = task_of()

    def test_every_case_matches_expectation(self):
        self.assertEqual(set(cs.CASES), set(cs.EXPECT))
        for name, raw in cs.CASES.items():
            with self.subTest(case=name):
                check = ec.contract_check(raw, self.task, cs.TOPIC)
                exp = cs.EXPECT[name]
                self.assertEqual(check["ok"], exp["ok"], check["triggers"])
                if "trigger" in exp:
                    self.assertTrue(any(t.startswith(exp["trigger"]) for t in check["triggers"]), check["triggers"])
                if "ops" in exp:
                    self.assertEqual({o["op"] for o in check["ops"]}, exp["ops"])
                if "wrapper" in exp:
                    self.assertIn(exp["wrapper"], check["parse"]["wrappers"])

    def test_cleanup_only_removes_whole_wrappers(self):
        """Every cleaned paragraph is verbatim original text; no sentence is edited or invented."""
        for name, raw in cs.CASES.items():
            check = ec.contract_check(raw, self.task, cs.TOPIC)
            if not check["clean"]:
                continue
            body = norm(ec.parse_output(raw)["body"])
            for para in ec.paragraphs(check["clean"]):
                self.assertIn(norm(para), body, name)
            removed = sum(ec.words(o["text"]) for o in check["ops"])
            self.assertEqual(ec.words(check["clean"]) + removed, ec.words(body), name)

    def test_legitimate_prose_is_not_removed(self):
        check = ec.contract_check(cs.CASES["legit_oto"], self.task, cs.TOPIC)
        self.assertTrue(check["clean"].startswith("Oto jeden z najważniejszych okresów"))
        self.assertEqual(check["ops"], [])
        labelled = ec.contract_check(cs.CASES["labelled_conclusion"], self.task, cs.TOPIC)
        self.assertIsNone(labelled["clean"])  # ambiguous -> regenerate, never a silent deletion

    def test_rendered_answer_is_identifier_plus_prose(self):
        check = ec.contract_check(cs.CASES["grader_comments"], self.task, cs.TOPIC)
        answer = ec.render_answer(cs.TOPIC, check["clean"])
        self.assertTrue(answer.startswith("Temat nr 1\n\n"))
        for junk in ("Liczba słów", "Komentarz", "Mam nadzieję", "{", "topic_id"):
            self.assertNotIn(junk, answer)

    def test_repair_prompt_names_precise_trigger(self):
        check = ec.contract_check(cs.CASES["underlength"], self.task, cs.TOPIC)
        prompt = ec.repair_prompt(self.task, cs.TOPIC, check["clean"], check, 1)
        self.assertIn("97 słów", prompt)
        self.assertIn("nie dodawaj powtórzeń", prompt)
        multi = ec.contract_check(cs.CASES["all_topics"], self.task, cs.TOPIC)
        self.assertIn("wyłącznie o temacie nr 1", ec.repair_prompt(self.task, cs.TOPIC, "", multi, 1))
        aspect = ec.contract_check(cs.CASES["missing_aspect"], self.task, cs.TOPIC)
        self.assertIn("kulturalny", ec.repair_prompt(self.task, cs.TOPIC, aspect["clean"] or "", aspect, 1))


class RepairLoop(unittest.TestCase):
    def setUp(self):
        self.task, self.info = task_of()

    def run_with(self, outputs, select="model", critic=False, budget=10, soft_repair=False):
        outs, calls = iter(outputs), []

        def send(stage, prompt):
            calls.append((stage, prompt))
            return {"text": next(outs)}
        rec = cr.run_item(send, self.task, self.info, cs.ITEM, select, critic, lambda: budget - len(calls),
                          soft_repair=soft_repair)
        return rec, calls

    def test_multi_topic_is_regenerated_not_picked(self):
        good = cs.as_json(cs.essay(4))
        rec, calls = self.run_with(["Temat: 1", cs.CASES["all_topics"], good])
        self.assertEqual([c[0] for c in calls], ["select", "draft", "repair1"])
        self.assertEqual(rec["final_stage"], "repair1")
        self.assertEqual(rec["repairs"][0]["triggers"][0].split(":")[0], "multi_topic")
        self.assertFalse(rec["initial_ok"])
        self.assertIn("Temat nr 1", rec["answer"])

    def test_at_most_two_repairs_then_fail_without_answer(self):
        rec, calls = self.run_with(["Temat: 1"] + [cs.CASES["invalid_json"]] * 5)
        self.assertEqual([c[0] for c in calls], ["select", "draft", "repair1", "repair2"])
        self.assertEqual(rec["status"], "failed")
        self.assertIsNone(rec["answer"])
        self.assertEqual(len(rec["versions"]), 3)  # initial + failed outputs are all kept

    def test_soft_target_repair_keeps_passing_initial_if_repair_breaks(self):
        rec, calls = self.run_with(["Temat: 1", cs.CASES["preamble"], cs.CASES["invalid_json"],
                                    cs.CASES["invalid_json"]], soft_repair=True)
        self.assertEqual(len(rec["repairs"]), 2)
        self.assertEqual(rec["final_stage"], "draft")  # last contract-passing version
        self.assertEqual(rec["status"], "ok")

    def test_soft_trigger_alone_spends_no_repair_by_default(self):
        rec, calls = self.run_with(["Temat: 1", cs.CASES["preamble"]])  # passes hard, 389 < 400 words
        self.assertEqual([c[0] for c in calls], ["select", "draft"])
        self.assertEqual(rec["final_stage"], "draft")
        self.assertEqual(rec["repairs"], [])

    def test_exhausted_budget_is_recorded(self):
        rec, calls = self.run_with(["Temat: 1", cs.CASES["underlength"]], budget=2)
        self.assertEqual(len(calls), 2)
        self.assertEqual(rec["unsent"], [{"stage": "repair1", "reason": "budget_exhausted"}])
        self.assertEqual(rec["status"], "failed")

    def test_bad_selection_falls_back_to_declared_policy(self):
        rec, _ = self.run_with(["Wybieram temat pierwszy albo drugi", cs.as_json(cs.essay(4))])
        self.assertEqual(rec["selection"]["fallback"], "most-aspects")
        self.assertEqual(rec["topic_id"], 1)

    def test_critic_needs_two_calls_and_is_separate_from_contract(self):
        good = cs.as_json(cs.essay(4))
        rec, calls = self.run_with(["Temat: 1", good, "1. Brak błędów.", good], critic=True, budget=4)
        self.assertEqual([c[0] for c in calls], ["select", "draft", "critic", "rewrite"])
        self.assertIn("UWAGI EGZAMINATORA", calls[3][1])
        self.assertEqual(rec["final_stage"], "rewrite")
        rec2, calls2 = self.run_with(["Temat: 1", good], critic=True, budget=3)
        self.assertEqual([c[0] for c in calls2], ["select", "draft"])
        self.assertEqual({u["reason"] for u in rec2["unsent"]}, {"budget_below_2_calls"})

    def test_writer_prompt_in_loop_has_single_topic(self):
        task = ec.parse_task(THREE_TOPICS)
        info = {"body": THREE_TOPICS}
        prompts = []

        def send(stage, prompt):
            prompts.append(prompt)
            return {"text": "Temat: 2" if stage == "select" else cs.as_json(cs.essay(4), topic=2)}
        cr.run_item(send, task, info, "x", "model", False, lambda: 10)
        self.assertIn("Pierwsza teza", prompts[0])  # the selector sees the full task
        for p in prompts[1:]:
            self.assertNotIn("Pierwsza teza", p)
            self.assertNotIn("Trzecia teza", p)


class LedgerEnforcement(unittest.TestCase):
    def test_ledger_stops_at_max_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "private" / "k"
            run_dir.mkdir(parents=True)
            now = time.time()
            env = {"max_calls": 2, "max_tokens": 10_000, "max_families": 1, "wall_seconds": 600,
                   "per_call_max_s": 60, "retries": 0, "prior_calls": 0, "prior_tokens": 0}
            wr.write_json_atomic(run_dir / "ledger.json", {"envelope": env, "entries": [], "families": [],
                                                           "wave_start": now, "deadline": now + 600})
            wave = wr.Wave(run_dir, backend=lambda p, cap, t: {"text": cs.CASES["invalid_json"]})
            task, info = task_of()

            def send(stage, prompt):
                cap = cr.CAPS["repair" if stage.startswith("repair") else stage]
                entry, timeout = wave.reserve("b", cr.FAMILY, cs.ITEM, stage, cap, prompt)
                result, _ = wr.call_with_timeout(wave.backend, prompt, cap, timeout)
                wave.settle(entry["seq"], "ok")
                return result
            with self.assertRaises(wr.StopWave) as ctx:
                cr.run_item(send, task, info, cs.ITEM, "first", False, lambda: 99)
            self.assertEqual(str(ctx.exception), "call_limit")
            self.assertEqual(len(wave.load()["entries"]), 2)

    def test_declared_item_budget(self):
        b = cr.item_budget(True, True)
        self.assertEqual(b["stages"], ["select", "draft", "critic", "rewrite", "repair1", "repair2"])
        self.assertEqual(b["max_tokens"], 128 + 2048 + 1024 + 2048 + 2 * 2048)
        self.assertEqual(cr.item_budget(False, False)["max_calls"], 3)


if __name__ == "__main__":
    unittest.main()
