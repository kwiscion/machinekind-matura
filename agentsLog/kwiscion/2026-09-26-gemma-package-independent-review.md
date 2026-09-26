# Organizer-package launcher independent review

26 September 2026, 17:29 Europe/Warsaw. GPT-6 Sol. **PASS for the reviewed CPU implementation after author fixes.** This is not a launch authorization or proof of isolated GPU execution. No reviewer code edits, namespace/server/model launches, or network calls.

The initial blockers were reproduced and fixed by the author: launcher validation now happens before a row is persisted; missing usage, context/runtime mismatch, truncation and unsupported finish signals mark the row failed, preserve its provider response, stop further calls, and export a blank. The wrapper now follows infer.MAX_CALLS=100. After asset verification, original config bytes are read once, hash-checked and parsed from those same bytes; only the endpoint port is changed.

Validation:
- All nine supplied tests pass independently (including arbitrary IDs/images, failed and unsent blanks, fresh output, pins, call cap, wall budget, supervisor exclusion and scoped cleanup).
- Seven independent revised edge checks pass: missing usage, runtime mismatch, unknown finish and truncation each cause exactly one call, zero exported answers and two unsent IDs; one-call cap retains the successful first answer and two blanks; three clean calls export all three answers;101-call declaration is rejected.
- Additional guard checks pass: waiting crop, bounded and policy runners are detected with an empty GPU list; cleanup does not signal a different group even in the recorded namespace. Provider content remains exact in the failed raw row.

Code review: fresh output is confined to the owner private directory. Package/template IDs, images and prepared/config/script hashes are frozen and verified before inside execution. Original model/projector digests and sizes total7,556,497,632 bytes; version0.30.7 and loaded4096 context are required. No retries or warmup; call reservations are flushed before dispatch. Parent wall supervision bounds a stuck request. All template IDs survive finalization, failed/unsent answers blank, malformed partial JSONL requires explicit recovery review.

The server and requests share a new user/network namespace; only loopback and no external routes are accepted before server startup. The parent and child share an exclusive rehearsal lock. Cleanup signals only the owned server group, with the parent safety net additionally matching the recorded namespace; host daemon/firewall are not changed.

Runbook review: clearly separates dry preparation, guarded launcher execution, diagnostic direct commands and actual submission. The direct CLI is explicitly not an unattended deadline/concurrency guard. Scope and remaining runtime/organizer unknowns are stated. No May2025 package or other grader outputs were read.

Remaining gates: actual isolated Ollama/CUDA execution, runtime timing/context fit for the final package, exclusive queue declaration, final candidate choice and organizer acceptance are unproven. These CPU checks do not establish them. Parent finalization intentionally refuses malformed raw JSONL rather than silently repairing it.

Evidence is preserved privately in package-review-20260926/{initial-edge-results,guard-edge-results,revised-edge-results,initial-review-hashes,final-review-hashes}.json. Initial failures are retained as audit history, not unresolved findings.

Reviewed raw-byte SHA-256:
- `agentsLog/kwiscion/run_gemma_package.py`: `64ebf4a89c3538ead8a8a84cdea471655eb2c321974530ac6032c4a9fbea0611`
- `agentsLog/kwiscion/test_final_offline.py`: `3febbed373a6ddafc5e6153a7709c31d0371387737c14f250879c4943db96000`
- `agentsLog/kwiscion/SUNDAY_OPERATOR_RUNBOOK.md`: `0a7a8b43311c7d3bbfe6fb1b72631a8f86f04eebf615ff4a9348f1d9b6c49f81`
- `agentsLog/kwiscion/offline_rehearsal.py`: `45b888db42a1b64398bb0f824a3397b9d10e19e58059430c74a3afe63d1c98e3`
- `infer.py`: `b702857347fd0fa99b9aba9a844afca1a4a8634b22eaa826199d27986dca1f0a`
- `scripts/Bukareszt/matura_package.py`: `bec8b33731e24ff1ea845e7c7b0908d3227121986125cef8967fc384a1d8af74`
- `outputs/local-smoke/gemma4-12b-val40-1024.config.json`: `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`

Follow-up executable-path verification (26 September, after the initial review): the exact Python subprocess call `subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True)` ran successfully under actual WSL, exit0, returning `5abf977fe5bf01aeffd5f92890498d4feaf48ba7`. The equivalent `git -C ROOT rev-parse HEAD` also exited0. No ownership failure occurred, so no safe.directory override or Git configuration change was needed. The default tool sandbox denied WSL startup; the authorized escalated read-only probe succeeded. This verifies metadata execution in the present WSL identity, not server/model execution or portability to another machine.

The final runbook now says nine tests and documents launcher-validation failure flags with raw-response preservation. All nine CPU tests were rerun successfully after the follow-up. No runtime code or test edits were necessary.

Publication follow-up by the lead: removed one surplus blank line at the test file's EOF to pass `git diff --check`; no executable statement changed. Final test-file SHA-256 is `1f3bb3209e15990572c3919d4459dc93a92ce75efa89811b52d9c561b0da2dd6`. All nine CPU tests passed again on main after the independently accepted optional-temperature change. The actual generic launcher qualification also completed successfully; see `2026-09-26-final-launcher-qualification-result.md`. Earlier hashes identify the original review snapshot; the runbook was subsequently updated with this runtime evidence and new H100 assignment.
