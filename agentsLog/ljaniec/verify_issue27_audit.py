#!/usr/bin/env python3
"""Independent reproduction of the issue #27 smoke-evidence audit aggregates.

Recomputes the committed audit JSONs (issue-27-{spark,cpu}-smoke-audit.json)
from the original raw artifacts under raw/. Numeric values use absolute
tolerance 1e-6; this does not establish byte-for-byte identity. No inference,
no downloads, no model calls — reads local files only.

Usage: python3 verify_issue27_audit.py   (from agentsLog/ljaniec/)
"""
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_records(path, inputs=False):
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            raise ValueError(f"Invalid JSON at line {number}") from None
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip():
            raise ValueError(f"Invalid record/id at line {number}")
        if inputs:
            if not isinstance(row.get("prompt"), str):
                raise ValueError(f"Invalid input prompt at line {number}")
        else:
            if row.get("error") is not None and not isinstance(row["error"], str):
                raise ValueError(f"Invalid error at line {number}")
            if "raw_response" not in row and row.get("error") is None:
                raise ValueError(f"Missing response/error at line {number}")
            if row.get("raw_response") is not None and not isinstance(row["raw_response"], str):
                raise ValueError(f"Invalid response at line {number}")
            if row.get("usage") is not None and not isinstance(row["usage"], dict):
                raise ValueError(f"Invalid usage at line {number}")
            fields = [(key, row.get(key)) for key in ("latency_s", "wall_s", "completion_tokens")]
            fields.append(("completion_tokens", (row.get("usage") or {}).get("completion_tokens")))
            for key, value in fields:
                if value is not None and (type(value) not in (int, float) or not math.isfinite(value)
                        or value < 0 or (key == "completion_tokens" and type(value) is not int)):
                    raise ValueError(f"Invalid numeric field at line {number}")
        rows.append(row)
    if not rows:
        raise ValueError("No records")
    return rows


def audit(raw_path, input_path):
    recs = read_records(raw_path)
    input_recs = read_records(input_path, inputs=True)
    expected = {r["id"]: r["prompt"] for r in input_recs}
    if len(expected) != len(input_recs):
        raise ValueError("Duplicate input IDs")
    ids = [r["id"] for r in recs]
    empty = [not isinstance(r.get("raw_response"), str) or not r["raw_response"].strip() for r in recs]
    errors = [r.get("error") is not None for r in recs]
    lats = [r.get("latency_s") if r.get("latency_s") is not None else r.get("wall_s") for r in recs]
    lats = [v for v in lats if v is not None]
    toks = [r.get("completion_tokens") if r.get("completion_tokens") is not None
            else (r.get("usage") or {}).get("completion_tokens") for r in recs]
    toks = [v for v in toks if v is not None]
    return {
        "artifact_sha256": sha256(raw_path), "record_count": len(recs),
        "unique_id_count": len(set(ids)), "duplicate_id_record_count": len(ids)-len(set(ids)),
        "response_empty_count": sum(empty), "response_nonempty_count": len(recs)-sum(empty),
        "reported_error_count": sum(errors),
        "empty_response_without_reported_error_count": sum(e and not err for e, err in zip(empty, errors)),
        "reported_error_or_empty_response_count": sum(e or err for e, err in zip(empty, errors)),
        "latency": {"denominator_records_with_latency": len(lats),
                    "sum_seconds": sum(lats) if lats else None,
                    "mean_seconds": statistics.mean(lats) if lats else None,
                    "median_seconds": statistics.median(lats) if lats else None},
        "completion_tokens": {"denominator_records_with_token_count": len(toks),
                              "sum": sum(toks) if toks else None, "configured_budget": 200,
                              "records_at_or_above_budget": sum(t >= 200 for t in toks),
                              "interpretation": "Possible truncation only; token counts do not prove finish reason."},
        "model_revision_present_count": sum(isinstance(r.get("model_revision"), str) and bool(r["model_revision"].strip()) for r in recs),
        "finish_reason_present_count": sum(isinstance(r.get("finish_reason"), str) and bool(r["finish_reason"].strip()) for r in recs),
        "input_kind": "synthetic-smoke",
        "input_comparison": {"input_sha256": sha256(input_path), "input_record_count": len(input_recs),
                             "exact_id_set_match": set(ids) == set(expected),
                             "all_record_prompts_match_by_id": all(r["id"] in expected and r.get("prompt") == expected[r["id"]] for r in recs),
                             "exact_id_sequence_match": ids == [r["id"] for r in input_recs]},
    }


def values_match(left, right):
    """Require exact structure/types and finite numbers; tolerate floats only."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(values_match(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(values_match(a, b) for a, b in zip(left, right))
    if isinstance(left, float):
        return math.isfinite(left) and math.isfinite(right) and abs(left-right) <= 1e-6
    return left == right


def compare(name, computed, committed_path):
    committed = json.loads(committed_path.read_text())
    ok = values_match(computed, committed)
    print(f"== {name}: {'MATCH (values reproduced; absolute float tolerance 1e-6)' if ok else 'MISMATCH'}")
    return ok


def main():
    ok = True
    ok &= compare(
        "spark audit",
        audit(BASE / "raw" / "spark-smoke.jsonl", BASE / "baselines" / "dev-smoke-prompts.jsonl"),
        BASE / "issue-27-spark-smoke-audit.json",
    )
    ok &= compare(
        "cpu audit",
        audit(BASE / "raw" / "qwen3-8b-q4_k_m-smoke.jsonl", BASE / "baselines" / "dev-smoke-prompts.jsonl"),
        BASE / "issue-27-cpu-smoke-audit.json",
    )
    print("VERDICT:", "AGGREGATES REPRODUCED — independent verification PASS" if ok else "VERIFICATION FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
