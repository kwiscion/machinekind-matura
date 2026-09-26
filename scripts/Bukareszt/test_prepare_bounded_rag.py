"""Tests for scripts/Bukareszt/prepare_bounded_rag.py on invented fixtures and a synthetic pinned root.

Run: python3 -m unittest -v scripts.Bukareszt.test_prepare_bounded_rag
No network, no real exam data, no model calls. CLI runs happen in child processes because the script installs
a process-wide socket guard.
"""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import prepare_bounded_rag as pbr  # noqa: E402
from test_stage_index import SyntheticCorpus  # noqa: E402

SCRIPT = HERE / "prepare_bounded_rag.py"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32  # invented bytes; only hashed, never decoded
CASES = [
    {"id": "fx-01", "prompt": "Źródło 1.\n„W roku 1569 w Lublinie zawarto unię.”\n\nZadanie 1. Podaj nazwę państwa, które powstało.",
     "images": ["img/a.png"], "split": "VALIDATION", "task_type": "source_analysis"},
    {"id": "fx-02", "prompt": "Zadanie 2. Kiedy odbyła się bitwa pod Grunwaldem? Odpowiedz jednym zdaniem."},
    {"id": "fx-03", "prompt": "Zadanie 3. Oceń skutki wojny z zakonem krzyżackim.", "images": []},
]
POLICY = "Answer in Polish. Follow the task's requested answer format exactly."


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


class BoundedRagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = SyntheticCorpus()
        cls.work = cls.c.tmp / "work"
        (cls.work / "in" / "img").mkdir(parents=True)
        (cls.work / "in" / "img" / "a.png").write_bytes(PNG)
        cls.input = cls.work / "in" / "cases.jsonl"
        cls.input.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in CASES), encoding="utf-8")
        cls.policy = cls.work / "policy.txt"
        cls.policy.write_text(POLICY + "\n", encoding="utf-8")
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        cls.c.cleanup()

    def out(self, sub="out"):
        type(self).n += 1
        return self.work / sub / f"run{self.n}.jsonl"

    def base(self, output, *extra, input_path=None, root=None, manifest=None):
        root = root or self.c.root
        return ["--input", input_path or self.input, "--output", output, "--root", root,
                "--manifest", manifest or (Path(root) / "staging" / "manifest.json"), "--allow-unpinned", *extra]

    def ok(self, output, *extra, **kw):
        proc = run_cli(*self.base(output, *extra, **kw))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = [json.loads(l) for l in Path(output).read_text(encoding="utf-8").splitlines()]
        trace = json.loads(Path(str(output) + ".trace.json").read_text(encoding="utf-8"))
        return rows, trace

    # ---------------------------------------------------------------- preservation
    def test_exact_preservation_of_prompt_images_ids_and_fields(self):
        output = self.out()
        rows, trace = self.ok(output, "--policy-file", self.policy)
        self.assertEqual([r["id"] for r in rows], [c["id"] for c in CASES])
        for case, row in zip(CASES, rows):
            self.assertTrue(row["prompt"].endswith(case["prompt"]))
            self.assertTrue(row["prompt"].startswith(POLICY + "\n\n"))
            self.assertEqual({k: v for k, v in row.items() if k not in ("prompt", "images")},
                             {k: v for k, v in case.items() if k not in ("prompt", "images")})
            self.assertEqual("images" in row, "images" in case)
            for orig, new in zip(case.get("images", []), row.get("images", [])):
                self.assertEqual((output.parent / new).read_bytes(), (self.input.parent / orig).read_bytes())
        self.assertEqual(rows[0]["images"], ["../in/img/a.png"])
        self.assertEqual(trace["cases"][0]["images"][0]["sha256"], sha(PNG))

    def test_image_paths_verbatim_when_output_next_to_input(self):
        output = self.work / "in" / "sibling.jsonl"
        rows, _ = self.ok(output)
        self.assertEqual(rows[0]["images"], CASES[0]["images"])

    def test_missing_image_is_refused(self):
        bad = self.work / "bad_img.jsonl"
        bad.write_text(json.dumps({"id": "x", "prompt": "Zadanie", "images": ["nope.png"]}) + "\n", encoding="utf-8")
        output = self.out()
        proc = run_cli(*self.base(output, input_path=bad))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not found", proc.stderr)
        self.assertFalse(output.exists())

    # ---------------------------------------------------------------- query
    def test_policy_is_excluded_from_query(self):
        seen = []
        real_rank = None

        def spy(idx, query, k, **kw):
            seen.append(query)
            return real_rank(idx, query, k, **kw)

        output = self.out()
        args = pbr.argparse.Namespace(input=str(self.input), output=str(output), trace=None, policy_file=str(self.policy),
                                      top_k=3, budget_chars=1600, root=str(self.c.root),
                                      manifest=str(self.c.manifest_path), allow_unpinned=True)
        orig_load = pbr.load_pinned_assets

        def load(*a):
            nonlocal real_rank
            retrieval, idx, graph, ident = orig_load(*a)
            real_rank = retrieval.rank
            retrieval.rank = spy
            return retrieval, idx, graph, ident

        with mock.patch.object(pbr, "guard_network", return_value="patched-in-test"), mock.patch.object(pbr, "load_pinned_assets", load):
            report = pbr.prepare(args)
        self.assertEqual(seen, [c["prompt"] for c in CASES])
        self.assertTrue(all(POLICY not in q for q in seen))
        self.assertEqual([c["query_sha256"] for c in report["cases"]], [sha(c["prompt"].encode()) for c in CASES])

    def test_trace_query_hash_is_original_prompt_with_and_without_policy(self):
        _, with_policy = self.ok(self.out(), "--policy-file", self.policy)
        _, without = self.ok(self.out())
        self.assertEqual([c["retrieved"] for c in with_policy["cases"]], [c["retrieved"] for c in without["cases"]])
        self.assertEqual(with_policy["policy"]["text_sha256"], sha(POLICY.encode()))
        self.assertIsNone(without["policy"])

    def test_policy_naming_a_case_id_is_refused(self):
        p = self.work / "hint_policy.txt"
        p.write_text("For fx-02 answer 1410.", encoding="utf-8")
        proc = run_cli(*self.base(self.out(), "--policy-file", p))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("generic", proc.stderr)

    # ---------------------------------------------------------------- budget
    def test_evidence_is_bounded_including_headers(self):
        for budget in (300, 450, 1600):
            rows, trace = self.ok(self.out(), "--budget-chars", budget, "--top-k", 5)
            for case, row, tc in zip(CASES, rows, trace["cases"]):
                added = len(row["prompt"]) - len(case["prompt"])
                self.assertEqual(added, tc["evidence_chars"])
                self.assertLessEqual(added, budget)
                if added:
                    self.assertTrue(row["prompt"].startswith(pbr.HEADER))
                    self.assertIn(pbr.FOOTER + pbr.BLOCK_TAIL + case["prompt"], row["prompt"])
                ids = [h["chunk_id"] for h in tc["retrieved"]]
                self.assertEqual(sorted(tc["included_chunk_ids"] + tc["skipped_chunk_ids"]), sorted(ids))
                self.assertTrue(set(tc["truncated_chunk_ids"]) <= set(tc["included_chunk_ids"]))

    def test_build_evidence_truncates_and_skips_with_ids(self):
        hits = [{"chunk_id": f"c{i}", "title": "Tytuł", "text": ("słowo " * 200)} for i in range(3)]
        block, stats = pbr.build_evidence(hits, 700)
        self.assertLessEqual(len(block), 700)
        self.assertEqual(stats["evidence_chars"], len(block))
        self.assertEqual(stats["included"], ["c0"])
        self.assertEqual(stats["truncated"], ["c0"])
        self.assertEqual(stats["skipped"], ["c1", "c2"])
        empty, stats = pbr.build_evidence(hits, len(pbr.HEADER) + 10)
        self.assertEqual((empty, stats["evidence_chars"], stats["skipped"]), ("", 0, ["c0", "c1", "c2"]))

    def test_no_citation_instruction_or_marker(self):
        rows, _ = self.ok(self.out())
        for row in rows:
            self.assertNotIn("[[", row["prompt"])
            self.assertNotIn("cite", row["prompt"].lower())

    # ---------------------------------------------------------------- refusals
    def test_key_answer_rubric_grade_fields_are_rejected(self):
        for extra in ({"answer": "x"}, {"Rubric": {}}, {"meta": {"expected_choice": "B"}}, {"grade": 1},
                      {"model_answer": "y"}, {"raw_response": {}}):
            bad = self.work / f"bad_{list(extra)[0]}.jsonl"
            bad.write_text(json.dumps({"id": "b1", "prompt": "Zadanie", **extra}) + "\n", encoding="utf-8")
            output = self.out()
            proc = run_cli(*self.base(output, input_path=bad))
            self.assertEqual(proc.returncode, 2, extra)
            self.assertIn("not allowed", proc.stderr)
            self.assertFalse(output.exists())

    def test_forbidden_fields_cover_evaluator_key_only_fields(self):
        tree = ast.parse((REPO / "agentsLog/Pewciu6/harness/matura_harness.py").read_text(encoding="utf-8"))
        key_only = next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n, ast.Assign)
                        and any(getattr(t, "id", None) == "KEY_ONLY_FIELDS" for t in n.targets))
        self.assertTrue(set(key_only) <= pbr.FORBIDDEN_FIELDS, set(key_only) - pbr.FORBIDDEN_FIELDS)

    def test_overwrite_refusal(self):
        output = self.out()
        self.ok(output)
        before = output.read_bytes()
        proc = run_cli(*self.base(output))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("overwrite", proc.stderr)
        self.assertEqual(output.read_bytes(), before)
        # output == input, trace pre-existing, trace == input
        self.assertEqual(run_cli(*self.base(self.input)).returncode, 2)
        fresh = self.out()
        Path(str(fresh) + ".trace.json").parent.mkdir(parents=True, exist_ok=True)
        Path(str(fresh) + ".trace.json").write_text("{}", encoding="utf-8")
        self.assertEqual(run_cli(*self.base(fresh)).returncode, 2)
        self.assertFalse(fresh.exists())
        self.assertEqual(run_cli(*self.base(self.out(), "--trace", self.input)).returncode, 2)
        self.assertEqual(self.input.read_text(encoding="utf-8").count("\n"), len(CASES))

    def test_repo_output_outside_private_is_refused(self):
        with self.assertRaises(pbr.PrepError):
            pbr.check_private_location(REPO / "scripts" / "Bukareszt" / "leak.jsonl")
        pbr.check_private_location(REPO / "agentsLog" / "Bukareszt" / "private" / "rag_input" / "x.jsonl")
        pbr.check_private_location(REPO / "outputs" / "x.jsonl")

    def test_wrong_pin_refusal(self):
        # 1) the synthetic manifest does not carry the issue #44 pins -> refused without --allow-unpinned
        output = self.out()
        args = [a for a in self.base(output) if a != "--allow-unpinned"]
        proc = run_cli(*args)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("pinned", proc.stderr)
        # 2) tampered index / graph / retriever / sources -> refused, nothing written
        for rel, tamper in (("index/bm25_index.json", lambda b: b + b" "), ("index/graph.json", lambda b: b.replace(b"{", b'{"x":1,', 1)),
                            ("scripts/retrieval.py", lambda b: b + b"\n# changed\n"), ("sources/sources.jsonl", lambda b: b + b"\n")):
            clone = self.c.tmp / f"tamper-{rel.replace('/', '-')}"
            shutil.copytree(self.c.root, clone)
            p = clone / rel
            p.write_bytes(tamper(p.read_bytes()))
            output = self.out()
            proc = run_cli(*self.base(output, root=clone))
            self.assertEqual(proc.returncode, 2, rel)
            self.assertIn("expected", proc.stderr, rel)
            self.assertFalse(output.exists(), rel)

    def test_missing_index_is_refused_without_fetch(self):
        clone = self.c.fresh_clone()  # no raw/, no index/
        output = self.out()
        proc = run_cli(*self.base(output, root=clone))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("never fetches", proc.stderr)
        self.assertFalse((clone / "index").exists())

    def test_real_manifest_pins_are_enforced(self):
        m = pbr.si.load_manifest(pbr.si.MANIFEST_FILE)
        self.assertEqual(m["index_sha256"], "350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429")
        self.assertEqual(m["sources_sha256"], "8b77a63afd25317d783a3e511e3f1f99f09b6cec3c740bdf101a0d069aadfeed")

    # ---------------------------------------------------------------- network
    def test_no_network_socket_guard_is_active_during_preparation(self):
        code = (
            "import sys, runpy; sys.argv = ['x'] + sys.argv[1:]\n"
            f"sys.path.insert(0, {str(HERE)!r})\n"
            "import prepare_bounded_rag as p\n"
            "rc = p.main(sys.argv[1:])\n"
            "import socket\n"
            "try:\n    socket.socket()\n    print('SOCKET_OPEN')\nexcept RuntimeError:\n    print('SOCKET_BLOCKED')\n"
            "sys.exit(rc)\n")
        output = self.out()
        proc = subprocess.run([sys.executable, "-c", code, *map(str, self.base(output))], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("SOCKET_BLOCKED", proc.stdout)
        trace = json.loads(Path(str(output) + ".trace.json").read_text(encoding="utf-8"))
        self.assertIn("socket guard", trace["network"])
        self.assertEqual((trace["model_calls"], trace["fetch_or_rebuild"]), (0, False))

    def test_trace_hashes(self):
        output = self.out()
        _, trace = self.ok(output, "--policy-file", self.policy)
        self.assertEqual(trace["input"]["sha256"], sha(self.input.read_bytes()))
        self.assertEqual(trace["output"]["sha256"], sha(output.read_bytes()))
        self.assertEqual(trace["policy"]["file_sha256"], sha(self.policy.read_bytes()))
        self.assertEqual(trace["index"]["index_sha256"], self.c.manifest["index_sha256"])
        self.assertEqual(trace["index"]["sources_sha256"], self.c.manifest["sources_sha256"])
        self.assertEqual(trace["index"]["retrieval_script_sha256"], self.c.manifest["retrieval_script_sha256"])
        self.assertEqual(trace["settings"]["top_k"], 3)
        self.assertEqual(trace["settings"]["budget_chars"], 1600)


if __name__ == "__main__":
    unittest.main()
