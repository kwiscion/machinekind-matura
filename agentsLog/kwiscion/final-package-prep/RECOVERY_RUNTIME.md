# Reusable champion runtime — operator guide

This is the actual isolated native binding for `recovery_harness.py`. CPU tests qualify code paths only; the first real scored request must verify the requested 65,536 runtime context. Do not access FINAL while any code, prompts or settings remain changeable.

## Prepare (no inference)

Stage a fresh cache containing only the pinned Gemma manifest and referenced blobs. Existing caches may contain runtime sidecars; only declared native members are copied/hardlinked. Reports live outside the cache. Original files/services remain untouched.

```sh
python3 stage_recovery_cache.py /existing/project/models /fresh/private/cache --report /fresh/private/cache-report.json
```

On the repository machine, use the actual organizer directory and explicit received essay IDs (or `--no-essay`). No validation-specific ID is hardcoded.

```sh
python -X utf8 agentsLog/kwiscion/final-package-prep/prepare_recovery_package.py --exam-dir PRIVATE_ORGANIZER_DIR --output agentsLog/kwiscion/private/champion-rehearsal/package --essay-id ACTUAL_ESSAY_ID --cache /fresh/private/cache --binary /owned/runtime/bin/ollama --lock /owned/offline.lock --minutes 60 --inject-faults
python -X utf8 agentsLog/kwiscion/private/champion-rehearsal/package/run_recovery_package.py agentsLog/kwiscion/private/champion-rehearsal/package
```

Omit `--inject-faults` for normal final use. It selects the two shortest nonessay original prompts, tie-breaking by ID: the first is an injected client timeout, the second requests one output token. The cap stress is not claimed to produce a length stop unless actually observed. Requests and injected outcomes are separately recorded. The timeout injection allows up to three seconds for dispatch and records timed-out usage as unknown; it does not claim active GPU cancellation unless independently observed. The same original sources and full image bytes reach both attempts and recoveries.

## Declare and run once

After independent review and root execution authorization, preserve PREPARED `launch.json`, then set only `status=DECLARED`, aware UTC `declared_utc`, `deadline_utc`, and `authorization`. The deadline is at most60/120minutes after declaration. Authorization contains owner `root`, reference, exact `max_calls`, `max_requested_tokens`, `max_seconds`, and `above_240k_explicit: true` where necessary. For40items the worst-case envelope is160calls/5,898,240requested tokens (not an estimate of actual generation). Root must explicitly authorize that envelope or revise the reviewed policy; no implicit enlargement.

```sh
python3 -B /fresh/private/package/run_recovery_package.py /fresh/private/package --execute
```

This enters the frozen `operator_recovery.sh` GNU timeout guardian automatically. The parent locks the existing offline lock, verifies exact runtime and fresh-cache inventory, checks no competing worker and original port11436 unloaded, then creates a no-egress network namespace. Its owned server serves only the staged cache on namespace-local11435. It never stops/changes the original service. Anonymous FD challenge plus live PID/start/argv binds the namespace child without protected host-parent `/proc/exe` reads.

Every reserved call/request is durable before send. HTTP runs in a bounded child; a timeout kills/reaps that child and then kills/reaps the exact owned Ollama/backend group before another request. A cold scored request gets up to240seconds, clamped by the whole deadline and recovery reserve; no uncounted warmup. Warm requests return to measured remaining-time allocation. Provider load/eval durations and actual usage are retained. Complete native `done=true` responses permit the verified service to stay warm. Final cleanup always stops owned processes; parent/guardian retain proof-bound crash cleanup. Runtime-created metadata does not invalidate the initial exact inventory: subsequent checks bind immutable declared files/stat identities, full code/source hashes, service identity/environment, native digest and actual loaded context.

## Evidence and limits

`results/engine/events.jsonl` and `requests.jsonl` retain every reservation, response and retry. `results/answers.json` is the exact original organizer template populated with all IDs, no blanks; `answer-status.json` in the engine directory marks incomplete partials/placeholders, selected recovery and unmet attempts. Terminal source/infrastructure failure preserves checkpoint answers/fallbacks. Final export uses the actual adapter for package/prompt/template construction and exact site-compatible schema/IDs/100k-codepoints/1MiB checks; it does not claim the legacy adapter finalizer's stricter UTF16 limit was run.

Current structured multistage route orchestration is separate and not silently enabled. This path executes the four-attempt single-answer recovery policy only. Dynamic throughput,65k-context memory use and whole-run quality await the declared full rehearsal; no additional standalone smoke is required by this guide.

CPU checks: `test_recovery_harness.py`, `test_recovery_binding.py`, `test_native_package.py` (Python3, `-X utf8`).
