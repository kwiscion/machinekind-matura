# Generic deadline-limited RAG preparation

CPU-only additive integration. This does not promote RAG, access a final package,
authorize a model run, or alter the preserved Qwen40/60 candidate. The diagnostic
and reviewer decide whether the extension may be frozen for final use.

## Policy frozen before diagnostic grades

- Prepare the exact generic Qwen coverage package first. Its original exam,
  source/image files, direct input rows, closed Qwen profile and recovery prompts
  remain byte-identical. Runtime-only stage expansion adds no model weights.
- Complete the ordinary direct scheduler for **all original items** first,
  including up to three recovery retries and existing essay-format recovery.
- Every explicitly nonessay item is structurally eligible, in the received
  **answer-template order**. No fixed item IDs, history answers, keys, scores or
  validation-specific selection appear in the policy.
- Then process one query, five independent relevance judges, and an optional
  final for each item. Finish each item's dependency phases before proceeding to
  the next item. The same full-corpus search and strict query/judge semantics as
  the fast diagnostic are reused.
- **If no evidence is admitted, skip that optional final and preserve direct.**
  This additional generic gate was requested and implemented before diagnostic
  grades were viewed; the diagnostic itself stays unchanged.
- Auxiliaries use thinking off: query512 and judge384 initial output tokens;
  each of up to three retries requests1024. Direct/final answer budgets and
  reasoning remain the reviewed32768 / conditionally49152 recovery profile.
  Every reservation records its actual cap, including failures.
- Four diagnostic format probes are deliberately absent from final inference.
  Strict per-response validation remains; this integration does not claim
  independent format qualification or measured score improvement.

## Time bounds and saved answers

The qualified configuration remains `minutes=60`, context65536. The actual
declared final model-operation window is enforced at **at most3300seconds
(55minutes)**. The existing guardian honors the earlier declared deadline.
Optional RAG ends at `min(optional_start +1200, actual_deadline -600)`.
The ten-minute reserve cannot be consumed by optional work. Direct mandatory
recovery may consume it, in which case RAG is skipped. Service startup, runtime
verification and HTTP transport use the optional deadline too; a response arriving
after it is rejected. Fifteen seconds are additionally withheld from each
optional request for terminal handling.

The operational target is55minutes model operations plus at most10minutes
transfer/checks =65minutes, leaving5minutes below the owner's70minute limit.
This is a deadline policy, **not measured end-to-end performance or a guarantee
against external transfer delays**. Startup and synchronous export are inside
the declared window; the existing guardian reserves shutdown time. CPU tests do
not qualify Linux process termination or final-host throughput anew.

`results/answers.direct.json` is produced by the preserved baseline exporter on
the original template and direct states only, including its qualified nonblank,
partial and aggregate-size handling. `results/answers.json` has only original
template IDs in their original order. A successful complete optional final may
replace its direct string; unprocessed, failed, late, partial, no-evidence or
oversized optional output keeps the saved direct string **exactly**. A literal
`Tadeusz Kościuszko` is explicitly marked as a placeholder, never recovery
success. Raw complete outputs and failed calls remain in the private engine
ledger. Auxiliaries are never exported as organizer answers.

For `N` original items and `E` nonessay items, maximum primary slots are `N+7E`;
maximum attempts are `4(N+7E)`. The exact requested-token ceiling is
`147456(N+E) + E(3584 +5*3456)`. These are finite worst-case ceilings, not forecasts
or permission invented by preparation. The optional wall deadline normally
allows only a subset. No extra inference model, copied Qwen weights, external
agent or online retrieval is used.

## Pre-acquisition final-host index proof

Run once on the selected final host **before requesting final questions**:

```sh
python3 -B verify_index.py /absolute/frozen/passages.sqlite /absolute/fresh/index-proof.json
```

This reads and hashes the10,464,555,008byte corpus once, verifies the fixed SHA256,
and records hostname, Linux boot ID, device/inode, size, mtime and ctime. It rejects
SQLite WAL/SHM/journal sidecars. The existing retrieval helper opens SQLite with
`mode=ro`. The assumption is explicit: **no writers, replacements or sidecars
until final inference finishes**. Preserve the database at its exact final-host
path. A host reboot, move, replacement or modification invalidates the receipt.
Do not move the10GB database merely to prepare the package elsewhere.

Copy the receipt to the qualified Windows preparation checkout. Then, only after
the chosen solution is committed/frozen and final access is authorized, prepare
the actual received package:

```powershell
python -B agentsLog/kwiscion/deadline-rag-prep/prepare_deadline_rag.py `
  --exam-dir <received-package> --output <fresh-project-private-output> `
  --essay-id <explicit-received-essay-id> `
  --cache <single-qwen-cache> --binary <owned-ollama-binary> --lock <owned-lock> `
  --index <exact-final-host-database-path> --index-proof <downloaded-proof.json>
```

Use `--no-essay` when explicitly appropriate. Preparation performs no model calls
or network actions, copies only required exam sources/images, and remains
`PREPARED` with no authorization. The lead must separately declare the actual
deadline, finite caps and cost estimate under existing authorization. Use the
generated existing `operator_recovery.sh` / `run_recovery_package.py` flow.

## Verification

```powershell
python -B -m unittest discover -s agentsLog/kwiscion/deadline-rag-prep -p test_deadline_rag.py -v
```

Synthetic CPU coverage includes arbitrary IDs (including slashes and namespace
collisions), original template order, complete images/text, direct-payload
equality, no essay RAG, exact cap ledger, all-direct-before-optional ordering,
five judges, forced timeouts, three direct retries, cutoffs in every optional
phase, late finals, no optional time, no-evidence skip, exact fallback, interrupted
export, nonblank placeholders,55minute declaration and aggregate1MiB handling.
No held-out exam content is used by these tests.

Remaining qualification: actual frozen index receipt on the final host, model
diagnostic quality/latency, independent exact-head review, and lead integration.
No claim of full-exam RAG coverage or improved full-exam score is made.
