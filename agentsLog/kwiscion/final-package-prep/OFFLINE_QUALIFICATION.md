# Two-item real offline qualification (prepared, not executed)

The original package-v4 attempt has now executed: both answers passed, but redundant outer cleanup failed. See the [immutable result](../2026-09-26-final-offline-result.md). Current code includes a [separately reviewed receipt-aware cleanup correction](../2026-09-27-offline-cleanup-independent-review.md); it has CPU approval only. Any subsequent run needs a freshly prepared package with the corrected code pins and a new declaration. Do not relabel the original attempt or silently reuse its declaration.

This executable vertical slice qualifies the actual staged single-Gemma cache through native thinking and the organizer adapter. It is **not** a generic Sunday runner: adapting the same native path to arbitrary organizer packages and explicit essay cap mappings remains a separate integration step. No validation IDs, essay policies or fallback behavior are introduced here.

## Frozen scope

- Two original synthetic organizer items: copy `gotowe`; identify the dominant red square in the complete pinned fixture PNG. Both use the real adapter preparation, finalizer and original answers template.
- Gemma 4 12B Q4, Ollama 0.34.4, context32768, thinking enabled, temperature omitted, native `truncate:false` and `shift:false`.
- At most2 sequential calls,10240 output tokens each (combined thinking/final),20480 requested total;420s/request;20min whole-operation deadline;0 retries/warmups. Estimated ceiling$1.10 at3.28/hour planning proxy, actual billing unverified.
- Existing host service is left untouched. A fresh isolated server uses **only** the actual verified staged cache. Parent holds the offline lock; process/GPU checks reject competitors. Both server and runner execute in a distinct `unshare -rn` network namespace with loopback only, empty routes and failed external-connect probes.
- Every dispatch has a durable fsynced reservation and exact request. Both truncation flags, usage/context reserve, complete final, thinking evidence and model/runtime identity must pass. Any failure stops dispatch; adapter output retains blank failed/missing entries. Synthetic correctness is exact normalized `gotowe` and red color morphology, not just nonempty text. Original returned final strings remain unchanged.

## Prepare and freeze

```sh
python agentsLog/kwiscion/final-package-prep/prepare_offline.py PRIVATE/package --cache ACTUAL_STAGE/models --binary RUNTIME/bin/ollama --lock PROJECT/offline-rehearsal.lock
python PRIVATE/package/run_gemma_offline.py PRIVATE/package
python -X utf8 agentsLog/kwiscion/final-package-prep/test_offline.py
```

Preparation requires a fresh project-private directory and emits a `PREPARED` manifest with unset timestamps. Package includes exact hashes of the runner, frozen guard, existing isolation/fixture helper, core input serializer, actual adapter and PNG. Default preflight starts no processes. Current normal-account namespace probe passed (distinct namespace, only loopback, no routes); actual serving remains unqualified.

## Separately authorized execution

After independent review and root declaration, preserve the prepared manifest. Set only `status: DECLARED`, `declared_utc`, and `deadline_utc` (aware UTC, no more than20min later) in a fresh upload package; preserve all reviewed code/file pins and exact cache/binary/lock paths. Upload the reviewed shell wrapper alongside it; normalize shell line endings to LF without changing semantics. Do not copy development weights.

```sh
bash operator_offline.sh /absolute/project/private/package --execute
```

The external guardian covers the entire process, including prehash/probe:1190s plus5s kill grace plus5s owned-namespace cleanup. The Python absolute deadline leaves10s for cleanup. The new server has a recorded PID/start ticks/network namespace; cleanup targets only that owned group. If the controller dies before the PID receipt, the outer fallback uses the previously written isolated-namespace proof and runtime executable directory, never the host namespace. The existing host daemon is neither stopped nor reconfigured. Inspect cleanup receipts and GPU/process status before declaring success.

Back up `results/` and the exact launch/dependency hashes after terminal exit. Verify archive SHA remotely and locally. Keep native thinking, infrastructure metadata and raw requests private. Report namespace proof, two-call semantic results, adapter answers hash, usages, errors/unsent IDs, cleanup and whole elapsed time. This qualification does not establish exam quality or generic final-package readiness.
