# Independent offline-qualification preparation review

**PASS for the frozen two-item qualification code and prepared package.** No remaining material code blocker was found. Root may separately declare and dispatch this bounded synthetic qualification using the reviewed shell guardian. This review did not launch a server, make a model call, use a GPU or establish actual offline serving success.

## Exact reviewed artifacts

Paths below are relative to `agentsLog/kwiscion/final-package-prep/`; hashes are SHA256 of file bytes.

| Artifact | SHA256 |
|---|---|
| `run_gemma_offline.py` | `c699adf93fa9f1d790d25219fb7de8ace508ba71516108c168fddcbcd389b15b` |
| `test_offline.py` | `07ca3a65bf5dc46413764cc77955ef5b8a57dc5e063b721482df744f8f7da4f8` |
| `prepare_offline.py` | `4c54a44dcd2919b9c9f0e76b1b528f68542cf43e44f5c9eefd85a39232f4755a` |
| `operator_offline.sh` | `7ed0d33b971101c196fa0bf7b43e08df2c105894d20342cc36bd18b19202f122` |
| `OFFLINE_QUALIFICATION.md` | `d005b11e1c9a99f475f7a20fcac97786079a7a99bc3c74ca42ebbd1f144ad31b` |

The private `final-offline-qualification-20260926/package-v4/launch.json` hashes to `a46b055f06dd8884c8a8ebba2e14cc67f68003ba1c0b131363dc49d4b1e2d5a2`. Its dependency membership and hashes match the frozen package; the actual packaged default file-only preflight passed. Status remains `PREPARED`, with declaration/deadline unset. Execution must use a fresh declared copy, changing only the documented declaration fields and preserving code, cache, binary and lock pins.

## Findings

- The actual organizer adapter prepares, finalizes and validates two original synthetic items: copying `gotowe` and identifying the complete pinned red-square image. Image bytes and SHA are checked. Returned final strings are retained; failed/unsent entries stay blank in the original template. Exact normalized text and accepted red-color forms are checked, so nonempty junk or a wrong color cannot pass.
- Both calls use native Gemma thinking, context 32768, temperature omitted, `truncate:false`, `shift:false`, and 10240 requested output tokens each. The durable fsynced reservation and exact request precede transport. There are at most two sequential calls, 20480 requested tokens, 420 seconds per request, no retries or warmups. Either truncation flag, invalid usage/context accounting, provider error, length termination or missing final/thinking evidence stops dispatch.
- The staged Gemma-only cache is checked by the previously reviewed exact native inventory guard; no Qwen dependency or development-cache substitution is introduced. The existing host daemon must be unloaded and is inspected without reconfiguration or shutdown. The new worker holds its own lock and checks competing process/GPU activity.
- Runner and new server share a distinct `unshare -rn` namespace. The inherited proof checks loopback-only interfaces, empty routes, failed external IPv4/IPv6 connections and distinct host namespace. Server PID/start ticks, executable, environment, model/runtime identity and context are checked. Existing saved namespace-probe evidence supports capability only; it is not an inference receipt.
- Cleanup targets the owned process group using identity and namespace evidence. The reviewed fixes cover death between server spawn and PID-receipt persistence: fallback uses the durable pre-spawn namespace proof and pinned runtime subtree, refuses the host namespace, and rechecks process identity. Foreign-UID processes are skipped before protected `/proc` reads; inaccessible same-UID candidates fail visibly. No host daemon is selected for cleanup.
- The internal execution path now enforces explicit execution, matching declared manifest and current deadline before side effects. Python's whole-operation alarm includes prehash/probe. The required external wrapper limits execution to 1190 seconds plus 5 seconds kill grace and 5 seconds cleanup. This bounds the intended complete operation to 20 minutes; actual terminal receipts, elapsed time and absence of owned survivors must still be checked after execution.

## Independent CPU validation

The final tests passed **11/11 on Windows and 11/11 on local WSL/Linux**; shell syntax validation passed. These include a real-adapter mocked dispatch loop, reservation-before-send ordering, two-call/token limits, first-error termination with both template entries blank, wrong-color rejection, deadline checks and missing-receipt/foreign-UID cleanup cases.

A separate fresh-package probe exercised the actual prepare CLI, packaged dry preflight, organizer prepare/load/finalize/validate, complete image hash, both native request envelopes and semantic checks. It passed without a transport, server or model. This additional probe is preserved privately as `offline_package_cpu_review.py`.

The [independent stage review](2026-09-26-final-package-stage-independent-review.md) separately confirms six staged file entries totaling **7,556,509,301 bytes**, including the **7,556,497,632-byte** pinned model/projector pair and **11,669 bytes** of metadata. Hardlinked entries count fully. The preserved local archive backs up evidence only, not model weights.

## Scope of approval

This approves preparation for the finite two-item qualification, not its unexecuted outcome, exam quality, a generic Sunday runner or final promotion. Require the reviewed shell wrapper, frozen dependencies and fresh bounded declaration; then verify actual semantic answers, namespace/server identity, usage, organizer output, cleanup and evidence backup. No full-exam quality result is a prerequisite for this synthetic runtime check.

Reviewer: independent Sol `/root/essay_corpus_sol`. CPU tests and local evidence/code inspection only; no inference, GPU, new server, remote execution, author-file edits or Git mutation.
