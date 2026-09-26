# Winning plan

Owner: @kwiscion. Current decision record: **26 September 2026, 17:54 Europe/Warsaw**. Consult this before dispatch, scope changes, accepting results and reporting progress. GitHub issues are the live scheduling authority. Explicit newer owner decisions override this document. [Earlier checkpoints](agentsLog/kwiscion/2026-09-26-plan-history-through-1608.md) are historical.

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

**Laptops and GPU ownership:** the laptop RAG run is terminal. Root owns only separately declared local offline qualification. Piotrek owns the newly declared [RTX runtime-transfer control](agentsLog/kwiscion/2026-09-26-rtx-runtime-transfer-launch.md) on #33: full40-case bare source-v2, existing Gemma/Ollama0.34.4/context32768, thinking off,1024 output, max40calls/$0/no retries. The laptop used0.30.7/context4096; this measures a distinct runtime configuration and actual full-exam throughput. Target18:15 if input acquisition permits, dispatch cutoff18:40 or2400 elapsed seconds. No duplicate worker or temperature call yet.

**Completed retrieval attempt:** all40 responses completed normally in27.63minutes, zero errors/unsent,58,549 total tokens,$0. Exact answer handoff is merged in [PR75](https://github.com/kwiscion/machinekind-matura/pull/75). Disjoint Sol first-pass reviews give26/60 [23,31]; Paweł's [complete independent review](agentsLog/Pewciu6/2026-09-26T1747-score-gemma-rag-full.md) gives **27/60 [22,33]**, versus bare35. The short items lost2 points and the essay lost6 on this draw. Do not promote retrieval. Original launch, disagreement ranges and immutable outputs remain preserved.

| Completed intervention | Reviewed result | Decision |
| --- | --- | --- |
| Blanket answer format, exploratory interrupted11+29 run |35/60 [28,39], tied with bare |Not promoted; [PR58 review](agentsLog/Pewciu6/2026-09-26T1623-score-gemma-format.md) and earlier history preserve its ownership/continuation caveat |
| Generic question policy, full40-case source-v2 run |Sol30/60 [24,34]; independent adjudication32/60 [22,35] |Not promoted; [PR61 review](agentsLog/Pewciu6/2026-09-26T1651-score-gemma-policy.md) |
| Three source-group crops, selected6-point diagnostic |Independent3/6 [1,3] versus bare2/6 [1,2] |No demonstrated crop effect or full-score promotion; [PR65 review](agentsLog/Pewciu6/2026-09-26T1704-score-gemma-crops.md) |
| Bounded chrono retrieval, complete40-case source-v2 |Sol26/60 [23,31]; independent27/60 [22,33] |Not promoted; all40 exact answers published, essay/contradiction uncertainty retained |

The visual audit found no further missing sources after the z13 repair. Higher DPI alone retains the same backend spatial budget; crops preserve full source panels but have not established a gain. Original inputs, attempts and exact answer handoffs remain preserved. All runs used unfixed server sampling defaults, so individual changes do not establish causal effects.

The17:00 improvement gate slipped: tested prompts did not beat35. RAG completed17:30 and its full independent review arrived17:49. The48/60 target remains unmet. Bare Gemma remains fallback until a complete better result is reviewed. Do not reinterpret a missed deadline as permission to inflate grades or open May2025.

Greg's optional organizer-package retrieval integration #62 is accepted inPR68 after84 independent tests. The fixed [two-item synthetic offline rehearsal](agentsLog/kwiscion/2026-09-26-offline-rehearsal-result.md) passed actual isolated server/CUDA execution and cleanup: valid2/2 answers,7completion tokens,68.89seconds,$0. The generic arbitrary-package launcher [#66](https://github.com/kwiscion/machinekind-matura/issues/66) passed9 independent CPU tests plus7 edge checks and its [separate actual isolated qualification](agentsLog/kwiscion/2026-09-26-final-launcher-qualification-result.md):2/2 valid nonempty answers,7completion tokens,$0, cleanup verified. Neither synthetic check is an exam score or an organizer receipt. The runnable [operator runbook](agentsLog/kwiscion/SUNDAY_OPERATOR_RUNBOOK.md) applies to the verified laptop runtime; remote portability is a separate gate.

**New central worker:** the owner supplied Brev instance `voiceless-amaranth-zebra` in `kwiscion-ff7442-omfi`, stated $3.28/hour. Root Sol is the sole worker on[#81](https://github.com/kwiscion/machinekind-matura/issues/81), following the [readiness declaration](agentsLog/kwiscion/2026-09-26-h100-readiness-launch.md). Actual hardware reports H100PCIe81,559MiB, driver580.126.09, no active compute,125GiB RAM and1.2TB free. Runtime/text/image verification and local backup are in progress: max60minutes/$3.28 estimated instance time,2syntheticcalls/2048requestedtokens. No full H100 batch yet. Piotrek keeps his claimed RTX control; the H100 owns subsequent experiments after readiness. No provision/resize/extra purchase or unrelated credentials.

Piotrek delivered three successful synthetic calls inPR73 on an RTX5090 Laptop with24,463MiB. The [independent review](agentsLog/kwiscion/2026-09-26-pr73-runtime-review.md) accepts readiness for the next bounded run; synthetic54decode tokens/s does not establish mixed-exam speed or stage compliance. Łukasz delivered0.34.4 runtime guidance inPR71 and reviews actual evidence. The supplied rules describe a few-minute stage window; the owner has been asked for the actual allowance. No purchases or unavailable Blackwells.

After18:00, choose one next hypothesis from the [Sunday decision memo](agentsLog/kwiscion/2026-09-26-sunday-score-decision.md) and RTX result. Greg'sPR77 is independently reviewed and merged: optional explicit-temperature0.2 candidate, omitted request bytes unchanged, zero model calls. It offers a single-pass comparison before adding latency. Root Sol prepares the separate essay pilot on[#80](https://github.com/kwiscion/machinekind-matura/issues/80), CPU only; only the VALIDATION essay is currently available, DEV remains missing. Increased visual-token budget is another proposal requiring a frozen test; do not stack these. Perfecting the8/15 essay alone still leaves six points missing from48. No specialist fleet, new retriever or training on24 smoke examples.

## Owners and handoffs

| Owner | Live issue | Current deliverable |
| --- | --- | --- |
| @kwiscion | [#3](https://github.com/kwiscion/machinekind-matura/issues/3), [#81](https://github.com/kwiscion/machinekind-matura/issues/81), [#80](https://github.com/kwiscion/machinekind-matura/issues/80) | H100 readiness Sol worker; separate CPU essay-pilot Sol worker; root owns integration and candidate decisions; generic laptop qualification passed |
| @Pewciu6 | [#11](https://github.com/kwiscion/machinekind-matura/issues/11) | Full RAG27/60 delivered; RTX control next when delivered |
| @Bukareszt | [#72](https://github.com/kwiscion/machinekind-matura/issues/72) | Explicit-temperature PR77 accepted; next remote offline-portability handoff being assigned, zero model calls |
| @ljaniec | [#38](https://github.com/kwiscion/machinekind-matura/issues/38) | Review Piotrek runtime/throughput evidence; check visual-token control support without calls |
| @semberecki | [#33](https://github.com/kwiscion/machinekind-matura/issues/33) | Readiness delivered; execute the separately declared full RTX runtime-transfer control |
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
