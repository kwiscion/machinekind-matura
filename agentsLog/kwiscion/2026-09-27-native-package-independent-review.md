# Independent generic native organizer package CPU review

**CPU PASS for the frozen files below.** No remaining material blocker was found. This approves the code/preparation slice for a separately declared finite runtime qualification; a live model pass is not a prerequisite for this CPU approval. It is not final offline qualification, an exam score or candidate promotion.

| File under final-package-prep | SHA256 |
|---|---|
| run_native_package.py | `1bca2caef1f49ea83aa77c5970db2b9a00e26c02f28ee60a3c45af6663bd12f2` |
| prepare_native_package.py | `94c5cec3fd8d166543374c499c6fa60ca9ecbad41a6ff21bf03dd0e6a3979ad3` |
| test_native_package.py | `96df22c889f336466820f658f967274d0e0be47646bae95bd74c04fe853c2c8c` |
| NATIVE_PACKAGE.md | `57b19a82761fa8170182282b5713a4a5911d28a3e927474830f6a624b112c461` |
| run_gemma_offline.py | `d4f26d319b88d479ad3eaa0a7afe2d4ce68706e4dd75324e5d4d4d83fa1c036b` |

## Findings

- Preparation uses the real organizer adapter and only copies exam.json, the original answer template and referenced images, plus explicitly pinned dependencies. Unrelated files are excluded; generated packages must remain in the project-private directory. Source bytes, source/image order, original adapter prompts, Unicode and extra source fields survive. The actual received item count governs; the 101-item CPU fixture passes without a 40-item assumption.
- Essay routing is explicit through received item IDs or an explicit no-essay declaration. Unknown/duplicate/contradictory mapping fails. Ordinary caps are 10240, essay caps 20480; the sole essay addition exactly matches the established generic choose-one/400-500-word/clean-prose policy. Per-item original/routed prompt hashes, routes and aggregate caps are checked by reconstruction, not merely trusted after rehashing.
- Default invocation is file-only preflight. Execution requires a fresh declared manifest, exact root-referenced call/token/time authorization, aware UTC start/deadline and an explicit above-240k exception when relevant. Requested caps are reserved durably before transport. Absolute deadline and full-request/cleanup-window checks surround pre-request checks. HTTP redirects are refused, and no retries, warmups, downloads or fallback model calls are present.
- Normal execution automatically enters the pinned shell guardian. Its timeout is computed from the absolute deadline and reserves termination/cleanup time; the Python alarm starts before input/image preflight. The guarded entry checks the actual timeout parent. Lock, pinned runtime/aggregate cache, competing worker/GPU and unchanged idle host-daemon checks precede the child.
- The initial hidden inside entry trusted a caller-chosen parent PID. This was the sole material blocker found. The corrected entry verifies a recorded live supervisor's PID/start ticks, executable, exact runner/package arguments and host namespace; it verifies the actual timeout ancestry and pinned launch/weight receipts, then consumes the inherited anonymous-pipe challenge before namespace or server operations. The supervisor writes that evidence after the locked checks. This is a narrow accidental-bypass check, not a general authorization system for a malicious local operator who can edit the code.
- Terminal correctly accounted length, empty or adapter-invalid finals become explicit item failures and blank template entries, while dispatch may continue within the remaining bounds. Truncation flags, wrong runtime/model, usage/context errors, uncertain transport, ownership, pins or global failures stop new dispatch. Reservations retain failed calls. Unsent IDs remain blank.
- Finalization uses the real adapter, keeps its output separately, restores exact accepted native final strings including surrounding whitespace, and validates the final original-template submission. Embedded reasoning that would be removed is rejected instead of silently cleaned. No semantic correctness is inferred from format validity.
- The previously reviewed receipt-aware cleanup helper is pinned unchanged. Both parent and guardian paths use it; a valid receipt with absent recorded PIDs avoids broad fallback, while incomplete/tampered evidence retains strict recovery and uncertain ownership remains visible. The new code does not modify the old two-item package, original attempt or older bare runner.
- Runtime evidence and native reasoning/provider envelopes stay private. Only the explicit source package and known project dependencies are read/copied; no credentials are requested or imported from unrelated projects. Full cache aggregate size and source/rights rules remain applicable to any later final bundle.

## Independent focused CPU validation

The final frozen revision passed **14/14 tests on Windows** (12.105 seconds) and **14/14 on local WSL/Linux** (80.558 seconds). Commands used the test_native_package.py entry point with Python -B; Linux tests also check generated shell syntax. These are independent reruns, not merely author-reported results.

Coverage includes actual-adapter preparation/finalization; arbitrary N=101; explicit essay/no-essay mapping; complete image bytes and original Unicode source; template order and exact accepted finals; source/route tampering; reservation-before-send budgets; local error continuation; global error termination; zero dispatch on ownership/time failure; absolute/above-240k declarations; cleanup integration; redirect refusal; direct-inside refusal before Popen; and valid versus wrong inherited supervisor challenge. Existing helper cleanup tests were separately reviewed and passed in the linked cleanup review.

## Scope and handoff

Stop CPU review here and use a fresh bounded declaration for the next useful runtime qualification. Actual native serving/context behavior, network/process receipts, cleanup outcome, complete output validation and evidence backup remain runtime observations to collect. No requested model call, server start, GPU use or remote action was performed by this reviewer; no Git mutation or author-file edits were made. Only this report was written. The reviewed package directory already has -text byte preservation; this report uses LF.

The initial two-item semantic success/guardian failure remains attributable. Nothing in this CPU PASS changes historical exit status or adds recovered answers to the frozen exam score.

Reviewer: independent Sol `/root/full40_second_sol`; 2026-09-26T22:12:29.277817+00:00.
