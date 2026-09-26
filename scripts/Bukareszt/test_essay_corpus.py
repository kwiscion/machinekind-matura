import hashlib
import json
import shutil
import subprocess
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


class CrlfCheckoutTest(unittest.TestCase):
    """Frozen export bytes must survive a core.autocrlf=true (Windows-style) checkout."""
    EXPORTS = ["export_pilot_v1", "export_v1"]

    def git(self, *a, cwd):
        return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_attributes_unset_text_for_exports(self):
        paths = [str((ec.CORPUS / d / "train_sft.jsonl").relative_to(ec.ROOT)) for d in self.EXPORTS]
        out = self.git("check-attr", "text", "--", *paths, cwd=ec.ROOT)
        self.assertEqual(out.count(": text: unset"), len(paths), out)

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_autocrlf_checkout_keeps_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self.git("init", "-q", cwd=repo)
            self.git("config", "core.autocrlf", "true", cwd=repo)
            dst = repo / "agentsLog" / "Bukareszt"
            dst.mkdir(parents=True)
            shutil.copy(ec.ROOT / "agentsLog" / "Bukareszt" / ".gitattributes", dst / ".gitattributes")
            files = []
            for exp in self.EXPORTS:
                for f in ("train_sft.jsonl", "eval16_input.jsonl"):
                    rel = Path("agentsLog/Bukareszt/essay_corpus") / exp / f
                    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(ec.ROOT / rel, repo / rel)
                    files.append(rel)
            control = repo / "control.txt"          # no attribute: must be converted
            control.write_bytes(b"a\nb\n")
            self.git("add", "-A", cwd=repo)
            self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "t", cwd=repo)
            for rel in files + [Path("control.txt")]:
                (repo / rel).unlink()
            self.git("checkout", "--", ".", cwd=repo)
            self.assertEqual(control.read_bytes(), b"a\r\nb\r\n")  # proves conversion is active
            for exp in self.EXPORTS:
                man = json.loads((ec.CORPUS / exp / "export_manifest.json").read_text(encoding="utf-8"))
                for f, key in (("train_sft.jsonl", "train_sha256"), ("eval16_input.jsonl", "eval_sha256")):
                    rel = Path("agentsLog/Bukareszt/essay_corpus") / exp / f
                    disk = hashlib.sha256((repo / rel).read_bytes()).hexdigest()
                    blob = hashlib.sha256(subprocess.run(["git", "cat-file", "blob", f"HEAD:{rel.as_posix()}"], cwd=repo,
                                                         check=True, capture_output=True).stdout).hexdigest()
                    self.assertEqual(disk, blob, rel)
                    self.assertEqual(disk, man[key], rel)


class SourceErrorAuditTest(unittest.TestCase):
    """Cards carrying audited pinned-source errors must not back exported text (source_error_audit.json)."""
    BAD = {"b1-charlemagne-f06": set(), "b2-conferences-f05": set(), "b2-ussr-f14": set(),
           "b1-versailles-f08": {"bk117-b1-versailles"}}  # f08 only for the 2010 date, wording corrected
    ERR_STRINGS = ["799/800", "Śląsk Opolski", "Litwa, Łotwa, Estonia i Ukraina", "reparacje spłacono"]

    def test_exports_free_of_audited_errors(self):
        latest = {}
        for f in sorted((ec.CORPUS / "drafts").glob("*_essays.jsonl")):
            for r in ec.load_jsonl(f):
                if r["id"] not in latest or r.get("repair_round", 0) >= latest[r["id"]].get("repair_round", 0):
                    latest[r["id"]] = r
        for exp in ("export_pilot_v1", "export_v1"):
            rows = ec.load_jsonl(ec.CORPUS / exp / "train_sft.jsonl")
            text = "\n".join(m["content"] for r in rows for m in r["messages"])
            for s in self.ERR_STRINGS:
                self.assertNotIn(s, text, (exp, s))
            ids = {r["id"] for r in rows}
            for eid in ids & set(latest):
                used = set(latest[eid]["fact_ids_used"])
                if f"{eid}-repair-extra_topic" in ids:
                    used |= set(latest[eid].get("off_topic_fact_ids", []))
                for card in used & set(self.BAD):
                    self.assertIn(eid, self.BAD[card], (exp, eid, card))


if __name__ == "__main__":
    unittest.main()
