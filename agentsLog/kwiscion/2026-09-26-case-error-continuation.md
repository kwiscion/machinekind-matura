# Issue 100: opt-in continuation after case-local generation failure

`run_gemma_package.py --continue-case-errors` permits the next original item after a narrowly recognized generation failure. Without the flag, the existing stop-on-error behavior remains unchanged. The launch record freezes the flag; old records default to false.

Eligible responses must have the successful-transport runner shape, exactly one choice, an explicit `length` finish or `stop` with empty final content, no provider error/refusal/tool request, valid bounded integer token usage, no reported context truncation, and verified loaded model/context. Unknown finish reasons, malformed responses, transport/auth/server errors, changed pins, competing workers, usage failures, runtime/context mismatch and exhausted budgets still stop. Frozen files are rechecked before each reservation.

A continued case retains its original raw provider envelope and an error; the adapter emits a blank for that ID. Later original IDs are attempted once within the same call/time/token limits. No retries, repaired answers, resumed attempts, model calls or candidate promotion are introduced. The final command still returns failure when the finalized package has failed answers, even when every item was attempted.

## CPU verification

Run from the repository root under Linux/WSL:

```sh
python3 -m unittest discover -s agentsLog/kwiscion -p test_final_offline.py -q
python3 -m unittest discover -s agentsLog/kwiscion -p test_runtime_profile.py -q
python3 -m unittest discover -s agentsLog/kwiscion -p test_offline_rehearsal.py -q
```

Results: 14 launcher tests, 15 runtime-profile tests and 6 rehearsal-helper tests pass. Synthetic cases cover length/empty/reasoning-only finals followed by a good essay, all original IDs exactly once, unchanged raw envelopes, blank failed output, no extra reservation/retry, unchanged default, frozen opt-in, strict malformed/transport/provider/runtime/context/usage stops, and call/deadline/worker/pin gates.

The Windows-native suite encounters the existing Linux model-cache path assumption in runtime-profile validation; verification was performed in WSL, the launcher's supported environment. All transport, server and GPU interactions in these tests are mocked. Exact-head independent review remains required before merge or operational use. Completed experiments remain immutable.

Independent-review follow-up: both explicit top-level `truncated` and `context_truncated` response flags stop dispatch, including otherwise eligible length errors. Both are covered by the strict-stop regression. The launcher tests create their private temporary parent in a fresh checkout.
