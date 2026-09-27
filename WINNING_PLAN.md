# Winning plan

**Goal:** highest final history score; target48/60. Current champion: **Gemma4 12B Q4, 38/60** on known validation with legacy full-page images; preserved fallback35/60. Recovery rehearsal also38/60, with no blanks. Updated27September03:08. This is strategy, not a log; issues own tasks.

## Finish the harness, then improve answers

**Use the corrected inputs for the next visual run.** The supplied 37-item May2023 mock passes independent CPU input/export checks, including the essay-topic diagnostic fix: [commands and evidence](agentsLog/kwiscion/2026-09-27-mock2023-package-compatibility.md). May2024 now has a reviewed 40-item package with 21 source crops and corrected image links: [recipe and hashes](agentsLog/kwiscion/source-crops-prep/README.md). Old full-page runs remain immutable and their scores do not measure the cropped format. Next, measure the champion on the corrected visual inputs.

1. **Reuse the qualified autonomous harness.** Default60minutes; configurable120minutes, with10minutes reserved for recovery, validation and submission. Context65,536 and32,768 initial output ceiling are verified; short answers retain substantial reasoning. Adapt compute to time remaining, preserving complete text/images. No external agent participates in inference/recovery.
2. **No blank submission entries.** Preserve usable answers. After an empty, truncated, timed-out or malformed result, attempt at least3 retries: larger budget, thinking off, then bounded final-answer synthesis. Allocate recovery time before it is exhausted. If every attempt fails, use the owner's literal emergency fallback `Tadeusz Kościuszko`; mark it as a placeholder, never a successful recovery. Record any hard-deadline exception.
3. **Rehearsal complete; improve quality.**46calls, about20minutes,40/40 nonblank,0placeholders; all3 failures recovered and offline packaging/cleanup passed. Score38/60: nonessay31, essay7. Larger budgets alone gave no net gain. Automatic essay feedback/candidate preservation is corrected; quality gain remains unproven. Do not repeat full rehearsals per candidate.
4. **Change mechanisms when experiments fail.** Generic zoom tied1/6 versus1/6 with more tokens; keep it out of the default. Native Qwen scored6/8 [6,7] against Gemma4/8 [3,4] on the legacy six-item panel; it earns a full corrected-input challenge, not promotion. Prioritize structured reasoning and essay planning→prose; prepare per-topic essay drafts plus same-model selection to distinguish candidate quality from selector quality. Use one fast grading pass; second only for consequential uncertainty.
5. **Reject the unstable LoRA; test only a justified repair.** The3-epoch candidate produced2 complete essays,2 runaway partials and12 unattempted placeholders; its matched control completed16/16. It cannot be deployed. Grade the two complete pairs once for any argument benefit before deciding on a one-epoch pilot; otherwise park training and prioritize base-model composition. Essay-only adapter switching remains unproven.

## Owners

| Owner | Work |
|---|---|
| Root + Sol | Corrected-input Gemma40 live on central H100 [#173](https://github.com/kwiscion/machinekind-matura/issues/173); prepared Qwen40 next [#95](https://github.com/kwiscion/machinekind-matura/issues/95) |
| Root Sol | Reviewed essay branching [#168](https://github.com/kwiscion/machinekind-matura/issues/168), staging on reserved matura-lukasz |
| Paweł | Claim-triggered offline fact-check preparation [#163](https://github.com/kwiscion/machinekind-matura/issues/163); claim pending |
| Greg | CPU preparation for possible shorter pilot [#117](https://github.com/kwiscion/machinekind-matura/issues/117); no new training/inference yet |
| Łukasz | Awaiting WIP/blocker handoff [#151](https://github.com/kwiscion/machinekind-matura/issues/151); old launch window expired, host temporarily reserved for #168 |
| Piotrek | Adapter serving [#165](https://github.com/kwiscion/machinekind-matura/issues/165) secondary while checkpoint is rejected |
| Przemek | GPU occupied by other work; preserve it |

## Final constraints

One shared weight set: Gemma package7,556,509,301bytes; aggregate cap8,800,000,000bytes. Offline inference. No held-out training/retrieval, purchases or duplicate GPU workers. Preserve evidence and bound runtime/cost; old no-retry and double-grading policies are superseded.

**Requesting final questions freezes ALL team projects.** Commit code/prompts/settings and finish rehearsals before access; afterwards only run the frozen solution and submit. Planned freeze27September11:00Warsaw, earlier if access is requested. May2025 remains sealed. [Submission page](https://warsawmodeltrainers.dev/submissions.html?exam=final). Detailed tasks/results: GitHub issues and agentsLog; [previous plan](agentsLog/kwiscion/2026-09-27-plan-before-harness-priority.md).
