# Winning plan

**Goal:** highest final history score; target48/60. Current champion: **Gemma4 12B Q4, 38/60** on known validation with legacy full-page images; preserved fallback35/60. Recovery rehearsal also38/60, with no blanks. Updated27September02:50. This is strategy, not a log; issues own tasks.

## Finish the harness, then improve answers

**Use the corrected inputs for the next visual run.** The supplied 37-item May2023 mock passes independent CPU input/export checks, including the essay-topic diagnostic fix: [commands and evidence](agentsLog/kwiscion/2026-09-27-mock2023-package-compatibility.md). May2024 now has a reviewed 40-item package with 21 source crops and corrected image links: [recipe and hashes](agentsLog/kwiscion/source-crops-prep/README.md). Old full-page runs remain immutable and their scores do not measure the cropped format. Next, measure the champion on the corrected visual inputs.

1. **Reuse the qualified autonomous harness.** Default60minutes; configurable120minutes, with10minutes reserved for recovery, validation and submission. Context65,536 and32,768 initial output ceiling are verified; short answers retain substantial reasoning. Adapt compute to time remaining, preserving complete text/images. No external agent participates in inference/recovery.
2. **No blank submission entries.** Preserve usable answers. After an empty, truncated, timed-out or malformed result, attempt at least3 retries: larger budget, thinking off, then bounded final-answer synthesis. Allocate recovery time before it is exhausted. If every attempt fails, use the owner's literal emergency fallback `Tadeusz Kościuszko`; mark it as a placeholder, never a successful recovery. Record any hard-deadline exception.
3. **Rehearsal complete; improve quality.**46calls, about20minutes,40/40 nonblank,0placeholders; all3 failures recovered and offline packaging/cleanup passed. Score38/60: nonessay31, essay7. Larger budgets alone gave no net gain. Automatic essay feedback/candidate preservation is corrected; quality gain remains unproven. Do not repeat full rehearsals per candidate.
4. **Change mechanisms when experiments fail.** Generic zoom tied1/6 versus1/6 with more tokens; keep it out of the default. The legacy-input Qwen/Gemma comparison completed all12answers in14calls; masked grading is pending. Prioritize structured reasoning and essay planning→prose; prepare per-topic essay drafts plus same-model selection to distinguish candidate quality from selector quality. Use one fast grading pass; second only for consequential uncertainty.
5. **Measure the trained essay LoRA.**36 training steps completed; merged export fits and serves text/images. Compare16 separate evaluation inputs against its matched untrained export in one grading pass. Training loss is not quality. Promote only with argument gain and acceptable factual/nonessay regressions; essay-only adapter switching remains unproven.

## Owners

| Owner | Work |
|---|---|
| Root + Sol | Compatibility [#170](https://github.com/kwiscion/machinekind-matura/issues/170) and crops [#171](https://github.com/kwiscion/machinekind-matura/issues/171) reviewed; grade legacy pair [#95](https://github.com/kwiscion/machinekind-matura/issues/95), then corrected-input champion diagnostic |
| Root Sol | Essay branching prep [#168](https://github.com/kwiscion/machinekind-matura/issues/168) waits behind input correction |
| Paweł | Claim-triggered offline fact-check preparation [#163](https://github.com/kwiscion/machinekind-matura/issues/163); claim pending |
| Greg | LoRA pilot [#117](https://github.com/kwiscion/machinekind-matura/issues/117) |
| Łukasz | Structured-reasoning comparison [#151](https://github.com/kwiscion/machinekind-matura/issues/151); evaluation notes complete |
| Piotrek | Essay-only adapter serving feasibility [#165](https://github.com/kwiscion/machinekind-matura/issues/165); CPU claim pending |
| Przemek | Standby; root owns the central Qwen worker |

## Final constraints

One shared weight set: Gemma package7,556,509,301bytes; aggregate cap8,800,000,000bytes. Offline inference. No held-out training/retrieval, purchases or duplicate GPU workers. Preserve evidence and bound runtime/cost; old no-retry and double-grading policies are superseded.

**Requesting final questions freezes ALL team projects.** Commit code/prompts/settings and finish rehearsals before access; afterwards only run the frozen solution and submit. Planned freeze27September11:00Warsaw, earlier if access is requested. May2025 remains sealed. [Submission page](https://warsawmodeltrainers.dev/submissions.html?exam=final). Detailed tasks/results: GitHub issues and agentsLog; [previous plan](agentsLog/kwiscion/2026-09-27-plan-before-harness-priority.md).
