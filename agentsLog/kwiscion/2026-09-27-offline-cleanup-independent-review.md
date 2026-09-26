# Independent offline cleanup fix review

**CPU PASS for the exact cleanup patch below.** No remaining material blocker was found in the bounded fix. This does not rerun or retrospectively upgrade the original operator exit, establish a new runtime qualification, or approve final submission.

| Reviewed artifact | SHA256 |
|---|---|
| final-package-prep/run_gemma_offline.py | `d4f26d319b88d479ad3eaa0a7afe2d4ce68706e4dd75324e5d4d4d83fa1c036b` |
| final-package-prep/test_offline.py | `3060bb33b2b066c5afd488aa1aaf3901b3edae243b497c0e05abf003c8351fdc` |
| final-package-prep/operator_offline.sh (unchanged) | `7ed0d33b971101c196fa0bf7b43e08df2c105894d20342cc36bd18b19202f122` |

## Findings

- Parent execution cleanup and shell-invoked cleanup now share `cleanup_from_receipts`. A fast-path receipt must match the separate server identity exactly, match the recorded isolated namespace, contain valid positive integer PIDs and start ticks, a member list and recognized terminal status. The server plus every recorded group member must be absent. The fast path does not enumerate unrelated processes or send signals.
- `process_absent` uses `lstat` and catches only FileNotFoundError. Permission uncertainty is not silently reclassified as absence. A live/reused recorded PID prevents fast-path success without signaling it; operators receive an explicit identity-diagnosis failure.
- Missing/partial/invalid JSON receipts and structurally invalid, mismatched or unrecognized-status receipts use the existing independent-proof namespace fallback. An initial patch rejected mismatched receipts before recovery; this review raised that as a blocker, and the frozen revision corrects it. Non-dict identity data also uses fallback instead of failing accidentally on `.get`.
- Crash fallback retains namespace/runtime/start-time checks, host-namespace refusal and foreign-UID filtering. Inability to inspect a potentially owned process remains a visible error. No unconditional PermissionError suppression was added.
- AST comparison against immutable package-v4 finds changes to existing functions only in `execute` and `main`, plus the two new cleanup helpers. Model payload, token/call budgets, transport, semantics, namespace setup and original inner cleanup are unchanged. Original package-v4 runner SHA remains `c699adf93fa9f1d790d25219fb7de8ace508ba71516108c168fddcbcd389b15b`; original prepared launch SHA remains `a46b055f06dd8884c8a8ebba2e14cc67f68003ba1c0b131363dc49d4b1e2d5a2`. The original attempt was not edited or reclassified.

## Independent CPU verification

- Windows: 17/17 unit tests passed with bundled Python, `-B -m unittest discover -s agentsLog/kwiscion/final-package-prep -p test_offline.py -v`.
- Local WSL/Linux: the same 17/17 tests passed independently. Initial sandbox WSL startup was denied; the approved local CPU-only retry passed. No remote action was involved.
- A separate reviewer probe exercised the real `process_absent` helper with mocked `lstat`: both recorded PIDs returned FileNotFoundError, any unrelated inspection raised PermissionError, and broad enumeration was forbidden. Cleanup returned verified-completed mode, checked both recorded PIDs and did not invoke fallback.
- Regression coverage includes complete receipt plus protected unrelated proc, missing/partial receipt, tampered ticks/non-dict identity/bad status, live/reused recorded PID refusal, permission uncertainty, missing-receipt crash fallback, foreign UID and host namespace. Existing real-adapter mocked dispatch/semantic checks remain passing.

The frozen files are covered by the existing `final-package-prep/** -text` rule. Any later execution requires a newly prepared and explicitly declared package carrying the reviewed new hash; do not modify package-v4 or the preserved attempt to make its historical guardian exit appear successful. No extra model calls are authorized by this review.

Reviewer: independent Sol `/root/full40_second_sol`. 2026-09-26T22:02:55.764185+00:00. CPU tests/static inspection only; no model, server, GPU, remote action or Git mutation. Only this review note was authored, with LF line endings.
