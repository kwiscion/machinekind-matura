"""Blind grading packets and unblinded per-family aggregation for the #80 essay wave. No model calls.

  packet     answers from one or more wave batches -> shuffled, family-blind packet (codes E01..)
             plus a private key file mapping code -> (item, family). Graders see only the task
             text, the topic number and the essay.
  aggregate  grader JSON + key + deterministic word counts -> per-family table (DEVELOPMENT grading)

  python scripts/Pewciu6/essay_wave_grade.py packet --wave-dir W --batches b1 --source S --out W/grading/g1 --seed 1
  python scripts/Pewciu6/essay_wave_grade.py aggregate --grading W/grading/g1 [--markdown]
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import essay_report  # noqa: E402
import essay_route as er  # noqa: E402

GRADE_SCHEMA = {
    "code": "E01",
    "elements": [{"element": "aspect name", "level": "rich|satisfying|superficial|absent", "note": "..."}],
    "functional_knowledge": "full-3|full-2|full-1|none|nonfunctional",
    "A_before_deduction": "0-12 per the table",
    "factual_errors": [{"claim": "short paraphrase", "correction": "..."}],
    "A_deduction": "0/1/2/3 per error count",
    "A": "int 0-12",
    "B": "int 0-3",
    "total": "A+B",
    "comment": "one or two sentences",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def cmd_packet(args) -> int:
    wave = Path(args.wave_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    sources = {}
    for src in args.source:
        sources.update({row["id"]: row for row in er.read_jsonl(Path(src))})
    rows = []
    for batch in args.batches.split(","):
        rows += [r for r in read_jsonl(wave / "batches" / batch / "answers.jsonl")
                 if not args.families or r["family"] in args.families.split(",")]
    rng = random.Random(args.seed)
    rng.shuffle(rows)
    key, packet, missing = [], [], []
    for n, row in enumerate(rows, 1):
        code = f"E{n:02d}"
        entry = {"code": code, "item": row["item"], "family": row["family"], "batch": row["batch"],
                 "topic": row["topic"], "error_type": row["error_type"]}
        if row["error_type"] or not row["answer"]:
            missing.append(entry)
            continue
        key.append(entry)
        info = er.detect_essay(sources[row["item"]]["prompt"])
        packet.append({"code": code, "task": info["body"], "topic_written": row["topic"], "essay": row["answer"]})
    # renumber so that failed rows do not leave visible gaps that hint at structure
    for n, (k, p) in enumerate(zip(key, packet), 1):
        k["code"] = p["code"] = f"E{n:02d}"
    (out / "key.private.json").write_text(json.dumps({"key": key, "not_gradable": missing}, ensure_ascii=False,
                                                     indent=1), encoding="utf-8")
    with open(out / "packet.jsonl", "w", encoding="utf-8") as handle:
        for p in packet:
            handle.write(json.dumps(p, ensure_ascii=False) + "\n")
    (out / "grade_schema.json").write_text(json.dumps(GRADE_SCHEMA, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"gradable": len(packet), "not_gradable": len(missing), "out": str(out)}, indent=1))
    return 0


def words_of(text: str) -> int:
    return essay_report.count_words(text)


def cmd_aggregate(args) -> int:
    g = Path(args.grading)
    key = json.loads((g / "key.private.json").read_text(encoding="utf-8"))
    packet = {p["code"]: p for p in read_jsonl(g / "packet.jsonl")}
    grades = {}
    for path in sorted(g.glob("grades*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            grades[row["code"]] = row
    per_item, fam = [], {}
    for k in key["key"]:
        gr = grades.get(k["code"])
        words = words_of(packet[k["code"]]["essay"])
        rec = {"item": k["item"], "family": k["family"], "topic": k["topic"], "words": words,
               "A": gr and gr["A"], "B": gr and gr["B"], "total": gr and (gr["A"] + gr["B"]),
               "factual_errors": gr and len(gr.get("factual_errors", [])),
               "levels": gr and [e.get("level") for e in gr.get("elements", [])], "graded": gr is not None}
        per_item.append(rec)
        fam.setdefault(k["family"], []).append(rec)
    for k in key["not_gradable"]:
        rec = {"item": k["item"], "family": k["family"], "topic": k["topic"], "words": 0, "A": 0, "B": 0, "total": 0,
               "factual_errors": None, "levels": None, "graded": False, "error_type": k["error_type"]}
        per_item.append(rec)
        fam.setdefault(k["family"], []).append(rec)
    summary = {}
    for f, recs in sorted(fam.items()):
        graded = [r for r in recs if r["graded"]]
        summary[f] = {
            "n": len(recs), "graded": len(graded), "failed_or_unsent_scored_0": len(recs) - len(graded),
            "mean_total_all": round(sum(r["total"] or 0 for r in recs) / len(recs), 2),
            "mean_A": round(statistics.mean(r["A"] for r in graded), 2) if graded else None,
            "mean_B": round(statistics.mean(r["B"] for r in graded), 2) if graded else None,
            "factual_errors_total": sum(r["factual_errors"] for r in graded),
            "words_median": statistics.median(r["words"] for r in graded) if graded else None,
            "words_min": min((r["words"] for r in graded), default=None),
        }
    result = {"label": "DEVELOPMENT grading (single blind agent grader per batch; not promotion evidence)",
              "summary": summary, "per_item": sorted(per_item, key=lambda r: (r["item"], r["family"]))}
    (g / "aggregate.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.markdown:
        print("| family | n | graded | mean total /15 (fails=0) | mean A /12 | mean B /3 | factual errors | median words | min words |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for f, s in summary.items():
            print(f"| {f} | {s['n']} | {s['graded']} | {s['mean_total_all']} | {s['mean_A']} | {s['mean_B']} | "
                  f"{s['factual_errors_total']} | {s['words_median']} | {s['words_min']} |")
    else:
        print(json.dumps(summary, indent=1))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("packet")
    p.add_argument("--wave-dir", required=True)
    p.add_argument("--batches", required=True)
    p.add_argument("--families", default="")
    p.add_argument("--source", action="append", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=1)
    p.set_defaults(func=cmd_packet)
    p = sub.add_parser("aggregate")
    p.add_argument("--grading", required=True)
    p.add_argument("--markdown", action="store_true")
    p.set_defaults(func=cmd_aggregate)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
