# Generic native Gemma organizer path — preparation only

The four new files implement a CPU-preparable arbitrary-organizer-package runner. **No model call, server start, GPU work or remote operation was performed to build or test it. Independent code review and a separate bounded runtime declaration are required before execution.** The two-item native qualification is distinct evidence; its initial serving checks passed, but its redundant cleanup failed. The receipt-aware helper correction pinned here (`d4f26d319b88d479ad3eaa0a7afe2d4ce68706e4dd75324e5d4d4d83fa1c036b`) passed its separate independent CPU review.

The historical `agentsLog/kwiscion/run_gemma_package.py` is the older bare/laptop-compatible path with its own frozen configuration and profiles. It is unchanged. This new path explicitly uses the staged single-Gemma cache, Ollama 0.34.4, native thinking and context 32768; it makes no equivalence claim about the old path or exam quality.

## Prepare on CPU

Use an unpacked received organizer package containing `exam.json`, `answers-template.json` and its referenced images. Keep source packs and generated portable packages private. Only the adapter-required files are copied; unrelated keys or files are excluded. The real adapter checks the source package, prepares original prompts, finalizes outputs and validates the original answer template.

```powershell
python -B agentsLog/kwiscion/final-package-prep/prepare_native_package.py `
  --exam-dir PATH_TO_RECEIVED_PACKAGE `
  --output agentsLog/kwiscion/private/NEW_NATIVE_PACKAGE `
  --essay-id ACTUAL_RECEIVED_ESSAY_ID `
  --cache /absolute/owned/stage/models `
  --binary /absolute/owned/runtime/bin/ollama `
  --lock /absolute/project/offline-rehearsal.lock `
  --max-seconds 5400 --request-timeout 600

python -B agentsLog/kwiscion/final-package-prep/run_native_package.py agentsLog/kwiscion/private/NEW_NATIVE_PACKAGE
python -B -X utf8 agentsLog/kwiscion/final-package-prep/test_native_package.py
```

The time values above prepare a candidate envelope only, not permission to run it. Repeat `--essay-id` for multiple received essay items, or explicitly use `--no-essay`. Missing, duplicate, unknown or contradictory mappings are rejected. There is no validation-ID or question-text heuristic. The item count is the received package's actual N, including counts above 100; there is no fixed 40-item assumption.

Every ordinary item requests 10240 output tokens. Every explicitly mapped essay requests 20480 and appends exactly the existing full-thinking generic choose-one/400–500-word/clean-prose policy. No other policy is added. The routed JSONL, original JSONL, adapter manifest, original exam/template/image bytes, per-item prompt hashes and route manifest are pinned. The preflight reconstructs the original adapter prompts and route changes and verifies complete image order.

## Declaration and execution after independent review

Preparation emits `PREPARED`, with no timestamps or authorization. Root must freeze the generated package and reviewed file hashes, then declare a fresh execution copy by changing only `status`, `declared_utc`, `deadline_utc` and `authorization`. Times must be aware UTC; execution must fall within that window, whose span is no greater than the prepared `max_seconds`. The authorization object must contain:

```json
{
  "owner": "root",
  "reference": "explicit bounded declaration reference",
  "max_calls": "the exact integer N from launch.json",
  "max_requested_tokens": "the exact integer sum from launch.json",
  "max_seconds": "the exact integer bound from launch.json",
  "above_240k_explicit": true
}
```

The three explanatory strings above must be replaced with integers; the code rejects them as strings. `above_240k_explicit:true` is mandatory only when the exact requested-token sum exceeds 240000. Preparation may calculate a larger sum, but does not authorize that extension. Do not broaden bounds, replace runtime/cache paths or change code after review. Reprepare and review a new package for such changes.

On the assigned idle Linux host, upload only the frozen portable package; use the already staged verified cache. Ordinary `--execute` automatically enters the pinned generated shell guardian:

```sh
python3 -B /absolute/private/NEW_NATIVE_PACKAGE/run_native_package.py /absolute/private/NEW_NATIVE_PACKAGE --execute
```

The external `timeout` computes its window from the absolute deadline, reserving 5 seconds for kill grace and 5 seconds for owned cleanup. A Python alarm is installed before input/image preflight and leaves 15 seconds for normal cleanup/finalization. The guarded path checks its OS guardian parent. After locked runtime/weight preflight, it records supervisor PID/start ticks/executable/arguments/namespace and live guardian ancestry. The internal child verifies those bindings and an inherited anonymous-pipe challenge before any namespace or server operation; a caller-supplied `--parent` alone cannot enter serving. No fresh results directory may exist: retries/resume/fallback are absent.

The shared host lock and process/GPU checks must pass. The exact Gemma-only native cache and runtime binary are checked against the existing production pins, including the aggregate package guard; Qwen is unnecessary. The host daemon is inspected and must have no loaded model; the runner never unloads or reconfigures it. A separate owned server and runner share an isolated loopback-only network namespace. Native requests set `think:true`, context32768, `truncate:false`, `shift:false`, omit temperature and preserve complete source images.

## Failure and evidence contract

- Each send has an fsynced request and reservation first. Reservations count even when transport or generation fails. Caps are N calls and the exact sum of the mapped output caps; actual response usage is checked per call and preserved privately. No retries or warmups occur.
- A terminal, correctly accounted length, empty-final or adapter-invalid final becomes a blank entry with an explicit item failure. Dispatch continues only if the full next timeout and cleanup window remain. Both context-truncation flags, identity/usage/context errors, uncertain transport/provider failures, missing thinking, pins, ownership and namespace failures stop further dispatch. Unsent template entries remain blank.
- Native raw envelopes and final strings are retained privately. `answers.adapter.json` records the real adapter result. `answers.json` uses the same original template and exact accepted native final strings, preserving surrounding whitespace; it is independently validated against the real template. Embedded reasoning that the adapter would remove is rejected instead of silently rewriting the final. No semantic correctness is inferred.
- Normal cleanup binds server identity, namespace and killed process IDs, waits for its process, and writes a receipt. The updated pinned helper skips the broad fallback only for a complete identity-bound receipt with all recorded PIDs absent. Incomplete evidence retains the strict fallback; uncertain permissions or live/reused PIDs remain errors. The external guardian repeats this receipt-aware cleanup after abnormal exit.
- Preserve the launch manifest, all dependency hashes, requests, reservations, raw outputs, runtime/namespace proof, cleanup receipts, finalizer input, both answer artifacts, failures and terminal report. Check actual process/GPU absence and archive/hash evidence after execution. A hard kill during file writing can leave incomplete evidence: do not label that a clean success or automatically rerun it.

## Validation and remaining limits

Fourteen focused CPU tests passed on Windows and WSL/Linux, including shell syntax validation on Linux. Tests use only original synthetic source data and mocked transport through the real adapter: arbitrary N=101, essay routing, Unicode/source/image preservation, original template order and exact accepted strings, per-call reservations, error continuation, global fail-stop, zero-dispatch ownership/time failures, explicit above-240k authority, receipt-aware cleanup, direct-internal-entry refusal and valid/mismatched supervisor challenges. They also assert exact equality with the established essay-policy constant.

The received package still must fit the organizer's supported schema and output size limits. Context fit is not predicted from character counts; full prompts are sent with truncation disabled and response flags/usage checked. Runtime compatibility of the generic path and its full cleanup must be established by a separate finite execution. This is executable preparation, not a final promoted submission or a quality guarantee.
