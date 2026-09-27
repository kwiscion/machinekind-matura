# Winning plan

**Goal:** highest final history score; target **48/60**. Current corrected-input Gemma scores **39/60** in one agent grading pass (31 nonessay +8 essay; 40 complete answers). Legacy38 remains preserved. Updated 27 September, 04:10 Warsaw. Issues own detailed tasks; this file stays short.

## Hard schedule

- **Now–07:00:** parallel experiments, immediate delegation to local Sol agents if teammates do not acknowledge. Verify host ownership before starting; never wait on an unclaimed task.
- **07:00–07:40:** finish only bounded runs already justified; collect answers and one-pass grades. No run may extend beyond 07:40.
- **07:40–08:00:** choose and integrate the best measured system, commit model/prompt/runtime pins and package it.
- **08:00–11:00:** final checks and final execution/submission only. No new performance experiments. Requesting final questions freezes ALL team projects; access them only after code/prompts/settings are frozen.

## Priority order

1. **Corrected Gemma40 is complete and scored39/60** ([#173](https://github.com/kwiscion/machinekind-matura/issues/173)); exact outputs and runtime are backed up. Lost points: history7, source interpretation6, incomplete identification1, essay depth7. No blank losses. This is a known-validation agent grade, not an organizer score.
2. **Score the running corrected Qwen40** ([#95](https://github.com/kwiscion/machinekind-matura/issues/95)), deadline05:01 Warsaw on central H100. It beat Gemma6/8 versus4/8 on the small known panel; full results determine promotion. Prepare arbitrary organizer-package support in parallel.
3. **Essay branching is running** on reserved `matura-lukasz` ([#168](https://github.com/kwiscion/machinekind-matura/issues/168)), deadline05:05: direct control plus one draft per offered topic, then same-model selection/revision. Grade candidates and selected final once; distinguish best candidate from selector performance. If argument gains are weak, test an explicit evidence-and-causality policy next.
4. **Three-view image reasoning** ([#178](https://github.com/kwiscion/machinekind-matura/issues/178), Greg; local fallback if unclaimed): independent same-model text/transcription, small-detail and overall-composition descriptions, then answer with the complete original question/image and all three fallible views. Matched direct control, fixed visual subset, no extra model weights.

## Operating rules

Use existing qualified recovery: 65,536 context, substantial output budgets, 60-minute default/120-minute final option, ten-minute reserve, complete original inputs, and no external agent intervention during inference. Preserve usable answers; attempt up to three recovery retries, then the explicitly marked emergency `Tadeusz Kościuszko` fallback if necessary. Never submit blank entries. The full recovery rehearsal is done; only qualify affected changes, not another full rehearsal per candidate.

Freeze finite call/token/time/cost bounds before each run. One fast grading pass; repeat only for consequential uncertainty. Prefer large, testable changes over marginal tuning. **Park the unstable3-epoch essay LoRA** (2/16 complete versus16/16 control); no further training without new evidence. Generic RAG and generic zoom have not earned promotion.

Root dispatches three local Sol workers for runtime, grading/review and essay/image implementation. Check teammate issue claims once and assign useful bounded work immediately; unavailable teammates are not dependencies. Preserve Przemek's GPU, last observed occupied by other work. Never duplicate a live worker or restart one because observation timed out.

## Final constraints

**Aggregate saved weights ≤8,800,000,000 bytes**, including every projector/adapter. Gemma7,556,509,301 bytes; Qwen6,594,475,420 bytes separately. They cannot both be submitted. All expert calls reuse the chosen single weight set. Final inference is offline. No held-out training/retrieval, compute purchases, reset-credit redemption or unrelated-project credentials. May2025 remains sealed until an explicit release after candidate freeze. Detailed evidence and ownership: GitHub issues and agentsLog.
