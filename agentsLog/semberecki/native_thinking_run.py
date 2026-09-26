#!/usr/bin/env python3
"""Frozen native-thinking comparison runner (authorized in #95 comment 5849041941, Piotr).

Frozen envelope:
- SAME six source-heavy items as the parked multiscale diagnostic; full
  originals retained (110 DPI pages from the frozen v2 input, unchanged)
- control arm: think:false / 1024 total; thinking arm: think:true / 10240 total
- explicit temperature 1.0 / top_p 0.95 / top_k 64 in BOTH arms (organizer-
  inspired reasoning bundle); all other settings matched
- max 12 sequential calls / 67,584 requested generation tokens / 30-minute
  absolute guarded deadline from actual start, checked before each dispatch
  (in-flight may finish within the 420 s timeout) / $0 / no retries / no smokes
- capability established via zero-generation metadata (/api/show thinking
  levels) before dispatch; the actual first case records behavior
- native num_predict includes thinking; no invented final reserve
- native request shape and answer/usage validation reuse the reviewed native
  work (scripts/ljaniec/reasoning_lab.py semantics, PR #133); both
  truncated/context_truncated flags are enforced
- failure semantics (declared in the launch record): infra/systemic failures
  (transport, server identity change, response error field, response model
  mismatch, thinking-evidence violations) STOP the bundle on first occurrence;
  sampling outcomes (truncated final / length stop / empty final) are recorded
  as failures and NOT retried, and the bundle continues so all 8 points stay
  in each arm's denominator
- per-result flush, real pre-request timestamps, attempt ledger preserved
- raw thinking is preserved privately; published answer-only output excludes
  reasoning

No exam material is embedded here; inputs/outputs stay under the gitignored
owner-private dir. No purchases, no new models, one worker.
"""

import base64
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = None
for p in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
    if (p / ".git").exists():
        REPO = p
        break
if REPO is None:
    raise RuntimeError("repo root not found")

PRIV = REPO / "agentsLog/semberecki/private"
INPUT = PRIV / "validation_2024_keyfree/runner_input.v2.jsonl"
INPUT_EXPECTED_SHA = "6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4"
CONFIG = PRIV / "validation_2024_keyfree/native-thinking-bundle.config.json"
OUTPUT = PRIV / "validation_2024_keyfree/native-thinking-results.jsonl"
MANIFEST = PRIV / "validation_2024_keyfree/native-thinking-manifest.json"

# Frozen item list (launch record): (id, classification, baseline points)
ITEMS = [
    ("val2024-hist-z5.1", "failed_source_interpretation", 0),
    ("val2024-hist-z14.1", "failed_source_interpretation", 0),
    ("val2024-hist-z25", "failed_source_interpretation", 0),
    ("val2024-hist-z2", "control_source_dependent", 1),
    ("val2024-hist-z4", "control_source_dependent", 1),
    ("val2024-hist-z13", "control_source_dependent", 1),
]
MAX_CALLS = 12
REQUESTED_PER_ARM = {"control": 1024, "thinking": 10240}
MAX_TOTAL_REQUESTED = 6 * (1024 + 10240)  # 67,584
DISPATCH_SECONDS = 1800  # 30-minute absolute guarded deadline
EXPECTED_DIGEST = "4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c"


class StopBundle(RuntimeError):
    """Infra/systemic failure: stop the bundle on first occurrence."""


def sha256_file(path: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def api_show(model: str) -> dict:
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/show",
        data=json.dumps({"model": model}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def api_ps() -> dict:
    with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=10) as r:
        return json.loads(r.read().decode())


def assert_show_thinking(show: dict) -> None:
    caps = show.get("capabilities", [])
    if not isinstance(caps, list) or "thinking" not in caps:
        raise StopBundle("native thinking capability unavailable (zero-generation metadata)")


def assert_served_identity(ps: dict, expected_context: int) -> None:
    loaded = [m for m in ps.get("models", []) if isinstance(m, dict)]
    matches = [m for m in loaded if m.get("digest") == EXPECTED_DIGEST]
    if len(matches) != 1:
        raise StopBundle(f"expected loaded model unambiguous (matches={len(matches)})")
    cl = matches[0].get("context_length")
    if type(cl) is not int or cl <= 0 or type(cl) is bool:
        raise StopBundle("served context_length missing/invalid (fail closed)")
    if cl != expected_context:
        raise StopBundle(f"served context changed: {cl} != {expected_context}")


def native_case(case: dict) -> tuple[str, list[str]]:
    text = case["prompt"]
    images = []
    for rel in case["images"]:
        p = Path(rel)
        if not p.is_absolute():
            p = INPUT.parent / rel
        images.append(base64.b64encode(p.read_bytes()).decode())
    return text, images


def payload_for(text: str, images: list[str], arm: str, cfg: dict) -> dict:
    message = {"role": "user", "content": text}
    if images:
        message["images"] = images
    return {"model": cfg["model"], "stream": False, "think": arm == "thinking",
            "truncate": False, "shift": False, "messages": [message],
            "options": {"num_ctx": cfg["context_length"],
                        "num_predict": REQUESTED_PER_ARM[arm],
                        "temperature": cfg["temperature"],
                        "top_p": cfg["top_p"], "top_k": cfg["top_k"]}}


def run_native(payload: dict, cfg: dict) -> dict:
    req = urllib.request.Request(
        cfg["base_url"] + "/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout_seconds"]) as r:
            body = json.loads(r.read().decode())
    except Exception as exc:  # transport/timeout: systemic failure
        return {"raw": None, "latency_seconds": round(time.monotonic() - t0, 3),
                "error": {"type": "infrastructure", "message": str(exc)}}
    return {"raw": body, "latency_seconds": round(time.monotonic() - t0, 3),
            "error": None}


def evaluate(response: dict, arm: str, cfg: dict) -> dict:
    """Validate one native response. Returns (outcome, detail) metadata.

    outcome: 'ok' | 'failed_sampling' (recorded, continue) | raises StopBundle
    for infra/systemic failures.
    """
    if response["error"] is not None:
        raise StopBundle(f"transport/systemic: {response['error']['message'][:120]}")
    raw = response["raw"]
    if not isinstance(raw, dict):
        raise StopBundle("native response is not a JSON object")
    if raw.get("error") is not None:
        raise StopBundle(f"native error: {str(raw.get('error'))[:120]}")
    if raw.get("model") != cfg["model"]:
        raise StopBundle(f"response model changed: {raw.get('model')}")
    if raw.get("truncated") is True or raw.get("context_truncated") is True:
        return {"outcome": "failed_sampling", "reason": "truncated_flag"}
    if raw.get("done") is not True or raw.get("done_reason") != "stop":
        return {"outcome": "failed_sampling",
                "reason": f"incomplete:{raw.get('done_reason')}"}
    message = raw.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str) \
            or not message["content"].strip():
        return {"outcome": "failed_sampling", "reason": "empty_final"}
    reasoning = message.get("thinking", "")
    if not isinstance(reasoning, str):
        raise StopBundle("invalid native thinking field")
    if arm == "thinking" and not reasoning.strip():
        raise StopBundle("requested thinking produced no thinking evidence")
    if arm == "control" and reasoning.strip():
        raise StopBundle("thinking appeared despite explicit think:false")
    usage = raw.get("prompt_eval_count"), raw.get("eval_count")
    for v in usage:
        if type(v) is not int or type(v) is bool or v < 0:
            raise StopBundle("missing or invalid native usage counts")
    if usage[0] + REQUESTED_PER_ARM[arm] > cfg["context_length"]:
        raise StopBundle("reported prompt plus generation reserve exceeds context")
    if usage[1] > REQUESTED_PER_ARM[arm]:
        raise StopBundle("native generation exceeds requested cap")
    return {"outcome": "ok", "reason": None,
            "prompt_eval_count": usage[0], "eval_count": usage[1]}


def build_sequence() -> list[dict]:
    want = {i[0] for i in ITEMS}
    loaded = {}
    for line in INPUT.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        if c["id"] in want:
            loaded[c["id"]] = c
    missing = want - set(loaded)
    if missing:
        raise RuntimeError(f"frozen items missing from input: {sorted(missing)}")
    seq = []
    for item_id, classification, baseline in ITEMS:
        for arm in ("control", "thinking"):
            seq.append({"id": item_id, "arm": arm, "classification": classification,
                        "baseline_points": baseline})
    return seq


def main() -> int:
    actual_input_sha = sha256_file(INPUT)
    if actual_input_sha != INPUT_EXPECTED_SHA:
        print(f"FATAL: input SHA mismatch: {actual_input_sha}", file=sys.stderr)
        return 2
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    show = api_show(cfg["model"])  # zero-generation capability metadata
    assert_show_thinking(show)

    seq = build_sequence()
    loaded_map = {}
    for line in INPUT.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        if c["id"] in {i[0] for i in ITEMS}:
            loaded_map[c["id"]] = c
    if len(seq) > MAX_CALLS:
        print(f"FATAL: {len(seq)} calls exceeds max {MAX_CALLS}", file=sys.stderr)
        return 2
    if OUTPUT.exists():
        print(f"FATAL: output exists (no overwrite): {OUTPUT}", file=sys.stderr)
        return 2

    start_utc = datetime.now(timezone.utc)
    deadline = start_utc.timestamp() + DISPATCH_SECONDS
    print(f"start_utc={start_utc.isoformat()} deadline_utc="
          f"{datetime.fromtimestamp(deadline, timezone.utc).isoformat()} "
          f"calls={len(seq)}", flush=True)

    results_meta = []
    unsent: list[str] = []
    stop_reason = None
    total_requested = 0
    served = None
    dispatched = 0
    sampling_failures = 0

    with OUTPUT.open("x", encoding="utf-8") as out:
        for idx, case in enumerate(seq):
            if time.time() >= deadline:
                stop_reason = "dispatch_deadline"
                unsent = [f"{c['id']}:{c['arm']}" for c in seq[idx:]]
                break
            total_requested += REQUESTED_PER_ARM[case["arm"]]
            if total_requested > MAX_TOTAL_REQUESTED:
                stop_reason = "output_token_budget"
                unsent = [f"{c['id']}:{c['arm']}" for c in seq[idx:]]
                total_requested -= REQUESTED_PER_ARM[case["arm"]]
                break

            row = loaded_map[case["id"]]
            text, images = native_case(row)
            payload = payload_for(text, images, case["arm"], cfg)
            request_started_utc = datetime.now(timezone.utc)
            response = run_native(payload, cfg)
            response_completed_utc = datetime.now(timezone.utc)
            dispatched += 1

            outcome = None
            try:
                outcome = evaluate(response, case["arm"], cfg)
            except StopBundle as exc:
                stop_reason = f"systemic_stop:{str(exc)[:120]}"
                out.write(json.dumps({"id": case["id"], "arm": case["arm"],
                                      "response": response, "outcome": "systemic_stop",
                                      "detail": str(exc)[:200]}, ensure_ascii=False) + "\n")
                out.flush()
                unsent = [f"{c['id']}:{c['arm']}" for c in seq[idx + 1:]]
                print(f"SYSTEMIC STOP: {exc}", file=sys.stderr, flush=True)
                break
            if outcome["outcome"] != "ok":
                sampling_failures += 1  # recorded, not retried, bundle continues

            out.write(json.dumps({"id": case["id"], "arm": case["arm"],
                                  "outcome": outcome["outcome"],
                                  "reason": outcome.get("reason"),
                                  "response": response}, ensure_ascii=False) + "\n")
            out.flush()

            raw = response["raw"] or {}
            results_meta.append({
                "id": case["id"], "arm": case["arm"],
                "outcome": outcome["outcome"], "reason": outcome.get("reason"),
                "latency_seconds": response["latency_seconds"],
                "prompt_eval_count": raw.get("prompt_eval_count"),
                "eval_count": raw.get("eval_count"),
                "request_started_utc": request_started_utc.isoformat(),
                "response_completed_utc": response_completed_utc.isoformat(),
            })
            print(f"[{dispatched}/{len(seq)}] {case['id']}:{case['arm']} "
                  f"{outcome['outcome']}"
                  f"{'' if outcome['outcome'] == 'ok' else ' (' + str(outcome.get('reason')) + ')'} "
                  f"{response['latency_seconds']}s", flush=True)

            if served is None and response["error"] is None:
                try:
                    served = api_ps()
                    served["queried_at"] = datetime.now(timezone.utc).isoformat()
                    assert_served_identity(served, cfg["context_length"])
                except StopBundle as exc:
                    stop_reason = f"systemic_stop:{str(exc)[:120]}"
                    unsent = [f"{c['id']}:{c['arm']}" for c in seq[idx + 1:]]
                    print(f"SYSTEMIC STOP: {exc}", file=sys.stderr, flush=True)
                    break

    end_utc = datetime.now(timezone.utc)
    manifest = {
        "run": "native-thinking-comparison-bundle (authorized #95 5849041941)",
        "owner": "semberecki",
        "session_id": "01a0de3f-e03d-75ba-8a97-eb400acb36a2",
        "start_utc": start_utc.isoformat(),
        "end_utc": end_utc.isoformat(),
        "dispatch_deadline_utc": datetime.fromtimestamp(deadline, timezone.utc).isoformat(),
        "stop_reason": stop_reason or "all_calls_dispatched",
        "dispatched": dispatched,
        "unsent_calls": unsent,
        "sampling_failures": sampling_failures,
        "input_sha256": actual_input_sha,
        "config_sha256": sha256_file(CONFIG),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "question_pdf_sha256": "ad66a7c4f212ee1248661141971afae21060a28586086cc57460247a64463d21",
        "model_tag": cfg["model"],
        "model_blob_sha256": "1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606",
        "projector_blob_sha256": "675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842",
        "ollama_version": "0.34.4",
        "capability_check": {"method": "zero-generation metadata /api/show", "show": show},
        "served_api_ps": served,
        "decoding": {"temperature": cfg["temperature"], "top_p": cfg["top_p"],
                     "top_k": cfg["top_k"],
                     "num_predict_control": REQUESTED_PER_ARM["control"],
                     "num_predict_thinking": REQUESTED_PER_ARM["thinking"],
                     "num_predict_scope": "native generated tokens including thinking"},
        "items": [{"id": i[0], "classification": i[1], "baseline_points": i[2]} for i in ITEMS],
        "limits": {"max_calls": MAX_CALLS,
                   "max_total_requested_output_tokens": MAX_TOTAL_REQUESTED,
                   "dispatch_seconds": DISPATCH_SECONDS,
                   "in_flight_timeout_seconds": cfg["timeout_seconds"],
                   "no_retry": True, "no_new_smokes": True, "paid_spend": "$0"},
        "failure_semantics": ("infra/systemic stops on first occurrence; sampling outcomes "
                              "(truncated/length/empty final) recorded as failures, not retried, "
                              "bundle continues so all 8 points stay in each arm's denominator"),
        "provenance": {
            "enforced_runtime_checks": [
                "input_sha256", "capability_metadata", "served_digest",
                "served_context_length", "unambiguous_loaded_model",
                "fail_closed_context", "truncated_and_context_truncated_flags",
                "thinking_evidence_both_directions", "usage_counts_validated",
                "context_reserve", "dispatch_deadline", "output_token_budget",
                "pre_request_timestamp", "no_retry"],
            "manual_retained_evidence": [
                "model_blob_sha256 (operator sha256sum before start)",
                "projector_blob_sha256 (operator sha256sum before start)",
                "question_pdf_sha256 (operator, frozen, re-verified this session)",
                "prompt_and_page_hashes (operator, launch record)",
                "ollama_version (operator)"],
        },
        "boundaries": "read/write on owner-private paths only; no purchases; no new models; "
                      "raw thinking private; published handoff excludes reasoning",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("dispatched", "unsent_calls", "stop_reason",
                                               "sampling_failures", "end_utc")},
                     ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
