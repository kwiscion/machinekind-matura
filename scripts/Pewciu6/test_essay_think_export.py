"""Tests for the #80 grading aggregator (issue #80 comment 5849237309: two raters grading the
same essay code must never overwrite each other). No model calls.

  cd scripts/Pewciu6 && python3 -m unittest test_essay_think_export -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import essay_think_export as te


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def grade_row(code: str, a: int = 3, b: int = 3, factual_errors=None, claims=None) -> dict:
    return {"code": code, "A": a, "B": b, "format_score": 1, "factual_errors": factual_errors or [],
            "claims": claims or []}


KEY = {"key": [{"code": "E01", "item": "dev-essay-001", "arm": "T", "stage": "draft"},
              {"code": "E02", "item": "dev-essay-001", "arm": "T", "stage": "final"}],
      # every item needs all 4 SLOTS present in `cells`; N-draft/N-final are unused by these tests
      # so they're recorded not_gradable rather than graded (real packets always cover all 4).
      "not_gradable": [{"item": "dev-essay-001", "arm": "N", "stage": "draft", "reason": "unused_in_test"},
                       {"item": "dev-essay-001", "arm": "N", "stage": "final", "reason": "unused_in_test"}]}


class RaterIdFromFilename(unittest.TestCase):
    def test_derives_rater_id(self):
        self.assertEqual(te.rater_id_from_path(Path("grades_graderA.json")), "graderA")
        self.assertEqual(te.rater_id_from_path(Path("grades_part1.json")), "part1")

    def test_rejects_unprefixed_filename(self):
        with self.assertRaises(ValueError):
            te.rater_id_from_path(Path("gradesA.json"))


class LoadGrades(unittest.TestCase):
    def test_two_raters_grading_the_same_code_are_both_kept(self):
        """This is the exact bug from #80 5849237309: grades[row["code"]]=row silently dropped
        every rater but the last one written whenever two raters graded the same code."""
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp)
            write_json(g / "grades_graderA.json", [grade_row("E01", a=3, b=3), grade_row("E02", a=2, b=2)])
            write_json(g / "grades_graderB.json", [grade_row("E01", a=1, b=1), grade_row("E02", a=2, b=2)])
            grades = te.load_grades(g)
            self.assertEqual(grades[("graderA", "E01")]["A"], 3)
            self.assertEqual(grades[("graderB", "E01")]["A"], 1)  # NOT overwritten by graderA
            self.assertEqual(len(grades), 4)

    def test_duplicate_code_within_one_rater_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp)
            write_json(g / "grades_graderA.json", [grade_row("E01"), grade_row("E01")])
            with self.assertRaises(ValueError):
                te.load_grades(g)


class ValidateCoverage(unittest.TestCase):
    def test_missing_rating_is_rejected(self):
        grades = {("graderA", "E01"): grade_row("E01")}
        with self.assertRaises(ValueError):
            te.validate_coverage(grades, ["E01", "E02"], ["graderA"])

    def test_full_coverage_passes(self):
        grades = {("graderA", "E01"): grade_row("E01"), ("graderA", "E02"): grade_row("E02")}
        te.validate_coverage(grades, ["E01", "E02"], ["graderA"])  # no raise


class AggregateSingleRaterLegacyShape(unittest.TestCase):
    """A single grades_<rater>.json file must behave exactly as the old single-rater aggregate:
    total/A/B available directly on the cell, needs_adjudication always False."""

    def test_single_rater_cell_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp)
            write_json(g / "key.private.json", KEY)
            write_json(g / "grades_solo.json", [grade_row("E01", a=3, b=2), grade_row("E02", a=1, b=1)])
            args = type("Args", (), {"grading": str(g)})()
            self.assertEqual(te.cmd_aggregate(args), 0)
            agg = json.loads((g / "aggregate.json").read_text(encoding="utf-8"))
            cell = agg["cells"]["dev-essay-001|T|draft"]
            self.assertEqual(cell["total"], 5)
            self.assertFalse(cell["needs_adjudication"])
            self.assertEqual(cell["raters"], ["solo"])


class AggregateTwoRaters(unittest.TestCase):
    def run_aggregate(self, rows_a, rows_b):
        tmp = tempfile.TemporaryDirectory()
        g = Path(tmp.name)
        write_json(g / "key.private.json", KEY)
        write_json(g / "grades_graderA.json", rows_a)
        write_json(g / "grades_graderB.json", rows_b)
        args = type("Args", (), {"grading": str(g)})()
        te.cmd_aggregate(args)
        agg = json.loads((g / "aggregate.json").read_text(encoding="utf-8"))
        tmp.cleanup()
        return agg

    def test_agreeing_raters_resolve_without_adjudication(self):
        agg = self.run_aggregate([grade_row("E01", a=3, b=3), grade_row("E02", a=2, b=2)],
                                 [grade_row("E01", a=3, b=3), grade_row("E02", a=2, b=2)])
        cell = agg["cells"]["dev-essay-001|T|draft"]
        self.assertFalse(cell["needs_adjudication"])
        self.assertEqual(cell["total"], 6)
        self.assertEqual(cell["ratings"]["graderA"]["total"], 6)
        self.assertEqual(cell["ratings"]["graderB"]["total"], 6)

    def test_disagreeing_raters_are_flagged_and_neither_score_is_picked(self):
        # graderA total=6, graderB total=2: gap of 4 > TOTAL_DISAGREEMENT_MAX
        agg = self.run_aggregate([grade_row("E01", a=3, b=3), grade_row("E02", a=2, b=2)],
                                 [grade_row("E01", a=1, b=1), grade_row("E02", a=2, b=2)])
        cell = agg["cells"]["dev-essay-001|T|draft"]
        self.assertTrue(cell["needs_adjudication"])
        self.assertIsNone(cell["total"])  # never auto-resolved to either rater's number
        self.assertEqual(cell["ratings"]["graderA"]["total"], 6)
        self.assertEqual(cell["ratings"]["graderB"]["total"], 2)

    def test_small_gap_within_tolerance_does_not_need_adjudication(self):
        agg = self.run_aggregate([grade_row("E01", a=3, b=3), grade_row("E02", a=2, b=2)],
                                 [grade_row("E01", a=2, b=3), grade_row("E02", a=2, b=2)])
        cell = agg["cells"]["dev-essay-001|T|draft"]  # totals 6 vs 5: gap of 1 <= TOTAL_DISAGREEMENT_MAX (2)
        self.assertFalse(cell["needs_adjudication"])
        # Regression: a within-tolerance but non-identical gap must still resolve to a total (the
        # mean, never either rater's own number) -- it must NOT be silently dropped to None, since
        # cmd_adjudicate refuses to touch any cell that isn't flagged needs_adjudication, so a
        # None here could never be filled in by anything.
        self.assertEqual(cell["total"], 5.5)

    def test_missing_rating_from_one_rater_raises_before_writing_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            g = Path(tmp)
            write_json(g / "key.private.json", KEY)
            write_json(g / "grades_graderA.json", [grade_row("E01"), grade_row("E02")])
            write_json(g / "grades_graderB.json", [grade_row("E01")])  # missing E02
            args = type("Args", (), {"grading": str(g)})()
            with self.assertRaises(ValueError):
                te.cmd_aggregate(args)
            self.assertFalse((g / "aggregate.json").exists())


class Adjudicate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.g = Path(self.tmp.name)
        write_json(self.g / "key.private.json", KEY)
        write_json(self.g / "grades_graderA.json", [grade_row("E01", a=3, b=3), grade_row("E02", a=2, b=2)])
        write_json(self.g / "grades_graderB.json", [grade_row("E01", a=1, b=1), grade_row("E02", a=2, b=2)])
        te.cmd_aggregate(type("Args", (), {"grading": str(self.g)})())

    def tearDown(self):
        self.tmp.cleanup()

    def test_resolves_a_flagged_cell_without_touching_the_original_aggregate(self):
        resolutions = [{"item": "dev-essay-001", "arm": "T", "stage": "draft", "resolved_total": 4,
                       "note": "adjudicator agrees with graderB's factual read"}]
        write_json(self.g / "resolutions.json", resolutions)
        args = type("Args", (), {"grading": str(self.g), "resolutions": str(self.g / "resolutions.json")})()
        self.assertEqual(te.cmd_adjudicate(args), 0)
        original = json.loads((self.g / "aggregate.json").read_text(encoding="utf-8"))
        self.assertIsNone(original["cells"]["dev-essay-001|T|draft"]["total"])  # untouched
        adjudicated = json.loads((self.g / "aggregate_adjudicated.json").read_text(encoding="utf-8"))
        self.assertEqual(adjudicated["cells"]["dev-essay-001|T|draft"]["resolved_total"], 4)
        self.assertEqual(adjudicated["adjudication"]["still_needs_adjudication"], [])

    def test_refuses_to_resolve_a_cell_that_was_never_flagged(self):
        resolutions = [{"item": "dev-essay-001", "arm": "T", "stage": "final", "resolved_total": 4}]
        write_json(self.g / "resolutions.json", resolutions)
        args = type("Args", (), {"grading": str(self.g), "resolutions": str(self.g / "resolutions.json")})()
        with self.assertRaises(ValueError):
            te.cmd_adjudicate(args)


if __name__ == "__main__":
    unittest.main()
