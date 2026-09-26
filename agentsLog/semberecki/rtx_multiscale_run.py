#!/usr/bin/env python3
"""Frozen RTX multiscale/crops diagnostic runner (claim #95, Piotr).

Frozen envelope (launch record 2026-09-26-rtx-multiscale-diagnostic-launch.md):
- six diagnostic items × three passes (control/observation/final) =
  max 18 sequential calls, 18,432 max REQUESTED output tokens, $0, no retry
- explicit temperature 0.2; 1024 output cap per pass; original inputs unchanged
- 45-minute dispatch deadline from actual start, checked before each dispatch
- stop on the FIRST declared failure (corrected wrapper guards, PR #120):
  any result error, served digest/context mismatch or missing context
  (fail closed), context-overflow risk
- per-result flush, real pre-request timestamps, every attempt preserved
- routing from the item's own referenced pages (question/source structure),
  never keys or validation IDs

Shared runner functions from infer.py and guard functions from the corrected
public wrapper are imported untouched. No exam material is embedded here;
inputs/outputs stay under the gitignored owner-private dir.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    """Walk up to the .git marker (mirrors the corrected wrapper; avoids parents[N] traps)."""
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    raise RuntimeError("repo root not found")


REPO = _find_repo_root(Path(__file__).resolve().parent)
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "agentsLog/semberecki"))
import infer  # noqa: E402
import rtx_transfer_run as w  # noqa: E402  (corrected guards: find_repo_root, assert_served_identity)

INPUT = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/runner_input.v2.jsonl"
INPUT_EXPECTED_SHA = "6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4"
CONFIG = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/multiscale-diagnostic.config.json"
PAGES110 = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/pages"
PAGES220 = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/hires"
OUTPUT = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/multiscale-results.jsonl"
MANIFEST = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/multiscale-manifest.json"

# Frozen item list (launch record): (id, classification, baseline points, routed pages)
ITEMS = [
    ("val2024-hist-z5.1", "failed_source_interpretation", 0, ["page-08"]),
    ("val2024-hist-z14.1", "failed_source_interpretation", 0, ["page-16", "page-17"]),
    ("val2024-hist-z25", "failed_source_interpretation", 0, ["page-28"]),
    ("val2024-hist-z2", "control_source_dependent", 1, ["page-05"]),
    ("val2024-hist-z4", "control_source_dependent", 1, ["page-07"]),
    ("val2024-hist-z13", "control_source_dependent", 1, ["page-16"]),
]
MAX_CALLS = 18
MAX_TOTAL_REQUESTED_OUTPUT_TOKENS = 18 * 1024
OUTPUT_BUDGET_PER_CALL = 1024
DISPATCH_SECONDS = 2700  # 45 minutes
CONTEXT_LIMIT = 32768

OBSERVATION_INSTRUCTION = (
    "Opisz dokładnie zamieszczone wyżej źródło(-a) graficzne w wyższej "
    "rozdzielczości. Wymień widoczne elementy graficzne: tytuły i napisy, "
    "postacie i ich atrybuty, symbole, daty, miejsca, znaki kartograficzne "
    "lub elementy ryciny. Nie odpowiadaj na żadne pytanie — opisz tylko to, "
    "co widać na źródle."
)


def image_part(path: Path) -> dict:
    return {"type": "image_url", "image_url": {"url": infer.image_data_url(path)}}


def build_cases() -> list[dict]:
    """Build the frozen three-pass case sequence."""
    # load once via infer (validated loader), then filter
    loaded = {c["id"]: c for c in infer.load_cases(INPUT, 40)}  # loader cap >= file rows; dispatch cap enforced below
    seq = []
    for item_id, classification, baseline, pages in ITEMS:
        orig = loaded[item_id]
        orig_content = list(orig["content"]) if isinstance(orig["content"], list) else [
            {"type": "text", "text": orig["content"]}]
        hires_parts = []
        for p in pages:
            hires_parts.append(image_part(PAGES220 / f"{p}.png"))
        obs_content = [{"type": "text", "text": OBSERVATION_INSTRUCTION}] + hires_parts
        seq.append({"id": item_id, "pass": "control", "classification": classification,
                    "baseline_points": baseline, "routed_pages": pages,
                    "content": orig_content})
        seq.append({"id": item_id, "pass": "observation", "classification": classification,
                    "baseline_points": baseline, "routed_pages": pages,
                    "content": obs_content})
        final_content = (orig_content
                         + [{"type": "text",
                             "text": "Obserwacja źródła w wyższej rozdzielczości (220 DPI): "
                                     "(załączona poniżej jako dodatkowe źródło)"}]
                         + hires_parts)
        seq.append({"id": item_id, "pass": "final", "classification": classification,
                    "baseline_points": baseline, "routed_pages": pages,
                    "content": final_content})
    return seq


def main() -> int:
    actual_input_sha = w.sha256_file(INPUT)
    if actual_input_sha != INPUT_EXPECTED_SHA:
        print(f"FATAL: input SHA mismatch: {actual_input_sha}", file=sys.stderr)
        return 2
    config = infer.load_config(CONFIG, allow_remote=False)
    if config.get("temperature") != 0.2:
        print("FATAL: explicit temperature 0.2 required", file=sys.stderr)
        return 2
    seq = build_cases()
    if len(seq) > MAX_CALLS:
        print(f"FATAL: {len(seq)} passes exceeds max {MAX_CALLS} calls", file=sys.stderr)
        return 2

    start_utc = datetime.now(timezone.utc)
    dispatch_deadline_utc = start_utc.timestamp() + DISPATCH_SECONDS
    print(f"start_utc={start_utc.isoformat()} dispatch_deadline_utc="
          f"{datetime.fromtimestamp(dispatch_deadline_utc, timezone.utc).isoformat()} "
          f"passes={len(seq)}", flush=True)

    if OUTPUT.exists():
        print(f"FATAL: output exists (no overwrite): {OUTPUT}", file=sys.stderr)
        return 2

    results_meta = []
    unsent: list[str] = []
    stop_reason = None
    total_requested = 0
    served = None
    served_assertion = None
    dispatched = 0

    with OUTPUT.open("x", encoding="utf-8") as out:
        for idx, case in enumerate(seq):
            if time.time() >= dispatch_deadline_utc:
                stop_reason = "dispatch_deadline"
                unsent = [f"{c['id']}:{c['pass']}" for c in seq[idx:]]
                break
            if total_requested + OUTPUT_BUDGET_PER_CALL > MAX_TOTAL_REQUESTED_OUTPUT_TOKENS:
                stop_reason = "output_token_budget"
                unsent = [f"{c['id']}:{c['pass']}" for c in seq[idx:]]
                break

            request_started_utc = datetime.now(timezone.utc)  # real pre-request stamp
            result = infer.run_case(case, config)
            response_completed_utc = datetime.now(timezone.utc)
            dispatched += 1
            total_requested += OUTPUT_BUDGET_PER_CALL

            usage = result.get("usage") or {}
            pt = usage.get("prompt_tokens")
            err = result.get("error")

            out.write(json.dumps({"id": case["id"], "pass": case["pass"],
                                  "routed_pages": case["routed_pages"],
                                  "result": result}, ensure_ascii=False) + "\n")
            out.flush()

            results_meta.append({
                "id": case["id"], "pass": case["pass"],
                "error_type": err["type"] if err else None,
                "latency_seconds": result.get("latency_seconds"),
                "prompt_tokens": pt,
                "completion_tokens": usage.get("completion_tokens"),
                "request_started_utc": request_started_utc.isoformat(),
                "response_completed_utc": response_completed_utc.isoformat(),
            })
            print(f"[{dispatched}/{len(seq)}] {case['id']}:{case['pass']} "
                  f"{'OK' if not err else 'ERR:' + err['type']} "
                  f"{result.get('latency_seconds')}s", flush=True)

            if err is not None:  # FIRST declared failure stops
                stop_reason = f"declared_failure:{w.classify_result_error(err)}"
                unsent = [f"{c['id']}:{c['pass']}" for c in seq[idx + 1:]]
                break
            if served is None:
                try:
                    served = w.api_ps()
                    served["queried_at"] = datetime.now(timezone.utc).isoformat()
                    served_assertion = w.assert_served_identity(served)
                except w.GuardFailure as exc:
                    stop_reason = str(exc).split(":")[0]
                    unsent = [f"{c['id']}:{c['pass']}" for c in seq[idx + 1:]]
                    print(f"GUARD STOP: {exc}", file=sys.stderr, flush=True)
                    break
            if pt is not None and pt > CONTEXT_LIMIT - OUTPUT_BUDGET_PER_CALL:
                stop_reason = "context_overflow_risk"
                unsent = [f"{c['id']}:{c['pass']}" for c in seq[idx + 1:]]
                break

    end_utc = datetime.now(timezone.utc)
    manifest = {
        "run": "rtx-multiscale-crops-diagnostic (claim #95)",
        "owner": "semberecki",
        "session_id": "01a0de3f-e03d-75ba-8a97-eb400acb36a2",
        "launch_record": "agentsLog/semberecki/2026-09-26-rtx-multiscale-diagnostic-launch.md",
        "start_utc": start_utc.isoformat(),
        "end_utc": end_utc.isoformat(),
        "dispatch_deadline_utc": datetime.fromtimestamp(dispatch_deadline_utc, timezone.utc).isoformat(),
        "stop_reason": stop_reason or "all_passes_dispatched",
        "dispatched": dispatched,
        "unsent_passes": unsent,
        "input_sha256": actual_input_sha,
        "config_sha256": w.sha256_file(CONFIG),
        "question_pdf_sha256": "ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21",
        "renderer": "pdftoppm (Poppler 24.02.0); 110 DPI originals + 220 DPI additions",
        "model_tag": config["model"],
        "model_blob_sha256": "1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606",
        "projector_blob_sha256": "675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842",
        "ollama_version": "0.34.4",
        "expected_context": CONTEXT_LIMIT,
        "explicit_temperature": config.get("temperature"),
        "served_api_ps": served,
        "served_assertion": served_assertion,
        "items": [{"id": i[0], "classification": i[1], "baseline_points": i[2],
                   "routed_pages": i[3]} for i in ITEMS],
        "limits": {
            "max_calls": MAX_CALLS,
            "max_total_requested_output_tokens": MAX_TOTAL_REQUESTED_OUTPUT_TOKENS,
            "dispatch_seconds": DISPATCH_SECONDS,
            "in_flight_timeout_seconds": config["timeout_seconds"],
            "output_budget_per_call": OUTPUT_BUDGET_PER_CALL,
            "no_retry": True,
            "no_warmup": True,
            "paid_spend": "$0",
        },
        "provenance": {
            "enforced_runtime_checks": [
                "input_sha256", "served_digest", "served_context_length",
                "unambiguous_loaded_model", "fail_closed_missing_context",
                "stop_on_first_declared_failure", "pre_request_timestamp",
                "dispatch_deadline", "output_token_budget", "context_overflow",
            ],
            "manual_retained_evidence": [
                "model_blob_sha256 (operator sha256sum before start)",
                "projector_blob_sha256 (operator sha256sum before start)",
                "question_pdf_sha256 (operator, re-verified before render)",
                "page_hashes (operator, orig110 + hires220, launch record)",
                "renderer (operator, pdftoppm/Poppler 24.02.0)",
                "ollama_version (operator, serve.log)",
            ],
        },
        "boundaries": "wrapper is read/write on owner-private paths only; no purchases; no exam material embedded in public paths",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("dispatched", "unsent_passes", "stop_reason", "end_utc")}, ensure_ascii=False), flush=True)
    errors = sum(1 for m in results_meta if m["error_type"])
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
