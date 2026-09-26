"""Organizer exam package -> canonical infer.py JSONL -> validated answers.json.

Offline adapter for the Warsaw Model Trainers matura submission format
(https://matura-json-guide.ania-olchowik.chatgpt.site/). Standard library only.

Subcommands:
  fetch-mock  preparation step (network): download the public mock package, verify pinned SHA-256
  check       validate an unpacked package (exam.json, answers-template.json, images) and print aggregates
  prepare     package -> {id,prompt,images} JSONL for infer.py plus a sidecar manifest
  finalize    infer.py output JSONL -> answers.json (template order, exact IDs) plus a local failure report
  validate    check a final answers.json against the package template (nonzero exit when invalid)
  run         prepare -> infer.py (subprocess, loopback endpoint only) -> finalize -> validate
  synthetic-outputs  write clearly SYNTHETIC infer.py-shaped records for format tests (never a model result)

Exit codes: 0 ok; 1 answers.json written and valid but some answers are empty because model output
failed (see the failure report); 2 invalid package/input/output or invalid answers.json.

Nothing in this module fetches URLs except `fetch-mock`. Exam contents and model outputs belong in
ignored paths (`outputs/`, `agentsLog/**/private/`), never in a public commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 1024 * 1024
MAX_ANSWER_CHARS = 100_000
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
INFER_MAX_CALLS = 100
REPO_ROOT = Path(__file__).resolve().parents[2]

MOCK_BASE = "https://matura-json-guide.ania-olchowik.chatgpt.site/"
MOCK_ZIP_NAME = "history-2023-mock-v1.zip"
FETCH_USER_AGENT = "matura-package-adapter/1.0 (kwiscion/machinekind-matura issue 37)"
# SHA-256 of the public mock as retrieved 2026-09-26 14:41 Europe/Warsaw (see agentsLog/Bukareszt/submission/).
MOCK_PINS = {
    "exam-pack-1.bin": "62232180c0e2ee41042a44debf81d9e57950fa5f63381dd662c9a65daa6f7c03",
    "exam-pack-2.bin": "9256fa36f7f1464e2b8394f1860b0a8fec946c220c005c7a781f74fb27b3b732",
    MOCK_ZIP_NAME: "315d256ca9086bd03f3ccee8758cc89e2f95ba678f40a864395af72b04f19917",
    "exam/exam.json": "0d4559be6ffae26304b102d8cec14814849caec879fd53d8be0196f24116354c",
    "exam/answers-template.json": "35675b9a7766d2b5314188796b5d26fc97c75d9cd65a0bd8612cb74bdf81d9c0",
    "exam/README.md": "8cdcae95e2c177177bf81470819c76f5205af83f8c8998e301671bc01642d36a",
}

PROMPT_HEADER = "Egzamin maturalny. Odpowiedz na jedno zadanie."
PROMPT_FOOTER = (
    "Przykłady w formacie odpowiedzi pokazują tylko składnię, nie są rozwiązaniem.\n"
    "Zwróć wyłącznie końcową odpowiedź po polsku, bez rozumowania i komentarzy."
)


class PackageError(ValueError):
    """Invalid package, model output, or answer file."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def reject_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise PackageError(f"Duplicate JSON key: {key!r}")
        seen[key] = value
    return seen


def load_json_strict(path: Path):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise PackageError(f"{path.name}: UTF-8 BOM is not allowed")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PackageError(f"{path.name}: not valid UTF-8 ({exc.reason} at byte {exc.start})") from exc
    try:
        return json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise PackageError(f"{path.name}: invalid JSON ({exc.msg}, line {exc.lineno})") from exc


def utf16_units(text: str) -> int:
    return len(text.encode("utf-16-le", "surrogatepass")) // 2


def has_lone_surrogate(text: str) -> bool:
    return any(0xD800 <= ord(char) <= 0xDFFF for char in text)


# str.splitlines() also splits on U+2028/U+2029/U+0085, which json.dumps(ensure_ascii=False) leaves raw;
# escape them in files we write and split JSONL only on "\n" when reading.
LINE_SEPARATORS = {"\u2028": "\\u2028", "\u2029": "\\u2029", "\x85": "\\u0085"}


def jsonl_line(record: dict) -> str:
    text = json.dumps(record, ensure_ascii=False)
    for raw, escaped in LINE_SEPARATORS.items():
        text = text.replace(raw, escaped)
    return text + "\n"


def jsonl_lines(text: str) -> list[str]:
    return [line.rstrip("\r") for line in text.split("\n")]


def is_number(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


# Fields whose meaning is known and which are deliberately not sent to the model (metadata).
EXAM_META_FIELDS = {"exam_id", "title", "language", "source_exam_id", "source_url", "input_format", "max_points",
                    "instructions", "items"}
ITEM_KNOWN_FIELDS = {"id", "group", "max_points", "question", "source_text", "images", "answer_format"}
IMAGE_KNOWN_FIELDS = {"path", "source_page", "sha256"}


def safe_relative(path_text: str, where: str) -> PurePosixPath:
    if not isinstance(path_text, str) or not path_text:
        raise PackageError(f"{where}: image path must be a nonempty string")
    rel = PurePosixPath(path_text.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts or re.match(r"^[A-Za-z]:", path_text):
        raise PackageError(f"{where}: image path must stay inside the exam folder: {path_text!r}")
    return rel


def check_new_outputs(outputs: list[Path | None], protected: list[Path]) -> None:
    """Refuse before any write: outputs must be new, distinct, and never an input artifact."""
    resolved = [path.resolve() for path in outputs if path is not None]
    guarded = {path.resolve() for path in protected}
    if len(set(resolved)) != len(resolved):
        raise PackageError(f"Output paths collide: {[str(p) for p in resolved]}")
    for path in resolved:
        if path in guarded:
            raise PackageError(f"Output would overwrite an input artifact: {path}")
        if path.exists():
            raise PackageError(f"Output must be a new path: {path}")


# ---------------------------------------------------------------- package check

def exact_case(root: Path, rel: PurePosixPath) -> bool:
    """True when every path component exists with exactly this spelling (macOS/Windows ignore case)."""
    current = root
    for part in rel.parts:
        if part not in os.listdir(current):
            return False
        current = current / part
    return True


def extra_fields(exam: dict) -> dict:
    """Unknown fields that prepare will pass to the model verbatim instead of dropping them."""
    found = {"exam": sorted(set(exam) - EXAM_META_FIELDS), "item": set(), "image": set()}
    for item in exam.get("items", []):
        if isinstance(item, dict):
            found["item"] |= set(item) - ITEM_KNOWN_FIELDS
            for image in item.get("images") or []:
                if isinstance(image, dict):
                    found["image"] |= set(image) - IMAGE_KNOWN_FIELDS
    return {key: sorted(value) for key, value in found.items()}


def load_package(exam_dir: Path, template_path: Path | None = None) -> dict:
    """Validate exam.json + template + images. Returns a dict with exam, template and summary."""
    exam_dir = exam_dir.resolve()
    exam_path = exam_dir / "exam.json"
    template_path = (template_path or exam_dir / "answers-template.json").resolve()
    for path in (exam_path, template_path):
        if not path.is_file():
            raise PackageError(f"Missing file: {path}")
    exam = load_json_strict(exam_path)
    template = load_json_strict(template_path)
    errors: list[str] = []

    if not isinstance(exam, dict):
        raise PackageError("exam.json must be a JSON object")
    exam_id = exam.get("exam_id")
    if not isinstance(exam_id, str) or not exam_id:
        errors.append("exam.json: exam_id must be a nonempty string")
    if "instructions" not in exam:  # the organizer guide requires the field; an empty string is allowed
        errors.append("exam.json: instructions is required (a string; may be empty)")
    elif not isinstance(exam["instructions"], str):
        errors.append("exam.json: instructions must be a string")
    items = exam.get("items")
    if not isinstance(items, list) or not items:
        raise PackageError("exam.json: items must be a nonempty array")

    item_ids: list[str] = []
    points = 0
    image_refs = 0
    images: dict[str, dict] = {}
    for index, item in enumerate(items):
        where = f"exam.json items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where}: must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{where}: id must be a nonempty string")
            continue
        where = f"exam.json item {item_id!r}"
        item_ids.append(item_id)
        for field in ("question", "answer_format"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{where}: {field} must be a nonempty string")
        if "source_text" not in item:  # required by the organizer guide; an explicit empty string is allowed
            errors.append(f"{where}: source_text is required (a string; may be empty)")
        elif not isinstance(item["source_text"], str):
            errors.append(f"{where}: source_text must be a string")
        max_points = item.get("max_points")
        if not is_number(max_points) or max_points < 0:
            errors.append(f"{where}: max_points must be a nonnegative number")
        else:
            points += max_points
        item_images = item.get("images", [])
        if not isinstance(item_images, list):
            errors.append(f"{where}: images must be an array")
            continue
        for image in item_images:
            image_refs += 1
            if not isinstance(image, dict):
                errors.append(f"{where}: image entry must be an object")
                continue
            try:
                rel = safe_relative(image.get("path"), where)
            except PackageError as exc:
                errors.append(str(exc))
                continue
            key = rel.as_posix()
            expected = image.get("sha256")
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected.lower()):
                errors.append(f"{where}: image {key} needs a 64-hex sha256")
                continue
            if key in images:
                if images[key]["sha256"] != expected.lower():
                    errors.append(f"{where}: image {key} listed with conflicting sha256 values")
                continue
            file_path = (exam_dir / rel).resolve()
            if exam_dir not in file_path.parents:
                errors.append(f"{where}: image {key} resolves outside the exam folder")
                continue
            if not file_path.is_file() or not exact_case(exam_dir, rel):
                errors.append(f"{where}: image file missing (paths are case-sensitive): {key}")
                images[key] = {"sha256": expected.lower(), "bytes": None}
                continue
            data = file_path.read_bytes()
            if not data.startswith(PNG_MAGIC):
                errors.append(f"{where}: image {key} is not a PNG file")
            actual = sha256_bytes(data)
            if actual != expected.lower():
                errors.append(f"{where}: image {key} sha256 mismatch (expected {expected.lower()}, got {actual})")
            images[key] = {"sha256": expected.lower(), "bytes": len(data)}

    duplicates = sorted({i for i in item_ids if item_ids.count(i) > 1})
    if duplicates:
        errors.append(f"exam.json: duplicate item ids {duplicates}")
    if "max_points" in exam and (not is_number(exam["max_points"]) or exam["max_points"] != points):
        errors.append(f"exam.json: max_points {exam['max_points']} != sum of item points {points}")

    template_ids: list[str] = []
    if not isinstance(template, dict) or set(template) != {"exam_id", "answers"}:
        errors.append("template: top level must have exactly exam_id and answers")
    else:
        if template["exam_id"] != exam_id:
            errors.append(f"template exam_id {template['exam_id']!r} != exam.json exam_id {exam_id!r}")
        if not isinstance(template["answers"], list):
            errors.append("template: answers must be an array")
        else:
            for index, entry in enumerate(template["answers"]):
                if not isinstance(entry, dict) or set(entry) != {"id", "answer"}:
                    errors.append(f"template answers[{index}]: must have exactly id and answer")
                    continue
                if not isinstance(entry["id"], str) or not entry["id"]:
                    errors.append(f"template answers[{index}]: id must be a nonempty string")
                    continue
                if not isinstance(entry["answer"], str):
                    errors.append(f"template answers[{index}]: answer must be a string")
                template_ids.append(entry["id"])
    template_dupes = sorted({i for i in template_ids if template_ids.count(i) > 1})
    if template_dupes:
        errors.append(f"template: duplicate ids {template_dupes}")
    only_exam = sorted(set(item_ids) - set(template_ids))
    only_template = sorted(set(template_ids) - set(item_ids))
    if only_exam:
        errors.append(f"ids in exam.json but not in template: {only_exam}")
    if only_template:
        errors.append(f"ids in template but not in exam.json: {only_template}")
    if errors:
        raise PackageError("Invalid package:\n  " + "\n  ".join(errors))

    summary = {
        "exam_id": exam_id,
        "items": len(item_ids),
        "points": points,
        "declared_max_points": exam.get("max_points"),
        "unique_image_files": len(images),
        "image_references": image_refs,
        "items_with_images": sum(1 for item in items if item.get("images")),
        "image_bytes": sum(meta["bytes"] or 0 for meta in images.values()),
        "template_ids_match": True,
        "unknown_fields_passed_to_model": extra_fields(exam),
        "exam_json_sha256": sha256_file(exam_path),
        "template_sha256": sha256_file(template_path),
        "item_ids_sha256": sha256_bytes("\n".join(item_ids).encode("utf-8")),
    }
    return {"exam_dir": exam_dir, "exam": exam, "template": template, "template_path": template_path,
            "exam_path": exam_path, "images": images, "summary": summary}


def package_inputs(package: dict) -> list[Path]:
    return [package["exam_path"], package["template_path"]] + [package["exam_dir"] / rel for rel in package["images"]]


# ---------------------------------------------------------------- prepare

def field_text(value) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def build_prompt(exam: dict, item: dict) -> str:
    parts = [PROMPT_HEADER]
    instructions = exam.get("instructions", "")
    if instructions.strip():
        parts.append("Instrukcja do całego egzaminu:\n" + instructions)
    for field in sorted(set(exam) - EXAM_META_FIELDS):  # unknown exam-level material is sent, not dropped
        parts.append(f"{field}:\n" + field_text(exam[field]))
    parts.append(f"Zadanie {item['id']} (maks. {item['max_points']} pkt)\n" + item["question"])
    if item.get("source_text", "").strip():
        parts.append("Materiał źródłowy:\n" + item["source_text"])
    for field in sorted(set(item) - ITEM_KNOWN_FIELDS):
        parts.append(f"{field}:\n" + field_text(item[field]))
    if item.get("images"):
        lines = []
        for image in item["images"]:
            line = f"- {PurePosixPath(image['path']).as_posix()}"
            extra = {k: image[k] for k in sorted(set(image) - IMAGE_KNOWN_FIELDS)}
            lines.append(line + (" " + json.dumps(extra, ensure_ascii=False) if extra else ""))
        parts.append("Załączone obrazy (w tej kolejności):\n" + "\n".join(lines))
    parts.append("Wymagany format odpowiedzi:\n" + item["answer_format"])
    parts.append(PROMPT_FOOTER)
    return "\n\n".join(parts)


def prepare(package: dict, output: Path) -> dict:
    output = output.resolve()
    manifest_path = output.with_name(output.name + ".manifest.json")
    check_new_outputs([output, manifest_path], package_inputs(package))
    exam = package["exam"]
    records = []
    for item in exam["items"]:
        image_paths = []
        for image in item.get("images", []):
            target = package["exam_dir"] / safe_relative(image["path"], item["id"])
            try:
                image_paths.append(Path(os.path.relpath(target, output.parent)).as_posix())
            except ValueError:  # different drive on Windows: infer.py also accepts absolute paths
                image_paths.append(target.as_posix())
        record = {"id": item["id"], "prompt": build_prompt(exam, item), "images": image_paths}
        # Every source string must survive verbatim; fail loudly instead of guessing a context window.
        for field in ("question", "source_text", "answer_format"):
            if item.get(field) and item[field] not in record["prompt"]:
                raise PackageError(f"Item {item['id']}: {field} not preserved in prompt")
        records.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(jsonl_line(record))
    manifest = {
        **package["summary"],
        "prepared_jsonl": output.name,
        "prepared_sha256": sha256_file(output),
        "records": len(records),
        "prompt_chars_total": sum(len(r["prompt"]) for r in records),
        "prompt_chars_max": max(len(r["prompt"]) for r in records),
        "images_per_record_max": max(len(r["images"]) for r in records),
        "ids": [r["id"] for r in records],
    }
    with manifest_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


# ---------------------------------------------------------------- finalize

REASONING_BLOCK = re.compile(r"<(think|thinking|reasoning)>.*?</\1>", re.S | re.I)
REASONING_TAG = re.compile(r"</?(think|thinking|reasoning)>", re.I)
HARMONY_FINAL = "<|channel|>final<|message|>"
HARMONY_MARKER = re.compile(r"<\|(channel|message|start|end|return|call)\|>")
# Only an explicit, supported terminal signal counts as a complete answer (issue #45). A missing, null or
# unknown finish_reason keeps the ID as a blank answer with a failure record; nonempty content alone is not enough.
COMPLETE_FINISH = {"stop", "eos", "end_turn", "stop_sequence"}


def final_content(content: str) -> tuple[str | None, str | None]:
    """Remove reasoning channels. Returns (text, problem)."""
    if HARMONY_MARKER.search(content):
        if HARMONY_FINAL not in content:
            return None, "harmony channel markers without a final channel"
        content = content.rsplit(HARMONY_FINAL, 1)[1]
        content = re.split(r"<\|(end|return)\|>", content, maxsplit=1)[0]
        if HARMONY_MARKER.search(content):
            return None, "unexpected harmony markers inside the final channel"
    content = REASONING_BLOCK.sub("", content)
    tags = REASONING_TAG.findall(content)
    if tags:
        # Qwen-style chat templates open <think> in the prompt, so only the closing tag reaches the output.
        opening = re.search(r"<(think|thinking|reasoning)>", content, re.I)
        closing = list(re.finditer(r"</(think|thinking|reasoning)>", content, re.I))
        if opening or not closing:
            return None, "unbalanced reasoning block in final content"
        content = content[closing[-1].end():]
    return content, None


def extract_answer(row: dict) -> tuple[str | None, dict | None]:
    """Return (answer, failure). failure is None only for a usable complete final answer."""
    def fail(kind: str, message: str) -> tuple[None, dict]:
        return None, {"type": kind, "message": message}

    if row.get("error") is not None:  # every non-null error is a failure, even "" or {} (issue #45)
        error = row["error"]
        message = error.get("message") if isinstance(error, dict) else error
        kind = error.get("type") if isinstance(error, dict) else None
        if not isinstance(kind, str) or not kind:
            kind = "error"
        if message is None or not str(message).strip():
            message = "non-null error without a message: " + json.dumps(error, ensure_ascii=False)[:200]
        return fail(f"infer_{kind}", str(message)[:500])
    raw = row.get("raw_response")
    if isinstance(raw, str) and "provider_raw_response" in row:  # scripts/normalize_outputs.py format
        raw = row["provider_raw_response"]
    if not isinstance(raw, dict):
        return fail("malformed", "raw_response is not a chat-completions object")
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        return fail("malformed", "raw_response has no choices")
    problem = ("empty", "no nonempty final answer content")
    for choice in choices:
        if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
            continue
        content = choice["message"].get("content")
        if isinstance(content, list):  # only plain text parts; reasoning/thinking parts are never submitted
            content = "".join(part["text"] for part in content if isinstance(part, dict)
                              and part.get("type", "text") in ("text", "output_text") and isinstance(part.get("text"), str))
        if not isinstance(content, str) or not content.strip():
            continue
        finish = choice.get("finish_reason")
        if finish == "length":
            problem = ("truncated", "finish_reason=length: output cut by the token limit")
            continue
        if "finish_reason" not in choice:
            problem = ("incomplete", "finish_reason missing: no explicit completion signal")
            continue
        if finish not in COMPLETE_FINISH:
            problem = ("incomplete", f"finish_reason={finish!r} is not a supported completion signal "
                                     f"(expected one of {sorted(COMPLETE_FINISH)})")
            continue
        text, issue = final_content(content)
        if issue:
            problem = ("malformed", issue)
            continue
        text = text.strip()
        if not text:
            continue
        if has_lone_surrogate(text):
            problem = ("malformed", "answer is not encodable as UTF-8 (lone surrogate)")
            continue
        if len(text) > MAX_ANSWER_CHARS or utf16_units(text) > MAX_ANSWER_CHARS:
            problem = ("over_limit", f"answer has {len(text)} characters (> {MAX_ANSWER_CHARS}); not truncated")
            continue
        return text, None
    return fail(*problem)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise PackageError(f"{path.name}: not valid UTF-8 ({exc.reason})") from exc
    for number, line in enumerate(jsonl_lines(text), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line, object_pairs_hook=reject_duplicate_keys)
        except (json.JSONDecodeError, ValueError) as exc:
            raise PackageError(f"{path.name} line {number}: invalid JSON ({exc})") from exc
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise PackageError(f"{path.name} line {number}: record needs a string id")
        rows.append(row)
    return rows


def finalize(package: dict, outputs: list[Path], answers_path: Path, report_path: Path | None,
             manifest_path: Path | None = None) -> dict:
    template = package["template"]
    exam_id = template["exam_id"]
    template_ids = [entry["id"] for entry in template["answers"]]
    check_new_outputs([answers_path, report_path],
                      package_inputs(package) + list(outputs) + ([manifest_path] if manifest_path else []))
    if manifest_path:
        manifest = load_json_strict(manifest_path)
        if manifest.get("exam_id") != exam_id:
            raise PackageError(f"Prepared manifest exam_id {manifest.get('exam_id')!r} != template exam_id {exam_id!r}")
        if manifest.get("ids") != [item["id"] for item in package["exam"]["items"]]:
            raise PackageError("Prepared manifest ids differ from this package")
        for key in ("exam_json_sha256", "template_sha256"):
            if manifest.get(key) != package["summary"][key]:
                raise PackageError(f"Prepared manifest {key} differs from this package (outputs from another exam?)")
    rows = [row for path in outputs for row in read_jsonl(path)]
    by_id: dict[str, dict] = {}
    for row in rows:
        if row["id"] in by_id:
            raise PackageError(f"Duplicate model output id: {row['id']!r}")
        if row["id"] not in template_ids:
            raise PackageError(f"Unknown model output id (not in template): {row['id']!r}")
        if isinstance(row.get("exam_id"), str) and row["exam_id"] != exam_id:
            raise PackageError(f"Model output {row['id']!r} has exam_id {row['exam_id']!r} != {exam_id!r}")
        by_id[row["id"]] = row

    answers, failures = [], []
    for item_id in template_ids:
        row = by_id.get(item_id)
        if row is None:
            text, failure = None, {"type": "missing", "message": "no model output for this id"}
        else:
            text, failure = extract_answer(row)
        if failure:
            failures.append({"id": item_id, **failure})
        answers.append({"id": item_id, "answer": text or ""})
    submission = {"exam_id": exam_id, "answers": answers}
    encoded = encode_submission(submission)
    problems = validate_submission_bytes(encoded, template)
    if problems:
        raise PackageError("Refusing to write invalid answers.json:\n  " + "\n  ".join(problems))
    answers_path.parent.mkdir(parents=True, exist_ok=True)
    with answers_path.open("xb") as handle:
        handle.write(encoded)
    report = {
        "exam_id": exam_id,
        "answers_json": str(answers_path),
        "answers_sha256": sha256_bytes(encoded),
        "answers_bytes": len(encoded),
        "template_ids": len(template_ids),
        "model_output_records": len(rows),
        "model_output_sha256": {str(path): sha256_file(path) for path in outputs},
        "prepared_sha256": manifest.get("prepared_sha256") if manifest_path else None,
        "answered": sum(1 for a in answers if a["answer"]),
        "empty": sum(1 for a in answers if not a["answer"]),
        "failures": failures,
        "max_answer_chars": max((len(a["answer"]) for a in answers), default=0),
        "note": "Format validity only; this is not a correctness score.",
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


# ---------------------------------------------------------------- validate

def encode_submission(submission: dict) -> bytes:
    return (json.dumps(submission, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def validate_submission_bytes(data: bytes, template: dict) -> list[str]:
    problems: list[str] = []
    if len(data) > MAX_FILE_BYTES:
        problems.append(f"file is {len(data)} bytes (> {MAX_FILE_BYTES} = 1 MiB)")
    if data.startswith(b"\xef\xbb\xbf"):
        problems.append("UTF-8 BOM is not allowed")
        data = data[3:]
    try:
        doc = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except UnicodeDecodeError as exc:
        return problems + [f"not valid UTF-8: {exc.reason}"]
    except (json.JSONDecodeError, PackageError, ValueError) as exc:  # ValueError: e.g. >4300-digit integers
        return problems + [f"invalid JSON: {exc}"]
    if not isinstance(doc, dict):
        return problems + ["top level must be an object"]
    if set(doc) != {"exam_id", "answers"}:
        problems.append(f"top-level fields must be exactly exam_id and answers, got {sorted(doc)}")
    if doc.get("exam_id") != template["exam_id"]:
        problems.append(f"exam_id {doc.get('exam_id')!r} != template exam_id {template['exam_id']!r}")
    answers = doc.get("answers")
    if not isinstance(answers, list):
        return problems + ["answers must be an array"]
    expected = [entry.get("id") for entry in template["answers"] if isinstance(entry, dict)]
    if len(expected) != len(template["answers"]) or not all(isinstance(i, str) for i in expected):
        return problems + ["template entries must be objects with string ids"]
    seen: list[str] = []
    for index, entry in enumerate(answers):
        if not isinstance(entry, dict) or set(entry) != {"id", "answer"}:
            problems.append(f"answers[{index}]: must have exactly id and answer")
            continue
        if not isinstance(entry["id"], str):
            problems.append(f"answers[{index}]: id must be a string, got {type(entry['id']).__name__}")
            continue
        seen.append(entry["id"])
        if not isinstance(entry["answer"], str):
            problems.append(f"answer {entry['id']!r}: must be a string, got {type(entry['answer']).__name__}")
            continue
        if has_lone_surrogate(entry["answer"]):
            problems.append(f"answer {entry['id']!r}: contains a lone surrogate (not encodable as UTF-8)")
            continue
        if len(entry["answer"]) > MAX_ANSWER_CHARS or utf16_units(entry["answer"]) > MAX_ANSWER_CHARS:
            problems.append(f"answer {entry['id']!r}: {len(entry['answer'])} characters (> {MAX_ANSWER_CHARS})")
    duplicates = sorted({i for i in seen if seen.count(i) > 1})
    if duplicates:
        problems.append(f"duplicate ids {duplicates}")
    missing = [i for i in expected if i not in seen]
    unknown = sorted(set(seen) - set(expected))
    if missing:
        problems.append(f"missing template ids {missing}")
    if unknown:
        problems.append(f"ids not in template {unknown}")
    return problems


def load_template(args) -> dict:
    if args.template:
        template = load_json_strict(args.template)
    else:
        template = load_package(args.exam_dir)["template"]
    if not isinstance(template, dict) or not isinstance(template.get("answers"), list) or not isinstance(template.get("exam_id"), str):
        raise PackageError("template must have exam_id and an answers array")
    return template


# ---------------------------------------------------------------- fetch-mock (preparation step, network)

def fetch_mock(out_dir: Path, manifest_path: Path | None, allow_hash_change: bool) -> dict:
    import urllib.request  # only this preparation step touches the network

    out_dir = out_dir.resolve()
    download_dir = out_dir / "download"
    package_dir = out_dir / "package"
    if package_dir.exists():
        raise PackageError(f"Package folder already exists: {package_dir}")
    download_dir.mkdir(parents=True, exist_ok=True)
    retrieved = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    blobs = {}
    for name in ("exam-pack-1.bin", "exam-pack-2.bin", "exam/exam.json", "exam/answers-template.json", "exam/README.md"):
        # The CDN answers the default "Python-urllib" agent with 403 (Cloudflare 1010); identify honestly instead.
        request = urllib.request.Request(MOCK_BASE + name, headers={"User-Agent": FETCH_USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            blobs[name] = response.read()
        (download_dir / name.replace("/", "__")).write_bytes(blobs[name])
    blobs[MOCK_ZIP_NAME] = blobs["exam-pack-1.bin"] + blobs["exam-pack-2.bin"]
    (download_dir / MOCK_ZIP_NAME).write_bytes(blobs[MOCK_ZIP_NAME])
    files = {name: {"url": None if name == MOCK_ZIP_NAME else MOCK_BASE + name, "bytes": len(data),
                    "sha256": sha256_bytes(data), "pinned_sha256": MOCK_PINS.get(name)}
             for name, data in blobs.items()}
    files[MOCK_ZIP_NAME]["derived_from"] = "exam-pack-1.bin + exam-pack-2.bin (byte concatenation, in order)"
    changed = [name for name, meta in files.items() if meta["pinned_sha256"] and meta["pinned_sha256"] != meta["sha256"]]
    if changed and not allow_hash_change:
        raise PackageError(f"Downloaded bytes differ from pinned SHA-256: {changed} (use --allow-hash-change to accept)")
    with zipfile.ZipFile(download_dir / MOCK_ZIP_NAME) as archive:
        for member in archive.namelist():
            safe_relative(member, "zip member")
        archive.extractall(package_dir)
    for name in ("exam.json", "answers-template.json"):
        if (package_dir / name).read_bytes() != blobs["exam/" + name]:
            raise PackageError(f"Zip {name} differs from the published endpoint copy")
    package = load_package(package_dir)
    manifest = {
        "source": "Warsaw Model Trainers matura JSON guide, public mock package",
        "guide_url": MOCK_BASE,
        "retrieved_at": retrieved,
        "license": "unknown (organizer mock of the CKE May 2023 paper); contents kept local, not redistributed",
        "files": files,
        "hash_changed_vs_pins": changed,
        "zip_members": len(zipfile.ZipFile(download_dir / MOCK_ZIP_NAME).namelist()),
        "package": package["summary"],
        "images": {path: meta for path, meta in sorted(package["images"].items())},
        "local_package_dir": str(package_dir),
    }
    if manifest_path:
        public = {k: v for k, v in manifest.items() if k != "local_package_dir"}
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


# ---------------------------------------------------------------- run (wrapper)

def run_pipeline(args) -> int:
    workdir = args.workdir.resolve()
    if workdir.exists() and any(workdir.iterdir()):
        raise PackageError(f"Work folder must be new or empty: {workdir}")
    package = load_package(args.exam_dir)
    try:
        tokens = json.loads(args.config.read_text(encoding="utf-8")).get("max_output_tokens", 512)
        if isinstance(tokens, int) and tokens < 2048:
            print(f"Warning: max_output_tokens={tokens}; long answers/essays may be cut (finish_reason=length) "
                  "and then become empty answers. Consider 2048-4096.", file=sys.stderr)
    except (OSError, ValueError, AttributeError):
        pass  # infer.py reports config problems itself
    prepared = workdir / "input.jsonl"
    manifest = prepare(package, prepared)
    ids = manifest["ids"]
    if len(ids) > args.max_calls_total:
        raise PackageError(f"{len(ids)} items exceed --max-calls-total {args.max_calls_total}; no requests sent")
    lines = [line for line in jsonl_lines(prepared.read_text(encoding="utf-8")) if line.strip()]
    chunks = []
    for start in range(0, len(ids), INFER_MAX_CALLS):
        number = start // INFER_MAX_CALLS + 1
        chunk_input = prepared
        if len(ids) > INFER_MAX_CALLS:  # infer.py accepts at most 100 cases per call
            chunk_input = workdir / f"input.part{number}.jsonl"
            chunk_input.write_text("\n".join(lines[start:start + INFER_MAX_CALLS]) + "\n", encoding="utf-8")
        chunks.append((chunk_input, workdir / f"raw.part{number}.jsonl", len(lines[start:start + INFER_MAX_CALLS])))

    def infer(chunk_input, raw, count, dry_run):
        command = [sys.executable, str(args.infer), "--config", str(args.config), "--input", str(chunk_input),
                   "--output", str(raw), "--max-calls", str(count)] + (["--dry-run"] if dry_run else [])
        print("+ " + " ".join(command), file=sys.stderr)
        return subprocess.run(command).returncode

    for chunk in chunks:  # validate every chunk before the first model call
        if infer(*chunk, dry_run=True) != 0:
            raise PackageError("infer.py rejected config/input in dry run; no requests sent")
    if args.dry_run:
        print(json.dumps({"dry_run": True, "prepared": str(prepared), **{k: manifest[k] for k in ("exam_id", "items", "points", "unique_image_files")}}))
        return 0
    raw_paths = []
    for chunk in chunks:
        status = infer(*chunk, dry_run=False)
        if status not in (0, 1) or not chunk[1].is_file():
            raise PackageError(f"infer.py exited {status} for {chunk[0].name}; raw records kept in {workdir}")
        raw_paths.append(chunk[1])
    report = finalize(package, raw_paths, workdir / "answers.json", workdir / "failures.json",
                      prepared.with_name(prepared.name + ".manifest.json"))
    print(json.dumps({k: v for k, v in report.items() if k != "failures"} | {"failures": len(report["failures"])}, ensure_ascii=False))
    return 1 if report["failures"] else 0


# ---------------------------------------------------------------- synthetic fixture outputs

SYNTHETIC_TEXT = "SYNTETYCZNA ODPOWIEDŹ TESTOWA (nie jest odpowiedzią modelu) — zażółć gęślą jaźń."


def synthetic_record(item_id: str, content: str | None, finish_reason: str = "stop", error: dict | None = None) -> dict:
    raw = None if content is None else {
        "id": "synthetic", "model": "synthetic-fixture", "object": "chat.completion",
        "choices": [{"index": 0, "finish_reason": finish_reason, "message": {"role": "assistant", "content": content}}]}
    return {"id": item_id, "backend": {"name": "synthetic-fixture", "base_url": "none", "model": "synthetic-fixture",
            "model_revision": None, "response_model": None, "response_id": None, "system_fingerprint": None},
            "raw_response": raw, "usage": None, "latency_seconds": 0.0, "error": error}


def synthetic_outputs(package: dict, output: Path, failures: bool) -> int:
    """Invented answers in infer.py output format. The last text item gets a >300-word invented essay."""
    output = output.resolve()
    if output.exists():
        raise PackageError(f"Output must be a new path: {output}")
    ids = [entry["id"] for entry in package["template"]["answers"]]
    essay_words = " ".join(f"słowo{n}" for n in range(1, 351))
    rows = []
    for index, item_id in enumerate(ids):
        content = f"{SYNTHETIC_TEXT} [{item_id}]"
        if index == len(ids) - 1:
            content = f"Temat 1.\n{SYNTHETIC_TEXT}\n{essay_words}"
        rows.append(synthetic_record(item_id, content))
    if failures and len(rows) >= 5:
        rows[1] = synthetic_record(ids[1], "urwana odpowiedź", finish_reason="length",
                                   error={"type": "incomplete", "message": "No complete choice contains a nonempty final answer"})
        rows[2] = synthetic_record(ids[2], None, error={"type": "URLError", "message": "synthetic connection refused"})
        rows[3] = synthetic_record(ids[3], "<think>synthetic hidden reasoning</think>\n" + SYNTHETIC_TEXT)
        del rows[4]  # missing output -> empty answer + failure entry
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(jsonl_line(row))
    return len(rows)


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("fetch-mock", help="download + verify the public mock package (network; preparation only)")
    p.add_argument("--out", required=True, type=Path, help="ignored local folder, e.g. outputs/mock-2023")
    p.add_argument("--manifest", type=Path, help="write the aggregate acquisition manifest (no exam text)")
    p.add_argument("--allow-hash-change", action="store_true", help="accept bytes that differ from the pinned SHA-256")

    p = sub.add_parser("check", help="validate an unpacked package and print aggregate counts")
    p.add_argument("--exam-dir", required=True, type=Path, help="folder containing exam.json and images/")
    p.add_argument("--template", type=Path, help="default: <exam-dir>/answers-template.json")
    p.add_argument("--expect-items", type=int, help="optional assertion, e.g. 37 for the mock")
    p.add_argument("--expect-points", type=float)
    p.add_argument("--expect-images", type=int, help="unique image files")

    p = sub.add_parser("prepare", help="package -> infer.py JSONL {id,prompt,images} + <output>.manifest.json")
    p.add_argument("--exam-dir", required=True, type=Path)
    p.add_argument("--template", type=Path)
    p.add_argument("--output", required=True, type=Path, help="new JSONL path; image paths are written relative to it")

    p = sub.add_parser("finalize", help="infer.py output JSONL -> answers.json + local failure report")
    p.add_argument("--exam-dir", required=True, type=Path)
    p.add_argument("--template", type=Path)
    p.add_argument("--raw", required=True, type=Path, nargs="+", help="infer.py output JSONL file(s)")
    p.add_argument("--output", required=True, type=Path, help="new answers.json path")
    p.add_argument("--report", type=Path, help="failure report JSON (default: <output>.failures.json)")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest", type=Path, help="<input>.jsonl.manifest.json from prepare: ties outputs to this exam")
    group.add_argument("--no-manifest", action="store_true", help="skip the cross-check (exam_id cannot be verified)")

    p = sub.add_parser("validate", help="check answers.json against the template; exit 2 when invalid")
    p.add_argument("answers", type=Path)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--exam-dir", type=Path)
    group.add_argument("--template", type=Path)

    p = sub.add_parser("run", help="prepare -> infer.py -> finalize -> validate (loopback model endpoint only)")
    p.add_argument("--exam-dir", required=True, type=Path)
    p.add_argument("--config", required=True, type=Path, help="verified infer.py model config (local endpoint)")
    p.add_argument("--workdir", required=True, type=Path, help="new folder for input, raw records, answers.json")
    p.add_argument("--infer", type=Path, default=REPO_ROOT / "infer.py")
    p.add_argument("--dry-run", action="store_true", help="validate package + config only; no model calls")
    p.add_argument("--max-calls-total", type=int, default=200, help="refuse packages with more items (default 200)")

    p = sub.add_parser("synthetic-outputs", help="write SYNTHETIC infer.py-format records for format tests only")
    p.add_argument("--exam-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--with-failures", action="store_true", help="inject truncated/error/think/missing cases (needs >=5 ids)")

    args = parser.parse_args(argv)
    try:
        if args.command == "synthetic-outputs":
            count = synthetic_outputs(load_package(args.exam_dir), args.output, args.with_failures)
            print(json.dumps({"synthetic_records": count, "output": str(args.output), "note": "SYNTHETIC, not a model result"}))
            return 0
        if args.command == "fetch-mock":
            manifest = fetch_mock(args.out, args.manifest, args.allow_hash_change)
            print(json.dumps({"package_dir": manifest["local_package_dir"], **manifest["package"]}, ensure_ascii=False))
            return 0
        if args.command == "check":
            summary = load_package(args.exam_dir, args.template)["summary"]
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            for flag, key in (("expect_items", "items"), ("expect_points", "points"), ("expect_images", "unique_image_files")):
                if getattr(args, flag) is not None and getattr(args, flag) != summary[key]:
                    raise PackageError(f"{key} = {summary[key]}, expected {getattr(args, flag)}")
            return 0
        if args.command == "prepare":
            manifest = prepare(load_package(args.exam_dir, args.template), args.output)
            print(json.dumps({k: v for k, v in manifest.items() if k != "ids"}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "finalize":
            report_path = args.report or args.output.with_name(args.output.name + ".failures.json")
            report = finalize(load_package(args.exam_dir, args.template), args.raw, args.output, report_path, args.manifest)
            print(json.dumps({k: v for k, v in report.items() if k != "failures"} | {"failures": len(report["failures"]),
                              "failure_report": str(report_path)}, ensure_ascii=False))
            return 1 if report["failures"] else 0
        if args.command == "validate":
            template = load_template(args)
            problems = validate_submission_bytes(args.answers.read_bytes(), template)
            doc = None if problems else json.loads(args.answers.read_text(encoding="utf-8"))
            result = {"file": str(args.answers), "valid": not problems, "bytes": args.answers.stat().st_size,
                      "problems": problems}
            if doc:
                result |= {"exam_id": doc["exam_id"], "answers": len(doc["answers"]),
                           "empty_answers": sum(1 for a in doc["answers"] if not a["answer"])}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if not problems else 2
        if args.command == "run":
            return run_pipeline(args)
    except (PackageError, OSError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # never let a crash look like exit 1 ("valid file with blanks")
        print(f"Error: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
