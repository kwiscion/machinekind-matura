# Winning plan — control document

Owner: @kwiscion. Active from 26 September 2026, 14:25 Europe/Warsaw. Consult this document before dispatching work, changing scope, accepting a result, or reporting progress. GitHub issues are the live scheduling authority; this document defines the objective and decision rules. Newer explicit owner decisions override it and must be recorded here.

## Objective and score definition

**Reach at least 80% (48/60 points) on the frozen May 2024 history validation exam by 18:00 today.** Then deliver the strongest measured offline system for Sunday's exam. This is a target, not a promised or already measured result. Highest final matura score is the only competition track we optimize.

A qualifying score uses all 40 items and all 60 available points, includes required source text/images, counts failed/incomplete answers as zero, and includes independent review of points the automatic evaluator cannot determine. Report confirmed points, unresolved points, completion, and grading disagreements separately. An automatic lower/upper bound, five-question diagnostic, or synthetic smoke result is not the target score. Manual grading is provisional evidence; it must not edit model answers.

No training/retrieval material derived from fixed 2023/2024/2025 exam questions, keys, source packs or paraphrases. May 2025 remains sealed. Final served weights must fit within 8,000,000,000 bytes per model, including vision/projector; adapter bytes are reported separately under the event rule. Final inference uses no internet knowledge or external AI API. Final freeze: Sunday 27 September, 11:00 Europe/Warsaw.

## Operating facts

- Piotrek (@semberecki) has an RTX 5090 and an active issue watcher. The two Blackwells are **unavailable**. Confirm actual VRAM at claim; do not disturb other workloads.
- The lead laptop completed the single Qwen 3.5 9B full baseline, thinking off and 1024 output tokens: 40 responses, 36 complete and four truncated. Its heuristic floor is 5/60 with substantial review unresolved; no independently reviewed full score is established. Preserve the run and do not duplicate it.
- Gemma 4 12B Q4 is the next candidate. A local v1 run was discovered at 14:56, started at 14:53 by a separate process; its first 13 responses had nonempty final content and no errors. Preserve this single run. Piotrek prepares the RTX 5090 for the next measured arm and must not duplicate the laptop baseline. Spark's earlier failed load remains historical.
- Runner, evaluator, pinned chrono retrieval and strict data exporter already exist. Reuse them. The local source-alias correction passes checks and produces 23 train / one holdout from 24 unchanged eligible examples; it still needs reviewed integration.
- Organizer packages contain exam.json, PNGs and answers-template.json. The adapter must preserve package IDs and emit only valid answers.json. The published May 2023 mock is a format/DEV exercise, not the May 2024 target or the unreleased final exam.
- No HF publication, specialist fleet, speculative large corpus, or new evaluation framework on the critical path. No purchases, reset credits, or unrelated-project credentials.

## Ownership and immediate deliverables

| Owner | Primary responsibility | Immediate deliverable | Safe parallel work if blocked |
| --- | --- | --- | --- |
| @semberecki | GPU candidate execution, #33 | Prepare and verify Gemma on RTX 5090; execute the next lead-declared improvement after the now-running laptop baseline | Resolve one bounded runtime blocker or validate local submission dry-run; no duplicate Qwen/Gemma baseline or speculative training |
| @Pewciu6 | Score and diagnose candidates, #11 | Independently adjudicate the lead's disjoint Sol first-pass grades, then review Gemma; fixed denominators and loss-by-cause table | Start with disputed/uncertain cases, avoid duplicating the already-dispatched first pass |
| @Bukareszt | Pinned retrieval deployment, #44; adapter #37 completed | Stage and verify the existing chrono index from exact source revisions or a rights-cleared portable bundle | Support the accepted organizer adapter only for concrete integration failures; no new retriever/corpus/model arm |
| @przemeknowak781 | Data/split readiness, #4 | Review/integrate the existing source-alias fix, preserve all 24 records, report 23/1 and tiny-holdout limitation | Prepare a source-backed error-category data plan from the scorecard; no exam-derived examples or blind volume chase |
| @ljaniec | Runtime and throughput support, #38 | Help Piotrek reuse verified Gemma recipes; independently check context/image fidelity and final offline runtime | Diagnose a concrete handoff/latency problem or prepare deployment verification, without starting another candidate worker |
| @kwiscion | Lead coordination and acceptance, #3 | Unblock handoffs, maintain this plan/issue board, review exact PR heads, compare scorecards, select next arm | Run bounded Sol subagents on private-input bootstrap, output completeness/context diagnosis, integration review and local score preparation |

An issue assignment is not execution. Each worker must claim with session ID, start time and ETA, then post the first artifact or concrete blocker. Keep one active parent worker per owner/issue. When a worker finishes, the lead assigns the next useful task from measured bottlenecks; do not manufacture work merely to spend tokens.

## Time gates — today, Europe/Warsaw

| Gate | Required evidence | Lead decision |
| --- | --- | --- |
| 14:45 | Every owner acknowledged or marked unavailable; Piotrek runtime/model route chosen; Qwen partial outputs being graded | Reassign an unclaimed critical task; stop duplicate preparation |
| 15:15 | Working Gemma text+image load or a precise blocker; Qwen full/partial score and error categories; Greg's adapter vertical slice | Protect a usable baseline; if Gemma is blocked, choose one supported fallback route and time-box it |
| 16:00 | Both baseline scorecards if operationally possible; unresolved points explicitly listed; submission adapter usable | Freeze the strongest working base and choose the highest-value next intervention |
| 17:00 | One paired improvement result: answer format/budget, source-image handling, or existing RAG, chosen from errors | Keep only measured improvements; one targeted LoRA only if data/runtime are already ready and it can be evaluated before the deadline |
| 17:30 | Candidate selected, remaining grading disagreements resolved or bounded; offline package rehearsal | Stop broad experiments, repair only concrete submission/runtime defects |
| 18:00 | Report fixed-denominator score against 48/60, all artifacts and failures, and next Sunday plan | If below target, state the gap honestly and choose the next evidence-backed action; never inflate grades or silently change the denominator |

These are coordination targets, not permission to fabricate results or bypass blockers. If a gate slips, record why and move resources to the actual bottleneck.

## Experiment and promotion rules

1. Measure usable answers first. Downloaded weights, successful HTTP, nonempty reasoning and lower training loss are not exam success.
2. Preserve every attempt. No silent retries, failed-row exclusions, post-hoc prompt changes, or cherry-picked model comparisons. Reuse unchanged evidence; predeclare each new arm's settings, input hash, call/token budget and stopping rule.
3. Prioritize image/source fidelity, context headroom and completion before attributing misses to missing historical knowledge. Thinking/output policy and effective runtime settings must be recorded.
4. After the baseline, pick one intervention with a plausible points payoff from the error table. Compare it against the strongest baseline, on the same fixed denominator. Do not automatically start RAG, training and a multi-agent ensemble together.
5. Keep the strongest verified constituent as a fallback. No specialist fleet unless a later measured comparison justifies its overhead. Existing 24 examples and a one-record internal holdout do not establish broad fine-tuning readiness.
6. Independent scoring keeps keys outside inference/generation/retrieval. The owner explicitly authorized public GitHub sharing of model answers at14:38: publish answer-only files and safe aggregates after checking for copied source passages. Do not include question packs, official keys/rubrics, credentials, reasoning channels or provider envelopes. This makes scoring handoffs executable without a private transfer. Preserve original raw artifacts locally and retain IDs, failures and provenance hashes in the public evaluation handoff.
7. Merge passing scoped changes at the exact reviewed head; no admin merge or force push. Preserve attributable dirty work. Do not serialize GPU progress behind unrelated documentation or HF work.

## Coordination cadence and local lead work

At each meaningful checkpoint, consult this plan, take one compact GitHub/worker snapshot, and record: owner, latest artifact, blocker, ETA, next action. The user's active Codex goal now drives continued lead work; the older morning heartbeat remains paused to avoid duplicate dispatch. During sustained work, check for external changes about every15minutes and act sooner on delivered worker results. Keep unchanged polls quiet.

Use GPT-6 Sol for bounded local implementation/review and Luna for extraction/checks. Give each subagent an exact artifact, owned paths, budget, stopping rule and independent acceptance check. Avoid asking the user to relay instructions that can be posted to an issue. Escalate only missing human facts/access or decisions that materially change the course.

Checkpoint at 14:55: the key-free bootstrap and owner dispatch are merged (#40); the existing split repair is published as a patch for Przemek, and Greg has delivered his first tested adapter slice. Qwen is finished. Its answer-only handoff is `agentsLog/kwiscion/model-answers/qwen35-9b-val40-1024.jsonl`, preserving every final answer and all four failures. Paweł owns independent scoring; 5/60 is only the current automatic floor. Piotrek has not yet acknowledged a working GPU run. The 14:45 acknowledgment gate slipped; the lead re-pinged the unclaimed owners with concrete artifacts.

The source-completeness audit found one omitted visual on one available point. Preserve v1 and its score; explicitly version the correction as v2 before the new Gemma arm. Root will predeclare a single affected-item Qwen correction and label the resulting reuse of 39 unchanged v1 answers. This repairs input fidelity; it is not a fresh independent full run or evidence that the broad score gap is solved. Output-budget changes remain a separate intervention. No additional full laptop baseline is authorized by this correction.

At 15:00 the lead reconciled the unexpected local Gemma v1 process: preserve it and stop dispatch of a duplicate baseline on #33. Piotrek can prepare his runtime and synthetic smoke, but the next full RTX arm requires a declared intervention from the baseline score/error table. The lead's one-item Qwen repair remains pending until this local worker finishes. Latest local Gemma snapshot was 13/40 complete without errors, not a score.

15:15 checkpoint: Gemma has 18 responses with zero recorded errors as of 15:12. The owner confirmed Grok is stopped; the lead manages the surviving bounded process. Greg's adapter is merged (#42), its reported overwrite defect fixed, and #37 closed; Greg now has #44 for exact pinned-index staging. Łukasz claimed #38 at 15:04 with a 16:00 handoff target. Piotrek, Paweł and Przemek have not yet acknowledged the refreshed assignments. To avoid waiting on scoring, two Sol reviewers own disjoint Qwen halves with 15:40 targets; Paweł owns independent adjudication of their provisional grades. This is agent review, not an official organizer score. The source-v2 repair is merged (#43); no correction inference has started.

## End-state checklist

Record the selected model/adapter hashes and legal sizes, runnable offline environment, frozen prompts/retrieval, exact organizer-package command, validated answers.json, full scorecard and limitations. Confirm team registration, team-code custody and Sunday attendance privately. Organizers' submission link is separate from the guide; do not invent it or publish the team code. Format acceptance and the submission receipt are separate from grading.

Live tasks: [lead #3](https://github.com/kwiscion/machinekind-matura/issues/3), [data #4](https://github.com/kwiscion/machinekind-matura/issues/4), [scoring #11](https://github.com/kwiscion/machinekind-matura/issues/11), [GPU #33](https://github.com/kwiscion/machinekind-matura/issues/33), [runtime #38](https://github.com/kwiscion/machinekind-matura/issues/38), [index staging #44](https://github.com/kwiscion/machinekind-matura/issues/44). [Adapter #37](https://github.com/kwiscion/machinekind-matura/issues/37) is completed.

Organizer format: https://matura-json-guide.ania-olchowik.chatgpt.site/ . The frozen source/evaluation boundaries remain in SOURCE.md and docs/overnight/CONTRACTS.md.
