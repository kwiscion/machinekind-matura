# Winning plan

Owner: @kwiscion. Current decision record: **26 September 2026, 17:12 Europe/Warsaw**. Consult this before dispatch, scope changes, accepting results and reporting progress. GitHub issues are the live scheduling authority. Explicit newer owner decisions override this document. [Earlier checkpoints](agentsLog/kwiscion/2026-09-26-plan-history-through-1608.md) are historical.

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

**Sole active model worker:** the lead's frozen bounded-RAG attempt started at17:02:14 on the laptop. It uses original bare source-v2 prompts/images/settings, pinned chrono top-k3/titleweight1/1600 evidence characters, no generic policy or crops. Limits:40calls/40960 requested output tokens/$0/no retries, dispatch cutoff17:40 or2400 elapsed seconds, with runtime/context/concurrency and completion-projection guards. A420-second in-flight request can finish17:47. Preserve all attempts and unsent IDs in the60-point denominator. See the [launch declaration](agentsLog/kwiscion/2026-09-26-bounded-rag-launch.md) and [preflight evidence](agentsLog/kwiscion/2026-09-26-bounded-rag-preflight.md). Do not start another laptop worker.

| Completed intervention | Reviewed result | Decision |
| --- | --- | --- |
| Blanket answer format, exploratory interrupted11+29 run |35/60 [28,39], tied with bare |Not promoted; [PR58 review](agentsLog/Pewciu6/2026-09-26T1623-score-gemma-format.md) and earlier history preserve its ownership/continuation caveat |
| Generic question policy, full40-case source-v2 run |Sol30/60 [24,34]; independent adjudication32/60 [22,35] |Not promoted; [PR61 review](agentsLog/Pewciu6/2026-09-26T1651-score-gemma-policy.md) |
| Three source-group crops, selected6-point diagnostic |Independent3/6 [1,3] versus bare2/6 [1,2] |No demonstrated crop effect or full-score promotion; [PR65 review](agentsLog/Pewciu6/2026-09-26T1704-score-gemma-crops.md) |

The visual audit found no further missing sources after the z13 repair. Higher DPI alone retains the same backend spatial budget; crops preserve full source panels but have not established a gain. Original inputs, attempts and exact answer handoffs remain preserved. All runs used unfixed server sampling defaults, so individual changes do not establish causal effects.

The17:00 improvement gate slipped: tested prompts did not beat35 and RAG preparation/review finished17:01. Aim for completed RAG output17:30–17:40 and independent review by18:00; grade immutable halves while generation continues, never stop based on interim correctness. Paweł owns adjudication; Sol handles separate first-pass halves. Bare Gemma remains fallback until a complete better result is reviewed.

Greg's #57 is independently accepted; [#62](https://github.com/kwiscion/machinekind-matura/issues/62) adds optional bounded retrieval to the organizer-package runner without changing the bare default. A two-synthetic-item isolated rehearsal is reviewed and ready; user/network namespace creation is verified, but actual isolated server/CUDA execution is pending. Give it a separate two-call declaration after RAG terminates. The reusable final-package launcher is a distinct gap now assigned to lead Sol on[#66](https://github.com/kwiscion/machinekind-matura/issues/66); CPU preparation only, no duplicate inference. Łukasz's #38 handoff remains overdue.

Piotrek still needs an actual RTX5090 readiness claim. The supplied rules describe a stage window of only a few minutes, while the measured laptop policy run took24.8minutes. Actual final timing allowance and faster-GPU throughput must be established; an unclaimed5090 is not available capacity. No purchases or waiting for unavailable Blackwells.

After18:00, use the [Sunday decision memo](agentsLog/kwiscion/2026-09-26-sunday-score-decision.md) to choose a single next hypothesis from today's score. Essay planning and visual verification are proposals, not launch authorizations. Even perfecting the current8/15 essay adds at most7points; the13-point gap also needs gains elsewhere. No specialist fleet, new retriever or training on the24-example smoke set.

## Owners and handoffs

| Owner | Live issue | Current deliverable |
| --- | --- | --- |
| @kwiscion | [#3](https://github.com/kwiscion/machinekind-matura/issues/3) | Own laptop queue, score handoffs, exact-head reviews and next experiment; Sol handles bounded review and visual audit |
| @Pewciu6 | [#11](https://github.com/kwiscion/machinekind-matura/issues/11) | Policy/crop adjudication delivered in #61/#65; independently score the bounded-RAG arm |
| @Bukareszt | [#62](https://github.com/kwiscion/machinekind-matura/issues/62) | Add opt-in bounded retrieval to the organizer-package runner without calls; #57 accepted after independent review |
| @ljaniec | [#38](https://github.com/kwiscion/machinekind-matura/issues/38) | Offline runtime and organizer-package rehearsal handoff; original 16:00 ETA slipped, artifact requested |
| @semberecki | [#33](https://github.com/kwiscion/machinekind-matura/issues/33) | Prepare RTX 5090 and claim readiness/ETA; no acknowledgment yet, no duplicate baseline |
| @przemeknowak781 | [#4](https://github.com/kwiscion/machinekind-matura/issues/4) | Integrate reviewed source-alias patch preserving 24 records (23 train/one holdout); unacknowledged, outside critical path |

An assignment is not proof of execution. Claim with session, start time and ETA; maintain one active parent worker per owner/issue. Publish the first useful artifact or concrete blocker. Blackwells are unavailable. Do not wait for an unclaimed GPU when the laptop can execute the declared arm.

## Decision gates today

| Time | Required decision/evidence |
| --- | --- |
| 16:00 — achieved | Stronger working base selected: Gemma; organizer adapter implemented; both baseline scorecards reviewed |
| 17:00 — slipped | Policy did not beat bare35; three-crop gain disputed. Retrieval attempt declared17:02 after preparation/review |
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
