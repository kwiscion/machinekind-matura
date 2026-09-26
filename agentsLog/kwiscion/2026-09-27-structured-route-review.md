# Structured routes — independent CPU review

**PASS as a bounded CPU handoff for issue151.** The semantic modules are ready for shared-session integration; no model-quality or executable live-integration result is claimed.

Independently ran22 route tests,2 driver tests and the actual four-case source/image assembly check: all passed. Checked budget arithmetic and every declared dependency/input pin. The active panel is three already-exposed May2024 validation items plus one original DEV essay; parked extension items are not dispatched.

The source loader verifies exact task text and complete image hashes/order. Each invocation receives a deep copy of the original case; source assembly remains the shared invoker's responsibility. Stage types keep plans, observations and selector envelopes outside final-answer candidates. Essay writer plan envelopes are rejected; eligible short prose may survive as explicitly incomplete. Closed candidates are independent, retained exactly, and selection must identify an available candidate without changing its text. NEW answers remain separately labelled. Invalid selection now fails the pure semantic validator inside the intended retry boundary, with deterministic retained-candidate fallback after exhaustion. Fatal stops preserve the eight-slot denominator.

Review findings were corrected in study-owned files: route events now carry arm/case identity; selector validation receives exact candidate context; freeze pins cover the actual modules, imported parser dependencies and essay aspect metadata; stale budget/fallback prose was reconciled.

The budget is internally consistent:16 primary slots (14 thinking,2 direct),466944 initial requested tokens, at most64 attempts and1409024 requested tokens. Thinking profiles are32768/49152/8192/8192; direct writers are4096 per attempt. Matching240-second nonessay and600-second essay windows total2640seconds across both arms. The separate600-second scheduling/quiescence reserve plus360-second setup/export/cleanup allowance makes3600seconds. The ambiguous300-second per-arm field has been removed. The global reserve cannot extend matched generation windows.

Issue151 needs only the documented integration work:

1. Expose one typed stage operation in the existing owned session and reservation ledger, keyed by arm-specific case ID, stage and attempt. Compose full original text/images with the frozen suffix; pin each dependent request before dispatch.
2. Apply native checks and the semantic validator within the same three-retry ladder. Preserve direct/thinking profiles, eligible partials and exact candidate strings; keep typed intermediates outside organizer export. Quiescence failure stops later dispatch.
3. Enforce one deadline per arm-item and the whole run, including cold load. Admit the exact stage/call/token envelope; record deadline exceptions. Freeze all eight final slots and retain unsent outcomes.
4. Run focused combined CPU checks for selector retries, intermediate exclusion, source completeness, one ledger, deadlines and final-slot preservation. Reuse the existing runtime/guardian evidence; this review requests no additional standalone GPU qualification. A fresh bounded root declaration governs the eventual four-case study.

One fast grading pass should report achieved selected scores separately from the oracle over independent c1/c2/c3. Selector-created NEW answers are excluded from that oracle and reported separately. The same applies to draft/coverage and interpretation/revisit changes.

Exact reviewed SHA256 pins:

- `structured_routes.py`: `44340c0572e82999ac074f47fb8e5810d777cdea37e855298d55e5c11ef3bb18`
- `study_driver.py`: `493df23c67c426323537ecbcb1e03231d842c8ca921a8b51186081558a447346`
- `prompt-study-budget-v2.json`: `f09bbfc7da51fa671f2411e0cacc0a155893d1b0b22d22709198bc22ea8c2b5a`
- `STRUCTURED_HANDOFF.md`: `27d5417692ffd85c41b04945859effe1adfeeebc45d96d282658d51ec8729d32`
- `SHARED_RUNTIME_INTEGRATION.md`: `2045383915f7f43f0e197bd96578e1706740af8461d30416f51fd1dd154369d2`
- `test_structured_routes.py`: `bd8060ef4d5f7c6bf2c5b8c379c036e239972ed7ef54d8618d4e8757636ec1a5`
- `test_study_driver.py`: `06fcd24469bdd74095217aba04304ad2bae1b56af307c1cc3da557a0d465fcca`

Review used local CPU checks only. The live central harness, its frozen files and Git were untouched; zero model calls or final-access requests. Source passages, images and keys are not included in this report.
