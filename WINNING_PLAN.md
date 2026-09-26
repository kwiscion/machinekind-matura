# Winning plan

**Goal:** the highest Sunday history-matura score. Target 48/60. Leading experiment:38/60, pending second review and final packaging; preserved fallback:35/60. Final freeze: **27 September, 11:00 Europe/Warsaw**. Updated 26 September, 23:08. Read this before dispatch or promotion; GitHub issues own tasks and claims.

## One model, better answers

All submitted model weights together must fit **8 GB + 10%**. We use **8,800,000,000 bytes**, conservatively counting projectors and adapters. Pinned Gemma 4 12B Q4 plus projector uses 7,556,497,632 bytes, leaving 1,243,502,368 bytes. No Gemma+Qwen/Bielik or two full essay/base copies in the submission. Development may use other models. [Rule and impact](docs/SUBMISSION_WEIGHT_BUDGET.md).

Keep one multimodal Gemma as the leading architecture. Vary prompts, thinking budgets and review steps by question structure/evidence. Reuse the same weights across calls. No new specialist fleet.

## Three priorities

1. **Integrate the strongest tested routes.** Full40 thinking scored38/60 provisionally. Fresh failure retry recovered only1/6; reasoning-note recovery0/6 and is parked. Obtain second full grading, use new paired evidence to choose routes, then run the complete organizer path before promotion.
2. **Build stronger essay arguments.** One topic, 400–500 body words, clean prose. Independent thinking review improved52/90→62/90. A second panel reports the same direction but no aggregate benefit from factual span edits; independent audit continues. Paweł now tests explicit argument planning before prose.
3. **Run a small, controlled training pilot.** 90 cleared rows (34 essays, 56 repairs), 16 separate evaluation inputs, tiny CPU backward and base export are ready. Full-model backward and serving remain unqualified. Deploy ONE merged model with nonessay regression checks or a proven adapter on ONE shared base; compare against the same export pipeline.

## Owners

| Owner | Active responsibility |
|---|---|
| @kwiscion + Sol | Full-exam integration, aggregate package check and freeze [#3](https://github.com/kwiscion/machinekind-matura/issues/3) |
| @Pewciu6 | Planned argument construction versus thinking drafts [#80](https://github.com/kwiscion/machinekind-matura/issues/80) |
| @Bukareszt | Bounded single-model LoRA pilot on cleared data [#117](https://github.com/kwiscion/machinekind-matura/issues/117) |
| @ljaniec | Independent second full-exam grading [#38](https://github.com/kwiscion/machinekind-matura/issues/38) |
| @semberecki | Standalone Qwen thinking challenger after Gemma panel tied [#95](https://github.com/kwiscion/machinekind-matura/issues/95) |
| @przemeknowak781 | Standby; root proxy's Bielik comparison is terminal [#97](https://github.com/kwiscion/machinekind-matura/issues/97) |

## Decisions and guardrails

- Park generic RAG/policy, multiscale and heterogeneous observation: no replicated gain. Observer replication tied 4/6→4/6.
- One worker per host; claim before starting. Freeze call/token/time/cost bounds and back up outputs. Pivot after an uninformative failure.
- Final inference is offline. Inventory the **entire submission's** weight files. Promotion requires a complete 40-item/60-point organizer-path result, hashes and runnable answers.json.
- May 2025 stays sealed. Exam prompts/keys never become training/retrieval data. Publish our findings; keep credentials and unlicensed packs private. No purchases/reset credits.

Tasks: linked issues. Detailed evidence: [checkpoint archive](agentsLog/kwiscion/2026-09-26-plan-history-through-2200.md), [essay review](agentsLog/kwiscion/2026-09-26-essay-thinking-independent-review.md), [observer decision](agentsLog/kwiscion/2026-09-26-hetero-replication-decision.md), [operator runbook](agentsLog/kwiscion/SUNDAY_OPERATOR_RUNBOOK.md). Update this page only when priorities, owners, eligibility or the leading result change.
