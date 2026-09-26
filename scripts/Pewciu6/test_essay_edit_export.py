"""Tests for the #80 constrained claim-edit wave export/packet/aggregate. No model calls.

  cd scripts/Pewciu6 && python3 -m unittest test_essay_edit_export -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import essay_edit_export as ee
import essay_wave_run as wr


def make_run_dir(tmp: Path) -> Path:
    run_dir = tmp / "private" / "edit-test"
    (run_dir / "batches" / "t1").mkdir(parents=True)
    bundle = {"revision": "essay-edit-v1", "items": [
        {"item": "dev-essay-001", "topic": 1, "full_task": "TASK 1", "evidence": []},
        {"item": "dev-essay-003", "topic": 1, "full_task": "TASK 3", "evidence": []}]}
    wr.write_json_atomic(run_dir / "bundle.json", bundle)
    wr.write_json_atomic(run_dir / "ledger.json", {"revision": "essay-edit-v1", "base_url": "http://x"})
    records = [
        {"item": "dev-essay-001", "topic_id": 1, "draft_T_status": "ok", "draft_N_status": "ok",
         "draft_T_answer": "Temat nr 1\n\nT draft one.\n", "draft_N_answer": "Temat nr 1\n\nN draft one.\n",
         "final_status": "patched", "final_answer": "Temat nr 1\n\nT patched one.\n",
         "verify": {"edits_accepted": 1}},
        {"item": "dev-essay-003", "topic_id": 1, "draft_T_status": "ok", "draft_N_status": "ok",
         "draft_T_answer": "Temat nr 1\n\nT draft three.\n", "draft_N_answer": "Temat nr 1\n\nN draft three.\n",
         "final_status": "fallback", "fallback_reason": "parse:invalid_json",
         "final_answer": "Temat nr 1\n\nT draft three.\n", "verify": {"edits_accepted": 0}},
    ]
    for r in records:
        wr.append_jsonl(run_dir / "batches" / "t1" / "records.jsonl", r)
    wr.write_json_atomic(run_dir / "batches" / "t1" / "batch_manifest.json", {"status": "complete"})
    return run_dir


class ExportPacket(unittest.TestCase):
    def test_export_and_packet_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            run_dir = make_run_dir(tmp)
            out = tmp / "private" / "results"
            args = type("A", (), {"run_dir": str(run_dir), "batch": "t1", "out": str(out)})()
            self.assertEqual(ee.cmd_export(args), 0)
            answers = [json.loads(l) for l in (out / "answers.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(answers), 2)
            fallback = next(a for a in answers if a["item"] == "dev-essay-003")
            self.assertEqual(fallback["final_status"], "fallback")
            self.assertEqual(fallback["fallback_reason"], "parse:invalid_json")

            grading_dir = tmp / "private" / "grading" / "g1"
            pargs = type("A", (), {"run_dir": str(run_dir), "batch": "t1", "out": str(grading_dir), "seed": 80})()
            self.assertEqual(ee.cmd_packet(pargs), 0)
            key = json.loads((grading_dir / "key.private.json").read_text(encoding="utf-8"))
            self.assertEqual(len(key["key"]), 6)  # 2 items x 3 families, all gradable
            packet = [json.loads(l) for l in (grading_dir / "packet.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(packet), 6)
            families = {k["family"] for k in key["key"]}
            self.assertEqual(families, set(ee.FAMILIES))


def cal_row(code: str, levels=(3, 3, 3), coherence: int = 2, deduction: int = 1) -> dict:
    """A grade row under the published calibration protocol (3 aspects 0/1/3/4 + coherence 0-3 -
    error_deduction, /15)."""
    return {"code": code,
            "aspects": [{"aspect": n, "passage": "p", "claims": ["c"], "level": lvl}
                       for n, lvl in zip(("polityczny", "gospodarczy", "kulturalny"), levels)],
            "coherence": coherence, "error_deduction": deduction,
            "factual_errors": [{"claim": "x", "correction": "y", "source": "z"}] * deduction}


class ScoreRowV2(unittest.TestCase):
    def test_matches_the_published_calibration_anchor_examples(self):
        # Root's DEV011 anchor: A aspects 3/3/1, one-point deduction, coherence 2 -> 8/15.
        a = ee.score_row_v2(cal_row("A", levels=(3, 3, 1), coherence=2, deduction=1))
        self.assertEqual(a["total"], 8)
        # C3 aspects 3/3/3, one-point deduction, coherence 2 -> 10/15.
        c3 = ee.score_row_v2(cal_row("C3", levels=(3, 3, 3), coherence=2, deduction=1))
        self.assertEqual(c3["total"], 10)

    def test_total_is_recomputed_not_trusted_from_the_grader(self):
        row = cal_row("E01", levels=(4, 4, 4), coherence=3, deduction=0)
        row["total"] = 1  # a wrong/malicious value the grader might have supplied
        self.assertEqual(ee.score_row_v2(row)["total"], 15)

    def test_rejects_wrong_number_of_aspects(self):
        row = cal_row("E01")
        row["aspects"] = row["aspects"][:2]
        with self.assertRaises(ValueError):
            ee.score_row_v2(row)

    def test_rejects_invalid_aspect_level(self):
        row = cal_row("E01")
        row["aspects"][0]["level"] = 2  # not one of 0/1/3/4
        with self.assertRaises(ValueError):
            ee.score_row_v2(row)

    def test_never_goes_below_zero_or_above_fifteen(self):
        row = cal_row("E01", levels=(0, 0, 0), coherence=0, deduction=99)
        self.assertEqual(ee.score_row_v2(row)["total"], 0)


class Aggregate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.g = Path(self.tmp.name)
        self.key = {"key": [{"code": "E01", "item": "dev-essay-001", "family": "T-patched"},
                            {"code": "E02", "item": "dev-essay-003", "family": "T-patched"}],
                   "not_gradable": []}
        (self.g / "key.private.json").write_text(json.dumps(self.key), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def grade(self, name, rows):
        (self.g / f"grades_{name}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    def test_two_raters_kept_separately_and_flagged_on_large_total_gap(self):
        self.grade("graderA", [cal_row("E01", levels=(4, 4, 4), coherence=3, deduction=0),
                               cal_row("E02", levels=(3, 3, 3), coherence=2, deduction=1)])
        self.grade("graderB", [cal_row("E01", levels=(1, 1, 1), coherence=0, deduction=0),
                               cal_row("E02", levels=(3, 3, 3), coherence=2, deduction=1)])
        args = type("A", (), {"grading": str(self.g)})()
        self.assertEqual(ee.cmd_aggregate(args), 0)
        agg = json.loads((self.g / "aggregate.json").read_text(encoding="utf-8"))
        cell_disagree = agg["cells"]["dev-essay-001|T-patched|score"]  # 15 vs 3: gap 12 > 2
        self.assertTrue(cell_disagree["needs_adjudication"])
        self.assertIsNone(cell_disagree["total"])
        cell_agree = agg["cells"]["dev-essay-003|T-patched|score"]  # identical: 10 vs 10
        self.assertFalse(cell_agree["needs_adjudication"])
        self.assertEqual(cell_agree["total"], 10)
        self.assertEqual(agg["summary"]["T-patched"]["needs_adjudication"], 1)

    def test_flags_1_vs_3_aspect_disagreement_even_when_totals_are_close(self):
        # Totals: graderA 3+1+3+coh1-ded0=8, graderB 1+3+3+coh1-ded0=8 -- identical totals, but
        # aspect 1 is 3-vs-1 and aspect 2 is 1-vs-3: the protocol requires adjudication anyway.
        self.grade("graderA", [cal_row("E01", levels=(3, 1, 3), coherence=1, deduction=0),
                               cal_row("E02", levels=(3, 3, 3), coherence=1, deduction=1)])
        self.grade("graderB", [cal_row("E01", levels=(1, 3, 3), coherence=1, deduction=0),
                               cal_row("E02", levels=(3, 3, 3), coherence=1, deduction=1)])
        ee.cmd_aggregate(type("A", (), {"grading": str(self.g)})())
        agg = json.loads((self.g / "aggregate.json").read_text(encoding="utf-8"))
        cell = agg["cells"]["dev-essay-001|T-patched|score"]
        self.assertTrue(cell["needs_adjudication"])
        self.assertIn("aspect_1v3", cell["disagreement_reason"])
        self.assertIsNone(cell["total"])
        # Same totals here (identical rows) should NOT need adjudication.
        self.assertFalse(agg["cells"]["dev-essay-003|T-patched|score"]["needs_adjudication"])

    def test_adjudicate_resolves_via_shared_core(self):
        self.grade("graderA", [cal_row("E01", levels=(4, 4, 4), coherence=3, deduction=0),
                               cal_row("E02", levels=(3, 3, 3), coherence=2, deduction=1)])
        self.grade("graderB", [cal_row("E01", levels=(1, 1, 1), coherence=0, deduction=0),
                               cal_row("E02", levels=(3, 3, 3), coherence=2, deduction=1)])
        ee.cmd_aggregate(type("A", (), {"grading": str(self.g)})())
        resolutions = [{"item": "dev-essay-001", "arm": "T-patched", "stage": "score", "resolved_total": 8,
                       "note": "adjudicator settles between the two extremes"}]
        (self.g / "resolutions.json").write_text(json.dumps(resolutions), encoding="utf-8")
        self.assertEqual(ee.main(["adjudicate", "--grading", str(self.g),
                                 "--resolutions", str(self.g / "resolutions.json")]), 0)
        adjudicated = json.loads((self.g / "aggregate_adjudicated.json").read_text(encoding="utf-8"))
        self.assertEqual(adjudicated["cells"]["dev-essay-001|T-patched|score"]["resolved_total"], 8)


if __name__ == "__main__":
    unittest.main()
