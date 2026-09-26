"""Deterministic gate for examples.jsonl: schema, verbatim evidence, year grounding, duplicates.

Usage: python scripts/przemeknowak781/validate.py [EXAMPLES ...] [--sources PATH] [--report PATH]
Needs the cache produced by fetch_sources.py. Exit code 1 if any example fails.
"""
import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REQUIRED = ["id", "subject", "split", "task_type", "source_ids", "source_group_id", "prompt",
            "answer", "evidence", "provenance", "rights_status"]
SPLITS = {"TRAIN", "DEV", "VALIDATION", "SEALED_TEST"}
PROVENANCE = {"human", "synthetic", "exam"}
RIGHTS = {"clear", "restricted", "unknown"}
TASK_TYPES = {"short_answer", "chronology", "source_analysis", "essay_plan", "vision_ocr"}
YEAR = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-2][0-9])(?!\d)")
DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−"), "-")
QUOTES = dict.fromkeys(map(ord, "„”“«»’‘"), '"')
NEAR_DUP_RATIO = 0.9


def norm(text):
    text = unicodedata.normalize("NFKC", text).translate(DASHES).translate(QUOTES)
    return " ".join(text.lower().split())


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def check(ex, sources, texts):
    errors = []
    for key in REQUIRED:
        if key not in ex or ex[key] in ("", None, []):
            errors.append(f"missing:{key}")
    if errors:
        return errors
    if ex["split"] not in SPLITS:
        errors.append(f"bad_split:{ex['split']}")
    if ex["split"] != "TRAIN":
        errors.append("non_train_split_in_training_file")
    if ex["provenance"] not in PROVENANCE:
        errors.append(f"bad_provenance:{ex['provenance']}")
    if ex["rights_status"] not in RIGHTS:
        errors.append(f"bad_rights:{ex['rights_status']}")
    if ex["task_type"] not in TASK_TYPES:
        errors.append(f"bad_task_type:{ex['task_type']}")
    if ex["provenance"] == "synthetic" and not ex.get("generator"):
        errors.append("synthetic_without_generator")
    for sid in ex["source_ids"]:
        if sid not in sources:
            errors.append(f"unknown_source:{sid}")
    if len(ex["source_ids"]) == 1 and sources.get(ex["source_ids"][0], {}).get("source_group_id") not in (None, ex["source_group_id"]):
        errors.append("source_group_mismatch")
    claims_norm = []
    for ev in ex["evidence"]:
        sid, claim = ev.get("source_id"), ev.get("claim", "")
        if sid not in ex["source_ids"]:
            errors.append(f"evidence_source_not_listed:{sid}")
        if not ev.get("locator"):
            errors.append("evidence_without_locator")
        if len(claim) > 300:
            errors.append("evidence_claim_too_long")
        text = texts.get(sid)
        if text is None:
            errors.append(f"no_cached_text:{sid}")
        elif norm(claim) not in text:
            errors.append(f"claim_not_in_source:{sid}:{claim[:60]}")
        claims_norm.append(norm(claim))
    evidence_blob = " ".join(claims_norm)
    for year in set(YEAR.findall(ex["answer"])):
        if year not in evidence_blob:
            errors.append(f"year_not_in_evidence:{year}")
    return errors


def main():
    root = Path(__file__).resolve().parents[2]
    base = root / "data/przemeknowak781"
    ap = argparse.ArgumentParser()
    ap.add_argument("examples", nargs="*", default=[base / "examples.jsonl"])
    ap.add_argument("--sources", default=base / "sources.jsonl")
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    sources = {s["source_id"]: s for s in load_jsonl(args.sources)}
    texts = {}
    for sid, s in sources.items():
        cached = Path(args.sources).parent / s.get("local_path", "")
        if cached.is_file():
            doc = json.loads(cached.read_text(encoding="utf-8"))
            texts[sid] = norm(" ".join(sec["text"] for sec in doc["sections"]))

    examples = [ex for path in args.examples for ex in load_jsonl(path)]
    results, seen_ids, by_hash = {}, Counter(), defaultdict(list)
    for ex in examples:
        errs = check(ex, sources, texts)
        seen_ids[ex.get("id")] += 1
        results[ex.get("id")] = errs
        by_hash[hashlib.sha256(norm(ex.get("prompt", "")).encode()).hexdigest()].append(ex.get("id"))
    for eid, n in seen_ids.items():
        if n > 1:
            results[eid].append("duplicate_id")
    exact_dups = [ids for ids in by_hash.values() if len(ids) > 1]
    for ids in exact_dups:
        for eid in ids[1:]:
            results[eid].append(f"exact_duplicate_prompt_of:{ids[0]}")

    near_dups = []
    prompts = [(ex["id"], norm(ex.get("prompt", ""))) for ex in examples]
    for i, (a_id, a) in enumerate(prompts):
        for b_id, b in prompts[i + 1:]:
            if a != b and difflib.SequenceMatcher(None, a, b).ratio() >= NEAR_DUP_RATIO:
                near_dups.append([a_id, b_id])

    passed = [eid for eid, errs in results.items() if not errs]
    by_era, by_task = Counter(), Counter()
    for ex in examples:
        if not results[ex["id"]]:
            by_era[ex.get("era", "unknown")] += 1
            by_task[ex.get("task_type")] += 1
    report = {
        "examples": len(examples),
        "passed_gate": len(passed),
        "failed_gate": len(examples) - len(passed),
        "passed_by_era": dict(by_era),
        "passed_by_task_type": dict(by_task),
        "exact_duplicate_groups": exact_dups,
        "near_duplicate_pairs_warning": near_dups,
        "failures": {eid: errs for eid, errs in results.items() if errs},
    }
    out = json.dumps(report, ensure_ascii=False, indent=1)
    if args.report:
        Path(args.report).write_text(out, encoding="utf-8")
    print(out if len(out) < 4000 else json.dumps({k: v for k, v in report.items() if k != "failures"}, ensure_ascii=False, indent=1))
    sys.exit(1 if report["failed_gate"] else 0)


if __name__ == "__main__":
    main()
