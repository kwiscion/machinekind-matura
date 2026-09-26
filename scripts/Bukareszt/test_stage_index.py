"""Tests for scripts/Bukareszt/stage_index.py on a tiny synthetic corpus (no network, no real sources).

Run: python3 -m unittest -v scripts.Bukareszt.test_stage_index
"""
from __future__ import annotations

import hashlib
import json
import os
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
import stage_index as si  # noqa: E402

RETRIEVAL_SRC = REPO / "agentsLog" / "Bukareszt" / "scripts" / "retrieval.py"
SOURCES_SRC = REPO / "agentsLog" / "Bukareszt" / "sources" / "sources.jsonl"
MANIFEST_SRC = REPO / "agentsLog" / "Bukareszt" / "staging" / "manifest.json"


def to_crlf(path: Path) -> None:
    """What a Windows `core.autocrlf=true` checkout does to a Git-tracked text file."""
    data = path.read_bytes().replace(b"\r\n", b"\n")
    path.write_bytes(data.replace(b"\n", b"\r\n"))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class SyntheticCorpus:
    """A two-source corpus with a real BM25 index built by the unchanged retrieval module."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="stage-index-test-"))
        self.root = self.tmp / "root"
        for sub in ("scripts", "sources", "raw", "index", "queries", "private", "staging"):
            (self.root / sub).mkdir(parents=True)
        shutil.copy(RETRIEVAL_SRC, self.root / "scripts" / "retrieval.py")
        texts = {
            "plwiki-alfa": "Alfa\n\nUnia lubelska została zawarta w 1569 roku w Lublinie.\n\n== Skutki ==\nPowstała Rzeczpospolita Obojga Narodów.\n",
            "plwiki-beta": "Beta\n\nBitwa pod Grunwaldem odbyła się w 1410 roku.\n\n== Tło ==\nWojna z zakonem krzyżackim trwała od 1409 roku.\n",
        }
        rows = []
        for sid, text in texts.items():
            data = text.encode("utf-8")
            (self.root / "raw" / f"{sid}.txt").write_bytes(data)
            rows.append({"source_id": sid, "url": f"https://pl.wikipedia.org/w/index.php?title={sid}&oldid=1", "title": sid.split("-")[1].title(),
                         "publisher": "test", "revision_id": 1, "sha256": sha(data), "bytes": len(data), "license": "CC BY-SA 4.0 (test)",
                         "allowed_use": ["retrieve"], "local_path": f"raw/{sid}.txt", "site": "wikipedia_pl"})
        with open(self.root / "sources" / "sources.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.rows = rows
        (self.root / "queries" / "train_queries.jsonl").write_text(
            json.dumps({"id": "t-q01", "split": "TRAIN", "prompt": "Kiedy zawarto unię lubelską?"}) + "\n", encoding="utf-8")
        retrieval = si.load_retrieval(self.root)
        si.rebuild_index(retrieval, self.root)
        self.retrieval = retrieval
        self.manifest = si.build_manifest(self.root, None, si.sha256_file(self.root / "scripts" / "retrieval.py"))
        proof = si.run_offline_query(self.root, "Kiedy zawarto unię lubelską?", "chrono", 2, 1.0)
        self.manifest["query_proof"] = {"query_id": "t-q01", "query": "Kiedy zawarto unię lubelską?", "mode": "chrono", "k": 2,
                                        "title_weight": 1.0, "results": proof["results"]}
        self.bundle = self.root / "private" / "bundle.tar.gz"
        info = si.write_bundle(self.root, self.manifest, self.bundle)
        self.manifest["bundle"] = {"name": self.bundle.name, "sha256": info["sha256"], "bytes": info["bytes"]}
        self.manifest_path = self.root / "staging" / "manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def fresh_clone(self) -> Path:
        """A copy without raw/ and index/ (what a fresh git clone has)."""
        dest = self.tmp / f"clone{len(list(self.tmp.iterdir()))}"
        shutil.copytree(self.root, dest, ignore=shutil.ignore_patterns("raw", "index", "private"))
        return dest

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class StageIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = SyntheticCorpus()

    @classmethod
    def tearDownClass(cls):
        cls.c.cleanup()

    def test_verify_staged_passes_on_original(self):
        checks = si.verify_staged(self.c.root, self.c.manifest)
        self.assertEqual(checks["index_sha256"]["actual"], self.c.manifest["index_sha256"])
        self.assertEqual(checks["raw_files"]["problems"], [])

    def test_bundle_is_deterministic(self):
        out = self.c.tmp / "again.tar.gz"
        info = si.write_bundle(self.c.root, self.c.manifest, out)
        self.assertEqual(info["sha256"], self.c.manifest["bundle"]["sha256"])

    def test_stage_from_bundle_in_fresh_clone(self):
        clone = self.c.fresh_clone()
        self.assertFalse((clone / "index").exists())
        report = clone / "report.json"
        rc = si.main(["stage", "--allow-unpinned", "--root", str(clone), "--bundle", str(self.c.bundle), "--report", str(report)])
        self.assertEqual(rc, 0)
        rep = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(rep["status"], "PASS")
        self.assertEqual(rep["path_used"], "bundle")
        self.assertTrue(rep["phases"]["offline_query"]["ok"])
        self.assertIn("socket-guard", rep["phases"]["offline_query"]["detail"]["guards"])
        self.assertEqual(si.sha256_file(clone / "index" / "bm25_index.json"), self.c.manifest["index_sha256"])
        # second run: already staged, nothing unpacked
        rc = si.main(["stage", "--allow-unpinned", "--root", str(clone), "--bundle", str(self.c.bundle), "--report", str(report)])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["path_used"], "already-staged")

    def test_tampered_bundle_member_is_named(self):
        clone = self.c.fresh_clone()
        bad_manifest = json.loads(json.dumps(self.c.manifest))
        bad_manifest["files"]["raw/plwiki-beta.txt"]["sha256"] = "0" * 64
        with self.assertRaises(si.StageError) as ctx:
            si.unpack_bundle(self.c.bundle, clone, bad_manifest)
        self.assertIn("raw/plwiki-beta.txt", str(ctx.exception))
        self.assertFalse((clone / "index").exists(), "nothing is moved into place after a failed member check")

    def test_wrong_bundle_hash_fails_before_extract(self):
        clone = self.c.fresh_clone()
        bad_manifest = json.loads(json.dumps(self.c.manifest))
        bad_manifest["bundle"]["sha256"] = "f" * 64
        with self.assertRaisesRegex(si.StageError, "bundle differs"):
            si.unpack_bundle(self.c.bundle, clone, bad_manifest)

    def test_tampered_raw_file_reports_source_and_hashes(self):
        clone = self.c.fresh_clone()
        si.unpack_bundle(self.c.bundle, clone, self.c.manifest)
        target = clone / "raw" / "plwiki-alfa.txt"
        target.write_bytes(target.read_bytes() + b"x")
        with self.assertRaises(si.StageError) as ctx:
            si.verify_staged(clone, self.c.manifest)
        msg = str(ctx.exception)
        self.assertIn("plwiki-alfa", msg)
        self.assertIn(self.c.rows[0]["sha256"], msg)

    def test_rebuild_reports_drift_per_source_and_never_refreshes_manifest(self):
        clone = self.c.fresh_clone()
        before = si.sha256_file(clone / "sources" / "sources.jsonl")
        drifted = {r["source_id"]: (self.c.root / r["local_path"]).read_text(encoding="utf-8") for r in self.c.rows}

        def fake_fetch(row):
            if row["source_id"] == "plwiki-beta":
                return {"revid": 2, "text": drifted[row["source_id"]] + "\nNowy akapit.\n", "method": "fake"}
            return {"revid": 1, "text": drifted[row["source_id"]], "method": "fake"}

        diffs = si.rebuild_raw(clone, self.c.rows, fake_fetch, sleep=0, log=lambda *_: None)
        self.assertEqual([d["source_id"] for d in diffs], ["plwiki-beta"])
        self.assertEqual(diffs[0]["reason"], "revision drifted")
        self.assertEqual(diffs[0]["expected_revid"], 1)
        self.assertEqual(diffs[0]["actual_revid"], 2)
        self.assertEqual(si.sha256_file(clone / "sources" / "sources.jsonl"), before)
        self.assertFalse((clone / "raw").exists(), "raw/ is not written when any source drifts")
        self.assertTrue((clone / "private" / "rebuild-drift" / "plwiki-beta.txt").exists())

    def test_unpinned_manifest_without_bundle_hash_is_refused(self):
        clone = self.c.fresh_clone()
        bad_manifest = json.loads(json.dumps(self.c.manifest))
        bad_manifest.pop("bundle")
        with self.assertRaisesRegex(si.StageError, "no bundle SHA-256"):
            si.unpack_bundle(self.c.bundle, clone, bad_manifest)

    def test_stage_refuses_modified_retriever_or_manifest(self):
        clone = self.c.fresh_clone()
        (clone / "scripts" / "retrieval.py").write_text((clone / "scripts" / "retrieval.py").read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8")
        report = clone / "report.json"
        rc = si.main(["stage", "--allow-unpinned", "--root", str(clone), "--bundle", str(self.c.bundle), "--report", str(report)])
        self.assertEqual(rc, 1)
        self.assertIn("retrieval_script_sha256", json.loads(report.read_text(encoding="utf-8"))["blocker"])
        self.assertFalse((clone / "index").exists())

    def test_score_tolerance_but_exact_order(self):
        base = {"results": [{"chunk_id": "a", "source_id": "s", "locator": "l", "score": 1.0}, {"chunk_id": "b", "source_id": "s", "locator": "l", "score": 0.5}]}
        near = json.loads(json.dumps(base)); near["results"][0]["score"] = 1.0004
        si.compare_query_proof(near, base)
        swapped = json.loads(json.dumps(base)); swapped["results"].reverse()
        with self.assertRaisesRegex(si.StageError, "ranking differs"):
            si.compare_query_proof(swapped, base)

    def test_rebuild_exact_reproduction_gives_pinned_index_hash(self):
        clone = self.c.fresh_clone()
        exact = {r["source_id"]: (self.c.root / r["local_path"]).read_text(encoding="utf-8") for r in self.c.rows}
        diffs = si.rebuild_raw(clone, self.c.rows, lambda r: {"revid": 1, "text": exact[r["source_id"]], "method": "fake"}, sleep=0, log=lambda *_: None)
        self.assertEqual(diffs, [])
        retrieval = si.load_retrieval(clone)
        si.rebuild_index(retrieval, clone)
        checks = si.verify_staged(clone, self.c.manifest)
        self.assertEqual(checks["index_sha256"]["actual"], self.c.manifest["index_sha256"])
        self.assertEqual(checks["graph_content_sha256"]["actual"], self.c.manifest["graph_content_sha256"])
        # reports/index_meta.json of the clone must not have been created/overwritten
        self.assertFalse((clone / "reports" / "index_meta.json").exists())

    def test_query_proof_mismatch_is_detected(self):
        actual = {"results": [{"chunk_id": "a", "source_id": "s", "locator": "l", "score": 1.0}]}
        expected = {"results": [{"chunk_id": "b", "source_id": "s", "locator": "l", "score": 1.0}]}
        with self.assertRaisesRegex(si.StageError, "ranking differs"):
            si.compare_query_proof(actual, expected)

    def test_offline_child_blocks_sockets(self):
        code = "import stage_index as si; si.install_socket_guard(); import urllib.request, socket, ssl\n" \
               "for f in (lambda: urllib.request.urlopen('http://127.0.0.1:9/', timeout=1), socket.SocketType, socket.socket):\n" \
               "    try:\n        f(); print('OPEN')\n    except RuntimeError as e:\n        print('BLOCKED', e)\n"
        proc = subprocess.run([sys.executable, "-c", code], cwd=HERE, capture_output=True, text=True)
        self.assertEqual(proc.stdout.count("BLOCKED"), 3, proc.stdout + proc.stderr)
        self.assertNotIn("OPEN", proc.stdout)

    def test_manifest_must_carry_pinned_values(self):
        with self.assertRaisesRegex(si.StageError, "pinned values"):
            si.load_manifest(self.c.manifest_path)  # synthetic manifest is not the #44 index


    # ---- #44 follow-up: CRLF-safe text identity, fail-closed pinned inputs, cwd/relative paths ----

    def test_lf_normalization_policy(self):
        d = self.c.tmp / "norm"
        d.mkdir(exist_ok=True)
        cases = {"trail.txt": (b"a\r\nb\r\n", b"a\nb\n"), "notrail.txt": (b"a\r\nb", b"a\nb"),
                 "lonecr.txt": (b"a\rb\n", b"a\rb\n"), "mixed.txt": (b"a\r\nb\nc\r\n", b"a\nb\nc\n"),
                 "bom.txt": (b"\xef\xbb\xbfa\r\n", b"\xef\xbb\xbfa\n")}
        for name, (raw, want) in cases.items():
            (d / name).write_bytes(raw)
            self.assertEqual(si.lf_bytes(d / name), want, name)
            self.assertEqual(si.sha256_text_file(d / name), sha(want), name)
        # a trailing newline is significant: it is neither added nor stripped
        self.assertNotEqual(si.sha256_text_file(d / "trail.txt"), si.sha256_text_file(d / "notrail.txt"))

    def test_real_pinned_inputs_have_same_identity_in_crlf_checkout(self):
        """The committed sources.jsonl / retrieval.py give the pinned hashes both as LF and as CRLF."""
        manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
        d = self.c.tmp / "real-crlf"
        d.mkdir(exist_ok=True)
        for src, pinned in ((SOURCES_SRC, si.PINNED_SOURCES_SHA256), (RETRIEVAL_SRC, manifest["retrieval_script_sha256"])):
            self.assertEqual(si.sha256_text_file(src), pinned, src)
            self.assertEqual(si.sha256_file(src), pinned, f"{src} is committed with LF, so the byte hash is unchanged")
            crlf = d / src.name
            shutil.copy(src, crlf)
            to_crlf(crlf)
            self.assertIn(b"\r\n", crlf.read_bytes())
            self.assertNotEqual(si.sha256_file(crlf), pinned, "raw CRLF bytes differ (the reported 701ad15... failure)")
            self.assertEqual(si.sha256_text_file(crlf), pinned)

    def test_stage_passes_in_crlf_checkout_and_bundle_is_identical(self):
        clone = self.c.fresh_clone()
        for rel in ("sources/sources.jsonl", "scripts/retrieval.py", "queries/train_queries.jsonl", "staging/manifest.json"):
            to_crlf(clone / rel)
        self.assertNotEqual(si.sha256_file(clone / "sources" / "sources.jsonl"), self.c.manifest["sources_sha256"])
        report = clone / "report.json"
        rc = si.main(["stage", "--allow-unpinned", "--root", str(clone), "--bundle", str(self.c.bundle), "--report", str(report)])
        rep = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(rc, 0, rep["blocker"])
        self.assertEqual(rep["path_used"], "bundle")
        self.assertEqual(rep["sources_sha256"]["actual"], self.c.manifest["sources_sha256"])
        self.assertEqual(rep["retrieval_script_sha256"]["actual"], self.c.manifest["retrieval_script_sha256"])
        # a manifest and bundle built from the CRLF checkout are identical to the LF ones
        m = si.build_manifest(clone, self.c.manifest["query_proof"], si.sha256_text_file(clone / "scripts" / "retrieval.py"))
        for key in ("sources_sha256", "index_sha256", "graph_content_sha256", "retrieval_script_sha256", "files"):
            self.assertEqual(m[key], self.c.manifest[key], key)
        info = si.write_bundle(clone, self.c.manifest, self.c.tmp / "crlf-bundle.tar.gz")
        self.assertEqual(info["sha256"], self.c.manifest["bundle"]["sha256"])

    def _stage_without_side_effects(self, clone, *extra):
        """Run `stage` with every import/network/rebuild entry point replaced by a recorder."""
        calls = []
        report = clone / "report.json"
        with mock.patch.object(si, "load_retrieval", side_effect=lambda *a: calls.append("load_retrieval")), \
                mock.patch.object(si, "rebuild_raw", side_effect=lambda *a, **k: calls.append("rebuild_raw") or []), \
                mock.patch.object(si, "fetch_pinned", side_effect=lambda *a: calls.append("fetch_pinned")), \
                mock.patch.object(si, "api_get", side_effect=lambda *a, **k: calls.append("api_get")), \
                mock.patch.object(si, "unpack_bundle", side_effect=lambda *a: calls.append("unpack_bundle")):
            rc = si.main(["stage", "--allow-unpinned", "--root", str(clone), "--report", str(report), *extra])
        return rc, json.loads(report.read_text(encoding="utf-8")), calls

    def test_tampered_retriever_fails_closed_before_import_or_rebuild(self):
        clone = self.c.fresh_clone()
        (clone / "scripts" / "retrieval.py").write_bytes((clone / "scripts" / "retrieval.py").read_bytes() + b"# tampered\n")
        tampered = si.sha256_text_file(clone / "scripts" / "retrieval.py")
        for extra in (["--rebuild"], []):  # explicit rebuild and the automatic no-bundle fallback
            rc, rep, calls = self._stage_without_side_effects(clone, *extra)
            self.assertEqual(rc, 1)
            self.assertEqual(calls, [], "nothing imported, fetched, unpacked or rebuilt")
            self.assertIn("retrieval_script_sha256", rep["blocker"])
            self.assertIn(str(clone / "scripts" / "retrieval.py"), rep["blocker"])
            self.assertIn(self.c.manifest["retrieval_script_sha256"], rep["blocker"])
            self.assertIn(tampered, rep["blocker"])
            self.assertFalse(rep["phases"]["pinned_inputs"]["ok"])
            self.assertEqual(rep["status"], "FAIL")
        self.assertFalse((clone / "raw").exists())
        self.assertFalse((clone / "index").exists())
        rc = si.main(["verify", "--root", str(clone), "--manifest", str(self.c.manifest_path)])
        self.assertEqual(rc, 1)

    def test_tampered_sources_fails_closed_before_rebuild(self):
        clone = self.c.fresh_clone()
        path = clone / "sources" / "sources.jsonl"
        path.write_bytes(path.read_bytes().replace(b'"revision_id": 1', b'"revision_id": 7', 1))
        rc, rep, calls = self._stage_without_side_effects(clone, "--rebuild")
        self.assertEqual(rc, 1)
        self.assertEqual(calls, [])
        self.assertIn("sources_sha256", rep["blocker"])
        self.assertIn(str(path), rep["blocker"])
        self.assertIn(self.c.manifest["sources_sha256"], rep["blocker"])

    def test_missing_retriever_fails_closed(self):
        clone = self.c.fresh_clone()
        (clone / "scripts" / "retrieval.py").unlink()
        rc, rep, calls = self._stage_without_side_effects(clone, "--rebuild")
        self.assertEqual(rc, 1)
        self.assertEqual(calls, [])
        self.assertIn("is missing", rep["blocker"])

    def test_stage_from_other_cwd_with_relative_paths(self):
        """Fresh clone staged by a subprocess whose cwd is elsewhere, with relative --root/--bundle/--report."""
        clone = self.c.fresh_clone()
        other = self.c.tmp / "elsewhere" / "deeper"
        other.mkdir(parents=True)
        rel = lambda p: os.path.relpath(p, other)  # noqa: E731
        proc = subprocess.run([sys.executable, str(HERE / "stage_index.py"), "stage", "--allow-unpinned", "--root", rel(clone),
                               "--bundle", rel(self.c.bundle), "--report", "rep.json"], cwd=other, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        rep = json.loads((other / "rep.json").read_text(encoding="utf-8"))
        self.assertEqual(rep["status"], "PASS")
        self.assertEqual(rep["root"], str(clone.resolve()))
        self.assertEqual(si.sha256_file(clone / "index" / "bm25_index.json"), self.c.manifest["index_sha256"])
        self.assertFalse((other / "raw").exists())
        self.assertFalse((other / "index").exists())

    def test_default_root_does_not_depend_on_cwd(self):
        self.assertEqual(si.DEFAULT_ROOT, REPO / "agentsLog" / "Bukareszt")
        self.assertTrue(si.DEFAULT_ROOT.is_absolute())
        self.assertTrue((si.DEFAULT_ROOT / "staging" / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
