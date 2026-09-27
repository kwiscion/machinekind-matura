# Winning plan

**Goal:** highest final history score; target **48/60**. Corrected Gemma leads at **39/60**; Qwen scores **36/60**, with stronger nonessay answers but a weak essay. These are agent grades on known validation. Updated 27 September, 04:55 Warsaw. Issues own detailed tasks; this file stays short.

## Hard schedule

- **Now–07:00:** parallel experiments, immediate delegation to local Sol agents if teammates do not acknowledge. Verify host ownership before starting; never wait on an unclaimed task.
- **07:00–07:40:** finish only bounded runs already justified; collect answers and one-pass grades. No run may extend beyond 07:40.
- **07:40–08:00:** choose and integrate the best measured system, commit model/prompt/runtime pins and package it.
- **08:00–11:00:** final checks and final execution/submission only. No new performance experiments. Requesting final questions freezes ALL team projects; access them only after code/prompts/settings are frozen.

## Priority order

1. **Corrected Gemma40 is complete and scored39/60** ([#173](https://github.com/kwiscion/machinekind-matura/issues/173)); exact outputs and runtime are backed up. Lost points: history7, source interpretation6, incomplete identification1, essay depth7. No blank losses. This is a known-validation agent grade, not an organizer score.
2. **Full Polish Wikipedia is indexed** ([#184](https://github.com/kwiscion/machinekind-matura/issues/184), root Sol on `matura-pawel`): all 1,587,721 articles and 2,729,746 passages from the complete cleaned November 2023 Polish snapshot. Qualify retrieval and run independent top-five relevance filtering on nonessays ([#182](https://github.com/kwiscion/machinekind-matura/issues/182)), then six-query essay research ([#183](https://github.com/kwiscion/machinekind-matura/issues/183)). Earlier retrieval had only 107 articles; its negative result does not measure full-corpus RAG.
3. **Improve Qwen essays on central H100** ([#95](https://github.com/kwiscion/machinekind-matura/issues/95)): the full run scored 33/45 nonessay +3/15 essay, versus Gemma 31+8. A four-case coverage-prompt diagnostic is running. Keep models separate; no cross-model answer selection or combined submission.
4. **Essay experiments on `matura-lukasz`:** branching ([#168](https://github.com/kwiscion/machinekind-matura/issues/168)) produced an 11/15 draft, but its selector returned 6/15 versus the direct control's 8/15. Reject that selector. The coverage prompt improved its matched control from 8/15 to 10/15. Strict candidate-ID selection chose the 11/15 draft but failed on fenced JSON; a generic parser repair is being qualified. Next: evidence-led writing using the full corpus.
5. **Three-view image reasoning** ([#178](https://github.com/kwiscion/machinekind-matura/issues/178), Greg claimed): independent same-model text, detail and overview descriptions; answer with complete original inputs and all three fallible views. Matched direct control, fixed visual subset, no extra model weights.

## Operating rules

Use existing qualified recovery: 65,536 context, substantial output budgets, 60-minute default/120-minute final option, ten-minute reserve, complete original inputs, and no external agent intervention during inference. Preserve usable answers; attempt up to three recovery retries, then the explicitly marked emergency `Tadeusz Kościuszko` fallback if necessary. Never submit blank entries. The full recovery rehearsal is done; only qualify affected changes, not another full rehearsal per candidate.

Freeze finite call/token/time/cost bounds before each run. One fast grading pass; repeat only for consequential uncertainty. Prefer large, testable changes over marginal tuning. **Park the unstable3-epoch essay LoRA** (2/16 complete versus16/16 control); no further training without new evidence. Generic RAG and generic zoom have not earned promotion.

Keep all available project H100s assigned; use local Sol workers when teammates are unavailable. Central: Qwen/verification; Greg: images; Lukasz: essays; Pawel: full-corpus retrieval. Przemek is verified occupied by other work and remains untouched. Never duplicate a live worker or restart one because observation timed out. Ranked next ideas live in the last-effort experiment report, not this plan.

## Final constraints

**Aggregate saved weights ≤8,800,000,000 bytes**, including every projector/adapter. Gemma7,556,509,301 bytes; Qwen6,594,475,420 bytes separately. They cannot both be submitted. All expert calls reuse the chosen single weight set. Final inference is offline. No held-out training/retrieval, compute purchases, reset-credit redemption or unrelated-project credentials. May2025 remains sealed until an explicit release after candidate freeze. Detailed evidence and ownership: GitHub issues and agentsLog.
