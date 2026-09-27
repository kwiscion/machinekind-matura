# Winning plan

**Goal:** highest final history score; target **48/60**. Provisional final choice: **Qwen with coverage essay prompt,40/60**, versus Gemma39/60. Target not reached. These are single-agent grades on known validation, with a narrow advantage rather than a proven generalization gain. Updated 27 September, 07:15 Warsaw. Issues own detailed tasks; this file stays short.

## Hard schedule

- **Now–07:00:** parallel experiments, immediate delegation to local Sol agents if teammates do not acknowledge. Verify host ownership before starting; never wait on an unclaimed task.
- **07:00–07:40:** finish only bounded runs already justified; collect answers and one-pass grades. No run may extend beyond 07:40.
- **07:40–08:00:** choose and integrate the best measured system, commit model/prompt/runtime pins and package it.
- **08:00–11:00:** final checks and final execution/submission only. No new performance experiments. Requesting final questions freezes ALL team projects; access them only after code/prompts/settings are frozen.

## Priority order

1. **Package the measured leader:** Qwen coverage ([#95](https://github.com/kwiscion/machinekind-matura/issues/95)) scored40/60 (32/45 nonessay +8/15 essay),40/40 complete, zero placeholders,44calls/28minutes; all4timeouts recovered automatically. Gemma39/60 remains fallback. The separate11/15 essay did not reproduce: this run added factual errors and weakened the economic argument. Do not report posthoc44/60 as measured.
2. **Finish generic final integration** ([#3](https://github.com/kwiscion/machinekind-matura/issues/3)): apply the exact tested essay suffix to explicit essay IDs in any organizer package, preserve other questions and all sources/images, retain qualified recovery. Root Sol implements; root independently reviews and freezes one model/prompt/runtime set.
3. **Full-corpus RAG measured:** all1,587,721 Polish Wikipedia articles/2,729,746 passages indexed ([#184](https://github.com/kwiscion/machinekind-matura/issues/184)). Correctly staged query/filter pipeline ([#182](https://github.com/kwiscion/machinekind-matura/issues/182)) scored direct3/6 versus filtered4/6: two gains, one regression. It remains exploratory; no full-exam improvement established. Earlier107-article results do not measure this corpus. Essay RAG ([#183](https://github.com/kwiscion/machinekind-matura/issues/183)) missed preparation cutoff; no GPU run.
4. **Reject unhelpful additions:** Greg's three-view images ([#178](https://github.com/kwiscion/machinekind-matura/issues/178)) scored direct4/9 versus three-view3/9; extra descriptions lost a correct identification. Factual candidate/referee experiment ([#186](https://github.com/kwiscion/machinekind-matura/issues/186)) exported7/12, unchanged from direct; alternate candidates5/12. Preserve evidence without importing these runners into final inference.
5. **Keep essay gains honest:** generic coverage improved Gemma8→10/15; strict-ID parser replay selected an existing11/15 draft. Qwen free-topic coverage scored11/15. These are subset/replay results until confirmed in an integrated full run; no cross-model answer selection.

## Operating rules

Use existing qualified recovery: 65,536 context, substantial output budgets, 60-minute default/120-minute final option, ten-minute reserve, complete original inputs, and no external agent intervention during inference. Preserve usable answers; attempt up to three recovery retries, then the explicitly marked emergency `Tadeusz Kościuszko` fallback if necessary. Never submit blank entries. The full recovery rehearsal is done; only qualify affected changes, not another full rehearsal per candidate.

Freeze finite call/token/time/cost bounds before each run. One fast grading pass; repeat only for consequential uncertainty. Prefer large, testable changes over marginal tuning. **Park the unstable3-epoch essay LoRA** (2/16 complete versus16/16 control); no further training without new evidence. Generic RAG and generic zoom have not earned promotion.

GPU experiments are now terminal; prioritize their grades, backups and final integration over another speculative run. Central: Qwen score; Greg/Lukasz: image-result review and handoff; Pawel: RAG result and generic final wrapper. Przemek is occupied by other work and remains untouched. Never restart a worker because observation timed out. The existing15-minute heartbeat is active until08:00, then reports and pauses.

## Final constraints

**Aggregate saved weights ≤8,800,000,000 bytes**, including every projector/adapter. Gemma7,556,509,301 bytes; Qwen6,594,475,420 bytes separately. They cannot both be submitted. All expert calls reuse the chosen single weight set. Final inference is offline. No held-out training/retrieval, compute purchases, reset-credit redemption or unrelated-project credentials. May2025 remains sealed until an explicit release after candidate freeze. Detailed evidence and ownership: GitHub issues and agentsLog.
