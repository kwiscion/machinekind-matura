"""Deterministic post-hoc essay report (issue #80). No model calls.

Reads infer.py output JSONL (provider raw_response) or evaluator-format JSONL
(raw_response as text) and reports, per essay id:
  - words: whitespace tokens containing a letter or digit, excluding heading lines and
    leading labels such as "Aspekt 1 – polityczny:" / "Teza:" / "Zakończenie:"
  - underlength: words < 300 (the matura criterion-B threshold)
  - thesis, three labelled aspects, conclusion, distinct years, named-fact proxy
  - preamble: the first line is assistant chatter ("Oto…", "Jasne…", "Poniżej…")
  - solver_format_leak: short-item labels ("Rozstrzygnięcie:"/"Uzasadnienie:") inside the essay
Rows with an error are never "completed", even when they carry partial text; see report().
These are structural heuristics for comparing arms, not grades.

  python scripts/Pewciu6/essay_report.py --input run.output.jsonl [--output report.json] [--markdown]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from normalize_outputs import final_text  # noqa: E402

MIN_WORDS = 300
REPORT_REVISION = "essay-report-v2"

WORD = re.compile(r"[0-9A-Za-zÀ-ÿĄąĆćĘęŁłŃńÓóŚśŹźŻż]")
MARKDOWN_HEADING = re.compile(r"^\s*#{1,6}\s")
BOLD_LINE = re.compile(r"^\s*\*\*[^*]+\*\*\s*:?\s*$")
TOPIC_LINE = re.compile(r"^\s*(\*\*)?\s*(Temat|WYPRACOWANIE)\b", re.I)
LEADING_LABEL = re.compile(
    r"^\s*(\*\*)?\s*(Aspekt\s*\d*\s*[–—-]?[^:.\n]{0,40}|Teza|Wstęp|Wprowadzenie|Rozwinięcie|Zakończenie|Podsumowanie)\s*:\s*(\*\*)?",
    re.I,
)
ASPECT_LABEL = re.compile(r"(?m)^\s*(\*\*|#+\s*)?\s*Aspekt\s*(\d+|[IVX]+)?\b", re.I)
THESIS = re.compile(r"(?m)(^\s*(\*\*)?\s*Teza\s*:)|\b(uważam|moim zdaniem|twierdzę|stoję na stanowisku|należy uznać|teza)\b", re.I)
CONCLUSION = re.compile(r"(?m)(^\s*(\*\*)?\s*(Zakończenie|Podsumowanie)\s*:?)|\b(podsumowując|reasumując|w konkluzji|podsumowanie)\b", re.I)
YEAR = re.compile(r"(?<![\d.,])(\d{3,4})(?!\d)(?![.,]\d)")
PREAMBLE = re.compile(
    r"^\s*(oto|jasne|oczywiście|poniżej|chętnie|dobrze|z przyjemnością|przedstawiam|sure|here|certainly|okay|ok)\b"
    r"|dołączył|nie podał|brak treści|jako model|z uwagi na to, że nie",
    re.I,
)
TOPIC_DECLARATION = re.compile(r"^\s*(\*\*)?\s*(Wybieram\s+temat|Temat|WYPRACOWANIE)\b", re.I)
SOLVER_LABELS = re.compile(r"(?m)^\s*(\*\*)?\s*(Rozstrzygnięcie|Uzasadnienie)\s*:?", re.I)
SENTENCE_START = re.compile(r"(^|[.!?:]\s+|\n\s*)$")
CAPITALIZED = re.compile(r"\b([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,})\b")
STOP_CAPS = {"Aspekt", "Teza", "Temat", "Zakończenie", "Podsumowanie", "Wstęp", "Rozwinięcie", "Polska", "Polski", "Polacy"}


def is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if MARKDOWN_HEADING.match(line) or BOLD_LINE.match(line) or TOPIC_LINE.match(line):
        return True
    # A short label line without sentence punctuation, e.g. "Aspekt polityczny:".
    words = stripped.split()
    return len(words) <= 6 and stripped.endswith(":")


def body_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        if is_heading(line):
            continue
        lines.append(LEADING_LABEL.sub("", line, count=1))
    return lines


def count_words(text: str) -> int:
    return sum(1 for line in body_lines(text) for token in line.split() if WORD.search(token))


def years(text: str) -> list[int]:
    found = set()
    for match in YEAR.finditer(text):
        value = int(match.group(1))
        if 100 <= value <= 2030:
            found.add(value)
    return sorted(found)


def named_terms(text: str) -> list[str]:
    """Capitalized words not at a sentence start: a crude proper-name proxy."""
    names = set()
    for match in CAPITALIZED.finditer(text):
        before = text[: match.start()]
        if SENTENCE_START.search(before) or match.group(1) in STOP_CAPS:
            continue
        names.add(match.group(1))
    return sorted(names)


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def analyse(text: str) -> dict:
    words = count_words(text)
    aspect_labels = ASPECT_LABEL.findall(text)
    length = len(text)
    head = first_line(text)
    return {
        "words": words,
        "underlength": words < MIN_WORDS,
        "thesis_present": bool(THESIS.search(text[: max(1, length // 3)])),
        "aspects_labelled": len(aspect_labels),
        "three_aspects": len(aspect_labels) >= 3,
        "conclusion_present": bool(CONCLUSION.search(text[length * 2 // 3:])),
        "distinct_years": len(years(text)),
        "named_terms": len(named_terms(text)),
        "preamble": bool(PREAMBLE.match(head)),
        "topic_line": bool(TOPIC_DECLARATION.match(head)),
        "solver_format_leak": bool(SOLVER_LABELS.search(text)),
    }


def row_text(row: dict) -> tuple[str, object]:
    raw = row.get("raw_response")
    text = raw if isinstance(raw, str) else final_text(raw)
    return text, row.get("error")


def report(rows: list[dict]) -> dict:
    """Only completed answers (text and no error) enter structural and length statistics.

    An errored row that still carries text (e.g. a truncated 301-word response) is a
    partial: it counts in empty_or_error and partial_with_error, its diagnostics are kept
    under partial_diagnostics, and it never enters min/max words or structural counts.
    """
    items = []
    for row in rows:
        text, error = row_text(row)
        item = {"id": row["id"], "error": error if error else None}
        if text.strip() and not error:
            item.update(analyse(text), completed=True)
        elif text.strip():
            item.update(words=0, underlength=True, completed=False, partial=True, partial_diagnostics=analyse(text))
        else:
            item.update(words=0, underlength=True, completed=False, empty=True)
        items.append(item)
    ok = [item for item in items if item["completed"]]
    summary = {
        "items": len(items),
        "completed": len(ok),
        "empty_or_error": len(items) - len(ok),
        "partial_with_error": sum(item.get("partial", False) for item in items),
        "underlength": sum(item["underlength"] for item in items),
        "preamble": sum(item.get("preamble", False) for item in ok),
        "solver_format_leak": sum(item.get("solver_format_leak", False) for item in ok),
        "three_aspects": sum(item.get("three_aspects", False) for item in ok),
        "thesis_present": sum(item.get("thesis_present", False) for item in ok),
        "conclusion_present": sum(item.get("conclusion_present", False) for item in ok),
        "min_words": min((item["words"] for item in ok), default=0),
        "max_words": max((item["words"] for item in ok), default=0),
    }
    return {"report_revision": REPORT_REVISION, "min_words": MIN_WORDS, "summary": summary, "items": items}


def markdown(result: dict) -> str:
    cols = ["id", "completed", "words", "underlength", "thesis_present", "aspects_labelled", "conclusion_present",
            "distinct_years", "named_terms", "preamble", "solver_format_leak"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for item in result["items"]:
        lines.append("| " + " | ".join(str(item.get(col, "")) for col in cols) + " |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, type=Path, help="infer.py or evaluator-format output JSONL")
    parser.add_argument("--output", type=Path, help="write the JSON report to a new file")
    parser.add_argument("--markdown", action="store_true", help="print a Markdown table instead of JSON")
    args = parser.parse_args(argv)
    try:
        rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not rows:
            raise ValueError("Input has no rows")
        result = report(rows)
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(text)
        print(markdown(result) if args.markdown else text, end="")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
