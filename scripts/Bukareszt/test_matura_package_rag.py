"""Issue #62: opt-in bounded retrieval for `matura_package.py run`, on invented packages and a synthetic index.

Run: python3 -m unittest -v scripts.Bukareszt.test_matura_package_rag
No network, no real exam data, no model calls: `--infer` points at a fake transport script that logs every
invocation to a sentinel file and writes clearly synthetic records. Package IDs/counts are arbitrary on purpose
(not the 40-item validation shape) and the template order differs from the exam order.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import matura_package as mp  # noqa: E402
from test_stage_index import SyntheticCorpus  # noqa: E402

PNG_A = mp.PNG_MAGIC + b"invented-image-A"
PNG_B = mp.PNG_MAGIC + b"invented-image-B"
# Arbitrary IDs and count (7), unusual characters; the template lists them in a different order.
ITEMS = [
    ("Z-9", "Wymyślone: kiedy zawarto unię lubelską?", "", []),
    ("zad.3b", "Wymyślone: opisz obraz.", "Opis testowy [Obraz: images/a.png]", ["images/a.png"]),
    ("A/1", "Wymyślone: porównaj oba obrazy.", "", ["images/a.png", "images/b.png"]),
    ("ż-4", "Wymyślone: bitwa pod Grunwaldem — podaj rok.", "Zdanie testowe: „zażółć gęślą jaźń”.", []),
    ("100", "Wymyślone: prawda/fałsz.", "", []),
    ("x", "Wymyślone: wojna z zakonem krzyżackim.", "", ["images/b.png"]),
    ("ostatnie", "Wymyślone wypracowanie: temat 1 albo 2.", "", []),
]
TEMPLATE_ORDER = ["ostatnie", "A/1", "Z-9", "100", "zad.3b", "x", "ż-4"]
FAIL_ID = "100"

FAKE_INFER = textwrap.dedent('''
    """Fake infer.py transport for tests: logs argv, never opens a socket, writes SYNTHETIC records."""
    import json, os, sys
    args = sys.argv[1:]
    get = lambda flag: args[args.index(flag) + 1]
    with open(os.environ["FAKE_INFER_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\\n")
    config = json.load(open(get("--config"), encoding="utf-8"))
    host = config["base_url"].split("//", 1)[1].split("/", 1)[0].split(":", 1)[0]
    if host not in ("127.0.0.1", "localhost", "::1"):
        sys.exit(2)
    cases = [json.loads(l) for l in open(get("--input"), encoding="utf-8") if l.strip()]
    if len(cases) > int(get("--max-calls")):
        sys.exit(2)
    if "--dry-run" in args:
        sys.exit(0)
    with open(get("--output"), "x", encoding="utf-8") as out:
        for case in cases:
            failed = case["id"] == os.environ.get("FAKE_INFER_FAIL")
            raw = None if failed else {"choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": "SYNTETYCZNA " + case["id"] + " rag=" + str("Reference excerpts" in case["prompt"])}}]}
            out.write(json.dumps({"id": case["id"], "backend": {"name": "fake"}, "raw_response": raw, "usage": None,
                                  "error": {"type": "URLError", "message": "synthetic"} if failed else None},
                                 ensure_ascii=False) + "\\n")
    sys.exit(1 if os.environ.get("FAKE_INFER_FAIL") else 0)
''')


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mp.main([str(a) for a in args])
    return code, out.getvalue(), err.getvalue()


class BoundedRagRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = SyntheticCorpus()

    @classmethod
    def tearDownClass(cls):
        cls.corpus.cleanup()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="issue62-")).resolve()
        self.pkg = self.tmp / "pkg"
        (self.pkg / "images").mkdir(parents=True)
        (self.pkg / "images" / "a.png").write_bytes(PNG_A)
        (self.pkg / "images" / "b.png").write_bytes(PNG_B)
        hashes = {"images/a.png": sha(PNG_A), "images/b.png": sha(PNG_B)}
        items = [{"id": i, "max_points": 1, "question": q, "source_text": s, "answer_format": "Krótko.",
                  "images": [{"path": p, "sha256": hashes[p]} for p in imgs]} for i, q, s, imgs in ITEMS]
        exam = {"exam_id": "invented-issue62", "instructions": "SYNTETYCZNY TEST.", "max_points": len(items), "items": items}
        (self.pkg / "exam.json").write_text(json.dumps(exam, ensure_ascii=False), encoding="utf-8")
        template = {"exam_id": "invented-issue62", "answers": [{"id": i, "answer": ""} for i in TEMPLATE_ORDER]}
        (self.pkg / "answers-template.json").write_text(json.dumps(template, ensure_ascii=False), encoding="utf-8")
        self.config = self.tmp / "config.json"
        self.config.write_text(json.dumps({"name": "t", "base_url": "http://127.0.0.1:9/v1", "model": "m",
                                           "max_output_tokens": 4096}), encoding="utf-8")
        self.infer = self.tmp / "fake_infer.py"
        self.infer.write_text(FAKE_INFER, encoding="utf-8")
        self.log = self.tmp / "infer-calls.log"
        self.work = self.tmp / "w"
        self._env = {k: mp.os.environ.get(k) for k in ("FAKE_INFER_LOG", "FAKE_INFER_FAIL")}
        mp.os.environ["FAKE_INFER_LOG"] = str(self.log)
        mp.os.environ.pop("FAKE_INFER_FAIL", None)

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                mp.os.environ.pop(k, None)
            else:
                mp.os.environ[k] = v
        shutil.rmtree(self.tmp)

    def run_cmd(self, *extra, rag=True, root=None, manifest=None, unpinned=True, infer=None, config=None):
        args = ["run", "--exam-dir", self.pkg, "--config", config or self.config, "--workdir", self.work,
                "--infer", infer or self.infer, *extra]
        if rag:
            args += ["--bounded-rag", "--rag-root", root or self.corpus.root,
                     "--rag-manifest", manifest or self.corpus.manifest_path]
            if unpinned:
                args.append("--rag-allow-unpinned")
        return cli(*args)

    def calls(self):
        return [json.loads(l) for l in self.log.read_text(encoding="utf-8").splitlines()] if self.log.exists() else []

    def rows(self, path):
        return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]

    # ---------------------------------------------------------------- full run
    def test_rag_run_binds_original_manifest_and_template(self):
        code, out, err = self.run_cmd()
        self.assertEqual(code, 0, err)
        summary = json.loads(out)
        bare, rag = self.work / "input.jsonl", self.work / "input.bounded-rag.jsonl"
        manifest = json.loads((self.work / "input.jsonl.manifest.json").read_text(encoding="utf-8"))
        # original prepared input and manifest preserved and still bound to each other
        self.assertEqual(mp.sha256_file(bare), manifest["prepared_sha256"])
        self.assertEqual(manifest["ids"], [i[0] for i in ITEMS])
        # transport received the RAG input, never the bare one
        sent = [c for c in self.calls() if "--dry-run" not in c]
        self.assertEqual(len(sent), 1)
        self.assertEqual(Path(sent[0][sent[0].index("--input") + 1]), rag)
        self.assertEqual(sent[0][sent[0].index("--max-calls") + 1], str(len(ITEMS)))
        # final answers: template order, exact IDs, every answer came from a RAG prompt
        answers = json.loads((self.work / "answers.json").read_text(encoding="utf-8"))
        self.assertEqual(answers["exam_id"], "invented-issue62")
        self.assertEqual([a["id"] for a in answers["answers"]], TEMPLATE_ORDER)
        with_evidence = {r["id"] for r in self.rows(rag) if "Reference excerpts" in r["prompt"]}
        self.assertTrue(with_evidence)
        self.assertTrue(all(a["answer"] == f"SYNTETYCZNA {a['id']} rag={a['id'] in with_evidence}" for a in answers["answers"]))
        report = json.loads((self.work / "failures.json").read_text(encoding="utf-8"))
        self.assertEqual(report["prepared_sha256"], manifest["prepared_sha256"])
        self.assertEqual(summary["bounded_rag"]["input_sha256"], mp.sha256_file(rag))
        self.assertEqual((summary["bounded_rag"]["top_k"], summary["bounded_rag"]["budget_chars"]), (3, 1600))
        self.assertEqual(mp.main(["validate", str(self.work / "answers.json"), "--exam-dir", str(self.pkg)]), 0)

    def test_text_and_images_preserved_and_settings_uniform(self):
        self.assertEqual(self.run_cmd("--dry-run")[0], 0)
        bare = self.rows(self.work / "input.jsonl")
        rag = self.rows(self.work / "input.bounded-rag.jsonl")
        self.assertEqual([r["id"] for r in rag], [r["id"] for r in bare])
        for b, r in zip(bare, rag):
            self.assertEqual(set(r), set(b))
            self.assertTrue(r["prompt"].endswith(b["prompt"]))
            self.assertEqual(r["images"], b["images"])  # verbatim strings, same bytes
            for img in r["images"]:
                self.assertIn((self.work / img).resolve().read_bytes(), (PNG_A, PNG_B))
        self.assertEqual(rag[2]["images"], bare[2]["images"])
        self.assertEqual(len(rag[2]["images"]), 2)
        self.assertTrue(any(r["prompt"] != b["prompt"] for b, r in zip(bare, rag)), "synthetic index should add evidence")
        trace = json.loads((self.work / "input.bounded-rag.jsonl.trace.json").read_text(encoding="utf-8"))
        self.assertIsNone(trace["policy"])
        self.assertEqual((trace["settings"]["top_k"], trace["settings"]["budget_chars"], trace["settings"]["mode"]), (3, 1600, "chrono"))
        self.assertTrue(all(c["evidence_chars"] <= 1600 for c in trace["cases"]))
        self.assertEqual(trace["model_calls"], 0)

    def test_inference_failure_preserved_as_blank(self):
        mp.os.environ["FAKE_INFER_FAIL"] = FAIL_ID
        code, _, err = self.run_cmd()
        self.assertEqual(code, 1, err)
        answers = {a["id"]: a["answer"] for a in json.loads((self.work / "answers.json").read_text(encoding="utf-8"))["answers"]}
        self.assertEqual(answers[FAIL_ID], "")
        self.assertEqual(sum(1 for v in answers.values() if v), len(ITEMS) - 1)
        failures = json.loads((self.work / "failures.json").read_text(encoding="utf-8"))["failures"]
        self.assertEqual([f["id"] for f in failures], [FAIL_ID])

    # ---------------------------------------------------------------- refusals before any model call
    def assert_refused_without_transport(self, result, needle=None):
        code, _, err = result
        self.assertEqual(code, 2, err)
        if needle:
            self.assertIn(needle, err)
        self.assertEqual(self.calls(), [], "transport must not be invoked (not even --dry-run)")
        self.assertFalse((self.work / "answers.json").exists())

    def test_tampered_index_refused_before_any_call(self):
        root = self.tmp / "root-tampered"
        shutil.copytree(self.corpus.root, root)
        index = root / "index" / "bm25_index.json"
        index.write_bytes(index.read_bytes() + b"\n")
        self.assert_refused_without_transport(self.run_cmd(root=root, manifest=root / "staging" / "manifest.json"),
                                              "no requests sent")
        self.assertFalse((self.work / "input.bounded-rag.jsonl").exists())

    def test_wrong_manifest_pin_refused_before_any_call(self):
        root = self.tmp / "root-drift"
        shutil.copytree(self.corpus.root, root)
        manifest = json.loads((root / "staging" / "manifest.json").read_text(encoding="utf-8"))
        manifest["index_sha256"] = "0" * 64
        (root / "staging" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        self.assert_refused_without_transport(self.run_cmd(root=root, manifest=root / "staging" / "manifest.json"))

    def test_unpinned_synthetic_manifest_refused_without_test_flag(self):
        self.assert_refused_without_transport(self.run_cmd(unpinned=False))

    def test_real_pinned_manifest_does_not_match_synthetic_root(self):
        real = REPO / "agentsLog" / "Bukareszt" / "staging" / "manifest.json"
        self.assert_refused_without_transport(self.run_cmd(manifest=real, unpinned=False))

    def test_total_call_guard_refuses_before_rag_and_transport(self):
        self.assert_refused_without_transport(self.run_cmd("--max-calls-total", len(ITEMS) - 1), "--max-calls-total")
        self.assertFalse((self.work / "input.bounded-rag.jsonl").exists())

    def test_remote_endpoint_refused_by_real_infer_dry_run(self):
        remote = self.tmp / "remote.json"
        remote.write_text(json.dumps({"name": "t", "base_url": "https://example.com/v1", "model": "m"}), encoding="utf-8")
        code, _, _ = self.run_cmd("--dry-run", config=remote, infer=REPO / "infer.py")
        self.assertEqual(code, 2)
        self.assertFalse((self.work / "answers.json").exists())

    def test_remote_endpoint_refused_by_transport_before_generation(self):
        remote = self.tmp / "remote.json"
        remote.write_text(json.dumps({"name": "t", "base_url": "http://10.0.0.5/v1", "model": "m"}), encoding="utf-8")
        code, _, _ = self.run_cmd(config=remote)
        self.assertEqual(code, 2)
        self.assertTrue(all("--dry-run" in c for c in self.calls()))

    def test_fresh_output_refusal(self):
        self.work.mkdir()
        (self.work / "input.bounded-rag.jsonl").write_text("keep me\n", encoding="utf-8")
        self.assert_refused_without_transport(self.run_cmd(), "must be new or empty")
        self.assertEqual((self.work / "input.bounded-rag.jsonl").read_text(encoding="utf-8"), "keep me\n")

    def test_rag_targets_never_overwritten(self):
        workdir = self.tmp / "direct"
        workdir.mkdir()
        (workdir / "input.bounded-rag.jsonl.trace.json").write_text("{}", encoding="utf-8")
        ns = mp.argparse.Namespace(rag_top_k=3, rag_budget_chars=1600, rag_root=None, rag_manifest=None, rag_allow_unpinned=True)
        with self.assertRaises(mp.PackageError):
            mp.build_bounded_rag(ns, workdir / "input.jsonl", {}, workdir)
        self.assertEqual((workdir / "input.bounded-rag.jsonl.trace.json").read_text(encoding="utf-8"), "{}")

    def test_rag_options_require_flag(self):
        code, _, err = cli("run", "--exam-dir", self.pkg, "--config", self.config, "--workdir", self.work,
                           "--infer", self.infer, "--rag-top-k", "5", "--dry-run")
        self.assertEqual(code, 2)
        self.assertIn("--bounded-rag", err)
        self.assertEqual(self.calls(), [])

    # ---------------------------------------------------------------- dry run and default path
    def test_dry_run_proves_both_paths_without_generation(self):
        code, out, err = cli("run", "--exam-dir", self.pkg, "--config", self.config, "--workdir", self.tmp / "bare",
                             "--infer", REPO / "infer.py", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertNotIn("bounded_rag", json.loads(out))
        self.assertEqual(sorted(p.name for p in (self.tmp / "bare").iterdir()), ["input.jsonl", "input.jsonl.manifest.json"])
        code, out, err = self.run_cmd("--dry-run", infer=REPO / "infer.py")
        self.assertEqual(code, 0, err)
        self.assertTrue(json.loads(out)["dry_run"])
        self.assertEqual(json.loads(out)["bounded_rag"]["input"], str(self.work.resolve() / "input.bounded-rag.jsonl"))
        self.assertEqual(sorted(p.name for p in self.work.iterdir()),
                         ["input.bounded-rag.jsonl", "input.bounded-rag.jsonl.trace.json", "input.jsonl", "input.jsonl.manifest.json"])
        # both prepared inputs are byte-identical bare inputs; no raw records or answers were produced
        self.assertEqual((self.tmp / "bare" / "input.jsonl").read_bytes().count(b"\n"), len(ITEMS))
        self.assertEqual(json.loads((self.work / "input.jsonl.manifest.json").read_text(encoding="utf-8"))["prepared_sha256"],
                         json.loads((self.tmp / "bare" / "input.jsonl.manifest.json").read_text(encoding="utf-8"))["prepared_sha256"])

    def test_default_path_unchanged(self):
        code, out, err = self.run_cmd(rag=False)
        self.assertEqual(code, 0, err)
        self.assertNotIn("bounded_rag", json.loads(out))
        self.assertEqual(sorted(p.name for p in self.work.iterdir()),
                         ["answers.json", "failures.json", "input.jsonl", "input.jsonl.manifest.json", "raw.part1.jsonl"])
        calls = self.calls()
        self.assertEqual(len(calls), 2)  # one dry-run validation, one real call, both on the bare input
        self.assertTrue(all(Path(c[c.index("--input") + 1]) == self.work / "input.jsonl" for c in calls))
        answers = json.loads((self.work / "answers.json").read_text(encoding="utf-8"))["answers"]
        self.assertTrue(all(a["answer"].endswith("rag=False") for a in answers))
        self.assertEqual([a["id"] for a in answers], TEMPLATE_ORDER)


if __name__ == "__main__":
    unittest.main()
