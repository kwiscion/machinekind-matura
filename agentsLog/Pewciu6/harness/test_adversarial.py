"""Adversarial SYNTHETIC fixtures, adapter-shape ingestion, and blind two-rater checks (issue #11).

No real exam keys are used; see build_adversarial_fixtures.py.
Run:  python3 -m unittest discover -s agentsLog/Pewciu6/harness -v
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(os.path.dirname(HERE), "fixtures")
sys.path.insert(0, HERE)
import matura_harness as mh  # noqa: E402
from test_matura_harness import Args  # noqa: E402


def fx(name):
    return os.path.join(FIX, name)


class TestAdversarialFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sc, items = mh.score(Args(outputs=fx("adversarial_outputs.jsonl"),
                                      keys=fx("adversarial_eval_keys.jsonl"), split="DEV"))
        cls.items = {i["id"]: i for i in items}
        cls.excl = {e["id"]: e["reason"] for e in cls.sc["exclusions"] if e["reason"] != "duplicate_output"}
        cls.labels = mh.read_jsonl(fx("adversarial_labels.jsonl"))

    def test_every_label_matches(self):
        for lab in self.labels:
            with self.subTest(case=lab["id"]):
                if "expected_exclusion" in lab:
                    self.assertEqual(self.excl.get(lab["id"]), lab["expected_exclusion"])
                    self.assertNotIn(lab["id"], self.items)
                    continue
                it = self.items[lab["id"]]
                self.assertEqual(it["status"], lab["expected_status"])
                self.assertAlmostEqual(it["points"], lab["expected_points"])
                self.assertEqual(sorted(it["error_categories"]), sorted(lab["expected_error_categories"]))
        self.assertGreaterEqual(len(self.labels), 60)

    def test_record_level_denominator(self):
        d = self.sc["denominator"]
        self.assertEqual(d["excluded_items"], 3)          # timeout, error object, missing output
        self.assertEqual(d["orphan_outputs_ignored"], 1)  # id not in keys
        self.assertEqual(d["records_without_id"], 1)
        self.assertEqual(d["duplicate_records"], 3)       # retry, conflict, exact duplicate
        self.assertEqual(d["scored_items"] + d["excluded_items"], len(self.labels))
        notes = {e["id"]: e.get("note") for e in self.sc["exclusions"] if e["reason"] == "duplicate_output"}
        self.assertIn("superseded", notes["r-retry"])
        self.assertIn("first record kept", notes["r-dup-conflict"])

    def test_truncation_flagged_not_abstention(self):
        it = self.items["r-truncated-empty"]
        self.assertIn("truncated_output", it["review_flags"])
        self.assertFalse(it["abstained"])
        self.assertIn("truncated_output", self.items["r-truncated-openai"]["review_flags"])
        self.assertEqual(self.sc["truncated_outputs"], 2)

    def test_review_items_keep_upper_bound(self):
        for cid in ("e-hedge", "y-hedge"):
            self.assertEqual(self.items[cid]["points_upper_bound"], 1.0, cid)


class TestExtractors(unittest.TestCase):
    def test_extract_choices(self):
        cases = {"B": ["B"], "b": ["B"], "odp. b": ["B"], "Odpowiedź: A i C": ["A", "C"],
                 "A zatem odpowiedź B.": ["B"], "A zatem B.": ["B"], "B lub C": ["B", "C"],
                 "Odpowiedź: B, a nie C.": ["B"], "Odpowiedzi A i C są błędne.": ["A", "C"],
                 "": [], "bez litery": []}
        for text, exp in cases.items():
            with self.subTest(text=text):
                self.assertEqual(mh.extract_choices(text), exp)

    def test_grading_text_unwraps(self):
        g = lambda raw: mh.grading_text({"raw_response": raw})  # noqa: E731
        self.assertEqual(g("<think>A? C?</think>B").strip(), "B")
        self.assertEqual(g("```json\n{\"answer\": \"B\"}\n```"), "B")
        self.assertEqual(g({"answer": ["A", "C"]}), "A, C")
        self.assertEqual(g({"choices": [{"message": {"content": "C"}}]}), "C")
        self.assertEqual(g("{not json"), "{not json")
        self.assertEqual(g("<think>unterminated reasoning A B C").strip(), "")

    def test_normalize_id(self):
        self.assertEqual(mh.normalize_id(7), "7")
        self.assertEqual(mh.normalize_id(" x "), "x")
        self.assertIsNone(mh.normalize_id("  "))
        self.assertIsNone(mh.normalize_id(None))


class TestAdapterContractIngestion(unittest.TestCase):
    """Synthetic records in the CONTRACTS.md output shape plus common adapter variants."""

    def test_contract_shapes_ingest(self):
        keys = [{"id": "ad-%d" % i, "split": "DEV", "task_type": "multiple_choice",
                 "rubric": {"max_points": 1, "mode": "choice", "expected_choice": ["B"]}} for i in range(1, 5)]
        with tempfile.TemporaryDirectory() as d:
            kp = os.path.join(d, "keys.jsonl")
            mh.write_jsonl(kp, keys)
            self.assertEqual(mh.validate(Args(kind="outputs", path=fx("adapter_contract_sample.jsonl"))), 0)
            sc, items = mh.score(Args(outputs=fx("adapter_contract_sample.jsonl"), keys=kp, split="DEV"))
        by = {i["id"]: i for i in items}
        self.assertEqual([by[k]["status"] for k in ("ad-1", "ad-2", "ad-3")], ["correct"] * 3)
        self.assertEqual(sc["exclusions"][0]["reason"], "inference_error")
        self.assertAlmostEqual(by["ad-2"]["latency_s"], 0.83)
        models = {r["model"] for r in sc["model_revisions"]}
        self.assertIn("example/gemma-like-2b-it-q4", models)       # model_id alias
        revs = {r["model_revision"] for r in sc["model_revisions"]}
        self.assertIn("sha256:ffee", revs)                          # revision alias


class TestCohenKappa(unittest.TestCase):
    def test_known_values(self):
        self.assertEqual(mh.cohen_kappa([1, 2, 3], [1, 2, 3]), 1.0)
        # classic 2x2 example: po = 0.7, pe = 0.5 -> kappa 0.4
        a = [1] * 20 + [1] * 5 + [0] * 10 + [0] * 15
        b = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
        self.assertAlmostEqual(mh.cohen_kappa(a, b), 0.4, places=3)
        self.assertIsNone(mh.cohen_kappa([2, 2], [2, 2]))
        self.assertGreater(mh.cohen_kappa([0, 5, 10, 15], [1, 5, 9, 15], "quadratic"), 0.95)

    def test_blind_merge_reports_kappa_and_third_rater(self):
        with tempfile.TemporaryDirectory() as d:
            mp = os.path.join(d, "mapping.jsonl")
            mh.write_jsonl(mp, [{"blind_id": "b%d" % i, "id": "e%d" % i, "model": "m", "model_revision": "r"}
                                for i in range(4)])
            for name, pts in (("r1", [3, 10, 0, 7]), ("r2", [3, 6, 1, 7])):
                mh.write_jsonl(os.path.join(d, name + ".jsonl"),
                               [{"blind_id": "b%d" % i, "max_points": 15,
                                 "review": {"reviewer": name, "points": p}} for i, p in enumerate(pts)])
            summary, merged = mh.blind_merge(Args(reviewed=[os.path.join(d, "r1.jsonl"),
                                                            os.path.join(d, "r2.jsonl")],
                                                  mapping=mp, out=None, third_rater_range=3.0))
        self.assertEqual(summary["exact_agreement"], 0.5)
        self.assertEqual(summary["within_1_agreement"], 0.75)
        self.assertEqual(summary["needs_third_rater"], ["b1"])
        self.assertIsNotNone(summary["cohen_kappa_quadratic"])


if __name__ == "__main__":
    unittest.main()


REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
NORMALIZER = os.path.join(REPO, "scripts", "normalize_outputs.py")


def _infer_keys(d):
    keys = [{"id": "inf-%d" % i, "split": "DEV", "task_type": "multiple_choice",
             "rubric": {"max_points": 1, "mode": "choice", "expected_choice": ["B"]}} for i in range(1, 8)]
    keys[2] = {"id": "inf-3", "split": "DEV", "task_type": "short_answer",
               "rubric": {"max_points": 1, "mode": "criteria", "criteria": [
                   {"criterion_id": "city", "kind": "entity", "points": 1, "any_of": ["Źródłogród"]}]}}
    kp, cp = os.path.join(d, "keys.jsonl"), os.path.join(d, "corpus.jsonl")
    mh.write_jsonl(kp, keys)
    mh.write_jsonl(cp, [{"source_id": "ref-syn", "locator": "p1", "text": "Źródłogród był stolicą Ardenii."}])
    return kp, cp


class TestInferNormalizerIngestion(unittest.TestCase):
    """The lead's real shapes: infer.py raw records and scripts/normalize_outputs.py output.

    fixtures/infer_raw_sample.jsonl is synthetic infer.py output; fixtures/infer_normalized_sample.jsonl
    is that file passed through the real normalizer (origin/main 985aaf0).
    """

    def _score(self, name):
        with tempfile.TemporaryDirectory() as d:
            kp, cp = _infer_keys(d)
            sc, items = mh.score(Args(outputs=fx(name), keys=kp, corpus=[cp], split="DEV"))
        return sc, {i["id"]: i for i in items}

    def test_normalized_shape(self):
        self.assertEqual(mh.validate(Args(kind="outputs", path=fx("infer_normalized_sample.jsonl"))), 0)
        sc, by = self._score("infer_normalized_sample.jsonl")
        self.assertEqual({k: v["status"] for k, v in by.items()},
                         {"inf-1": "correct", "inf-2": "correct", "inf-3": "correct"})
        self.assertEqual(by["inf-3"]["citations"][0]["status"], "supported")
        excl = {e["id"]: e["reason"] for e in sc["exclusions"]}
        self.assertEqual(excl, {"inf-4": "incomplete_output", "inf-5": "incomplete_output",
                                "inf-6": "inference_error", "inf-7": "inference_error"})
        self.assertEqual(sc["denominator"]["exclusion_counts"], {"incomplete_output": 2, "inference_error": 2})
        self.assertAlmostEqual(by["inf-1"]["latency_s"], 1.234)
        self.assertIn("sha256:0000synthetic", {r["model_revision"] for r in sc["model_revisions"]})

    def test_raw_infer_shape(self):
        sc, by = self._score("infer_raw_sample.jsonl")
        self.assertEqual(sorted(by), ["inf-1", "inf-2", "inf-3"])
        self.assertTrue(all(v["status"] == "correct" for v in by.values()))
        self.assertEqual({r["backend"] for r in sc["model_revisions"]}, {"local-synthetic"})
        self.assertEqual(by["inf-1"]["latency_s"], 1.234)

    def test_prepare_rag_marker_resolves_against_rag_corpus(self):
        # prepare_rag.py prompts cite [[source_id#chunk_id]] with chunk_id "ref-1#0000", and
        # its corpus rows use locator "ref-1#0000"
        out = {"raw_response": "Zdarzenie miało miejsce w 1410 roku [[ref-1#ref-1#0000]]."}
        cits = mh.extract_citations(out)
        self.assertEqual((cits[0]["source_id"], cits[0]["locator"]), ("ref-1", "ref-1#0000"))
        corpus = {"ref-1": {"ref-1#0000": "The synthetic event (zdarzenie) occurred in 1410, miało miejsce."}}
        self.assertEqual(mh.audit_citation(cits[0], corpus)["status"], "supported")
        # retrieval_evidence is never credited as a model citation
        self.assertEqual(mh.extract_citations({"raw_response": "1410", "retrieval_evidence": [
            {"source_id": "ref-1", "chunk_id": "ref-1#0000"}]}), [])

    @unittest.skipUnless(os.path.exists(NORMALIZER), "scripts/normalize_outputs.py not in this checkout")
    def test_committed_sample_matches_current_normalizer(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("normalize_outputs", NORMALIZER)
        norm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(norm)
        fresh = [norm.normalize(r) for r in mh.read_jsonl(fx("infer_raw_sample.jsonl"))]
        self.assertEqual(fresh, mh.read_jsonl(fx("infer_normalized_sample.jsonl")),
                         "normalizer output shape drifted; regenerate the sample and re-check ingestion")
