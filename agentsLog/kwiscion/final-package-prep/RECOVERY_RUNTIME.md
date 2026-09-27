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

Use canonical UTC timestamps with at most six fractional digits and an explicit `+00:00` offset, for example `2026-09-27T00:57:13.067213+00:00`. The deployed Python3.10 guardian rejects Windows DateTimeOffset's default seven-digit precision. On Windows use `.ToString("yyyy-MM-ddTHH:mm:ss.ffffffzzz")` on a UTC DateTimeOffset. After declaration, rerun dry preflight on the actual remote Python before execution; a PREPARED-only check does not validate the later timestamps. A pre-call failure must retain its evidence; any precision-only retry keeps the original deadline and budgets.

```sh
python3 -B /fresh/private/package/run_recovery_package.py /fresh/private/package
python3 -B /fresh/private/package/run_recovery_package.py /fresh/private/package --execute
```

This enters the frozen `operator_recovery.sh` GNU timeout guardian automatically. The parent locks the existing offline lock, verifies exact runtime and fresh-cache inventory, checks no competing worker and original port11436 unloaded, then creates a no-egress network namespace. Its owned server serves only the staged cache on namespace-local11435. It never stops/changes the original service. Anonymous FD challenge plus live PID/start/argv binds the namespace child without protected host-parent `/proc/exe` reads.

Every reserved call/request is durable before send. HTTP runs in a bounded child; a timeout kills/reaps that child and then kills/reaps the exact owned Ollama/backend group before another request. A cold scored request gets up to240seconds, clamped by the whole deadline and recovery reserve; no uncounted warmup. Warm requests return to measured remaining-time allocation. Provider load/eval durations and actual usage are retained. Complete native `done=true` responses permit the verified service to stay warm. Final cleanup always stops owned processes; parent/guardian retain proof-bound crash cleanup. Runtime-created metadata does not invalidate the initial exact inventory: subsequent checks bind immutable declared files/stat identities, full code/source hashes, service identity/environment, native digest and actual loaded context.

## Evidence and limits

`results/engine/events.jsonl` and `requests.jsonl` retain every reservation, response and retry. `results/answers.json` is the exact original organizer template populated with all IDs, no blanks; `answer-status.json` in the engine directory marks incomplete partials/placeholders, selected recovery and unmet attempts. Terminal source/infrastructure failure preserves checkpoint answers/fallbacks. Final export uses the actual adapter for package/prompt/template construction and exact site-compatible schema/IDs/100k-codepoints/1MiB checks; it does not claim the legacy adapter finalizer's stricter UTF16 limit was run.

Current structured multistage route orchestration is separate and not silently enabled. This path executes the four-attempt single-answer recovery policy only. The completed champion rehearsal verified actual65,536 context, full40 recovery/export and cleanup; its legacy-input score was38/60. Later input/model changes need affected qualification and a quality evaluation, not another full injected-fault rehearsal.

CPU checks: `test_recovery_harness.py`, `test_recovery_binding.py`, `test_native_package.py` (Python3, `-X utf8`).

## Essay-only repair correction after the first rehearsal

The [completed rehearsal](../2026-09-27-champion-rehearsal-result.md) remains immutable and scored separately. Current-source essay retries now report the measured word count and contract warnings, include the best prior complete essay as an explicitly fallible draft, and request supported causal development toward 400–500 words without filler or invented facts. Complete original task text and images remain unchanged.

Selection uses only a deterministic mechanical tuple: number of hard format violations (under300 body words, detected plan/multiple-topic marker, or missing topic number when the original answer format requires it), then distance from the400–500 band. A single chosen-topic heading is accepted and excluded from the body count. Earlier candidates win ties. Failed/empty responses and mechanically worse complete repairs cannot replace the saved essay; replay uses the same selection. Nonessay selection and the four-attempt deadline/budget ladder are unchanged. Status distinguishes an initial failed-answer recovery from a mere mechanical improvement that still leaves warnings. This is not a factual-quality score or evidence of improved exam points; no grade keys or task-specific historical hints enter the policy. A new package must freeze the new scheduler hash before any later authorized execution.

Optional essay drafts are limited to `notes_chars` (6,000 characters) with an explicit excerpt label; the full candidate remains in the checkpoint. Admission conservatively charges every added UTF-8 byte plus 256 framing tokens against the maximum observed prompt usage. If escalation no longer fits, the lower output cap is retained; if optional feedback still lacks room, it is omitted. Original task text/images are never clipped. This is a conservative allowance, not an exact tokenizer proof; actual runtime/context checks still apply.
