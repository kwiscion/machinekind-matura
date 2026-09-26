# Winning plan

**Goal:** highest Sunday history-matura score; target 48/60. Best complete known-validation result: **38/60, independently reviewed**. Preserved fallback: 35/60. Final offline qualification is unfinished. Freeze: **27 September, 11:00 Europe/Warsaw**. Updated 26 September, 23:45. Consult this page before dispatch or promotion; issues own tasks and claims.

## One model, better answers

The **entire submitted weight set** must fit 8 GB + 10%; our conservative cap is 8,800,000,000 bytes. The verified Gemma 4 12B Q4 cache, including projector and metadata, is 7,556,509,301 bytes. Reuse those weights across question-specific prompts, planning and review. No Gemma+Qwen/Bielik fleet or two full essay/base copies. Other models remain development challengers. [Rule](docs/SUBMISSION_WEIGHT_BUDGET.md).

## Three priorities

1. **Finish the executable submission.** Qualify isolated text/image inference, integrate the complete organizer path, and preserve the 35-point fallback. The 38-point result loses 6 points to empty finals; a separate retry recovered only 1/6, and reasoning-note recovery 0/6. Neither is promoted.
2. **Improve essay arguments.** One topic, 400-500 body words, clean prose. Native thinking helped an independent panel 52/90 to 62/90; factual span editing showed no aggregate gain. Test explicit evidence-and-causality planning before writing. The full-exam essay is 8/15, losing 7 argument points.
3. **Test training, without multiplying models.** 90 cleared rows and 16 separate evaluation inputs are ready. Greg builds the missing serving runtime before a bounded LoRA pilot. Deploy one merged model with nonessay regression checks, or a proven adapter on one shared base; compare against the same export pipeline.

## Owners

| Owner | Live responsibility |
|---|---|
| @kwiscion + Sol | Integration, package qualification and freeze [#3](https://github.com/kwiscion/machinekind-matura/issues/3) |
| @Pewciu6 | Argument planning versus thinking essays [#80](https://github.com/kwiscion/machinekind-matura/issues/80) |
| @Bukareszt | Bounded single-model LoRA pilot [#117](https://github.com/kwiscion/machinekind-matura/issues/117) |
| @ljaniec | Source-grounded essay evaluation checklist [#143](https://github.com/kwiscion/machinekind-matura/issues/143) |
| @semberecki | Standalone Qwen thinking challenger [#95](https://github.com/kwiscion/machinekind-matura/issues/95) |
| @przemeknowak781 | Standby; Bielik proxy complete [#97](https://github.com/kwiscion/machinekind-matura/issues/97) |

## Guardrails

Park generic RAG/policy, multiscale and heterogeneous observation: no replicated gain. One claimed worker per host; bounded calls/time/cost and backed-up evidence. Pivot after uninformative failures. Promotion requires a complete organizer-path result, independent grading and actual offline/aggregate-size qualification. May 2025 stays sealed; no held-out training/retrieval, purchases or reset credits.

Details: [score reconciliation](agentsLog/kwiscion/2026-09-26-full-thinking-review-reconciliation.md), [package evidence](agentsLog/kwiscion/2026-09-26-final-package-stage.md), [history](agentsLog/kwiscion/2026-09-26-plan-history-through-2200.md), [operator runbook](agentsLog/kwiscion/SUNDAY_OPERATOR_RUNBOOK.md). Keep this page short; put tasks in issues and results in agentsLog.
