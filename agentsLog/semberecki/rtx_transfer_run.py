#!/usr/bin/env python3
"""Corrected reproduction wrapper for the frozen RTX runtime-transfer control.

Reproduction artifact for claim #33 / merged PR #85; corrections per the #88
acceptance findings (ljaniec audit). The historical private wrapper and its
raw results stay immutable; this file is the corrected, runnable public path.

Corrections over the historical wrapper:
- repo root resolved by walking up from __file__ to a .git/infer.py marker
  (was parents[3], which resolved above the repository)
- stops on the FIRST declared failure: any result error (infrastructure,
  provider HTTP 4xx/5xx, incomplete/other) — was 2-consecutive-infra only,
  with ordinary HTTP 4xx permitted
- after the first success, /api/ps is ASSERTED: the expected loaded model must
  be unambiguously present (arbitrary models[0] is not accepted) and its
  context_length must be a real integer equal to the expected context (32768);
  missing/null/non-integer context FAILS CLOSED — was sampled once without
  assertions; context_preserved was hardcoded
- records the real pre-request timestamp (request_started_utc) plus the
  post-response completion observation (response_completed_utc) — the old
  dispatch_utc was written after the response
- the generated manifest distinguishes enforced runtime checks from manually
  retained operator evidence (provenance kinds)

Shared runner functions from infer.py are imported untouched. No exam material
is embedded here; inputs/outputs stay under the gitignored owner-private dir.

Usage:
    python3 rtx_transfer_run.py            # full frozen run (same envelope)
    python3 rtx_transfer_run.py --check    # CPU-only preflight, no dispatch
"""

import json
import sys
import time
import urllib.request
from datetime import datetime, time as dtime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

MAX_CALLS = 40
MAX_TOTAL_REQUESTED_OUTPUT_TOKENS = 40960
OUTPUT_BUDGET_PER_CALL = 1024
DISPATCH_SECONDS = 2400
WARSAW_STOP = dtime(18, 40)
CONTEXT_LIMIT = 32768
EXPECTED_MODEL_DIGEST = "4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c"
INPUT_EXPECTED_SHA = "6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4"


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from *start* (default: this file) to the repository root.

    A directory containing a .git entry or infer.py is the repo root; raises
    RuntimeError at the filesystem root. Fixes the historical parents[3] bug.
    """
    p = (start or Path(__file__)).resolve()
    for cand in (p, *p.parents):
        if (cand / ".git").exists() or (cand / "infer.py").exists():
            return cand
    raise RuntimeError("repository root not found above " + str(p))


def classify_result_error(err: dict) -> str:
    """Classify a runner error dict: infrastructure / provider / other."""
    etype = err.get("type")
    status = err.get("status") if etype == "http" else None
    if etype in {"URLError", "TimeoutError", "OSError", "JSONDecodeError",
                 "ConnectionError", "ValueError"}:
        return "infrastructure"
    if etype == "http" and isinstance(status, int):
        return "provider_5xx" if status >= 500 else "provider_4xx"
    return "other"


def assert_served_identity(ps: dict, expected_digest: str = EXPECTED_MODEL_DIGEST,
                           expected_context: int = CONTEXT_LIMIT) -> dict:
    """Assert the served model digest and context length; return actual values.

    Raises GuardFailure on mismatch. Fails closed: a missing/null/non-integer/
    bool context_length is a guard failure, and the expected loaded model must
    be unambiguously present (arbitrary models[0] is not accepted).
    """
    models = ps.get("models") or []
    if not models:
        raise GuardFailure("served_identity_mismatch: /api/ps returned no loaded model")
    matches = [m for m in models if m.get("digest") == expected_digest]
    if len(matches) != 1:
        raise GuardFailure(
            f"served_identity_mismatch: expected loaded model unambiguous "
            f"(found {len(matches)} of {len(models)} loaded with digest {expected_digest})")
    actual_digest = matches[0].get("digest")
    actual_context = matches[0].get("context_length")
    # Fail closed: context must be a real integer (bool is excluded), never
    # missing/null/str — dispatching with an unqualified runtime is refused.
    if not isinstance(actual_context, int) or isinstance(actual_context, bool):
        raise GuardFailure(
            f"served_identity_mismatch: context_length missing or non-integer "
            f"({actual_context!r}); refusing to dispatch with unqualified runtime")
    if actual_context != expected_context:
        raise GuardFailure(
            f"served_identity_mismatch: context_length {actual_context} != expected {expected_context}")
    return {"digest": actual_digest, "context_length": actual_context,
            "context_validated": True}


class GuardFailure(RuntimeError):
    """A declared runtime/identity guard failed; the run must stop."""


REPO = find_repo_root()
sys.path.insert(0, str(REPO))
import infer  # noqa: E402  (shared runner; untouched)

INPUT = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/runner_input.v2.jsonl"
CONFIG = REPO / "agentsLog/kwiscion/gemma4-12b-val40-1024.config.json"
OUTPUT = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/rtx-transfer-results.jsonl"
MANIFEST = REPO / "agentsLog/semberecki/private/validation_2024_keyfree/rtx-transfer-manifest.json"


def sha256_file(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api_ps() -> dict:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def preflight() -> int:
    """CPU-only preflight: repo root, input SHA, config load. No dispatch."""
    actual = sha256_file(INPUT)
    if actual != INPUT_EXPECTED_SHA:
        print(f"CHECK FAIL: input SHA mismatch: {actual}", file=sys.stderr)
        return 2
    config = infer.load_config(CONFIG, allow_remote=False)
    print(json.dumps({
        "repo_root": str(REPO),
        "input_sha256_ok": True,
        "model_tag": config["model"],
        "expected_digest": EXPECTED_MODEL_DIGEST,
        "expected_context": CONTEXT_LIMIT,
        "max_calls": MAX_CALLS,
        "guards": "first-declared-failure stop; served digest+context assertion; "
                  "pre-request timestamp",
    }, ensure_ascii=False), flush=True)
    return 0


def main() -> int:
    if "--check" in sys.argv[1:]:
        return preflight()

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
    total_requested = 0
    served = None
    served_assertion = None
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

            request_started_utc = datetime.now(timezone.utc)  # real pre-request stamp
            result = infer.run_case(case, config)
            response_completed_utc = datetime.now(timezone.utc)
            dispatched += 1
            total_requested += OUTPUT_BUDGET_PER_CALL

            usage = result.get("usage") or {}
            pt = usage.get("prompt_tokens")
            err = result.get("error")

            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            out.flush()

            results_meta.append({
                "id": result["id"],
                "error_type": err["type"] if err else None,
                "finish": "ok" if not err else err["type"],
                "latency_seconds": result.get("latency_seconds"),
                "prompt_tokens": pt,
                "completion_tokens": usage.get("completion_tokens"),
                "request_started_utc": request_started_utc.isoformat(),
                "response_completed_utc": response_completed_utc.isoformat(),
            })
            print(f"[{dispatched}/{len(cases)}] {result['id']} "
                  f"{'OK' if not err else 'ERR:' + err['type']} "
                  f"{result.get('latency_seconds')}s", flush=True)

            # FIRST declared failure stops the run (infrastructure, provider
            # HTTP 4xx/5xx, incomplete, or any other runner error).
            if err is not None:
                stop_reason = f"declared_failure:{classify_result_error(err)}"
                unsent = [c["id"] for c in cases[idx + 1:]]
                break

            # After the first success, assert actual served identity/context.
            if served is None:
                try:
                    served = api_ps()
                    served["queried_at"] = datetime.now(timezone.utc).isoformat()
                    served_assertion = assert_served_identity(served)
                except GuardFailure as exc:
                    stop_reason = str(exc).split(":")[0]
                    unsent = [c["id"] for c in cases[idx + 1:]]
                    print(f"GUARD STOP: {exc}", file=sys.stderr, flush=True)
                    break

            if pt is not None and pt > CONTEXT_LIMIT - OUTPUT_BUDGET_PER_CALL:
                stop_reason = "context_overflow_risk"
                unsent = [c["id"] for c in cases[idx + 1:]]
                break

    end_utc = datetime.now(timezone.utc)
    manifest = {
        "run": "rtx-runtime-transfer-control (claim #33; corrected wrapper per #88)",
        "owner": "semberecki",
        "session_id": "01a0de3f-e03d-75ba-8a97-eb400acb36a2",
        "lead_declaration": "issue #33 comment 2026-09-26T15:44:13Z",
        "start_utc": start_utc.isoformat(),
        "end_utc": end_utc.isoformat(),
        "dispatch_deadline_utc": datetime.fromtimestamp(dispatch_deadline_utc, timezone.utc).isoformat(),
        "stop_reason": stop_reason or "all_cases_dispatched",
        "dispatched": dispatched,
        "unsent_ids": unsent,
        "results_meta": results_meta,
        "input_path": (str(INPUT.relative_to(REPO))
                       if INPUT.is_relative_to(REPO) else str(INPUT)),
        "input_sha256": actual_input_sha,
        "config_path": "agentsLog/kwiscion/gemma4-12b-val40-1024.config.json",
        "config_sha256": sha256_file(CONFIG),
        "question_pdf_sha256": "ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21",
        "renderer": "pdftoppm (Poppler 24.02.0), 110 DPI",
        "model_tag": config["model"],
        "model_blob_sha256": "1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606",
        "projector_blob_sha256": "675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842",
        "ollama_version": "0.34.4",
        "expected_context": CONTEXT_LIMIT,
        "served_api_ps": served,
        "served_assertion": served_assertion,
        "provenance": {
            "enforced_runtime_checks": [
                "input_sha256", "served_digest", "served_context_length",
                "stop_on_first_declared_failure", "pre_request_timestamp",
                "dispatch_deadline", "output_token_budget", "context_overflow",
            ],
            "manual_retained_evidence": [
                "model_blob_sha256 (operator sha256sum before start)",
                "projector_blob_sha256 (operator sha256sum before start)",
                "question_pdf_sha256 (operator, key-free bootstrap)",
                "renderer (operator, pdftoppm/Poppler 24.02.0, 110 DPI)",
                "ollama_version (operator, serve.log)",
            ],
        },
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
        "boundaries": "wrapper is read/write on owner-private paths only; no purchases; no exam material embedded",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("dispatched", "unsent_ids", "stop_reason", "end_utc")}, ensure_ascii=False), flush=True)
    errors = sum(1 for m in results_meta if m["error_type"])
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
