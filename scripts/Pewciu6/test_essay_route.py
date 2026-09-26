"""Tests for the essay route and report (synthetic fixtures only; no model calls)."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import essay_report  # noqa: E402
import essay_route  # noqa: E402

HEADER = "Rozwiąż zadanie z historii. Odpowiadaj po polsku, zwięźle i na podstawie źródeł."
ESSAY_NAMED = (
    "Wybierz jeden z tematów i napisz wypracowanie. Praca powinna liczyć co najmniej 300 słów.\n\n"
    "Temat 1. Oceń skutki reform króla X w latach 1500–1520. Uwzględnij aspekty: polityczny i gospodarczy.\n\n"
    "Temat 2. Przedstaw znaczenie traktatu Y z 1600 roku."
)
ESSAY_NUMBERED = (
    "Zadanie zawiera trzy tematy wypracowania. Wybierz jeden z nich. Praca powinna liczyć minimum 300 wyrazów.\n"
    "1. Pierwszy temat syntetyczny o epoce A.\n2. Drugi temat syntetyczny o epoce B.\n3. Trzeci temat o epoce C.\n\n"
    "WYPRACOWANIE\nna temat nr ....\n[miejsce na odpowiedź]"
)
SHORT = "Na podstawie źródła 1. podaj nazwę dokumentu. Uzasadnij odpowiedź.\n1. Pierwszy punkt.\n2. Drugi punkt."
# Mentions an essay but has neither topics nor a length requirement: ambiguous -> bare fallback.
AMBIGUOUS = "Wyjaśnij, dlaczego autor tekstu nazwał swoje wypracowanie manifestem."


def essay_text(words_per_aspect=40, preamble=False):
    filler = " ".join(["argument"] * words_per_aspect)
    parts = []
    if preamble:
        parts.append("Oto wypracowanie na wybrany temat.")
    parts += [
        "Temat nr 1",
        "Wstęp o epoce. Teza: reformy króla X wzmocniły państwo.",
        "Aspekt 1 – polityczny:",
        f"W 1505 roku sejm w Radomiu uchwalił konstytucję Nihil novi. {filler}",
        "Aspekt 2 – gospodarczy:",
        f"W 1510 r. rozwijał się handel przez Gdańsk. {filler}",
        "**Aspekt 3 – skutki**",
        f"Po 1520 roku król Zygmunt umocnił skarb. {filler}",
        "Zakończenie: podsumowując, teza się potwierdza.",
    ]
    return "\n".join(parts)


class DetectTests(unittest.TestCase):
    def test_named_topics(self):
        info = essay_route.detect_essay(ESSAY_NAMED)
        self.assertTrue(info["is_essay"])
        self.assertEqual(info["topics"], [1, 2])

    def test_numbered_topics_and_wyrazow(self):
        info = essay_route.detect_essay(ESSAY_NUMBERED)
        self.assertTrue(info["is_essay"])
        self.assertTrue(info["features"]["length_requirement"])
        self.assertEqual(info["topics"], [1, 2, 3])

    def test_short_item_not_essay(self):
        self.assertFalse(essay_route.detect_essay(SHORT)["is_essay"])

    def test_ambiguous_mention_not_routed(self):
        self.assertFalse(essay_route.detect_essay(AMBIGUOUS)["is_essay"])

    def test_detection_ignores_id(self):
        self.assertTrue(essay_route.detect_essay(HEADER + "\n\n" + ESSAY_NAMED)["is_essay"])


class PromptTests(unittest.TestCase):
    def test_header_stripped_body_verbatim(self):
        info = essay_route.detect_essay(HEADER + "\n\n" + ESSAY_NAMED)
        self.assertEqual(info["header"], HEADER)
        prompt = essay_route.single_prompt(info, 1)
        self.assertIn(ESSAY_NAMED, prompt)
        self.assertNotIn("zwięźle", prompt)

    def test_source_first_paragraph_with_krotko_preserved(self):
        # Regression (PR #102 review P1): a leading SOURCE paragraph that says "krótko"/"zwięźle"
        # is item text, not a solver header, and must reach the solver verbatim.
        source = ("Źródło 1. Kronikarz zapisał krótko i zwięźle: „W roku 1505 sejm zebrał się w Radomiu, "
                  "a król zatwierdził uchwały.”")
        text = source + "\n\n" + ESSAY_NAMED
        header, body = essay_route.split_header(text)
        self.assertEqual(header, "")
        self.assertEqual(body, text)
        info = essay_route.detect_essay(text)
        self.assertTrue(info["is_essay"])
        self.assertIn(source, essay_route.single_prompt(info, 1))
        self.assertIn(source, essay_route.plan_prompt(info, 1))
        self.assertIn(source, essay_route.write_prompt(info, 1, "- Teza: x"))
        # An author paragraph without any solver imperative is kept too.
        author = "Autor tekstu relacjonował wydarzenia krótko, pomijając szczegóły."
        self.assertEqual(essay_route.split_header(author + "\n\n" + ESSAY_NAMED)[0], "")

    def test_harness_header_recognized(self):
        harness = ("Rozwiąż poniższe zadanie z egzaminu maturalnego z historii (poziom rozszerzony). "
                   "Odpowiadaj po polsku, zwięźle i na podstawie źródeł zamieszczonych w zadaniu oraz własnej wiedzy.")
        self.assertEqual(essay_route.split_header(harness + "\n\n" + ESSAY_NAMED), (harness, ESSAY_NAMED))

    def test_essay_header_kept(self):
        # A first paragraph that itself mentions the essay is task text, not a solver header.
        text = "Napisz wypracowanie zwięźle.\n\nTemat 1. A\n\nTemat 2. B"
        self.assertEqual(essay_route.split_header(text)[0], "")

    def test_single_prompt_requirements(self):
        prompt = essay_route.single_prompt(essay_route.detect_essay(ESSAY_NAMED), 2)
        for needle in ("co najmniej 300 słów", "350–450", "Teza:", "Aspekt 3", "Zakończenie:",
                       "Temat nr 2", "Pisz na temat nr 2", "nie pisz żadnego wstępu"):
            self.assertIn(needle, prompt)

    def test_select_topic_ablation(self):
        info = essay_route.detect_essay(ESSAY_NAMED)
        prompt = essay_route.single_prompt(info, essay_route.resolve_topic(info, 1, True, "x"))
        self.assertIn("Wybierz ten temat", prompt)
        self.assertNotIn("Pisz na temat nr", prompt)

    def test_unknown_topic_rejected(self):
        info = essay_route.detect_essay(ESSAY_NAMED)
        with self.assertRaises(ValueError):
            essay_route.resolve_topic(info, 3, False, "x")

    def test_plan_and_write_same_topic(self):
        info = essay_route.detect_essay(ESSAY_NAMED)
        plan = essay_route.plan_prompt(info, 1)
        write = essay_route.write_prompt(info, 1, "- Teza: x")
        self.assertIn("Etap 1 z 2", plan)
        self.assertIn("Pisz na temat nr 1", plan)
        self.assertIn("Pisz na temat nr 1", write)
        self.assertIn("- Teza: x", write)
        self.assertIn(ESSAY_NAMED, write)


def write_rows(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def plan_output(item_id, text, error=None, finish="stop"):
    raw = {"choices": [{"message": {"content": text}, "finish_reason": finish}]}
    return {"id": item_id, "raw_response": raw, "error": error}


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "img").mkdir()
        (self.root / "img" / "p.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        self.input = self.root / "input.jsonl"
        write_rows(self.input, [
            {"id": "a", "prompt": HEADER + "\n\n" + ESSAY_NAMED, "images": ["img/p.png"]},
            {"id": "b", "prompt": SHORT},
            {"id": "c", "prompt": ESSAY_NUMBERED},
        ])
        self.config = self.root / "base.json"
        self.config.write_text(json.dumps({"name": "t", "base_url": "http://127.0.0.1:1/v1", "model": "m", "max_output_tokens": 256}))

    def tearDown(self):
        self.tmp.cleanup()

    def run_build(self, *extra):
        out = self.root / "private" / "out"
        with contextlib.redirect_stdout(io.StringIO()):
            code = essay_route.main(["build", "--input", str(self.input), "--out-dir", str(out), "--base-config", str(self.config), *extra])
        return code, out

    def test_both_modes_envelope(self):
        code, out = self.run_build("--mode", "both")
        self.assertEqual(code, 0)
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["envelope"]["calls"], 6)
        self.assertEqual(manifest["envelope"]["requested_output_tokens"], 2 * 1536 + 2 * 512 + 2 * 1536)
        self.assertTrue(manifest["envelope"]["within_envelope"])
        self.assertEqual(manifest["envelope"]["retries"], 0)
        self.assertEqual([i["id"] for i in manifest["items"]], ["a", "c"])
        self.assertEqual(json.loads((out / "config.plan.json").read_text())["max_output_tokens"], 512)
        self.assertEqual(json.loads((out / "config.final.json").read_text())["max_output_tokens"], 1536)
        single = [json.loads(l) for l in (out / "single.input.jsonl").read_text().splitlines()]
        plan = [json.loads(l) for l in (out / "plan.input.jsonl").read_text().splitlines()]
        self.assertEqual([r["id"] for r in single], ["a", "c"])
        self.assertEqual([r["id"] for r in plan], ["a__plan", "c__plan"])
        self.assertEqual(single[0]["images"], ["../../img/p.png"])
        self.assertEqual(set(single[0]), {"id", "prompt", "images"})

    def test_envelope_exceeded_refused(self):
        rows = [{"id": f"e{i}", "prompt": ESSAY_NAMED} for i in range(3)]
        write_rows(self.input, rows)
        code, out = self.run_build("--mode", "both")
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_dry_run_writes_nothing(self):
        code, out = self.run_build("--dry-run")
        self.assertEqual(code, 0)
        self.assertFalse(out.exists())

    def test_passthrough(self):
        code, out = self.run_build("--mode", "single", "--passthrough")
        self.assertEqual(code, 0)
        rows = [json.loads(l) for l in (out / "passthrough.input.jsonl").read_text().splitlines()]
        self.assertEqual(rows, [{"id": "b", "prompt": SHORT, "images": []}])

    def test_write_from_plan_with_fallback(self):
        code, out = self.run_build("--mode", "plan")
        self.assertEqual(code, 0)
        plan_out = self.root / "plan.output.jsonl"
        write_rows(plan_out, [plan_output("a__plan", "- Teza: plan A"),
                              plan_output("c__plan", "", error={"type": "incomplete"})])
        with contextlib.redirect_stdout(io.StringIO()):
            code = essay_route.main(["write-from-plan", "--manifest", str(out / "manifest.json"),
                                     "--source", str(self.input), "--plan-output", str(plan_out)])
        self.assertEqual(code, 0)
        rows = [json.loads(l) for l in (out / "write.input.jsonl").read_text().splitlines()]
        self.assertEqual([r["id"] for r in rows], ["a", "c"])
        self.assertIn("- Teza: plan A", rows[0]["prompt"])
        self.assertNotIn("PLAN:", rows[1]["prompt"])
        record = json.loads((out / "write.record.json").read_text())
        self.assertEqual(record["plan_fallback_to_single"], ["c"])

    def test_build_refuses_non_private_out_dir(self):
        out = self.root / "public"
        with contextlib.redirect_stderr(io.StringIO()):
            code = essay_route.main(["build", "--input", str(self.input), "--out-dir", str(out), "--mode", "plan"])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists())

    def test_build_refuses_existing_out_dir(self):
        self.assertEqual(self.run_build("--mode", "plan")[0], 0)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_build("--mode", "plan")[0], 2)

    def run_write(self, out, plan_rows):
        plan_out = self.root / "plan.output.jsonl"
        write_rows(plan_out, plan_rows)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return essay_route.main(["write-from-plan", "--manifest", str(out / "manifest.json"),
                                     "--source", str(self.input), "--plan-output", str(plan_out)])

    def test_write_from_plan_rejects_duplicate_plan_ids(self):
        # Regression (PR #102 review P2): two completed rows with one plan id must not "last wins".
        code, out = self.run_build("--mode", "plan")
        code = self.run_write(out, [plan_output("a__plan", "- Teza: pierwsza"), plan_output("a__plan", "- Teza: druga"),
                                    plan_output("c__plan", "- Teza: c")])
        self.assertEqual(code, 2)
        self.assertFalse((out / "write.input.jsonl").exists())

    def test_write_from_plan_rejects_unexpected_plan_id(self):
        code, out = self.run_build("--mode", "plan")
        self.assertEqual(self.run_write(out, [plan_output("a__plan", "x"), plan_output("zzz__plan", "y")]), 2)
        self.assertEqual(self.run_write(out, [plan_output("a", "x")]), 2)  # bare id, not a plan id
        self.assertFalse((out / "write.input.jsonl").exists())

    def test_write_from_plan_rejects_malformed_records(self):
        code, out = self.run_build("--mode", "plan")
        malformed = [
            {"id": "a__plan", "raw_response": {"choices": []}},  # no error field
            {"id": "a__plan", "raw_response": "tekst", "error": None},  # completed but not a provider object
            {"id": "a__plan", "raw_response": {"choices": [{"message": {"content": ""}}]}, "error": None},
            {"id": "a__plan", "raw_response": None, "error": "boom"},  # error must be an object
            ["a__plan"],
        ]
        for row in malformed:
            self.assertEqual(self.run_write(out, [row]), 2, row)
        plan_out = self.root / "plan.output.jsonl"
        plan_out.write_text('{"id": "a__plan", "raw_response": \n', encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            code = essay_route.main(["write-from-plan", "--manifest", str(out / "manifest.json"),
                                     "--source", str(self.input), "--plan-output", str(plan_out)])
        self.assertEqual(code, 2)
        self.assertFalse((out / "write.input.jsonl").exists())

    def test_failed_and_missing_plans_are_distinct_fallbacks(self):
        code, out = self.run_build("--mode", "plan")
        self.assertEqual(self.run_write(out, [plan_output("a__plan", "", error={"type": "http", "status": 500})]), 0)
        record = json.loads((out / "write.record.json").read_text())
        self.assertEqual(record["plan_fallback_to_single"], ["a", "c"])
        self.assertEqual(record["plan_fallback_reasons"], {"a": "failed_plan:http", "c": "missing_plan"})

    def test_write_from_plan_rejects_changed_source(self):
        code, out = self.run_build("--mode", "plan")
        write_rows(self.input, [{"id": "a", "prompt": ESSAY_NAMED + " zmiana"}])
        plan_out = self.root / "plan.output.jsonl"
        write_rows(plan_out, [plan_output("a__plan", "x")])
        code = essay_route.main(["write-from-plan", "--manifest", str(out / "manifest.json"),
                                 "--source", str(self.input), "--plan-output", str(plan_out)])
        self.assertEqual(code, 2)


class ReportTests(unittest.TestCase):
    def test_structure_detected(self):
        result = essay_report.analyse(essay_text())
        self.assertTrue(result["thesis_present"])
        self.assertEqual(result["aspects_labelled"], 3)
        self.assertTrue(result["conclusion_present"])
        self.assertFalse(result["preamble"])
        self.assertTrue(result["topic_line"])
        self.assertGreaterEqual(result["distinct_years"], 3)
        self.assertIn("Radomiu", essay_report.named_terms(essay_text()))

    def test_headings_excluded_from_word_count(self):
        text = "Temat nr 1\n## Aspekt 1 – polityczny\nAspekt 2 – gospodarczy:\nTeza: jeden dwa trzy."
        self.assertEqual(essay_report.count_words(text), 3)

    def test_underlength_and_preamble(self):
        short = essay_report.analyse(essay_text(words_per_aspect=10, preamble=True))
        self.assertTrue(short["underlength"])
        self.assertTrue(short["preamble"])
        long = essay_report.analyse(essay_text(words_per_aspect=100))
        self.assertFalse(long["underlength"])
        self.assertGreaterEqual(long["words"], 300)

    def test_report_handles_both_formats_and_errors(self):
        rows = [
            plan_output("x", essay_text(100)),
            {"id": "y", "raw_response": essay_text(5), "error": None},
            {"id": "z", "raw_response": None, "error": {"type": "http"}},
        ]
        result = essay_report.report(rows)
        self.assertEqual(result["summary"]["items"], 3)
        self.assertEqual(result["summary"]["empty_or_error"], 1)
        self.assertEqual(result["summary"]["underlength"], 2)
        self.assertEqual(essay_report.report(rows), result)  # deterministic

    def test_errored_partial_is_not_a_completed_answer(self):
        # Regression (PR #102 review P2): a 301-word response that carries an error is partial.
        partial = essay_text(words_per_aspect=90)
        self.assertGreaterEqual(essay_report.count_words(partial), 300)
        rows = [
            plan_output("ok", essay_text(120)),
            plan_output("part", partial, error={"type": "incomplete"}, finish="length"),
            {"id": "part2", "raw_response": partial, "error": {"type": "timeout"}},
        ]
        result = essay_report.report(rows)
        summary = result["summary"]
        self.assertEqual(summary["completed"], 1)
        self.assertEqual(summary["empty_or_error"], 2)
        self.assertEqual(summary["partial_with_error"], 2)
        ok_words = essay_report.count_words(essay_text(120))
        self.assertEqual((summary["min_words"], summary["max_words"]), (ok_words, ok_words))
        self.assertEqual(summary["three_aspects"], 1)
        self.assertEqual(summary["underlength"], 2)
        part = result["items"][1]
        self.assertFalse(part["completed"])
        self.assertTrue(part["partial"])
        self.assertEqual(part["words"], 0)
        self.assertGreaterEqual(part["partial_diagnostics"]["words"], 300)

    def test_solver_leak_and_chatter(self):
        text = "Z uwagi na to, że nie dołączyłeś źródła, piszę ogólnie.\n**Rozstrzygnięcie:** tak\n" + essay_text()
        result = essay_report.analyse(text)
        self.assertTrue(result["preamble"])
        self.assertTrue(result["solver_format_leak"])
        self.assertFalse(essay_report.analyse(essay_text())["solver_format_leak"])
        self.assertTrue(essay_report.analyse("Wybieram temat nr 2.\n" + essay_text())["topic_line"])

    def test_years_ignore_numbers_that_are_not_years(self):
        self.assertEqual(essay_report.years("W 1569 r. oraz 12 osób, 3,5 tys. i rok 966."), [966, 1569])


class FixtureTests(unittest.TestCase):
    def test_dev_fixtures_are_routed_and_fit_envelope(self):
        path = Path(__file__).resolve().parents[2] / "agentsLog" / "Pewciu6" / "essay" / "dev_fixtures.jsonl"
        rows = essay_route.read_jsonl(path)
        self.assertTrue(4 <= len(rows) <= 6)
        for row in rows:
            self.assertEqual(row["split"], "DEV")
            self.assertEqual(row["rights_status"], "clear")
            self.assertTrue(essay_route.detect_essay(row["prompt"])["is_essay"], row["id"])


if __name__ == "__main__":
    unittest.main()
