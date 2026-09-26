# Winning plan

Owner: @kwiscion. Current decision record: **26 September 2026, 16:45 Europe/Warsaw**. Consult this before dispatch, scope changes, accepting results and reporting progress. GitHub issues are the live scheduling authority. Explicit newer owner decisions override this document. [Earlier checkpoints](agentsLog/kwiscion/2026-09-26-plan-history-through-1608.md) are historical.

## Objective and evidence

**Reach 48/60 independently reviewed May 2024 history validation points by 18:00 today, then deliver the strongest measured offline system for Sunday's exam.** This is an unmet target, not a promised result. Final freeze: Sunday 27 September at 11:00 Europe/Warsaw. Highest final score is the only competition track.

A qualifying score covers all 40 items and 60 available points with every required source and image. Failed, incomplete and unsent items remain in the denominator. Agent rubric review is provisional; report uncertainty, completion and disagreements. Automatic bounds, partial runs, synthetic smoke and hypothetical oracle routing are not full scores. Never edit answers during grading.

| Preserved v1 baseline | Consolidated provisional score | Review range | Completion |
| --- | ---: | ---: | --- |
| Gemma 4 12B Q4 | **35/60 (58.3%)** | 28–40 | 40/40 complete |
| Qwen 3.5 9B | 25/60 | 16–29 | 36 complete; four truncated |

[PR #53 scorecard](agentsLog/Pewciu6/2026-09-26T1551-score-consolidated.md) governs these totals. Gemma is the working baseline, **13 points short** of the target. Main losses: visual interpretation, factual recall and essay reasoning. Even hypothetical perfect routing between these existing answers reaches only 40/60; a router alone cannot solve the gap.

Both v1 inputs omitted one required image. Source-v2 repairs it without changing the other 39 cases; Gemma's one correction is published separately for scoring. Any reuse is a labeled 39+1 composite, not a fresh full run. Qwen's unused correction call is canceled. May 2025 remains sealed; no candidate is finally frozen.

## Current experiment and queue

The lead's **single question-policy Gemma run completed at 16:34: 40/40 answers, zero errors, 24.8 minutes, $0**. Disjoint first-pass reviews give **10/21 + 20/39 = 30/60 (range 24–34)**; Paweł's independent adjudication remains pending. It is not promoted; bare Gemma's source-v2 composite remains the working 35/60. The run used source-v2 and an identical generic question-following policy for every case, unchanged weights, thinking off, context 4096, 1024 output tokens and a 420-second timeout. No retrieval or task-specific factual hints. Actual usage: 40,993 prompt and 5,893 completion tokens; 40 calls, no retries or continuation. See the [full review](agentsLog/kwiscion/2026-09-26-policy-review-full.md), [frozen launch record](agentsLog/kwiscion/2026-09-26-question-policy-launch.md) and [full handoff](agentsLog/kwiscion/model-answers/question-policy-gemma-val40-answer-only.manifest.json).

The reviewed dispatcher preserves every result and unsent ID. It verifies model identity and effective context after the first real load, watches actual prompt usage and infrastructure failures, and stops on competing inference, reported OOM/context truncation, prompt usage above 2816, two consecutive infrastructure failures, a failed completion-time projection after five calls, 60 elapsed minutes or 17:10. Exact multimodal pre-counting was unavailable; fit is explicitly estimated, not proven. Sampling defaults remain unchanged. Never stop based on interim correctness.

The earlier blanket-format run completed through an interrupted 11+29 continuation from another controller. Independent review in PR #58 gives **35/60 (range 28–39), tied with the baseline**: improved answer format was offset by source-reading losses. It remains exploratory and is not promoted. The separately reviewed source-v2 correction yields a labeled **35/60** composite with the other 39 baseline answers. Automatic 10 versus 11 was not a valid full-score comparison. Root stopped the first format process for question-compliance and ownership concerns before that comparison; the laptop queue is now lead-controlled.

CPU preparation may proceed during inference: source-image fidelity and bounded retrieval integration using the existing pinned index. **Neither preparation authorizes another model run.** The visual audit found no further missing sources, but small details and neighboring tasks remain possible error sources. Select the next intervention after the current score; keep the strongest measured constituent as fallback. No speculative specialist fleet or training on the 24-example smoke dataset.

At 16:44 the lead separately authorized at most **three source-group crop diagnostic calls** on the bare source-v2 prompts, IDs 1/6/25, unchanged Gemma/settings, 3072 requested output tokens total, $0 and no retries. Full source panels and external callouts were visually checked; only image regions change. The selected comparator is 2/6 provisional points from the preserved bare answers. Finish by 17:00; do not dispatch unless the entire 420-second timeout fits. Stop on any error, wrong runtime or competing worker, never interim correctness. This is a diagnostic, not a full score or automatic composite promotion. The model's fixed visual budget makes a DPI-only experiment unpromising; crops are a separate tested hypothesis.

Greg claimed #57 at 16:40; the first runnable retrieval slice is due around 17:05, so the earlier 16:45 handoff target slipped. Root will review immediately, freeze a separate full-arm manifest, and test RAG on **bare source-v2**, not the unsuccessful generic policy. No RAG model calls are authorized yet. If delivery threatens the 18:00 scoring window, keep the working baseline rather than launch an unreviewable run. Piotrek is investigating his watcher; the laptop continues. A local offline-rehearsal fallback is being prepared because #38 has not delivered an artifact.

## Owners and handoffs

| Owner | Live issue | Current deliverable |
| --- | --- | --- |
| @kwiscion | [#3](https://github.com/kwiscion/machinekind-matura/issues/3) | Own laptop queue, score handoffs, exact-head reviews and next experiment; Sol handles bounded review and visual audit |
| @Pewciu6 | [#11](https://github.com/kwiscion/machinekind-matura/issues/11) | Review published exploratory format answers and isolated source correction; then independently adjudicate the question-policy result |
| @Bukareszt | [#57](https://github.com/kwiscion/machinekind-matura/issues/57) | Prepare bounded offline RAG input without model calls; staging #54 is accepted via reviewed PR #55 |
| @ljaniec | [#38](https://github.com/kwiscion/machinekind-matura/issues/38) | Offline runtime and organizer-package rehearsal handoff; original 16:00 ETA slipped, artifact requested |
| @semberecki | [#33](https://github.com/kwiscion/machinekind-matura/issues/33) | Prepare RTX 5090 and claim readiness/ETA; no acknowledgment yet, no duplicate baseline |
| @przemeknowak781 | [#4](https://github.com/kwiscion/machinekind-matura/issues/4) | Integrate reviewed source-alias patch preserving 24 records (23 train/one holdout); unacknowledged, outside critical path |

An assignment is not proof of execution. Claim with session, start time and ETA; maintain one active parent worker per owner/issue. Publish the first useful artifact or concrete blocker. Blackwells are unavailable. Do not wait for an unclaimed GPU when the laptop can execute the declared arm.

## Decision gates today

| Time | Required decision/evidence |
| --- | --- |
| 16:00 — achieved | Stronger working base selected: Gemma; organizer adapter implemented; both baseline scorecards reviewed |
| 17:00 | Paired improvement result, full denominator and independent grading; select only measured gains |
| 17:30 | Candidate selection and offline package rehearsal; stop broad experiments and fix concrete submission defects |
| 18:00 | Honest score against 48/60, failures and uncertainty preserved, next Sunday work chosen from evidence |

If a gate slips, record the cause and move resources to the bottleneck. Do not inflate grades, change the denominator, stack unmeasured interventions or rush training merely to show activity.

## Non-negotiable boundaries

- Final inference is offline. Each saved model, including vision/projector components, is at most **8,000,000,000 bytes**; report adapters separately under the event rule. Gemma's current model plus projector is 7,556,497,632 bytes.
- Follow [SOURCE.md](SOURCE.md) and [contracts](docs/overnight/CONTRACTS.md). Fixed 2023/2024/2025 questions, keys, source packs and paraphrases never enter training or retrieval corpora. Independently licensed general history sources may be retrieved. May 2025 needs a separate lead release after candidate freeze; the time of day alone never releases it.
- User permits public model answers. Publish exact final strings, IDs/errors and provenance after checking quotations; keep official keys, question/source packs, reasoning/provider envelopes and credentials private. Flag quotation issues instead of editing scoring answers.
- User authorizes project Git/GitHub, HF and bounded paid inference through existing normal/project credentials. Record estimates and actual usage before paid runs. No purchases, reset credits or unrelated-project credentials. No HF publication on the current path.
- Preserve attempts and attributable dirty work. Merge only passing scoped changes at the reviewed head; no admin merge, force push, broad reset or another owner's silent overwrite.

## Operating loop and final handoff

Use Sol for bounded implementation/review and Luna for extraction/checks. During active work, inspect changed GitHub state about every 15 minutes and react to delivered results. Keep unchanged checks quiet. The active Codex goal drives lead continuation; the old morning heartbeat stays paused to avoid duplicate dispatchers.

Final handoff must contain model/projector hashes and legal sizes, frozen prompt/retrieval settings, runnable offline environment, exact organizer-package command, validated answers.json, complete scorecard and limitations. The [organizer guide](https://matura-json-guide.ania-olchowik.chatgpt.site/) specifies exam.json, PNGs and an answer template; preserve every ID and emit the required JSON schema. Adapter acceptance is separate from model quality and the submission receipt. Confirm registration, team-code custody and Sunday attendance privately; never invent a submission link or publish the team code.
