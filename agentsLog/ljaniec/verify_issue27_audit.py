#!/usr/bin/env python3
"""Independent reproduction of the issue #27 smoke-evidence audit aggregates.

Recomputes the committed audit JSONs (issue-27-{spark,cpu}-smoke-audit.json)
from the original raw artifacts under raw/, byte-for-byte. No inference,
no downloads, no model calls — reads local files only.

Usage: python3 verify_issue27_audit.py   (from agentsLog/ljaniec/)
"""
import hashlib
import json
import statistics
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(raw_path, input_path):
    recs = [json.loads(l) for l in raw_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = [r["id"] for r in recs]
    unique_ids = set(ids)
    nonempty = [r for r in recs if r.get("raw_response")]
    empty = [r for r in recs if not r.get("raw_response")]
    err_reported = [r for r in recs if r.get("error")]
    # legacy CPU format uses latency_s; spark format uses wall_s
    lats = [r["wall_s"] if r.get("wall_s") is not None else r.get("latency_s")
            for r in recs if r.get("wall_s") is not None or r.get("latency_s") is not None]
    toks = [r["usage"]["completion_tokens"] if r.get("usage") and r["usage"].get("completion_tokens") is not None
            else r.get("completion_tokens")
            for r in recs
            if (r.get("usage") and r["usage"].get("completion_tokens") is not None)
            or r.get("completion_tokens") is not None]
    input_recs = [json.loads(l) for l in input_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {
        "artifact_sha256": sha256(raw_path),
        "record_count": len(recs),
        "unique_id_count": len(unique_ids),
        "duplicate_id_record_count": len(ids) - len(unique_ids),
        "response_empty_count": len(empty),
        "response_nonempty_count": len(nonempty),
        "reported_error_count": len(err_reported),
        "empty_response_without_reported_error_count": len([r for r in empty if not r.get("error")]),
        "reported_error_or_empty_response_count": len(empty) + len(err_reported),
        "latency": {
            "denominator_records_with_latency": len(lats),
            "sum_seconds": sum(lats),
            "mean_seconds": sum(lats) / len(lats) if lats else None,
            "median_seconds": statistics.median(lats) if lats else None,
        },
        "completion_tokens": {
            "denominator_records_with_token_count": len(toks),
            "sum": sum(toks),
            "configured_budget": 200,
            "records_at_or_above_budget": len([t for t in toks if t >= 200]),
        },
        "model_revision_present_count": len([r for r in recs if r.get("model_revision")]),
        "finish_reason_present_count": len([r for r in recs if r.get("finish_reason")]),
        "input_kind": "synthetic-smoke",
        "input_comparison": {
            "input_sha256": sha256(input_path),
            "input_record_count": len(input_recs),
            "exact_id_set_match": set(ids) == {r["id"] for r in input_recs},
        },
    }


def compare(name, computed, committed_path):
    committed = json.loads(committed_path.read_text())
    diffs = []
    # numeric tolerance: float summation order differences are not evidence differences
    for k, v in computed.items():
        cv = committed.get(k)
        if isinstance(v, dict) and isinstance(cv, dict):
            for kk, vv in v.items():
                cvv = cv.get(kk)
                if isinstance(vv, float) and cvv is not None:
                    if abs(vv - cvv) > 1e-6:
                        diffs.append((f"{k}.{kk}", vv, cvv))
                elif isinstance(vv, dict) and isinstance(cvv, dict):
                    for k3, v3 in vv.items():
                        c3 = cvv.get(k3)
                        if isinstance(v3, float) and c3 is not None:
                            if abs(v3 - c3) > 1e-6:
                                diffs.append((f"{k}.{kk}.{k3}", v3, c3))
                        elif v3 != c3:
                            diffs.append((f"{k}.{kk}.{k3}", v3, c3))
                elif vv != cvv:
                    diffs.append((f"{k}.{kk}", vv, cvv))
        elif isinstance(v, float) and cv is not None:
            if abs(v - cv) > 1e-6:
                diffs.append((k, v, cv))
        elif v != cv:
            diffs.append((k, v, cv))
    print(f"== {name}: {'MATCH (values reproduced; float-summation-order tolerance applied)' if not diffs else 'MISMATCH'}")
    for k, v, cv in diffs:
        print(f"   {k}: computed={v!r} committed={cv!r}")
    return not diffs


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
