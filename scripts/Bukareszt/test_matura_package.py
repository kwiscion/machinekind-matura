"""Regression tests for matura_package.py on invented fixtures only (no exam content)."""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matura_package as mp  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[2] / "agentsLog" / "Bukareszt" / "submission" / "fixtures" / "tiny-package"
IDS = ["1", "2.1", "2.2", "3"]


def cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mp.main([str(a) for a in args])
    return code, out.getvalue(), err.getvalue()


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pkg = self.tmp / "pkg"
        shutil.copytree(FIXTURE, self.pkg)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def edit_exam(self, change):
        exam = json.loads((self.pkg / "exam.json").read_text(encoding="utf-8"))
        change(exam)
        (self.pkg / "exam.json").write_text(json.dumps(exam, ensure_ascii=False), encoding="utf-8")

    def edit_template(self, change):
        template = json.loads((self.pkg / "answers-template.json").read_text(encoding="utf-8"))
        change(template)
        (self.pkg / "answers-template.json").write_text(json.dumps(template, ensure_ascii=False), encoding="utf-8")

    def raw(self, answers, name="raw.jsonl"):
        return write_jsonl(self.tmp / name, [mp.synthetic_record(i, a) for i, a in answers.items()])

    def finalize(self, raw, name="answers.json"):
        return cli("finalize", "--exam-dir", self.pkg, "--raw", raw, "--output", self.tmp / name, "--no-manifest")

    def report(self, name="answers.json"):
        return json.loads((self.tmp / (name + ".failures.json")).read_text(encoding="utf-8"))


class PackageCheck(Base):
    def test_fixture_counts(self):
        code, out, _ = cli("check", "--exam-dir", self.pkg, "--expect-items", 4, "--expect-points", 7, "--expect-images", 2)
        self.assertEqual(code, 0)
        summary = json.loads(out)
        self.assertEqual((summary["items"], summary["image_references"]), (4, 3))

    def test_expectation_mismatch_fails(self):
        self.assertEqual(cli("check", "--exam-dir", self.pkg, "--expect-items", 37)[0], 2)

    def test_bad_image_hash(self):
        (self.pkg / "images" / "fixture-red.png").write_bytes(mp.PNG_MAGIC + b"tampered")
        code, _, err = cli("check", "--exam-dir", self.pkg)
        self.assertEqual(code, 2)
        self.assertIn("sha256 mismatch", err)

    def test_missing_image(self):
        (self.pkg / "images" / "fixture-blue.png").unlink()
        self.assertIn("image file missing", cli("check", "--exam-dir", self.pkg)[2])

    def test_path_traversal_rejected(self):
        self.edit_exam(lambda e: e["items"][0]["images"][0].update(path="../escape.png"))
        self.assertIn("inside the exam folder", cli("check", "--exam-dir", self.pkg)[2])

    def test_duplicate_exam_id(self):
        self.edit_exam(lambda e: e["items"][1].update(id="1"))
        self.assertIn("duplicate item ids", cli("check", "--exam-dir", self.pkg)[2])

    def test_template_disagreement(self):
        self.edit_template(lambda t: t["answers"].pop())
        self.assertIn("not in template", cli("check", "--exam-dir", self.pkg)[2])
        self.edit_template(lambda t: t.update(exam_id="other-exam"))
        self.assertIn("template exam_id", cli("check", "--exam-dir", self.pkg)[2])

    def test_missing_required_field(self):
        self.edit_exam(lambda e: e["items"][2].pop("answer_format"))
        self.assertIn("answer_format must be", cli("check", "--exam-dir", self.pkg)[2])

    def test_numeric_item_id_rejected(self):
        self.edit_exam(lambda e: e["items"][0].update(id=1))
        self.assertIn("id must be a nonempty string", cli("check", "--exam-dir", self.pkg)[2])


class Prepare(Base):
    def test_all_source_material_and_images_survive(self):
        out = self.tmp / "work" / "input.jsonl"
        self.assertEqual(cli("prepare", "--exam-dir", self.pkg, "--output", out)[0], 0)
        records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
        exam = json.loads((self.pkg / "exam.json").read_text(encoding="utf-8"))
        self.assertEqual([r["id"] for r in records], IDS)
        for record, item in zip(records, exam["items"]):
            self.assertEqual(set(record), {"id", "prompt", "images"})
            for field in ("question", "source_text", "answer_format"):
                self.assertIn(item[field], record["prompt"])
            self.assertIn(exam["instructions"], record["prompt"])
            resolved = [(out.parent / p).resolve() for p in record["images"]]
            self.assertEqual(resolved, [(self.pkg / i["path"]).resolve() for i in item["images"]])
            self.assertTrue(all(p.is_file() for p in resolved))
        self.assertIn("zażółć gęślą jaźń", records[1]["prompt"])
        manifest = json.loads((out.parent / "input.jsonl.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["exam_id"], "synthetic-fixture-v1")

    def test_infer_py_accepts_prepared_input(self):
        sys.path.insert(0, str(mp.REPO_ROOT))
        import infer
        out = self.tmp / "input.jsonl"
        cli("prepare", "--exam-dir", self.pkg, "--output", out)
        cases = infer.load_cases(out, 100)
        self.assertEqual(len(cases), 4)
        self.assertEqual(len(cases[1]["content"]), 3)  # text + 2 images as data URLs
        self.assertTrue(cases[1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_refuses_existing_output(self):
        out = self.tmp / "input.jsonl"
        out.write_text("x")
        self.assertEqual(cli("prepare", "--exam-dir", self.pkg, "--output", out)[0], 2)


class Finalize(Base):
    def test_complete_roundtrip_unicode(self):
        answers = {"1": "czerwony", "2.1": "Łódź — „cudzysłów” \"quote\" \\ ✓ 😀", "2.2": "1. F", "3": "Temat 2.\n" + "słowo " * 400}
        code, _, _ = self.finalize(self.raw(answers))
        self.assertEqual(code, 0)
        path = self.tmp / "answers.json"
        doc = json.loads(path.read_bytes().decode("utf-8"))
        self.assertEqual(set(doc), {"exam_id", "answers"})
        self.assertEqual([a["id"] for a in doc["answers"]], IDS)
        self.assertTrue(all(set(a) == {"id", "answer"} for a in doc["answers"]))
        self.assertEqual(doc["answers"][1]["answer"], answers["2.1"])
        self.assertEqual(doc["answers"][3]["answer"], answers["3"].strip())  # essay kept whole
        self.assertIn("Łódź".encode("utf-8"), path.read_bytes())
        self.assertEqual(cli("validate", path, "--exam-dir", self.pkg)[0], 0)
        self.assertEqual(self.report()["failures"], [])

    def test_failures_become_empty_answers_with_report(self):
        rows = [
            mp.synthetic_record("1", "cut", finish_reason="length"),  # truncated, no infer error
            mp.synthetic_record("2.1", None, error={"type": "http", "message": "500"}),
            {"id": "2.2", "raw_response": "not json", "error": None},  # malformed
        ]
        code, _, _ = self.finalize(write_jsonl(self.tmp / "raw.jsonl", rows))
        self.assertEqual(code, 1)
        doc = json.loads((self.tmp / "answers.json").read_text(encoding="utf-8"))
        self.assertEqual([a["answer"] for a in doc["answers"]], ["", "", "", ""])
        kinds = {f["id"]: f["type"] for f in self.report()["failures"]}
        self.assertEqual(kinds, {"1": "truncated", "2.1": "infer_http", "2.2": "malformed", "3": "missing"})
        self.assertEqual(cli("validate", self.tmp / "answers.json", "--exam-dir", self.pkg)[0], 0)

    def test_reasoning_stripped_and_unbalanced_rejected(self):
        raw = self.raw({"1": "<think>tajne</think>\nczerwony", "2.1": "<think>never closed", "2.2": "   ", "3": "x"})
        self.assertEqual(self.finalize(raw)[0], 1)
        doc = json.loads((self.tmp / "answers.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["answers"][0]["answer"], "czerwony")
        self.assertNotIn("tajne", (self.tmp / "answers.json").read_text(encoding="utf-8"))
        kinds = {f["id"]: f["type"] for f in self.report()["failures"]}
        self.assertEqual(kinds, {"2.1": "malformed", "2.2": "empty"})

    def test_unknown_duplicate_and_exam_id_errors(self):
        self.assertEqual(self.finalize(self.raw({"1": "a", "99": "b"}))[0], 2)
        dup = write_jsonl(self.tmp / "dup.jsonl", [mp.synthetic_record("1", "a"), mp.synthetic_record("1", "b")])
        code, _, err = self.finalize(dup)
        self.assertEqual(code, 2)
        self.assertIn("Duplicate model output id", err)
        other = mp.synthetic_record("1", "a") | {"exam_id": "another-exam"}
        self.assertEqual(self.finalize(write_jsonl(self.tmp / "ex.jsonl", [other]))[0], 2)
        self.assertFalse((self.tmp / "answers.json").exists())

    def test_manifest_exam_mismatch(self):
        prepared = self.tmp / "input.jsonl"
        cli("prepare", "--exam-dir", self.pkg, "--output", prepared)
        manifest = self.tmp / "input.jsonl.manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["exam_id"] = "history-2023-mock-v1"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        code, _, err = cli("finalize", "--exam-dir", self.pkg, "--raw", self.raw({"1": "a"}),
                           "--output", self.tmp / "a.json", "--manifest", manifest)
        self.assertEqual(code, 2)
        self.assertIn("exam_id", err)

    def test_over_limit_answer_not_truncated(self):
        self.assertEqual(self.finalize(self.raw({"1": "a" * (mp.MAX_ANSWER_CHARS + 1), "2.1": "b", "2.2": "c", "3": "d"}))[0], 1)
        self.assertEqual(self.report()["failures"][0]["type"], "over_limit")
        doc = json.loads((self.tmp / "answers.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["answers"][0]["answer"], "")

    def test_normalized_evaluator_format_accepted(self):
        row = mp.synthetic_record("1", "czerwony")
        normalized = {"id": "1", "raw_response": "czerwony", "provider_raw_response": row["raw_response"], "error": None}
        self.assertEqual(self.finalize(write_jsonl(self.tmp / "n.jsonl", [normalized]))[0], 1)  # 3 missing
        doc = json.loads((self.tmp / "answers.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["answers"][0]["answer"], "czerwony")

    def test_synthetic_outputs_command(self):
        out = self.tmp / "syn.jsonl"
        self.assertEqual(cli("synthetic-outputs", "--exam-dir", self.pkg, "--output", out)[0], 0)
        self.assertEqual(self.finalize(out)[0], 0)
        doc = json.loads((self.tmp / "answers.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(doc["answers"][-1]["answer"].split()), 300)
        self.assertTrue(all("SYNTETYCZNA" in a["answer"] for a in doc["answers"]))


class ReviewRegressions(Base):
    """Defects found by the independent review of the first slice."""

    def answers(self):
        return json.loads((self.tmp / "answers.json").read_text(encoding="utf-8"))["answers"]

    def test_line_separators_in_model_output(self):
        raw = self.tmp / "raw.jsonl"
        raw.write_text(json.dumps(mp.synthetic_record("1", "linia\u2028druga\x85trzecia"), ensure_ascii=False) + "\n",
                       encoding="utf-8")
        self.assertEqual(self.finalize(raw)[0], 1)  # 3 missing, but the file is written
        self.assertEqual(self.answers()[0]["answer"], "linia\u2028druga\x85trzecia")

    def test_line_separators_in_exam_text(self):
        sys.path.insert(0, str(mp.REPO_ROOT))
        import infer
        self.edit_exam(lambda e: e["items"][0].update(question="pytanie\u2028z separatorem\u2029i\x85NEL"))
        out = self.tmp / "input.jsonl"
        self.assertEqual(cli("prepare", "--exam-dir", self.pkg, "--output", out)[0], 0)
        self.assertEqual(len(infer.load_cases(out, 100)), 4)

    def test_crashes_exit_2_not_1(self):
        (self.tmp / "huge.jsonl").write_text('{"id":"1","n":' + "9" * 5000 + "}\n", encoding="utf-8")
        self.assertEqual(self.finalize(self.tmp / "huge.jsonl")[0], 2)
        (self.tmp / "latin.jsonl").write_bytes('{"id":"1","x":"\u0142"}'.encode("latin-1", "replace") + b"\xb3\n")
        self.assertEqual(self.finalize(self.tmp / "latin.jsonl")[0], 2)
        self.assertFalse((self.tmp / "answers.json").exists())
        template = self.pkg / "answers-template.json"
        for body in ('{"exam_id":"synthetic-fixture-v1","answers":[{"id":"1","answer":"a\\ud800b"}]}',
                     '{"exam_id":"synthetic-fixture-v1","answers":[{"id":"1","answer":' + "7" * 5000 + "}]}"):
            (self.tmp / "v.json").write_text(body, encoding="utf-8")
            self.assertEqual(cli("validate", self.tmp / "v.json", "--template", template)[0], 2)
        (self.tmp / "bad-template.json").write_text('{"exam_id":"x","answers":[{"answer":""}]}', encoding="utf-8")
        self.assertEqual(cli("validate", self.tmp / "v.json", "--template", self.tmp / "bad-template.json")[0], 2)

    def test_reasoning_parts_and_markers_never_submitted(self):
        parts = mp.synthetic_record("1", None)
        parts["raw_response"] = {"choices": [{"finish_reason": "stop", "message": {"content": [
            {"type": "reasoning", "text": "SECRET"}, {"type": "thinking", "text": "HIDDEN"}, {"type": "text", "text": "final"}]}}]}
        rows = [parts,
                mp.synthetic_record("2.1", "<thinking>SECRET</thinking>Y"),
                mp.synthetic_record("2.2", "<|channel|>analysis<|message|>SECRET<|end|><|start|>assistant<|channel|>final<|message|>Z<|return|>"),
                mp.synthetic_record("3", "<|channel|>analysis<|message|>SECRET only")]
        self.assertEqual(self.finalize(write_jsonl(self.tmp / "r.jsonl", rows))[0], 1)
        self.assertEqual([a["answer"] for a in self.answers()], ["final", "Y", "Z", ""])
        self.assertNotIn("SECRET", (self.tmp / "answers.json").read_text(encoding="utf-8"))

    def test_orphan_closing_think_keeps_final_text(self):
        self.finalize(self.raw({"1": "rozumowanie...</think>\n\nOdpowiedź A", "2.1": "a</think>b</think>c"}))
        self.assertEqual([a["answer"] for a in self.answers()][:2], ["Odpowiedź A", "c"])

    def test_content_filter_and_next_choice(self):
        filtered = mp.synthetic_record("1", "częściowa", finish_reason="content_filter")
        multi = mp.synthetic_record("2.1", "<think>open")
        multi["raw_response"]["choices"].append({"finish_reason": "stop", "message": {"content": "druga"}})
        self.finalize(write_jsonl(self.tmp / "r.jsonl", [filtered, multi]))
        self.assertEqual([a["answer"] for a in self.answers()][:2], ["", "druga"])
        self.assertEqual(self.report()["failures"][0]["type"], "incomplete")

    def test_duplicate_keys_in_raw_record(self):
        (self.tmp / "d.jsonl").write_text('{"id":"1","id":"2.1","raw_response":null,"error":null}\n', encoding="utf-8")
        self.assertEqual(self.finalize(self.tmp / "d.jsonl")[0], 2)

    def test_manifest_required_and_tied_to_package(self):
        raw = self.raw({"1": "a"})
        with self.assertRaises(SystemExit) as caught:  # argparse: --manifest or --no-manifest required
            cli("finalize", "--exam-dir", self.pkg, "--raw", raw, "--output", self.tmp / "a.json")
        self.assertEqual(caught.exception.code, 2)
        cli("prepare", "--exam-dir", self.pkg, "--output", self.tmp / "input.jsonl")
        other = self.tmp / "other"
        shutil.copytree(self.pkg, other)
        for name in ("exam.json", "answers-template.json"):
            path = other / name
            path.write_text(path.read_text(encoding="utf-8").replace("synthetic-fixture-v1", "other-exam-v9"), encoding="utf-8")
        code, _, err = cli("finalize", "--exam-dir", other, "--raw", raw, "--output", self.tmp / "a.json",
                           "--manifest", self.tmp / "input.jsonl.manifest.json")
        self.assertEqual(code, 2)
        self.assertIn("exam_id", err)

    def test_unknown_fields_are_sent_not_dropped(self):
        def change(exam):
            exam["preamble"] = "WSTĘP-XYZ"
            exam["items"][0]["hint"] = "PODPOWIEDŹ-XYZ"
            exam["items"][0]["images"][0]["caption"] = "PODPIS-XYZ"
        self.edit_exam(change)
        code, out, _ = cli("check", "--exam-dir", self.pkg)
        self.assertEqual(json.loads(out)["unknown_fields_passed_to_model"], {"exam": ["preamble"], "item": ["hint"], "image": ["caption"]})
        cli("prepare", "--exam-dir", self.pkg, "--output", self.tmp / "input.jsonl")
        first = json.loads((self.tmp / "input.jsonl").read_text(encoding="utf-8").split("\n")[0])
        for marker in ("WSTĘP-XYZ", "PODPOWIEDŹ-XYZ", "PODPIS-XYZ"):
            self.assertIn(marker, first["prompt"])

    def test_case_sensitive_image_paths_and_finite_points(self):
        self.edit_exam(lambda e: e["items"][0]["images"][0].update(path="images/FIXTURE-RED.png"))
        self.assertIn("case-sensitive", cli("check", "--exam-dir", self.pkg)[2])
        shutil.rmtree(self.pkg)
        shutil.copytree(FIXTURE, self.pkg)
        (self.pkg / "exam.json").write_text((self.pkg / "exam.json").read_text(encoding="utf-8")
                                           .replace('"max_points": 7', '"max_points": Infinity'), encoding="utf-8")
        self.assertEqual(cli("check", "--exam-dir", self.pkg)[0], 2)

    def test_failure_report_not_overwritten(self):
        (self.tmp / "answers.json.failures.json").write_text("{}")
        self.assertEqual(self.finalize(self.raw({"1": "a"}))[0], 2)
        self.assertFalse((self.tmp / "answers.json").exists())


class OutputPathGuards(Base):
    """Lead review P2: --report must never overwrite --output, the package, or raw inputs."""

    def run_finalize(self, output, report, raw=None, manifest=None):
        raw = raw or self.raw({i: "a" for i in IDS})
        extra = ["--manifest", manifest] if manifest else ["--no-manifest"]
        return cli("finalize", "--exam-dir", self.pkg, "--raw", raw, "--output", output, "--report", report, *extra)

    def test_report_equal_to_output_rejected_before_writing(self):
        target = self.tmp / "answers.json"
        code, _, err = self.run_finalize(target, self.tmp / "sub" / ".." / "answers.json")
        self.assertEqual(code, 2)
        self.assertIn("collide", err)
        self.assertFalse(target.exists())

    def test_outputs_never_overwrite_inputs(self):
        raw = self.raw({i: "a" for i in IDS})
        cli("prepare", "--exam-dir", self.pkg, "--output", self.tmp / "input.jsonl")
        manifest = self.tmp / "input.jsonl.manifest.json"
        protected = [self.pkg / "exam.json", self.pkg / "answers-template.json", self.pkg / "images" / "fixture-red.png",
                     raw, manifest]
        before = {path: path.read_bytes() for path in protected}
        for target in protected:
            for output, report in ((target, self.tmp / "r.json"), (self.tmp / "a.json", target)):
                with self.subTest(target=target.name, as_report=report == target):
                    code, _, err = self.run_finalize(output, report, raw, manifest)
                    self.assertEqual(code, 2)
                    self.assertIn("input artifact", err)
                    self.assertFalse((self.tmp / "a.json").exists() or (self.tmp / "r.json").exists())
        self.assertEqual(before, {path: path.read_bytes() for path in protected})

    def test_prepare_never_overwrites_package_or_manifest(self):
        self.assertEqual(cli("prepare", "--exam-dir", self.pkg, "--output", self.pkg / "exam.json")[0], 2)
        (self.tmp / "input.jsonl.manifest.json").write_text("keep")
        self.assertEqual(cli("prepare", "--exam-dir", self.pkg, "--output", self.tmp / "input.jsonl")[0], 2)
        self.assertEqual((self.tmp / "input.jsonl.manifest.json").read_text(), "keep")
        self.assertFalse((self.tmp / "input.jsonl").exists())


class Validate(Base):
    def check(self, doc=None, raw_bytes=None):
        path = self.tmp / "candidate.json"
        path.write_bytes(raw_bytes if raw_bytes is not None else json.dumps(doc, ensure_ascii=False).encode("utf-8"))
        code, out, _ = cli("validate", path, "--template", self.pkg / "answers-template.json")
        return code, json.loads(out)["problems"]

    def good(self):
        return {"exam_id": "synthetic-fixture-v1", "answers": [{"id": i, "answer": ""} for i in IDS]}

    def test_template_itself_is_valid(self):
        self.assertEqual(self.check(self.good()), (0, []))

    def test_order_does_not_matter(self):
        doc = self.good()
        doc["answers"].reverse()
        self.assertEqual(self.check(doc)[0], 0)

    def test_rejections(self):
        cases = {
            "missing": lambda d: d["answers"].pop(),
            "duplicate": lambda d: d["answers"].append({"id": "1", "answer": ""}),
            "unknown": lambda d: d["answers"].append({"id": "99", "answer": ""}),
            "number answer": lambda d: d["answers"][0].update(answer=1),
            "null answer": lambda d: d["answers"][0].update(answer=None),
            "array answer": lambda d: d["answers"][0].update(answer=["A"]),
            "numeric id": lambda d: d["answers"][0].update(id=1),
            "extra entry field": lambda d: d["answers"][0].update(reasoning="x"),
            "extra top field": lambda d: d.update(usage={}),
            "exam id": lambda d: d.update(exam_id="history-2023-mock-v1"),
            "too many chars": lambda d: d["answers"][0].update(answer="a" * (mp.MAX_ANSWER_CHARS + 1)),
            "utf16 over limit": lambda d: d["answers"][0].update(answer="😀" * 50_001),
        }
        for name, change in cases.items():
            doc = self.good()
            change(doc)
            with self.subTest(name):
                code, problems = self.check(doc)
                self.assertEqual(code, 2)
                self.assertTrue(problems)

    def test_char_limit_boundary_allowed(self):
        doc = self.good()
        doc["answers"][0]["answer"] = "ą" * mp.MAX_ANSWER_CHARS
        self.assertEqual(self.check(doc)[0], 0)

    def test_byte_limit(self):
        doc = self.good()
        for entry in doc["answers"]:
            entry["answer"] = "€" * 99_000  # 3 UTF-8 bytes each: each answer is legal, the file is > 1 MiB
        code, problems = self.check(doc)
        self.assertEqual(code, 2)
        self.assertIn("1 MiB", problems[0])

    def test_finalize_refuses_oversized_file(self):
        code, _, err = cli("finalize", "--exam-dir", self.pkg, "--output", self.tmp / "big.json", "--no-manifest", "--raw",
                           write_jsonl(self.tmp / "r.jsonl", [mp.synthetic_record(i, "€" * 99_000) for i in IDS]))
        self.assertEqual(code, 2)
        self.assertIn("1 MiB", err)
        self.assertFalse((self.tmp / "big.json").exists())

    def test_encoding_and_json_errors(self):
        good = json.dumps(self.good()).encode("utf-8")
        self.assertEqual(self.check(raw_bytes=b"\xef\xbb\xbf" + good)[0], 2)
        self.assertEqual(self.check(raw_bytes=good[:-5])[0], 2)  # truncated file
        self.assertEqual(self.check(raw_bytes=b"\xff" + good)[0], 2)
        self.assertEqual(self.check(raw_bytes=b'{"exam_id":"a","exam_id":"b","answers":[]}')[0], 2)


class RunWrapper(Base):
    def test_dry_run_uses_infer_py(self):
        config = self.tmp / "config.json"
        config.write_text(json.dumps({"name": "t", "base_url": "http://127.0.0.1:9/v1", "model": "m", "max_output_tokens": 4096}))
        code, out, _ = cli("run", "--exam-dir", self.pkg, "--config", config, "--workdir", self.tmp / "w", "--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["dry_run"])

    def test_remote_endpoint_refused(self):
        config = self.tmp / "config.json"
        config.write_text(json.dumps({"name": "t", "base_url": "https://example.com/v1", "model": "m"}))
        code, _, _ = cli("run", "--exam-dir", self.pkg, "--config", config, "--workdir", self.tmp / "w", "--dry-run")
        self.assertEqual(code, 2)


class Issue45Acceptance(Base):
    """Issue #45 (independent review of #37): explicit completion, any non-null error, mandatory source fields."""

    def answers(self, name="answers.json"):
        return json.loads((self.tmp / name).read_text(encoding="utf-8"))["answers"]

    def test_issue_repro_snippet_all_rejected(self):
        r = mp.synthetic_record("invented-review", "INVENTED ANSWER")
        r["raw_response"]["choices"][0].pop("finish_reason")
        self.assertIsNotNone(mp.extract_answer(r)[1], "missing finish_reason accepted")
        r["raw_response"]["choices"][0]["finish_reason"] = None
        self.assertIsNotNone(mp.extract_answer(r)[1], "null finish_reason accepted")
        r["raw_response"]["choices"][0]["finish_reason"] = "stop"
        self.assertIsNone(mp.extract_answer(r)[1], "explicit stop must still be complete")
        r["error"] = ""
        self.assertIsNotNone(mp.extract_answer(r)[1], "non-null empty error accepted")

    def test_missing_null_and_unknown_finish_reason_stay_blank_with_report(self):
        missing = mp.synthetic_record("1", "INVENTED A")
        missing["raw_response"]["choices"][0].pop("finish_reason")
        null = mp.synthetic_record("2.1", "INVENTED B", finish_reason=None)
        unknown = mp.synthetic_record("2.2", "INVENTED C", finish_reason="invented_reason")
        ok = mp.synthetic_record("3", "INVENTED D")
        code, _, _ = self.finalize(write_jsonl(self.tmp / "raw.jsonl", [ok, unknown, null, missing]))
        self.assertEqual(code, 1)
        self.assertEqual([a["id"] for a in self.answers()], IDS)  # template order and exact IDs preserved
        self.assertEqual([a["answer"] for a in self.answers()], ["", "", "", "INVENTED D"])
        self.assertNotIn("INVENTED A", (self.tmp / "answers.json").read_text(encoding="utf-8"))
        failures = {f["id"]: f for f in self.report()["failures"]}
        self.assertEqual({i: f["type"] for i, f in failures.items()}, {"1": "incomplete", "2.1": "incomplete", "2.2": "incomplete"})
        self.assertIn("missing", failures["1"]["message"])
        self.assertIn("None", failures["2.1"]["message"])
        self.assertIn("invented_reason", failures["2.2"]["message"])
        self.assertEqual(cli("validate", self.tmp / "answers.json", "--exam-dir", self.pkg)[0], 0)

    def test_every_supported_finish_reason_completes(self):
        for reason in sorted(mp.COMPLETE_FINISH):
            self.assertIsNone(mp.extract_answer(mp.synthetic_record("1", "x", finish_reason=reason))[1], reason)
        self.assertNotIn(None, mp.COMPLETE_FINISH)

    def test_null_error_is_not_a_failure_but_any_other_error_is(self):
        rows = [
            mp.synthetic_record("1", "INVENTED OK"),  # error: None -> accepted
            mp.synthetic_record("2.1", "INVENTED X", error=""),
            mp.synthetic_record("2.2", "INVENTED Y", error={}),
            mp.synthetic_record("3", "INVENTED Z", error={"type": "", "message": "   "}),
        ]
        self.assertEqual(rows[0]["error"], None)
        code, _, _ = self.finalize(write_jsonl(self.tmp / "raw.jsonl", rows))
        self.assertEqual(code, 1)
        self.assertEqual([a["answer"] for a in self.answers()], ["INVENTED OK", "", "", ""])
        failures = {f["id"]: f for f in self.report()["failures"]}
        self.assertEqual(sorted(failures), ["2.1", "2.2", "3"])
        for failure in failures.values():
            self.assertEqual(failure["type"], "infer_error")
            self.assertTrue(failure["message"].strip())
        for text in ("INVENTED X", "INVENTED Y", "INVENTED Z"):
            self.assertNotIn(text, (self.tmp / "answers.json").read_text(encoding="utf-8"))

    def test_error_false_or_zero_is_still_a_failure(self):
        for error in (False, 0, [], "0"):
            row = mp.synthetic_record("1", "INVENTED", error=error)
            self.assertIsNotNone(mp.extract_answer(row)[1], repr(error))

    def test_absent_instructions_rejected_empty_allowed(self):
        self.assertEqual(cli("check", "--exam-dir", self.pkg)[0], 0)  # unchanged fixture still valid
        self.edit_exam(lambda e: e.update(instructions=""))
        self.assertEqual(cli("check", "--exam-dir", self.pkg)[0], 0)
        self.assertEqual(cli("prepare", "--exam-dir", self.pkg, "--output", self.tmp / "w" / "in.jsonl")[0], 0)
        self.edit_exam(lambda e: e.pop("instructions"))
        code, _, err = cli("check", "--exam-dir", self.pkg)
        self.assertEqual(code, 2)
        self.assertIn("instructions is required", err)
        self.assertEqual(cli("prepare", "--exam-dir", self.pkg, "--output", self.tmp / "w2" / "in.jsonl")[0], 2)
        self.edit_exam(lambda e: e.update(instructions=None))
        self.assertIn("instructions must be a string", cli("check", "--exam-dir", self.pkg)[2])

    def test_absent_source_text_rejected_empty_allowed(self):
        exam = json.loads((self.pkg / "exam.json").read_text(encoding="utf-8"))
        self.assertEqual(exam["items"][1]["source_text"], "")  # the fixture already carries an explicit empty source
        self.assertEqual(cli("check", "--exam-dir", self.pkg)[0], 0)
        self.edit_exam(lambda e: e["items"][3].pop("source_text"))
        code, _, err = cli("check", "--exam-dir", self.pkg)
        self.assertEqual(code, 2)
        self.assertIn("item '3': source_text is required", err)
        self.assertEqual(cli("prepare", "--exam-dir", self.pkg, "--output", self.tmp / "w" / "in.jsonl")[0], 2)
        self.assertFalse((self.tmp / "w" / "in.jsonl").exists())
        self.edit_exam(lambda e: e["items"][3].update(source_text=None))
        self.assertIn("source_text must be a string", cli("check", "--exam-dir", self.pkg)[2])

    def test_finalize_also_requires_source_fields(self):
        self.edit_exam(lambda e: e.pop("instructions"))
        code, _, err = self.finalize(self.raw({"1": "a"}))
        self.assertEqual(code, 2)
        self.assertIn("instructions is required", err)
        self.assertFalse((self.tmp / "answers.json").exists())


if __name__ == "__main__":
    unittest.main()
