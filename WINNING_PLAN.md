# Winning plan

**Goal:** the highest Sunday history-matura score. Target 48/60; best reviewed fallback 35/60. Final freeze: **27 September, 11:00 Europe/Warsaw**. Updated 26 September, 22:10. Read this before dispatch or promotion; GitHub issues own tasks and claims.

## One model, better answers

All submitted model weights together must fit **8 GB + 10%**. We use **8,800,000,000 bytes**, conservatively counting projectors and adapters. Pinned Gemma 4 12B Q4 plus projector uses 7,556,497,632 bytes, leaving 1,243,502,368 bytes. No Gemma+Qwen/Bielik or two full essay/base copies in the submission. Development may use other models. [Rule and impact](docs/SUBMISSION_WEIGHT_BUDGET.md).

Keep one multimodal Gemma as the leading architecture. Vary prompts, thinking budgets and review steps by question structure/evidence. Reuse the same weights across calls. No new specialist fleet.

## Three priorities

1. **Measure the full system.** Root's 40-item native-thinking run is active: 10,240 total tokens per short task, 20,480 for the essay; 40 calls / 419,840 tokens / 90 minutes, no retries. Obtain independent grades including every failure. Never add subset gains into a claimed full score.
2. **Make essays reliable.** One topic, 400–500 body words, clean prose, conservative factual edits with unchanged-draft fallback. Independent thinking review improved 52/90→62/90 across six original topics. Paweł replicates on six different topics; whole rewrites remain unreliable.
3. **Test training without blocking the base route.**90 rows/34essays56repairs and16separate evaluation inputs now pass independent data review. Runtime/export are unqualified. Deploy either ONE merged model with nonessay regression checks or a proven small adapter on ONE shared base; two full copies are ineligible.

## Owners

| Owner | Active responsibility |
|---|---|
| @kwiscion + Sol | Full-exam run, integration, review and freeze [#3](https://github.com/kwiscion/machinekind-matura/issues/3) |
| @Pewciu6 | Essay thinking and exact-span edits [#80](https://github.com/kwiscion/machinekind-matura/issues/80) |
| @Bukareszt | Cleared data and single-model training preparation [#117](https://github.com/kwiscion/machinekind-matura/issues/117) |
| @ljaniec | Independent full-exam grading and aggregate package check [#38](https://github.com/kwiscion/machinekind-matura/issues/38) |
| @semberecki | Single-Gemma source-heavy thinking comparison [#95](https://github.com/kwiscion/machinekind-matura/issues/95) |
| @przemeknowak781 | Standby; root proxy's Bielik comparison is terminal [#97](https://github.com/kwiscion/machinekind-matura/issues/97) |

## Decisions and guardrails

- Park generic RAG/policy, multiscale and heterogeneous observation: no replicated gain. Observer replication tied 4/6→4/6.
- One worker per host; claim before starting. Freeze call/token/time/cost bounds and back up outputs. Pivot after an uninformative failure.
- Final inference is offline. Inventory the **entire submission's** weight files. Promotion requires a complete 40-item/60-point organizer-path result, hashes and runnable answers.json.
- May 2025 stays sealed. Exam prompts/keys never become training/retrieval data. Publish our findings; keep credentials and unlicensed packs private. No purchases/reset credits.

Tasks: linked issues. Detailed evidence: [checkpoint archive](agentsLog/kwiscion/2026-09-26-plan-history-through-2200.md), [essay review](agentsLog/kwiscion/2026-09-26-essay-thinking-independent-review.md), [observer decision](agentsLog/kwiscion/2026-09-26-hetero-replication-decision.md), [operator runbook](agentsLog/kwiscion/SUNDAY_OPERATOR_RUNBOOK.md). Update this page only when priorities, owners, eligibility or the leading result change.
