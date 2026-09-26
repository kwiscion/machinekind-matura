"""Checks for matura_harness.py against SYNTHETIC fixtures only (no real exam keys).

Run:  python3 -m unittest discover -s agentsLog/Pewciu6/harness -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIX = os.path.join(ROOT, "fixtures")
CLI = os.path.join(HERE, "matura_harness.py")
sys.path.insert(0, HERE)
import matura_harness as mh  # noqa: E402


def fx(name):
    return os.path.join(FIX, name)


class Args(object):
    def __init__(self, **kw):
        self.__dict__.update(dict(corpus=None, split=None, run_id="test", model_manifest=None,
                                  scorecard=None, items_out=None, sealed_release_ack=False,
                                  quiet=True))
        self.__dict__.update(kw)


class TestScoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sc, items = mh.score(Args(outputs=fx("synthetic_outputs.jsonl"),
                                      keys=fx("synthetic_eval_keys.jsonl"),
                                      corpus=[fx("synthetic_corpus.jsonl")], split="DEV"))
        cls.items = {i["id"]: i for i in items}
        cls.labels = mh.read_jsonl(fx("synthetic_labels.jsonl"))

    def test_labeled_fixture_classifications(self):
        n = 0
        for lab in self.labels:
            if "expected_status" not in lab:
                continue
            it = self.items[lab["id"]]
            self.assertEqual(it["status"], lab["expected_status"], lab["id"])
            self.assertAlmostEqual(it["points"], lab["expected_points"], msg=lab["id"])
            self.assertEqual(sorted(it["error_categories"]),
                             sorted(lab["expected_error_categories"]), lab["id"])
            n += 1
        self.assertGreaterEqual(n, 5)

    def test_exclusions_and_denominator(self):
        excl = {e["id"]: e["reason"] for e in self.sc["exclusions"]}
        for lab in self.labels:
            if "expected_exclusion" in lab:
                self.assertEqual(excl.get(lab["id"]), lab["expected_exclusion"])
        self.assertEqual(self.sc["denominator"]["scored_items"], 9)
        self.assertEqual(self.sc["denominator"]["excluded_items"], 2)
        self.assertEqual(self.sc["orphan_output_ids"], ["syn-999"])
        self.assertLess(self.sc["strict_points_rate"], self.sc["overall"]["points_rate"])

    def test_scorecard_has_contract_fields_and_no_key_content(self):
        for f in ("run_id", "model_revisions", "split", "command", "timestamp_utc", "machine",
                  "by_task_type", "by_era", "by_topic", "error_category_counts", "exclusions",
                  "denominator", "provisional"):
            self.assertIn(f, self.sc)
        blob = json.dumps(self.sc) + json.dumps(list(self.items.values()))
        for secret in ("Kazimierz Wielki", "Casimir the Great", "expected_order", "any_of",
                       "Rzeczpospolita Obojga Narodow"):
            self.assertNotIn(secret, blob)

    def test_sealed_split_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "k.jsonl")
            with open(p, "w") as fh:
                fh.write(json.dumps({"id": "x", "split": "SEALED_TEST", "task_type": "short_answer",
                                     "rubric": {"max_points": 1, "criteria": []}}) + "\n")
            with self.assertRaises(SystemExit):
                mh.score(Args(outputs=fx("synthetic_outputs.jsonl"), keys=p))


class TestCitationAudit(unittest.TestCase):
    def test_supported_vs_unsupported(self):
        corpus = mh.load_corpus([fx("synthetic_corpus.jsonl")])
        ok = mh.audit_citation({"source_id": "ref-syn-01", "locator": "p1",
                                "claim": "Grunwald was fought in 1410 against the Teutonic Order"}, corpus)
        self.assertEqual(ok["status"], "supported")
        wrong_year = mh.audit_citation({"source_id": "ref-syn-01", "locator": "p1",
                                        "claim": "Grunwald was fought in 1411 against the Teutonic Order"},
                                       corpus)
        self.assertEqual(wrong_year["status"], "unsupported")
        missing = mh.audit_citation({"source_id": "nope", "locator": "p1", "claim": "x"}, corpus)
        self.assertEqual(missing["status"], "source_missing")


class TestLeakcheck(unittest.TestCase):
    def test_clean_input_passes_and_leaky_fails(self):
        clean = subprocess.run([sys.executable, CLI, "leakcheck",
                                "--inputs", fx("synthetic_runner_input.jsonl"),
                                "--keys", fx("synthetic_eval_keys.jsonl")],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(clean.returncode, 0, clean.stdout)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "leaky.jsonl")
            with open(p, "w") as fh:
                fh.write(json.dumps({"id": "syn-003", "prompt": "Q", "answer": "Kazimierz Wielki"}) + "\n")
            leaky = subprocess.run([sys.executable, CLI, "leakcheck", "--inputs", p,
                                    "--keys", fx("synthetic_eval_keys.jsonl")],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(leaky.returncode, 1)


class TestValidate(unittest.TestCase):
    def test_fixture_and_manifest_files_validate(self):
        self.assertEqual(mh.main(["validate", "keys", fx("synthetic_eval_keys.jsonl")]), 0)
        self.assertEqual(mh.main(["validate", "outputs", fx("synthetic_outputs.jsonl")]), 0)
        man = os.path.join(ROOT, "sources", "validation_2024_sources.jsonl")
        if os.path.exists(man):
            self.assertEqual(mh.main(["validate", "sources", man]), 0)


if __name__ == "__main__":
    unittest.main()
