# Winning plan

**Goal:** highest final history score; target48/60. Current champion: **Gemma4 12B Q4, 38/60** on known validation; preserved fallback35/60. Updated27September00:45. This is strategy, not a log; issues own tasks.

## Finish the harness, then improve answers

1. **One reusable, timed harness.** Default60minutes; configurable120minutes if available, with10minutes reserved for recovery, validation and submission. Measure throughput and qualify larger context/output limits; short answers can need substantial reasoning. Adapt compute to time remaining, preserving complete question text and images.
2. **No blank submission entries.** Preserve usable answers. After an empty, truncated, timed-out or malformed result, attempt at least3 retries: larger budget, thinking off, then bounded final-answer synthesis. Allocate recovery time before it is exhausted. If every attempt fails, use the owner's literal emergency fallback `Tadeusz Kościuszko`; mark it as a placeholder, never a successful recovery. Record any hard-deadline exception.
3. **One champion end-to-end rehearsal.** Exercise the actual organizer package/answers path, forced failure recovery, schema/IDs, essay constraints and timing. Report score, blanks, placeholders, recovered items and elapsed time. Keep this harness for later candidates; repeat only checks affected by a change.
4. **Better prompts and purposeful extra calls.** Test evidence/causal planning, closed-answer disagreement resolution, open-answer coverage checks and essay planning→prose. Compare candidate quality with selector quality. Prefer large mechanism changes over wording sweeps. Use one fast grading pass; second review only for consequential uncertainty.
5. **Finish the essay LoRA pilot.**90 training rows/16 separate evaluation inputs; real backward works. Judge argument gain and factual errors. Use one merged model with regression checks, or prove essay-only adapter switching on one shared base.

## Owners

| Owner | Work |
|---|---|
| Root + Sol | Recovery/context/deadline harness and champion rehearsal [#3](https://github.com/kwiscion/machinekind-matura/issues/3) |
| Root Sol; Paweł grading standby | Structured prompt/essay experiments [#80](https://github.com/kwiscion/machinekind-matura/issues/80) |
| Greg | LoRA pilot [#117](https://github.com/kwiscion/machinekind-matura/issues/117) |
| Łukasz | Structured-reasoning comparison [#151](https://github.com/kwiscion/machinekind-matura/issues/151); evaluation notes complete |
| Piotrek / Przemek | Standby; Qwen preparation parked while harness takes priority |

## Final constraints

One shared weight set: Gemma package7,556,509,301bytes; aggregate cap8,800,000,000bytes. Offline inference. No held-out training/retrieval, purchases or duplicate GPU workers. Preserve evidence and bound runtime/cost; old no-retry and double-grading policies are superseded.

**Requesting final questions freezes ALL team projects.** Commit code/prompts/settings and finish rehearsals before access; afterwards only run the frozen solution and submit. Planned freeze27September11:00Warsaw, earlier if access is requested. May2025 remains sealed. [Submission page](https://warsawmodeltrainers.dev/submissions.html?exam=final). Detailed tasks/results: GitHub issues and agentsLog; [previous plan](agentsLog/kwiscion/2026-09-27-plan-before-harness-priority.md).
