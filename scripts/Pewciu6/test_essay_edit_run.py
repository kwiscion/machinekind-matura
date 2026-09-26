"""Tests for the #80 constrained claim-edit wave runner. No model calls.

  cd scripts/Pewciu6 && python3 -m unittest test_essay_edit_run -v
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
import essay_edit_run as er_run  # noqa: E402
import essay_wave_run as wr  # noqa: E402


def clean_essay(repeat: int) -> str:
    """A T-draft in the real pipeline is always the already-cleaned text (ec.clean_body's output),
    never the raw model text; clean_body is idempotent on its own output, so tests that exercise
    evaluate_edits/apply_edits/revalidate_patch must build their fixture the same way, or a merely
    cosmetic whitespace normalization (e.g. a trailing space before a paragraph break) looks like a
    "patch_altered_by_cleanup" false positive."""
    return ec.clean_body(cs.essay(repeat), 1)["text"]


TASK = ec.parse_task(
    "Wybierz jeden z podanych tematów i napisz wypracowanie. W wypracowaniu sformułuj stanowisko (tezę) i "
    "uzasadnij je, odwołując się do wiedzy historycznej. Wypracowanie powinno liczyć co najmniej 300 słów.\n\n"
    "Temat 1. Oceń znaczenie panowania Kazimierza III Wielkiego (1333–1370) dla rozwoju państwa polskiego. "
    "W pracy uwzględnij aspekty: polityczny, gospodarczy i kulturalny.\n\n"
    "Temat 2. Inny temat, nieużywany w tych testach.\n")


class Bounds(unittest.TestCase):
    def test_bounds_match_declaration(self):
        self.assertEqual(er_run.MAX_CALLS, 19)
        self.assertEqual(er_run.MAX_TOKENS, 290_816)
        self.assertEqual(er_run.THIS_RUN_MAX_CALLS, 18)
        self.assertEqual(er_run.THIS_RUN_MAX_TOKENS, 270_336)
        self.assertEqual(er_run.ARMS["T"], {"name": "K-think", "think": True, "cap": 20480})
        self.assertEqual(er_run.ARMS["N"], {"name": "K-nothink", "think": False, "cap": 4096})
        self.assertEqual(er_run.VERIFY_CAP, 20480)
        self.assertTrue(er_run.VERIFY_THINK)
        self.assertEqual(list(er_run.FIXTURE_IDS),
                         ["dev-essay-001", "dev-essay-003", "dev-essay-004", "dev-essay-005",
                          "dev-essay-009", "dev-essay-010"])


class DraftOrder(unittest.TestCase):
    def test_alternates_by_index(self):
        self.assertEqual(er_run.draft_order(0), ["T", "N"])
        self.assertEqual(er_run.draft_order(1), ["N", "T"])
        self.assertEqual(er_run.draft_order(2), ["T", "N"])


class ParseEditResponse(unittest.TestCase):
    def test_ok_empty_edits(self):
        out = er_run.parse_edit_response('{"edits": [], "notes": "brak błędów"}')
        self.assertTrue(out["ok"])
        self.assertEqual(out["edits"], [])
        self.assertEqual(out["notes"], "brak błędów")

    def test_ok_one_edit(self):
        raw = '{"edits": [{"original": "1335 roku", "replacement": "1335 r.", "reason": "skrót"}]}'
        out = er_run.parse_edit_response(raw)
        self.assertTrue(out["ok"])
        self.assertEqual(len(out["edits"]), 1)
        self.assertEqual(out["edits"][0]["original"], "1335 roku")

    def test_rejects_extra_top_level_key(self):
        out = er_run.parse_edit_response('{"edits": [], "body": "cały nowy esej"}')
        self.assertFalse(out["ok"])
        self.assertIn("extra_keys", out["error"])

    def test_rejects_invalid_json(self):
        out = er_run.parse_edit_response("to nie jest JSON")
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "invalid_json")

    def test_rejects_empty(self):
        out = er_run.parse_edit_response("")
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "empty")

    def test_rejects_edit_with_extra_key(self):
        raw = '{"edits": [{"original": "x", "replacement": "y", "reason": "z", "confidence": 0.9}]}'
        out = er_run.parse_edit_response(raw)
        self.assertFalse(out["ok"])
        self.assertIn("bad_edit_shape", out["error"])

    def test_accepts_code_fenced_json(self):
        raw = '```json\n{"edits": []}\n```'
        out = er_run.parse_edit_response(raw)
        self.assertTrue(out["ok"])


class EvaluateEdits(unittest.TestCase):
    """Real-case regression: draft text is the shared synthetic essay body (not model output)."""

    def setUp(self):
        self.draft = clean_essay(1)  # each paragraph appears exactly once

    def test_accepts_unambiguous_single_occurrence(self):
        edits = [{"original": "1343 roku pokój w Kaliszu", "replacement": "1343 roku pokój kaliski",
                 "reason": "nazwa"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(len(out["accepted"]), 1)
        self.assertEqual(out["rejected"], [])
        patched = er_run.apply_edits(self.draft, out["accepted"])
        self.assertIn("1343 roku pokój kaliski", patched)
        self.assertNotIn("1343 roku pokój w Kaliszu", patched)

    def test_rejects_invented_span(self):
        edits = [{"original": "fragment którego tu nie ma wcale", "replacement": "cokolwiek", "reason": "x"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        self.assertEqual(out["rejected"][0]["reject_reason"], "not_found")

    def test_rejects_ambiguous_multiple_occurrences(self):
        draft = clean_essay(2)  # POL/GOS/KUL each appear twice, verbatim
        edits = [{"original": "W aspekcie politycznym", "replacement": "W aspekcie polityki", "reason": "styl"}]
        out = er_run.evaluate_edits(draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        self.assertEqual(out["rejected"][0]["reject_reason"], "ambiguous_multiple_occurrences")

    def test_rejects_overlapping_spans(self):
        edits = [{"original": "1343 roku pokój w Kaliszu", "replacement": "1343 r. pokój kaliski", "reason": "a"},
                 {"original": "pokój w Kaliszu z zakonem", "replacement": "pokój z zakonem krzyżackim",
                 "reason": "b"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        reasons = {r["reject_reason"] for r in out["rejected"]}
        self.assertEqual(reasons, {"overlap"})

    def test_rejects_span_too_large(self):
        edits = [{"original": self.draft[:600], "replacement": "krótszy tekst", "reason": "x"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        self.assertEqual(out["rejected"][0]["reject_reason"], "span_too_large")

    def test_rejects_disguised_full_rewrite_via_replacement_size(self):
        edits = [{"original": "1343 roku", "replacement": "x" * 500, "reason": "rozwinięcie"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        self.assertEqual(out["rejected"][0]["reject_reason"], "replacement_too_large")

    def test_rejects_replacement_with_paragraph_break(self):
        edits = [{"original": "1343 roku", "replacement": "1343 roku.\n\nNowy akapit z nowymi faktami.",
                 "reason": "x"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        self.assertEqual(out["rejected"][0]["reject_reason"], "replacement_not_prose")

    def test_rejects_replacement_naming_another_topic(self):
        edits = [{"original": "1343 roku", "replacement": "Temat 2. 1343 roku", "reason": "x"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        self.assertEqual(out["rejected"][0]["reject_reason"], "replacement_other_topic")

    def test_deletion_is_an_empty_replacement(self):
        edits = [{"original": " Ujednolicił też prawo, wydając statuty wiślicko-piotrkowskie, co umacniało "
                              "władzę monarchy w całym kraju.", "replacement": "", "reason": "niepotwierdzone"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(len(out["accepted"]), 1)
        patched = er_run.apply_edits(self.draft, out["accepted"])
        self.assertNotIn("wiślicko-piotrkowskie", patched)


class RevalidatePatch(unittest.TestCase):
    def test_ok_when_length_and_topic_hold(self):
        out = er_run.revalidate_patch(clean_essay(3), TASK, 1)
        self.assertTrue(out["ok"])

    def test_flags_underlength(self):
        out = er_run.revalidate_patch("Za krótki tekst.", TASK, 1)
        self.assertFalse(out["ok"])
        self.assertTrue(any(h.startswith("underlength") for h in out["hard"]))

    def test_flags_other_topic_marker(self):
        text = clean_essay(1) + "\n\nTemat 2. Nowy wątek."
        out = er_run.revalidate_patch(text, TASK, 1)
        self.assertFalse(out["ok"])
        self.assertTrue(any(h.startswith("multi_topic") for h in out["hard"]))


class RunVerifyEndToEnd(unittest.TestCase):
    """Full parse -> evaluate -> apply -> revalidate path, on real (non-model) essay text."""

    def test_successful_patch(self):
        # repeat=3 so the draft clears the 300-word floor; the edited span sits in INTRO, which is
        # never repeated, so it stays unambiguous even though POL/GOS/KUL each occur three times.
        draft = clean_essay(3)
        raw = ('{"edits": [{"original": "odbudowy Królestwa po rozbiciu dzielnicowym", '
              '"replacement": "odbudowy Królestwa po rozbiciu dzielnicowym w XIV wieku", '
              '"reason": "doprecyzowanie"}]}')
        parsed = er_run.parse_edit_response(raw)
        outcome = er_run.run_verify(draft, TASK, 1, parsed)
        self.assertEqual(outcome["status"], "patched")
        self.assertIn("odbudowy Królestwa po rozbiciu dzielnicowym w XIV wieku", outcome["patched_text"])
        self.assertEqual(len(outcome["accepted"]), 1)
        self.assertEqual(outcome["rejected"], [])

    def test_fallback_on_parse_failure(self):
        parsed = er_run.parse_edit_response("not json")
        outcome = er_run.run_verify(clean_essay(3), TASK, 1, parsed)
        self.assertEqual(outcome["status"], "fallback")
        self.assertTrue(outcome["reason"].startswith("parse:"))
        self.assertIsNone(outcome["patched_text"])

    def test_fallback_when_patch_would_underlength(self):
        draft = "\n\n".join([cs.INTRO, cs.POL, cs.END])  # already near the floor
        # delete almost everything: patched text drops below the hard minimum
        raw = f'{{"edits": [{{"original": {er_run_json(cs.POL)}, "replacement": "", "reason": "błąd"}}]}}'
        parsed = er_run.parse_edit_response(raw)
        outcome = er_run.run_verify(draft, TASK, 1, parsed)
        self.assertEqual(outcome["status"], "fallback")
        self.assertTrue(outcome["reason"].startswith("revalidate:"))


def er_run_json(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


class LedgerInit(unittest.TestCase):
    """Regression for the reviewer-found bug: cmd_init omitted "families", so the very first
    wave.reserve() call raised KeyError (not a StopWave) and crashed before any model call."""

    def test_families_key_present_and_reserve_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "private" / "edit-test"
            run_dir.mkdir(parents=True)
            wr.write_json_atomic(run_dir / "bundle.json", {"revision": er_run.REVISION})
            deadline = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 1800))
            start = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            args = type("Args", (), {"run_dir": str(run_dir), "deadline_utc": deadline,
                                     "declared_start_utc": start,
                                     "base_url": "http://127.0.0.1:11434"})()
            self.assertEqual(er_run.cmd_init(args), 0)
            ledger = json.loads((run_dir / "ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(ledger["families"], [])
            self.assertEqual(ledger["envelope"]["max_calls"], 18)
            self.assertEqual(ledger["envelope"]["max_tokens"], 270_336)
            self.assertEqual(ledger["declared_ceiling"], {"max_calls": 19, "max_tokens": 290_816})
            wave = wr.Wave(run_dir)
            for stage, cap in (("T", 20480), ("N", 4096), ("verify", 20480)):
                entry, timeout = wave.reserve("t1", "edit", "dev-essay-001", stage, cap, "prompt")
                self.assertEqual(entry["status"], "reserved")
                self.assertGreater(timeout, 0)


class CumulativeEditBudget(unittest.TestCase):
    def test_rejects_more_than_max_edit_count(self):
        # zero-padded so no target ("fakt 01") is ever a substring of another ("fakt 010" doesn't
        # exist; "fakt 10" is a different 2-digit token) -- otherwise count_occurrences would (
        # correctly) call the shorter one ambiguous instead of exercising the count-budget check.
        draft = " ".join(f"Zdanie {i:02d} ma fakt {i:02d}." for i in range(20))
        n = er_run.MAX_EDIT_COUNT + 1
        edits = [{"original": f"fakt {i:02d}", "replacement": f"fakcik {i:02d}", "reason": "x"}
                for i in range(n)]
        out = er_run.evaluate_edits(draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        reasons = {r["reject_reason"] for r in out["rejected"]}
        self.assertEqual(reasons, {"cumulative_edit_budget_exceeded"})
        self.assertEqual(len(out["rejected"]), n)

    def test_rejects_cumulative_span_share_even_when_each_edit_is_individually_fine(self):
        segments = [f"Fragment{i:03d} niepowtarzalny tekst numer {i} z dodatkowymi slowami dla dlugosci."
                   for i in range(4)]
        draft = " ".join(segments)
        self.assertLess(len(segments[0]), er_run.MAX_EDIT_SPAN_SHARE * len(draft))  # ok individually
        self.assertGreater(sum(len(s) for s in segments[:2]),
                           er_run.MAX_CUMULATIVE_SPAN_SHARE * len(draft))  # but not together
        edits = [{"original": s, "replacement": s + "!", "reason": "x"} for s in segments[:2]]
        out = er_run.evaluate_edits(draft, 1, edits)
        self.assertEqual(out["accepted"], [])
        self.assertTrue(all(r["reject_reason"] == "cumulative_edit_budget_exceeded" for r in out["rejected"]))


class TighterExpansionLimit(unittest.TestCase):
    def test_rejects_moderate_expansion_that_the_old_4x_limit_would_have_allowed(self):
        draft = clean_essay(1)
        orig = "1343 roku pokój w Kaliszu"
        repl = orig + " " + ("dodatkowy nowy szczegół historyczny spoza wyciągów " * 3).strip()
        self.assertLessEqual(len(repl), 4 * len(orig) + 200)  # would have passed the old rule
        self.assertGreater(len(repl), er_run.MAX_REPLACEMENT_EXPANSION * len(orig) + er_run.MAX_REPLACEMENT_EXTRA_CHARS)
        out = er_run.evaluate_edits(draft, 1, [{"original": orig, "replacement": repl, "reason": "x"}])
        self.assertEqual(out["rejected"][0]["reject_reason"], "replacement_too_large")


class ReplacementProseGuards(unittest.TestCase):
    def setUp(self):
        self.draft = clean_essay(1)

    def test_rejects_single_newline_in_replacement(self):
        edits = [{"original": "1343 roku", "replacement": "1343 roku.\nUwaga: sprawdzone.", "reason": "x"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(out["rejected"][0]["reject_reason"], "replacement_not_prose")

    def test_rejects_heading_marker_in_replacement(self):
        edits = [{"original": "1343 roku", "replacement": "1343 roku ## nowy fakt", "reason": "x"}]
        out = er_run.evaluate_edits(self.draft, 1, edits)
        self.assertEqual(out["rejected"][0]["reject_reason"], "replacement_not_prose")


class RevalidatePatchCleanupGate(unittest.TestCase):
    def test_flags_patch_that_cleanup_would_alter(self):
        patched = "Oto moja odpowiedź:\n\n" + clean_essay(3)
        out = er_run.revalidate_patch(patched, TASK, 1)
        self.assertFalse(out["ok"])

    def test_unaltered_valid_patch_still_passes(self):
        out = er_run.revalidate_patch(clean_essay(3), TASK, 1)
        self.assertTrue(out["ok"])


def build_item(item_id: str = cs.ITEM, topic: int = 1) -> dict:
    import essay_route as route
    rows = {r["id"]: r for r in route.read_jsonl(er_run.FIXTURES)}
    info = route.detect_essay(rows[item_id]["prompt"])
    task = ec.parse_task(info["body"])
    return {"item": item_id, "topic": topic, "full_task": info["body"],
            "draft_prompt": ec.writer_prompt(task, topic), "evidence": []}


def stub_result(text: str, error: str | None = None) -> dict:
    return {"text": text, "error": error, "eval_count": 500 if text else 0, "prompt_eval_count": 10,
            "done_reason": "length" if error == "truncated" else "stop",
            "thinking_chars": 0, "content_chars": len(text)}


class RunItemVerifyGating(unittest.TestCase):
    """Regression for the reviewer's requested case: verify must never be attempted when the
    T-draft itself failed (nothing valid exists to run the verifier on, or to fall back to)."""

    def test_verify_never_called_when_t_draft_fails(self):
        item = build_item()
        calls = []

        def send(stage, prompt, cap, think):
            calls.append(stage)
            if stage == "T":
                return stub_result("", error="empty")
            if stage == "N":
                return stub_result(cs.as_json(cs.essay(3)))
            raise AssertionError(f"verify must never be reserved when the T-draft failed (got {stage!r})")

        rec = {"draft_order": ["T", "N"]}
        er_run.run_item(send, item, rec)
        self.assertEqual(calls, ["T", "N"])
        self.assertEqual(rec["final_status"], "failed")
        self.assertIsNone(rec["final_answer"])

    def test_verify_called_exactly_once_after_both_drafts_regardless_of_order(self):
        item = build_item()
        calls = []
        t_body = cs.as_json(cs.essay(3))

        def send(stage, prompt, cap, think):
            calls.append(stage)
            if stage in ("T", "N"):
                return stub_result(t_body)
            if stage == "verify":
                return stub_result('{"edits": []}')
            raise AssertionError(stage)

        rec = {"draft_order": ["N", "T"]}
        er_run.run_item(send, item, rec)
        self.assertEqual(calls, ["N", "T", "verify"])
        self.assertEqual(rec["final_status"], "patched")
        self.assertEqual(rec["verify"]["edits_accepted"], 0)


if __name__ == "__main__":
    unittest.main()
