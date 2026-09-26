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


class DependencyTest(unittest.TestCase):
    def test_declared_sol_dependencies_are_merged(self):
        cfg, _, c2p = ec.load_clusters()
        comp = ec.components(cfg)
        self.assertEqual(comp["C-reformation"], comp["C-vienna"])
        self.assertEqual(comp["C-league"], comp["C-cold-war"])
        for a, b in (("C-reformation", "C-vienna"), ("C-league", "C-cold-war")):
            self.assertEqual(ec.partition_family(c2p[a]), ec.partition_family(c2p[b]))

    def test_root_declared_dependencies_ingested_and_rows_hash_checked(self):
        cfg, _, c2p = ec.load_clusters()
        edges = ec.root_dependency_edges(cfg)
        if not (ec.ROOT_DIRS["root_sol"] / "repairs.jsonl").exists():
            self.skipTest("root Sol corpus not present")
        pairs = {tuple(sorted(e["clusters"])) for e in edges}
        self.assertIn(("C-reformation", "C-vienna"), pairs)
        self.assertIn(("C-cold-war", "C-league"), pairs)
        rows, rejected = ec.root_accepted_rows(cfg)
        self.assertEqual(rejected, [])
        self.assertTrue(all(ec.partition_family(c2p[r["source_group_id"]]) == "train" for r in rows))

    def test_dependency_across_eval_and_train_fails(self):
        cfg, _, _ = ec.load_clusters()
        orig = ec.load_clusters
        bad = json.loads(json.dumps(cfg))
        bad["dependencies"].append({"clusters": ["C-thirty-years", "C-persian-wars"], "reason": "test"})
        k2c = {m: c for c, v in bad["clusters"].items() for m in v["members"]}
        c2p = {c: p for p, cs in bad["partitions"].items() for c in cs}
        ec.load_clusters = lambda: (bad, k2c, c2p)
        try:
            self.assertEqual(ec.cmd_groups(None), 1)
        finally:
            ec.load_clusters = orig
            ec.cmd_groups(None)  # restore committed report


if __name__ == "__main__":
    unittest.main()
