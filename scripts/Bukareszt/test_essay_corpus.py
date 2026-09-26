import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import essay_corpus as ec

ESSAY = "\n\n".join(["Akapit pierwszy " + "słowo " * 148 + "koniec.",
                     "Akapit drugi " + "słowo " * 148 + "koniec.",
                     "Akapit trzeci " + "słowo " * 147 + "koniec."])


class ContractTest(unittest.TestCase):
    def test_clean_essay_passes(self):
        self.assertEqual(ec.contract_errors(ESSAY), [])

    def test_defects_detected(self):
        self.assertTrue(ec.contract_errors("Oto wypracowanie:\n\n" + ESSAY))
        self.assertTrue(ec.contract_errors(ESSAY + "\n\nMam nadzieję, że pomogłem."))
        self.assertTrue(ec.contract_errors("Temat 1\n\n" + ESSAY))
        self.assertTrue(ec.contract_errors(ESSAY.split("\n\n")[0]))

    def test_repair_defects_all_fail_contract_and_keep_answer(self):
        rec = {"essay": ESSAY, "selected_topic": 1, "off_topic_paragraph": "inny temat " * 30}
        for i, kind in enumerate(ec.KINDS):
            self.assertTrue(ec.contract_errors(ec.make_defect(rec, kind, i)), kind)


class AcceptanceTest(unittest.TestCase):
    def test_self_review_and_stale_hash_rejected(self):
        teacher = {"agent": "gen"}
        essays = {"e1": {"essay": ESSAY, "teacher": teacher}, "e2": {"essay": ESSAY, "teacher": teacher},
                  "e3": {"essay": ESSAY, "teacher": teacher}}
        h = hashlib.sha256(ESSAY.encode()).hexdigest()
        verdicts = [{"id": "e1", "verdict": "accept", "reviewer": {"agent": "rev"}, "essay_sha256": h},
                    {"id": "e2", "verdict": "accept", "reviewer": {"agent": "gen"}, "essay_sha256": h},
                    {"id": "e3", "verdict": "accept", "reviewer": {"agent": "rev"}, "essay_sha256": "x"}]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "v.jsonl"
            p.write_text("".join(json.dumps(v) + "\n" for v in verdicts), encoding="utf-8")
            self.assertEqual(sorted(ec.load_accepted([p], essays)), ["e1"])


class LeakageTest(unittest.TestCase):
    def test_committed_group_map_has_no_fails(self):
        self.assertEqual(ec.cmd_groups(None), 0)
        rep = json.loads((ec.CORPUS / "leakage_report.json").read_text(encoding="utf-8"))
        self.assertEqual(rep["fails"], [])
        self.assertEqual(rep["unmapped"], [])


if __name__ == "__main__":
    unittest.main()
