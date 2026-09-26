#!/usr/bin/env python3
"""Owned wrapper for the frozen RTX runtime-transfer control run (claim #33, Piotr).

Enforces the lead's frozen envelope (issue #33 comment 2026-09-26T15:44:13Z):
- max 40 sequential calls, 40,960 max REQUESTED output tokens, $0, no retry/warmup
- dispatch deadline = min(start_utc + 2400 s, 18:40 Europe/Warsaw), checked
  before each dispatch; the in-flight request may finish (run_case timeout 420 s)
- each result flushed immediately; every attempt preserved; unsent IDs recorded
- stop after 2 consecutive infrastructure/transport errors
- stop on context-overflow risk (usage prompt_tokens > 32768 - 1024)
- context 32768 preserved throughout (no per-call context overrides)

Shared runner functions from infer.py are imported untouched. No exam material
is embedded here; inputs/outputs stay under the gitignored owner-private dir.
"""

import json
import sys
import time
import urllib.request
from datetime import datetime, time as dtime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
import infer  # noqa: E402  (shared runner; untouched)

INPUT = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/runner_input.v2.jsonl"
CONFIG = REPO / "agentsLog/kwiscion/gemma4-12b-val40-1024.config.json"
OUTPUT = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/rtx-transfer-results.jsonl"
MANIFEST = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/rtx-transfer-manifest.json"
INPUT_EXPECTED_SHA = "6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4"

MAX_CALLS = 40
MAX_TOTAL_REQUESTED_OUTPUT_TOKENS = 40960
OUTPUT_BUDGET_PER_CALL = 1024
DISPATCH_SECONDS = 2400
WARSAW_STOP = dtime(18, 40)
CONTEXT_LIMIT = 32768
INFRA_TYPES = {"URLError", "TimeoutError", "OSError", "JSONDecodeError", "ConnectionError", "ValueError"}
MAX_CONSECUTIVE_INFRA = 2


def sha256_file(path: Path) -> str:
    return __import__("hashlib").sha256(path.read_bytes()).hexdigest()


def api_ps() -> dict:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def main() -> int:
    import hashlib

    actual_input_sha = sha256_file(INPUT)
    if actual_input_sha != INPUT_EXPECTED_SHA:
        print(f"FATAL: input SHA mismatch: {actual_input_sha}", file=sys.stderr)
        return 2

    config = infer.load_config(CONFIG, allow_remote=False)
    cases = infer.load_cases(INPUT, MAX_CALLS)
    if len(cases) > MAX_CALLS:
        print(f"FATAL: {len(cases)} cases exceeds max {MAX_CALLS}", file=sys.stderr)
        return 2

    start_utc = datetime.now(timezone.utc)
    warsaw = ZoneInfo("Europe/Warsaw")
    warsaw_stop_utc = datetime.combine(
        start_utc.astimezone(warsaw).date(), WARSAW_STOP, tzinfo=warsaw
    ).astimezone(timezone.utc)
    dispatch_deadline_utc = min(start_utc.timestamp() + DISPATCH_SECONDS, warsaw_stop_utc.timestamp())
    print(f"start_utc={start_utc.isoformat()} dispatch_deadline_utc="
          f"{datetime.fromtimestamp(dispatch_deadline_utc, timezone.utc).isoformat()} "
          f"cases={len(cases)}", flush=True)

    if OUTPUT.exists():
        print(f"FATAL: output exists (no overwrite): {OUTPUT}", file=sys.stderr)
        return 2

    results_meta = []
    unsent: list[str] = []
    stop_reason = None
    consecutive_infra = 0
    total_requested = 0
    served = None
    dispatched = 0

    with OUTPUT.open("x", encoding="utf-8") as out:
        for idx, case in enumerate(cases):
            if time.time() >= dispatch_deadline_utc:
                stop_reason = "dispatch_deadline"
                unsent = [c["id"] for c in cases[idx:]]
                break
            if total_requested + OUTPUT_BUDGET_PER_CALL > MAX_TOTAL_REQUESTED_OUTPUT_TOKENS:
                stop_reason = "output_token_budget"
                unsent = [c["id"] for c in cases[idx:]]
                break
            result = infer.run_case(case, config)
            dispatched += 1
            total_requested += OUTPUT_BUDGET_PER_CALL

            usage = result.get("usage") or {}
            pt = usage.get("prompt_tokens")
            if result.get("error") is None and served is None:
                served = api_ps()
                served["queried_at"] = datetime.now(timezone.utc).isoformat()

            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            out.flush()

            err = result.get("error")
            results_meta.append({
                "id": result["id"],
                "error_type": err["type"] if err else None,
                "finish": "ok" if not err else err["type"],
                "latency_seconds": result.get("latency_seconds"),
                "prompt_tokens": pt,
                "completion_tokens": (usage or {}).get("completion_tokens"),
                "dispatch_utc": datetime.now(timezone.utc).isoformat(),
            })
            print(f"[{dispatched}/{len(cases)}] {result['id']} "
                  f"{'OK' if not err else 'ERR:' + err['type']} "
                  f"{result.get('latency_seconds')}s", flush=True)

            if pt is not None and pt > CONTEXT_LIMIT - OUTPUT_BUDGET_PER_CALL:
                stop_reason = "context_overflow_risk"
                unsent = [c["id"] for c in cases[idx + 1:]]
                break

            infra = bool(err) and (
                err["type"] in INFRA_TYPES
                or (err["type"] == "http" and isinstance(err.get("status"), int) and err["status"] >= 500)
            )
            if infra:
                consecutive_infra += 1
                if consecutive_infra >= MAX_CONSECUTIVE_INFRA:
                    stop_reason = "consecutive_infrastructure_errors"
                    unsent = [c["id"] for c in cases[idx + 1:]]
                    break
            else:
                consecutive_infra = 0

    end_utc = datetime.now(timezone.utc)
    manifest = {
        "run": "rtx-runtime-transfer-control (claim #33)",
        "owner": "semberecki",
        "session_id": "01a0de3f-e03d-75ba-8a97-eb400acb36a2",
        "lead_declaration": "issue #33 comment 2026-09-26T15:44:13Z",
        "start_utc": start_utc.isoformat(),
        "end_utc": end_utc.isoformat(),
        "dispatch_deadline_utc": datetime.fromtimestamp(dispatch_deadline_utc, timezone.utc).isoformat(),
        "stop_reason": stop_reason or "all_cases_dispatched",
        "dispatched": dispatched,
        "unsent_ids": unsent,
        "input_path": str(INPUT.relative_to(REPO)),
        "input_sha256": actual_input_sha,
        "config_path": "agentsLog/kwiscion/gemma4-12b-val40-1024.config.json",
        "config_sha256": sha256_file(CONFIG),
        "question_pdf_sha256": "ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21",
        "renderer": "pdftoppm (Poppler 24.02.0), 110 DPI",
        "model_tag": config["model"],
        "model_blob_sha256": "1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606",
        "projector_blob_sha256": "675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842",
        "ollama_version": "0.34.4",
        "context_preserved": CONTEXT_LIMIT,
        "served_api_ps": served,
        "limits": {
            "max_calls": MAX_CALLS,
            "max_total_requested_output_tokens": MAX_TOTAL_REQUESTED_OUTPUT_TOKENS,
            "dispatch_seconds": DISPATCH_SECONDS,
            "warsaw_stop": "18:40 Europe/Warsaw",
            "in_flight_timeout_seconds": config["timeout_seconds"],
            "no_retry": True,
            "no_warmup": True,
            "paid_spend": "$0",
        },
        "results_meta": results_meta,
        "boundaries": "wrapper is read/write on owner-private paths only; no purchases; no exam material embedded",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("dispatched", "unsent_ids", "stop_reason", "end_utc")}, ensure_ascii=False), flush=True)
    errors = sum(1 for m in results_meta if m["error_type"])
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
