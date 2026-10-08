# Matura retrospective case details

[Return to the evidence record](RETROSPECTIVE_CASE_RECORD.md).

Cases separate recorded sequence from interpretation. Related IDs and timing references prevent double-counting. C39 and C40 are context, not independent experiments.

## C01

### Lead mandate and autonomous research expectations

**Group:** Strategy · **Classification:** governance · **Record type:** case.

**Initial expectation.** The lead would choose, coordinate, review and redirect research toward at least 48/60, with human involvement mainly for resources and submission.

**Recorded sequence**

1. Historical plan set 80% / 48 of 60 and required next useful tasks, pivots and resource changes.
2. The user repeatedly requested strategic audits, supplied ideas and restored scope.
3. Later review found meaningful pivots as well as missed follow-through.

**Verified outcome.** Ownership and pivot instructions existed; lack of instructions alone does not explain the outcome.

| Effect | Finding |
|---|---|
| Quality | No isolated quality effect measured. |
| Operations | Substantial owner intervention reported; its active time is unknown. |
| Learning | Separates an execution/initiative problem from a missing mandate. |

**Historical decision.** No separate historical decision asserted in this record.

**Retrospective implication.** Treat owner-dependent research direction as a central autonomy failure. Its underlying cause and the efficacy of a role split remain untested.

**Initiative and attribution.** Human established objective; exact origin of individual lead decisions remains mixed/unknown.

**Interpretation.** The delegated research lead did not reliably initiate consequential strategic reassessment; the owner supplied important direction, including Qwen reconsideration, budget increases, image correction and RAG scope. This does not imply that no useful agent decisions occurred.

**Limits and alternative explanations.** Literal active-goal tool configuration was not exposed. Lead account authorship is not proof of human or agent origin.

**Evidence status.** Primary records support the technical sequence; firsthand user clarification supplies initiative attribution where original prompts were not recovered.

**Related cases:** [C14](#c14), [C21](#c21), [C22](#c22), [C23](#c23), [C35](#c35). **Time entries:** No quantified interval.

**Correction history:** R15 — The user explicitly clarifies that both resulted from their intervention. Preserve the technical successes as owner-directed follow-through; exact contemporaneous prompt locations remain unrecovered.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/3742a94f5f19e051bc3ad2d2081e8f350704195f/WINNING_PLAN.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/5c0dd67b00cc06507e66ae5f84ce5f4f909b0849/WINNING_PLAN.md)
- [Evidence 3](thread://01a0da6d-1f45-7ae0-a046-5c2f651c5fed?hostId=local)
- Current retrospective user clarification: revisiting Qwen and changing reasoning budgets resulted from owner intervention.

## C02

### Initial full-exam baseline and working-model choice

**Group:** Evaluation · **Classification:** selection and measurement · **Record type:** case.

**Initial expectation.** Use a complete, graded baseline to choose the strongest available working model.

**Recorded sequence**

1. Two disjoint first-pass grading assignments were followed by independent rubric review/adjudication.
2. Provisional v1 scores were Gemma 35/60 and Qwen 25/60; Qwen had four length-stopped answers.
3. Gemma became the working base while expensive or unready alternatives were parked.

**Verified outcome.** A defensible provisional baseline choice was made; it did not establish permanent model superiority.

| Effect | Finding |
|---|---|
| Quality | Gemma's working score was higher under the tested configuration. |
| Operations | A complete candidate was preserved. |
| Learning | Failures stayed in denominators and grade uncertainties were recorded. |

**Historical decision.** Proceed with Gemma and one bounded intervention; reconsider Qwen later under a different qualified configuration.

**Retrospective implication.** Evidence-led prioritization with a practical advantage for complete outputs.

**Initiative and attribution.** Lead-coordinated choice; precise human versus agent origin not established.

**Interpretation.** Evidence-led prioritization with a practical advantage for complete outputs.

**Limits and alternative explanations.** Grades were agent-provisional and model labels visible. Ranges 28-40 and 16-29 are summed grading sensitivities, not confidence intervals.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C03](#c03), [C04](#c04), [C35](#c35). **Time entries:** No quantified interval.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/pull/53)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5846898528)

## C03

### Question-policy candidate and adjudication

**Group:** Evaluation · **Classification:** valid negative and confounded comparison · **Record type:** case.

**Initial expectation.** A generic question policy plus corrected source inputs would improve the working Gemma candidate.

**Recorded sequence**

1. The arm combined a prompt-policy change with source-v2 input changes.
2. First grading totaled 30/60; adjudication revised two judgments to 32/60.
3. The candidate was not promoted over the 35/60 baseline.

**Verified outcome.** The combined candidate failed to beat the baseline point estimate; policy-specific causality was not isolated.

| Effect | Finding |
|---|---|
| Quality | No observed gain for the combined candidate. |
| Operations | Bounded run and review completed without candidate promotion. |
| Learning | Regrading changed the magnitude of the loss but not the decision. |

**Historical decision.** Retain the baseline and move to another intervention.

**Retrospective implication.** A useful candidate screen, weaker as a test of which mechanism caused the result.

**Initiative and attribution.** Lead choice recorded prospectively; exact human contribution unknown.

**Interpretation.** A useful candidate screen, weaker as a test of which mechanism caused the result.

**Limits and alternative explanations.** Input and policy changes were combined; grading sensitivity ranges overlap. Active review time was not recorded.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C02](#c02), [C31](#c31). **Time entries:** No quantified interval.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/pull/61)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/11#issuecomment-5847141263)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5847309808)

## C04

### Qwen budget limitations and later challenger

**Group:** Model and runtime · **Classification:** configuration and model selection · **Record type:** case.

**Initial expectation.** Determine whether Qwen was genuinely weaker or constrained by its initial runtime configuration.

**Recorded sequence**

1. Early Qwen3.5:9B full40 used thinking off and 1024 output tokens; four answers ended at length limits.
2. The lead later tested Qwen as a different eligible multimodal candidate.
3. The eventual selected run used thinking on, larger output/context limits, recovery, corrected images and an essay-coverage suffix.

**Verified outcome.** The early completion limitation is documented. The later 40/60 package was not a budget-only experiment.

| Effect | Finding |
|---|---|
| Quality | Initial 25/60 and later 40/60 are configuration-specific results. |
| Operations | Later run completed all 40 answers. |
| Learning | A weak early model ranking was revisited rather than treated as permanent. |

**Historical decision.** Advance the later challenger to full confirmation.

**Retrospective implication.** Budgets and runtime compatibility mattered, alongside other changed inputs and prompts.

**Initiative and attribution.** Human-initiated Qwen reassessment and budget changes, explicitly clarified by the user in this retrospective. Agents implemented and evaluated the follow-up. The exact original chat messages were not recovered.

**Interpretation.** Budgets and runtime compatibility mattered, alongside other changed inputs and prompts.

**Limits and alternative explanations.** Early Qwen context was not pinned in the public manifest. The user attributes the reassessment and budget changes to their intervention; this firsthand attribution is distinct from a recovered contemporaneous prompt. Do not conflate this run with the separate Spark smoke.

**Evidence status.** Primary records support the technical sequence; firsthand user clarification supplies initiative attribution where original prompts were not recovered.

**Related cases:** [C02](#c02), [C05](#c05), [C20](#c20), [C35](#c35). **Time entries:** No quantified interval.

**Correction history:** R04 — The documented 40-point full validation used direct Qwen with RAG off. Multiple configuration changes confound the earlier comparison; the final exam was different. R15 — The user explicitly clarifies that both resulted from their intervention. Preserve the technical successes as owner-directed follow-through; exact contemporaneous prompt locations remain unrecovered.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/model-answers/qwen35-9b-val40-1024.manifest.json)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5849801820)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-qwen-coverage-full40-launch.json)
- Current retrospective user clarification: revisiting Qwen and changing reasoning budgets resulted from owner intervention.

## C05

### Spark smoke success and speedup claim corrected

**Group:** Runtime evidence · **Classification:** false readiness and correction · **Record type:** case.

**Initial expectation.** Twenty synthetic smoke requests and latency comparison would establish usable Spark inference.

**Recorded sequence**

1. PR25 reported 20/20 prompts, zero errors and roughly 16.3x speedup.
2. Raw inspection found only 4 nonempty Spark responses; 16 were empty despite error:null.
3. PR28 corrected the report and later lead summaries used the corrected numbers.

**Verified outcome.** The successful-answer speedup claim was invalid. The original failing Spark/Qwen path was not shown repaired and rerun.

| Effect | Finding |
|---|---|
| Quality | No exam-quality evidence was produced. |
| Operations | Reporting was corrected about 19 minutes after merge; further audit work was required. |
| Learning | Raw artifacts supported correction and prevented continued reliance on the headline. |

**Historical decision.** Do not use failed-request timings as usable throughput. No traced model promotion or hardware allocation relied on the false claim.

**Retrospective implication.** Transport success was mistaken for task success, then contained.

**Initiative and attribution.** Contributor report and subsequent agent audit; identity alone does not establish human authorship.

**Interpretation.** Transport success was mistaken for task success, then contained.

**Limits and alternative explanations.** All Spark outputs hit a 200-token budget, but finish reasons were absent; the cause of blanks was not isolated. No final-score harm was established.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C06](#c06), [C07](#c07). **Time entries:** E01.

**Correction history:** R09 — No successful rerun of the original Spark/Qwen failure was found. Reporting, verifier repair, later Gemma OOM and successful RTX execution are distinct events.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/pull/25)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/27)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/pull/28)
- [Evidence 4](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5844875576)

## C06

### Supplementary audit verifier false passes and provenance claims

**Group:** Runtime evidence · **Classification:** verification defect and repair · **Record type:** case.

**Initial expectation.** An independent audit verifier would reliably reproduce the Spark correction.

**Recorded sequence**

1. A supplementary verifier double-counted an empty timed-out response in a union metric.
2. A non-finite committed metric could falsely compare as MATCH; byte-for-byte and second-machine claims exceeded the checks.
3. PR31 introduced strict schema/type/finite checks, union counting and adversarial tests without new inference.

**Verified outcome.** The verifier was repaired; the valid finding of 16 empty Spark responses remained unchanged.

| Effect | Finding |
|---|---|
| Quality | No model-quality effect measured. |
| Operations | Additional repair/review was needed. |
| Learning | Verifier behavior itself was tested with failure cases. |

**Historical decision.** Preserve original artifacts and narrow provenance claims to what was demonstrated.

**Retrospective implication.** A checker can repeat the assurance problem it is intended to solve.

**Initiative and attribution.** Agent/lead review in project records; exact human involvement unknown.

**Interpretation.** A checker can repeat the assurance problem it is intended to solve.

**Limits and alternative explanations.** This was verify_issue27_audit.py, not proof that PR26's local inference runner tests were all invalid. Active repair time unknown.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C05](#c05). **Time entries:** No quantified interval.

**Correction history:** R09 — No successful rerun of the original Spark/Qwen failure was found. Reporting, verifier repair, later Gemma OOM and successful RTX execution are distinct events.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/ljaniec/2026-09-26-verifier-repair.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/30#issuecomment-5844680712)

## C07

### Gemma Spark load failure and RTX transfer

**Group:** Model and runtime · **Classification:** capacity failure and alternative execution · **Record type:** case.

**Initial expectation.** Run the eligible Gemma model and projector on provisioned hardware.

**Recorded sequence**

1. A separate Gemma-on-Spark probe returned CUDA OOM and no usable response.
2. Exact OOM cause was not isolated; service disruption and further retries were restricted.
3. The same native Gemma weights later produced 40/40 nonempty answers on RTX5090 with a different runner.

**Verified outcome.** The task became operational on another hardware path; Spark itself was not demonstrated repaired.

| Effect | Finding |
|---|---|
| Quality | The transfer run alone did not establish an exam score. |
| Operations | A working alternative inference path was obtained. |
| Learning | Hardware/runtime success was distinguished from model quality. |

**Historical decision.** Continue on available functioning hardware; preserve Qwen3-8B only as a text fallback.

**Retrospective implication.** A pragmatic hardware shift had independent support beyond the earlier bad Spark speed claim.

**Initiative and attribution.** Resource access was human-provisioned; lead/worker execution recorded.

**Interpretation.** A pragmatic hardware shift had independent support beyond the earlier bad Spark speed claim.

**Limits and alternative explanations.** No controlled diagnosis proves Spark intrinsically unsuitable. RTX publication defects were separate.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C05](#c05), [C08](#c08). **Time entries:** T12.

**Correction history:** R09 — No successful rerun of the original Spark/Qwen failure was found. Reporting, verifier repair, later Gemma OOM and successful RTX execution are distinct events.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/pull/36)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/ljaniec/2026-09-26-gemma-spark-load.md)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/pull/85)

## C08

### Working RTX run but broken published reproduction

**Group:** Integration · **Classification:** reproducibility defect and repair · **Record type:** case.

**Initial expectation.** The committed runner would reproduce the successful RTX transfer and enforce declared runtime guards.

**Recorded sequence**

1. A real transfer produced 40 complete answers.
2. Issue88 found the public wrapper resolved the repository path incorrectly, weak failure-stop and identity/context checks, and a post-response dispatch timestamp.
3. PR118 repaired the wrapper and checked failure paths with CPU tests; historical GPU evidence was preserved.

**Verified outcome.** Public reproducibility and guard claims were corrected without rerunning the historical transfer.

| Effect | Finding |
|---|---|
| Quality | No new accuracy result. |
| Operations | Future runner reliability improved; original private success did not imply public repeatability. |
| Learning | Testing the delivered invocation path exposed defects absent from the private working path. |

**Historical decision.** Merge the corrected wrapper for future runs and preserve the original transfer receipt.

**Retrospective implication.** The tested environment differed from the promised reproducible artifact.

**Initiative and attribution.** Independent review and lead integration; human attribution unknown.

**Interpretation.** The tested environment differed from the promised reproducible artifact.

**Limits and alternative explanations.** CPU repairs do not independently requalify the past GPU run. Issue lifetime is not labor time.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C07](#c07), [C37](#c37). **Time entries:** No quantified interval.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/88)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/pull/118)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/88#issuecomment-5849693036)

## C09

### Strict data eligibility and internal holdout export repair

**Group:** Data · **Classification:** construction defect and successful review · **Record type:** case.

**Initial expectation.** A training export would contain eligible verified records and preserve its internal source-group split.

**Recorded sequence**

1. A lexical exam-copy audit reported clean within its stated scope; it was not a merge approval.
2. Exact-head review found default export selected 197 legacy verified rows although only 24 passed both strict checks, and global distractors crossed internal holdout partitions.
3. The bad head was blocked; repaired strict-only exports passed six checks and independent review before merge.

**Verified outcome.** Unsafe export behavior was corrected before the flawed version merged; the 200-record target remained unmet.

| Effect | Finding |
|---|---|
| Quality | No contaminated training run or final-score damage was established. |
| Operations | Repair produced a smaller truthful handoff and fail-closed export. |
| Learning | Independent inspection of actual output overrode stale eligibility labels. |

**Historical decision.** Merge only the repaired partial handoff and exclude legacy/draft rows from training eligibility.

**Retrospective implication.** Successful containment of data construction defects.

**Initiative and attribution.** Contributor construction and lead/separate Sol review; exact human role unverified.

**Interpretation.** Successful containment of data construction defects.

**Limits and alternative explanations.** The clean exam-copy audit was not disproved: later blockers involved eligibility and an internal holdout, not demonstrated May2024 answer leakage. A later alias issue remained.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C10](#c10), [C11](#c11). **Time entries:** E02.

**Correction history:** R01 — The clean audit concerned lexical May2024 exam-copy overlap. Later defects concerned strict eligibility and internal source-group separation. These were different controls.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/pull/18#issuecomment-5842340473)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/pull/18#pullrequestreview-5324972948)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/pull/18#pullrequestreview-5325017706)

## C10

### Canonical-source aliases defeated the first split repair

**Group:** Data · **Classification:** residual leakage and correction · **Record type:** case.

**Initial expectation.** Distinct source_group_id values would enforce disjoint training and holdout sources.

**Recorded sequence**

1. A subsequent packaging check found the same underlying source on both sides under different identifiers.
2. Use of the holdout was stopped; grouping was expanded to source_group_id and source_ids.
3. A later repair yielded 23/1 rather than 22/2, and training remained gated.

**Verified outcome.** A second, different split defect was corrected; the tiny holdout was unsuitable for strong model-selection claims.

| Effect | Finding |
|---|---|
| Quality | No affected training or quality gain demonstrated. |
| Operations | Additional correction after an earlier successful review. |
| Learning | Identifier uniqueness is weaker than canonical source separation. |

**Historical decision.** Defer publication/holdout use and keep this small dataset out of the later separate essay corpus.

**Retrospective implication.** The initial repair checked partition labels but incompletely modeled source identity.

**Initiative and attribution.** Lead-side check; human versus agent origin unknown.

**Interpretation.** The initial repair checked partition labels but incompletely modeled source identity.

**Limits and alternative explanations.** Related repair of C09, not an independent dataset or separate training experiment.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C09](#c09), [C11](#c11). **Time entries:** No quantified interval.

**Correction history:** R01 — The clean audit concerned lexical May2024 exam-copy overlap. Later defects concerned strict eligibility and internal source-group separation. These were different controls.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/4#issuecomment-5844879574)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/4#issuecomment-5846254260)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/4#issuecomment-5845608681)

## C11

### Essay corpus collision checks and independent factual repairs

**Group:** Data · **Classification:** adaptive scoping and successful verification · **Record type:** case.

**Initial expectation.** Prepare a bounded essay pilot with disjoint evaluation topics and auditable examples.

**Recorded sequence**

1. After delayed claim and temporary lead coverage, the worker detected topic collisions and withdrew overlapping drafts.
2. PR130 delivered an 81-row pilot; follow-up PR131 corrected export counts/structure, yielding a 90-row, 28-component canonical export.
3. Independent checks covered grouping, CRLF behavior and four source errors; later model readiness was separately gated.

**Verified outcome.** A checked corpus handoff was produced without automatically authorizing training or claiming model gains.

| Effect | Finding |
|---|---|
| Quality | Dataset corrections are not measured accuracy gains. |
| Operations | Scoped owned-path artifacts enabled subsequent preparation. |
| Learning | Workers detected substantive data problems and acted on them. |

**Historical decision.** Accept the bounded data handoff; assess training and deployed behavior separately.

**Retrospective implication.** A positive correction-to-action loop, with high-touch scoping visible.

**Initiative and attribution.** Worker detection plus lead coordination; root account is not proof of human action.

**Interpretation.** A positive correction-to-action loop, with high-touch scoping visible.

**Limits and alternative explanations.** Not the same corpus as C09/C10; do not combine row counts. Coverage in this retrospective is less deep than the runtime cases.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C09](#c09), [C10](#c10), [C30](#c30). **Time entries:** No quantified interval.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/117)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/pull/130)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/pull/131)
- [Evidence 4](https://github.com/kwiscion/machinekind-matura/issues/117#issuecomment-5849500591)

## C12

### 107-source RAG result and overextended strategic inference

**Group:** Retrieval · **Classification:** scope mismatch and confounded negative · **Record type:** case.

**Initial expectation.** Determine whether retrieval could improve open-domain history answers.

**Recorded sequence**

1. The reference corpus contained 100 Wikipedia and 7 Wikisource documents, 3481 chunks.
2. A bounded Gemma RAG configuration scored 27/60 against a preserved 35/60 direct baseline.
3. Coverage and query limitations were recorded, but broad-corpus investigation remained deferred until a later reset.

**Verified outcome.** The tested configuration failed; this did not establish that full-Wikipedia retrieval was unhelpful.

| Effect | Finding |
|---|---|
| Quality | Observed configuration scored lower, with input/runtime/sampling/grading confounds. |
| Operations | A limited prototype influenced broader prioritization. |
| Learning | The key coverage-versus-retrieval uncertainty was not isolated. |

**Historical decision.** Reject the particular result; later reopen the corpus scope.

**Retrospective implication.** Generalization from a narrow implementation to a broader strategy exceeded the test's scope.

**Initiative and attribution.** User recalls discovering the 107-source limit; late owner scope reset is documented. Exact first discovery message was not recovered.

**Interpretation.** Generalization from a narrow implementation to a broader strategy exceeded the test's scope.

**Limits and alternative explanations.** No proven causal full-Wikipedia improvement; the final exam differed from validation.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C13](#c13), [C14](#c14), [C23](#c23), [C24](#c24), [C25](#c25), [C26](#c26). **Time entries:** No quantified interval.

**Correction history:** R03 — Several mechanisms were tested, but retained the same limited corpus. Their failures did not resolve the broader coverage question.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/Bukareszt/README.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-failure-audit-astra.md)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/182#issuecomment-5851984696)

## C13

### Retrieval variants stopped and resources reassigned

**Group:** Retrieval · **Classification:** valid narrow negatives and strategic pivot · **Record type:** case.

**Initial expectation.** Corrected query/evidence presentations might rescue the existing retrieval setup.

**Recorded sequence**

1. A corrected selective wave tied 1/5; another panel scored bare 7/13 versus 5, 6 and 4 for tested variants.
2. The worker stopped with unused call/token allowance and declined further threshold tuning.
3. The lead reassigned work to essay training.

**Verified outcome.** A real mechanism change followed negative evidence, but all retrieval variants retained the narrow corpus.

| Effect | Finding |
|---|---|
| Quality | No secure gain in the tested panels. |
| Operations | Remaining declared budget was not automatically spent. |
| Learning | Useful local negatives did not resolve whether missing coverage was the main bottleneck. |

**Historical decision.** Stop these families and reallocate; broad-corpus potential remained unresolved.

**Retrospective implication.** Counterevidence to a blanket claim of endless small tweaks.

**Initiative and attribution.** Worker stop and lead reassignment recorded; precise human contribution unknown.

**Interpretation.** Counterevidence to a blanket claim of endless small tweaks.

**Limits and alternative explanations.** Only five of forty validation prompts changed under one corrected gate. Source overlap and selected panels limit generalization.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C12](#c12), [C30](#c30). **Time entries:** T01.

**Correction history:** R03 — Several mechanisms were tested, but retained the same limited corpus. Their failures did not resolve the broader coverage question. R06 — Several documented stops and reassignments changed mechanisms. The quality and autonomy of all originating choices remain incompletely attributed.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/96#issuecomment-5848267686)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/96#issuecomment-5848591673)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/96#issuecomment-5848703080)

## C14

### Global expert audit informed a revised portfolio

**Group:** Strategy · **Classification:** expert synthesis and uncertain continuity · **Record type:** case.

**Initial expectation.** Use a global diagnosis to select experiments from measured bottlenecks.

**Recorded sequence**

1. Astra inspected all 40 cases, compared routes and examined visual cases.
2. It identified query contamination, coverage limitations and a ranked experiment menu.
3. The subsequent plan used it as common diagnosis and divided work across factual, essay and source-grounding labs.

**Verified outcome.** Expert synthesis existed and affected scheduling; persistent automatic re-synthesis after later results was not established.

| Effect | Finding |
|---|---|
| Quality | No isolated score effect. |
| Operations | A shared diagnosis guided multiple tracks. |
| Learning | Adding an occasional expert is not a new mechanism; continuous ownership would be the new hypothesis. |

**Historical decision.** Use the audit for the next portfolio; retain uncertainty about later follow-through.

**Retrospective implication.** Advisory quality and continuous strategic responsibility are different.

**Initiative and attribution.** Expert agent and lead coordination; original trigger may have been human, not verified.

**Interpretation.** Advisory quality and continuous strategic responsibility are different.

**Limits and alternative explanations.** The audit explicitly described proposals, not execution authorization. No evidence proves that a persistent expert role alone would have changed outcomes.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C01](#c01), [C12](#c12), [C13](#c13), [C15](#c15), [C16](#c16). **Time entries:** No quantified interval.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/5c0dd67b00cc06507e66ae5f84ce5f4f909b0849/agentsLog/kwiscion/2026-09-26-failure-audit-astra.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/5c0dd67b00cc06507e66ae5f84ce5f4f909b0849/WINNING_PLAN.md)

## C15

### Low reasoning cap recognized as an invalid capability test

**Group:** Model and runtime · **Classification:** failure diagnosis and revised experiment · **Record type:** case.

**Initial expectation.** Compare reasoning strategies under a bounded inference envelope.

**Recorded sequence**

1. A 2048-token thinking arm hit a length failure and left later items unattempted, producing a misleadingly low aggregate.
2. The lead explicitly recognized that this had not tested organizer-sized reasoning.
3. A larger-budget full-exam route was pursued, eventually yielding the native-thinking/recovery configuration.

**Verified outcome.** A configuration failure was not accepted as proof that thinking was ineffective.

| Effect | Finding |
|---|---|
| Quality | Later configurations scored better, without isolating one parameter's causal effect. |
| Operations | Failed calls and unattempted items remained visible. |
| Learning | The next experiment addressed the observed output-limit failure. |

**Historical decision.** Increase and qualify the reasoning allowance instead of abandoning the mechanism.

**Retrospective implication.** A positive example of interpreting a failed test at the correct scope.

**Initiative and attribution.** The user explicitly attributes the push to change reasoning budgets to their intervention. Agents performed diagnosis, implementation and subsequent testing; exact prompts for each sub-arm were not reconstructed.

**Interpretation.** A useful correction of the tested scope, with high-level direction attributed to the owner rather than autonomous strategic initiative.

**Limits and alternative explanations.** Larger full-run testing also increased integration/runtime exposure; not a clean single-variable causal estimate.

**Evidence status.** Primary records support the technical sequence; firsthand user clarification supplies initiative attribution where original prompts were not recovered.

**Related cases:** [C04](#c04), [C34](#c34), [C35](#c35). **Time entries:** No quantified interval.

**Correction history:** R06 — Several documented stops and reassignments changed mechanisms. The quality and autonomy of all originating choices remain incompletely attributed. R15 — The user explicitly clarifies that both resulted from their intervention. Preserve the technical successes as owner-directed follow-through; exact contemporaneous prompt locations remain unrecovered.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/38#issuecomment-5849217669)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/ljaniec/2026-09-26-reasoning-wave-terminal.md)
- Current retrospective user clarification: revisiting Qwen and changing reasoning budgets resulted from owner intervention.

## C16

### Visual assistance failed replication and was parked

**Group:** Vision · **Classification:** replication and valid stop · **Record type:** case.

**Initial expectation.** An initial visual-observer gain might transfer to another panel.

**Recorded sequence**

1. The first selected panel showed 3/6 to 5/6.
2. A mechanically selected second panel tied 4/6 to 4/6.
3. The lead parked the bundle and moved toward larger native reasoning.

**Verified outcome.** A promising small result did not earn promotion when replication failed.

| Effect | Finding |
|---|---|
| Quality | No replicated gain. |
| Operations | A bounded replication avoided continued automatic expansion. |
| Learning | A genuine pivot followed evidence. |

**Historical decision.** Park the observer bundle and test a different mechanism.

**Retrospective implication.** Useful counterexample to confirmation-only experimentation.

**Initiative and attribution.** Lead/agent process documented; original human involvement not fully attributable.

**Interpretation.** Useful counterexample to confirmation-only experimentation.

**Limits and alternative explanations.** Small panels and input-quality limitations constrain broader vision conclusions.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C15](#c15), [C17](#c17), [C19](#c19). **Time entries:** No quantified interval.

**Correction history:** R06 — Several documented stops and reassignments changed mechanisms. The quality and autonomy of all originating choices remain incompletely attributed.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-hetero-replication-decision.md)

## C17

### Whole-page visual inputs inspected with incomplete acceptance criteria

**Group:** Vision · **Classification:** input validity and review judgment · **Record type:** case.

**Initial expectation.** Evaluation images should supply the relevant visual evidence in a form representative of the organizer task.

**Recorded sequence**

1. The bootstrap rendered 21 full PDF pages at 110 DPI and attached page references to image-bearing items.
2. A contemporary audit recorded inspection of all pages and lists, noticing neighboring content and resolution dilution.
3. It treated extra material as nonblocking because required content was present.

**Verified outcome.** Visual inspection occurred, but its acceptance criterion did not require removing irrelevant neighboring material.

| Effect | Finding |
|---|---|
| Quality | Earlier scores reflected full-page inputs; the exact quality cost is not isolated. |
| Operations | Mis-scoped inputs persisted into experiments. |
| Learning | Observation alone did not cause correction when review judged the issue nonblocking. |

**Historical decision.** Later user intervention changed the required image unit to source-specific regions.

**Retrospective implication.** Criterion mismatch is better supported than the claim that no agent looked at images.

**Initiative and attribution.** Early audit agent-recorded; corrective whole-page diagnosis explicitly user-originated in the lead chat.

**Interpretation.** Criterion mismatch is better supported than the claim that no agent looked at images.

**Limits and alternative explanations.** Current local image assets were unavailable; code, manifests and contemporary inspection receipts were audited rather than pixels re-viewed now.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C18](#c18), [C19](#c19), [C20](#c20). **Time entries:** No quantified interval.

**Correction history:** R02 — Contemporary records describe inspections. The important failure was judging neighboring content nonblocking; the quadrant review separately omitted visual interpretation.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-visual-input-audit.md)

## C18

### Early source-group crop prototype had disputed gain

**Group:** Vision · **Classification:** limited prototype and uncertain measurement · **Record type:** case.

**Initial expectation.** Higher-resolution coherent source-group crops could reduce full-page dilution.

**Recorded sequence**

1. Three cases were cropped by layout from headings through complete source groups, directly rendered at 220 DPI.
2. A separate visual review recorded no clipping; multi-page generalization remained untested.
3. The diagnostic scored 3/6 versus a preserved 2/6, but the entire extra point was disputed.

**Verified outcome.** Genuine layout-aware cropping existed before the later correction, without a secure gain or general pipeline.

| Effect | Finding |
|---|---|
| Quality | No secure one-point benefit. |
| Operations | A bounded prototype and fallback were produced. |
| Learning | This was distinct from generic quadrants. |

**Historical decision.** No general crop pipeline or secure quality gain was promoted from the disputed three-case prototype.

**Retrospective implication.** Small evidence and disputed grading limited what the experiment established.

**Initiative and attribution.** Agent prototype; precise originating prompt unknown.

**Interpretation.** Small evidence and disputed grading limited what the experiment established.

**Limits and alternative explanations.** Three selected cases; no universal parser or full-exam result.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C17](#c17), [C19](#c19), [C20](#c20). **Time entries:** No quantified interval.

**Correction history:** R02 — Contemporary records describe inspections. The important failure was judging neighboring content nonblocking; the quadrant review separately omitted visual interpretation.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-source-group-crop-prototype.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-source-crops-review.md)

## C19

### Generic quadrant zoom was not source-image extraction

**Group:** Vision · **Classification:** valid narrow negative and review scope gap · **Record type:** case.

**Initial expectation.** Providing local views alongside a full page might help visual interpretation.

**Recorded sequence**

1. Each request retained the full page followed by four tiles covering 55% width and height with central overlap.
2. Review checked exact pixel mapping and explicitly omitted visual interpretation.
3. Eight paired answers completed in 6m11s; both arms scored 1/6 and the route was parked.

**Verified outcome.** The tiling method did not help this panel; it did not test removal of irrelevant page content.

| Effect | Finding |
|---|---|
| Quality | No gain in the tested zoom panel. |
| Operations | The intended algorithm ran successfully. |
| Learning | Pixel preservation did not prove the tiles formed useful visual units. |

**Historical decision.** Park the tested generic zoom route after its tied result.

**Retrospective implication.** Do not generalize that result to source-specific image extraction.

**Initiative and attribution.** Agent/lead diagnostic; user later challenged the image preparation.

**Interpretation.** Algorithm correctness and task suitability were different acceptance questions.

**Limits and alternative explanations.** Tiles can divide figures, although the intact full page remained in the request. No fresh pixel inspection in this audit.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C17](#c17), [C18](#c18), [C20](#c20). **Time entries:** T03.

**Correction history:** R02 — Contemporary records describe inspections. The important failure was judging neighboring content nonblocking; the quadrant review separately omitted visual interpretation.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/160)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-visual-zoom-prep-review.md)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-visual-zoom-result.md)

## C20

### User-requested source crops and organizer package integration

**Group:** Integration · **Classification:** input correction and successful compatibility test · **Record type:** case.

**Initial expectation.** Use relevant source images and accept the organizer's actual package structure.

**Recorded sequence**

1. User explicitly flagged full-page inputs; issue171 required complete source regions and correct associations.
2. PR172 delivered 21 lossless crops and 32 references, removing neighboring artwork from an incorrect association.
3. The real adapter/preparation/export path processed all 37 organizer mock items with a synthetic provider; visual and byte-level checks passed.

**Verified outcome.** Corrected inputs and package compatibility were demonstrated. Later Gemma scores were 39/60 versus 38/60 previously.

| Effect | Finding |
|---|---|
| Quality | Derived on the same 30 image-bearing IDs: original native-thinking 38-point reconciliation 21/34, corrected-input Gemma 39-point grade 24/34. This is not a comparison to every later run also scoring 38. |
| Operations | A concrete end-to-end package contract was delivered. |
| Learning | Checks matched deterministic input/export behavior; visual review assessed actual regions. |

**Historical decision.** Use the corrected source package; preserve previous runs as full-page evidence.

**Retrospective implication.** A successful bounded task after the appropriate input contract was specified.

**Initiative and attribution.** Explicit human diagnosis and request; agent implementation and independent review.

**Interpretation.** A successful bounded task after the appropriate input contract was specified.

**Limits and alternative explanations.** The synthetic run proves compatibility, not model quality. Later scores also differ in runtime/recovery and stochastic/grading conditions. Two related changes share one PR and are one case, not independent successes.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C17](#c17), [C18](#c18), [C19](#c19), [C35](#c35), [C37](#c37). **Time entries:** E08.

**Correction history:** R02 — Contemporary records describe inspections. The important failure was judging neighboring content nonblocking; the quadrant review separately omitted visual interpretation. R13 — The comparator is specifically the original native-thinking 38-point reconciliation, using the same 30 image-bearing IDs from crop-spec; it is not necessarily the later recovery rehearsal.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/170)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/171)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/pull/172)
- [Evidence 4](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-corrected-gemma40-grade.json)
- [Evidence 5](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-full-thinking-review-reconciliation.json)
- [Evidence 6](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/source-crops-prep/crop-spec-v1.json)

## C21

### Six-topic argument-planning study remained prepared but unused

**Group:** Execution · **Classification:** handoff and unfinished integration · **Record type:** case.

**Initial expectation.** After span edits showed no gain, compare a strong thinking control with plan-then-prose on six DEV topics.

**Recorded sequence**

1. The proposed wave specified 18 calls and a 45-minute envelope.
2. A promised manifest did not arrive and the root took over after a checkpoint.
3. A CPU reference with 14 tests existed, but live transport/guardian were not implemented or qualified; prepared-v1 remained archived and unused.

**Verified outcome.** The intended selection question was not answered by a model run.

| Effect | Finding |
|---|---|
| Quality | No quality comparison. |
| Operations | Preparation effort produced no executed study; active effort unknown. |
| Learning | Prepared code was not a qualified invocation path. |

**Historical decision.** Lead took over preparation; the six-topic prepared-v1 remained archived and unused.

**Retrospective implication.** Keep its prepared/unrun evidence separate from the later four-case study.

**Initiative and attribution.** Lead assignment after worker results; exact human origin unknown.

**Interpretation.** A missed handoff and incomplete integration, not a negative scientific result.

**Limits and alternative explanations.** Distinct from C22 / issue151. The latter's zero-call receipt must not substitute for this study's evidence.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C22](#c22), [C32](#c32). **Time entries:** No quantified interval.

**Correction history:** R07 — They were separate. Issue168 was created before issue151's final expiry, but dispatched later. No-call evidence must remain tied to its own study.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5849836497)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5850512012)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/essay-planning-prep/README.md)

## C22

### Structured-route diagnostic missed both launch windows

**Group:** Execution · **Classification:** dependency and blocker visibility failure · **Record type:** case.

**Initial expectation.** Complete a four-case structured-route comparison after the lead supplied shared inputs and runtime.

**Recorded sequence**

1. Initial host/handoff preparation was delivered; routes and panel were initially absent.
2. After handoff, a typed-stage invoker still needed integration; the worker promised completion and launch.
3. The first start window was missed; the lead extended once, checked no experiment was running, then expired the second window.
4. A later report attributed interrupted supporting agents to usage limits before both deadlines.

**Verified outcome.** Zero scored calls and zero warmups; the lead ultimately stopped and reassigned resources.

| Effect | Finding |
|---|---|
| Quality | The scientific question remained unanswered. |
| Operations | A 45m49s extension window ended without experiment calls; active coding and continuous GPU idle time unknown. |
| Learning | Assignment and prepared parts did not establish runnable work; blocker information arrived late. |

**Historical decision.** Expire the authorization and redirect the resource.

**Retrospective implication.** Unfinished integration plus late availability signaling; a pure approval-loop explanation is unsupported.

**Initiative and attribution.** Lead supplied prerequisites and checked execution; supporting-agent interruption retrospectively reported.

**Interpretation.** Unfinished integration plus late availability signaling; a pure approval-loop explanation is unsupported.

**Limits and alternative explanations.** Initial preparation ETA was not a launch promise. About 26m25 from PR157 creation to planned integration completion, then 20m launch margin, is not 20m total coding time. Alternative worker capacity is unknown.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C21](#c21), [C28](#c28), [C35](#c35). **Time entries:** E05.

**Correction history:** R07 — They were separate. Issue168 was created before issue151's final expiry, but dispatched later. No-call evidence must remain tied to its own study. R08 — The recorded ETA placed completion about 26m25 after PR157 creation, followed by a 20-minute launch margin. Actual work start and transfer completion remain unknown.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/151)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/151#issuecomment-5850949292)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/151#issuecomment-5851470230)
- [Evidence 4](https://github.com/kwiscion/machinekind-matura/issues/151#issuecomment-5853593104)

## C23

### Essay RAG preparation explicitly stopped at its deadline

**Group:** Retrieval · **Classification:** dependency delay and deliberate stop · **Record type:** case.

**Initial expectation.** Prepare a topic/query/filter/writer essay route using full Wikipedia, with a later bounded inference release.

**Recorded sequence**

1. Issue183 assigned preparation with a 07:20 Warsaw gate; full corpus superseded the small reference set.
2. The index arrived early, but filtering and essay integration remained dependencies.
3. At 07:19 the lead stopped before GPU calls to preserve final integration; no essay-RAG quality claim was made.
4. The user later asked whether the route existed and reopened the work.

**Verified outcome.** This was a documented deadline stop, not a negative experiment or purely unexplained abandonment.

| Effect | Finding |
|---|---|
| Quality | No quality trial at this stage. |
| Operations | No GPU calls; the elapsed preparation window does not measure labor. |
| Learning | The scope change was recorded but not shown proactively communicated to the user. |

**Historical decision.** Use qualified coverage prompting then; later owner direction reopened essay RAG.

**Retrospective implication.** The stop rationale was contemporaneous. Upstream readiness and user-facing visibility remain concerns.

**Initiative and attribution.** Lead preparation assignment and explicit stop; human later discovered omission and reactivated.

**Interpretation.** The stop rationale was contemporaneous. Upstream readiness and user-facing visibility remain concerns.

**Limits and alternative explanations.** The precise remaining essay blocker and whether continuation would have paid off are unknown. Preparation-only was not a promise of a GPU run.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C12](#c12), [C24](#c24), [C25](#c25), [C36](#c36), [C37](#c37). **Time entries:** E06.

**Correction history:** R05 — Its prep-only issue was explicitly stopped to preserve final integration. The user nevertheless had to ask to learn that the selected harness excluded it.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/183)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/183#issuecomment-5852933186)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/182#issuecomment-5852114323)

## C24

### Full-Wikipedia filter first run failed its auxiliary contract

**Group:** Auxiliary mechanisms · **Classification:** invalid mechanism and late detection · **Record type:** case.

**Initial expectation.** Queries and relevance judgments would admit useful evidence before final answering.

**Recorded sequence**

1. Nine CPU tests and host preflight passed; a fake provider emitted desired JSON when prompted.
2. The ordinary answer harness accepted nonempty outputs without checking relevance-judgment semantics.
3. Of 30 first-pass judgments, 26 violated the contract, three timed out and one validly rejected; no passages were admitted.

**Verified outcome.** 53 attempts and 28m48s yielded bare-fallback answers rather than a functioning RAG quality comparison.

| Effect | Finding |
|---|---|
| Quality | No inference about functioning retrieval benefit is justified. |
| Operations | The batch continued until downstream admission checks; repair was needed. |
| Learning | The acceptance unit did not match the stage's task. |

**Historical decision.** Repair framing, schema enforcement, semantic retries and real probes before a second run.

**Retrospective implication.** Task-level qualification was absent even though infrastructure/provenance checks were extensive.

**Initiative and attribution.** Lead/agent implementation and subsequent diagnosis.

**Interpretation.** Task-level qualification was absent even though infrastructure/provenance checks were extensive.

**Limits and alternative explanations.** Some direct/fallback output still existed; not every second is provably wasted. First invalid-response timestamp and contemporaneous human awareness are not established.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C25](#c25), [C27](#c27). **Time entries:** T05, E03.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-fullwiki-filtered-rag-result.json)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/final-package-prep/recovery_harness.py#L74)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/filtered-rag-prep/test_study.py#L80)

## C25

### Repaired filter became measurable but remained expensive

**Group:** Auxiliary mechanisms · **Classification:** successful repair and limited diagnostic · **Record type:** case.

**Initial expectation.** Qualify the query/judge contract before repeating the six-item comparison.

**Recorded sequence**

1. V2 put auxiliary instructions first, quoted the exam as data, added native schemas and semantic recovery.
2. Four actual-model probes passed before the main batch.
3. Thirty judgments became valid and 13 quotes were admitted; 55 attempts took 31m51s.

**Verified outcome.** The functioning diagnostic scored 3/6 to 4/6, with two gains and one regression; it was not a full-exam promotion.

| Effect | Finding |
|---|---|
| Quality | Small exploratory gain with relevance errors remaining. |
| Operations | Repair-to-declaration and grading consumed additional elapsed time; the report arrived near the diagnostic cutoff. |
| Learning | A real probe directly addressed the original qualification gap. |

**Historical decision.** Retain diagnostic evidence; generic integration and essay qualification remained separate.

**Retrospective implication.** Successful semantic qualification did not imply economical task allocation or broad quality benefit.

**Initiative and attribution.** Lead/agent repair; tied to the owner-requested full-corpus path.

**Interpretation.** Successful semantic qualification did not imply economical task allocation or broad quality benefit.

**Limits and alternative explanations.** Selected known panel, direct-grade sensitivity, and reviewer awareness limit causal strength. This is the repaired phase of C24, not independent replication of the whole strategy.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C23](#c23), [C24](#c24), [C26](#c26). **Time entries:** T07, E03.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/filtered-rag-prep/V2.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-fullwiki-filtered-rag-v2-result.json)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/182#issuecomment-5852932813)

## C26

### Fast Qwen full-Wikipedia diagnostic tied the direct route

**Group:** Retrieval · **Classification:** limited neutral diagnostic · **Record type:** case.

**Initial expectation.** A faster auxiliary profile might make full-corpus retrieval useful within final runtime limits.

**Recorded sequence**

1. Short thinking-off auxiliary calls were combined with direct/final reasoning.
2. The six-item result was 4/6 direct and 4/6 filtered.
3. Changed outcomes had no admitted evidence; the sole evidence-bearing item stayed correct.

**Verified outcome.** No demonstrated retrieval-backed gain on this panel; speed improvement was not a controlled cross-model comparison.

| Effect | Finding |
|---|---|
| Quality | Neutral aggregate with no identified evidence-caused improvement. |
| Operations | Approximately 15-minute diagnostic; direct/final reasoning dominated. |
| Learning | A tie did not test essay retrieval or prove full-exam futility. |

**Historical decision.** Lead recommended RAG off at that point; owner later selected both RAG routes despite limited evidence.

**Retrospective implication.** The local neutral finding was valid within scope, but broader strategy remained uncertain.

**Initiative and attribution.** Agent diagnostic; final both-route choice explicitly human.

**Interpretation.** The local neutral finding was valid within scope, but broader strategy remained uncertain.

**Limits and alternative explanations.** Small selected nonessay panel; stochastic reruns and model/profile differences. Not included in the original nine-run time subtotal.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C12](#c12), [C25](#c25), [C36](#c36), [C37](#c37). **Time entries:** T13.

**Correction history:** R04 — The documented 40-point full validation used direct Qwen with RAG off. Multiple configuration changes confound the earlier comparison; the final exam was different. R14 — The frozen primary report states 907.22 seconds; it is recorded as supplemental and excluded from the historical core-nine subtotal.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-fast-qwen-rag-independent-result.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5853913474)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5853542202)

## C27

### Factual referee returned rewrites instead of valid selections

**Group:** Auxiliary mechanisms · **Classification:** failed selection and mixed useful evidence · **Record type:** case.

**Initial expectation.** Select the stronger of two saved candidate answers using a strict candidate ID.

**Recorded sequence**

1. Seven CPU tests checked export and fallback; ordinary runtime acceptance did not validate selector semantics.
2. Twenty A/B finals were generated, then ten selectors ran before strict export parsing.
3. Nine selectors rewrote answers and one used an unknown ID; all failed, so baseline A was exported.

**Verified outcome.** The 33m46s batch yielded useful A/B evidence, 7/12 versus 5/12, but zero functioning referee selections.

| Effect | Finding |
|---|---|
| Quality | Export preserved 7/12; retrospective oracle was 8/12. |
| Operations | 31 calls include candidate generation, so selector-only cost is unavailable. |
| Learning | A working referee's value remained untested. |

**Historical decision.** Discard the route without successful requalification.

**Retrospective implication.** Fallback contained answer damage but did not stop time consumption by an invalid stage.

**Initiative and attribution.** Lead/agent experiment; final abandonment rationale should not be recast as a general anti-referee result.

**Interpretation.** Fallback contained answer damage but did not stop time consumption by an invalid stage.

**Limits and alternative explanations.** Do not count the whole duration as useless. Distinct from the essay ID-selector replay.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C24](#c24), [C28](#c28), [C29](#c29). **Time entries:** T06.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/186#issuecomment-5852521462)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/brainstorm-prep/handoff.json)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/brainstorm-prep/wave.py#L157)

## C28

### Essay branching found a better draft but rewriting lost it

**Group:** Essays · **Classification:** generation success and selection degradation · **Record type:** case.

**Initial expectation.** Generate alternative topic drafts and select or improve the strongest essay.

**Recorded sequence**

1. Saved candidates included an essay graded 11/15 against a direct 8/15.
2. Selection combined with rewriting produced a complete essay graded 6/15.
3. Further work separated saved-candidate selection from rewriting.

**Verified outcome.** The branch generated useful material, but the combined selector/rewrite degraded the exported result.

| Effect | Finding |
|---|---|
| Quality | 6/15 selected rewrite versus 8 direct and 11 best saved draft on a known task. |
| Operations | Candidate generation completed; downstream processing lost value. |
| Learning | Generation, selection and rewriting are separate mechanisms. |

**Historical decision.** Preserve candidate bytes and test ID-only selection separately.

**Retrospective implication.** Later processing can destroy useful earlier work even with complete, well-formed outputs.

**Initiative and attribution.** Lead/agent plan; no direct user origin established in exposed chat.

**Interpretation.** Later processing can destroy useful earlier work even with complete, well-formed outputs.

**Limits and alternative explanations.** Single known essay and provisional grades; oracle is retrospective, not an achieved autonomous score. Issue168 was created before issue151's final expiry and dispatched later.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C22](#c22), [C29](#c29). **Time entries:** No quantified interval.

**Correction history:** R07 — They were separate. Issue168 was created before issue151's final expiry, but dispatched later. No-call evidence must remain tied to its own study.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/168)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-essay-branching-comparison.md)

## C29

### Correct essay choice rejected by strict fence parsing

**Group:** Essays · **Classification:** serialization defect and replay repair · **Record type:** case.

**Initial expectation.** Return a valid ID and export the chosen saved essay without rewriting.

**Recorded sequence**

1. One real selector response chose the saved 11-point draft.
2. A JSON code fence caused strict parsing to reject it and fall back to the 8-point answer.
3. A generic optional-fence repair passed four CPU tests; replay of the same response exported the exact saved draft.

**Verified outcome.** The repair recovered an existing good choice; it was not a new model run or regraded 11-point result.

| Effect | Finding |
|---|---|
| Quality | Replay mapped to the frozen 11/15 draft instead of original 8/15 fallback. |
| Operations | No new inference; original export preserved. |
| Learning | A format error can hide successful model selection. |

**Historical decision.** Use a narrowly corrected parser while retaining original receipts.

**Retrospective implication.** Schema enforcement should distinguish harmless serialization from an invalid choice.

**Initiative and attribution.** Agent repair; exact human trigger unknown.

**Interpretation.** Schema enforcement should distinguish harmless serialization from an invalid choice.

**Limits and alternative explanations.** Child of C28; not independent evidence for general selector quality or full-exam gains.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C28](#c28), [C27](#c27). **Time entries:** No quantified interval.

**Correction history:** R11 — It replayed the same selector response and exported an already graded saved draft. No new inference or regrading occurred.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-essay-selector-id-result.md)

## C30

### LoRA qualification rejected a failing deployed candidate

**Group:** Training · **Classification:** useful negative and resource reallocation · **Record type:** case.

**Initial expectation.** A paired deployed-artifact test would establish whether the essay adapter improved useful answers.

**Recorded sequence**

1. Launch preparation involved changed recovery/context requirements, a real runner gap, and a redundant approval request.
2. The 45m50s evaluation completed 16/16 controls but only 2 complete candidate essays, 2 partial runaways and 12 unattempted placeholders.
3. Both complete content pairs favored control; further automatic training was parked and priority reassigned.

**Verified outcome.** The candidate failed operationally and on available content comparisons; it was not deployed.

| Effect | Finding |
|---|---|
| Quality | No quality win; incomplete attempts remained in denominators. |
| Operations | Training/preparation cost exceeds this evaluation duration and is not fully measured. |
| Learning | Negative evidence changed the next action and protected remaining resources. |

**Historical decision.** Reject candidate promotion; do not launch the proposed epoch retry automatically; redirect work.

**Retrospective implication.** Successful rejection and pivot. Some coordination churn existed, but genuine runtime changes prevent treating all exchanges as bureaucracy.

**Initiative and attribution.** Worker evidence and lead decision; account identity does not prove human authorship.

**Interpretation.** Successful rejection and pivot. Some coordination churn existed, but genuine runtime changes prevent treating all exchanges as bureaucracy.

**Limits and alternative explanations.** Does not prove LoRA generally ineffective or isolate the training failure's cause. Related data preparation C11 is not additional evaluation runtime.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C11](#c11), [C13](#c13). **Time entries:** T04.

**Correction history:** R06 — Several documented stops and reassignments changed mechanisms. The quality and autonomy of all originating choices remain incompletely attributed.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/117#issuecomment-5850879863)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/117#issuecomment-5851471034)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/117#issuecomment-5851842361)

## C31

### Essay critic gain shrank after independent calibration

**Group:** Grading · **Classification:** calibration disagreement and corrected claim · **Record type:** case.

**Initial expectation.** Critic/rewrite replication would demonstrate reliable essay improvement.

**Recorded sequence**

1. On the same four essays, the experimenter's grader scored direct 14/60 and rewrite 27/60, reporting four wins.
2. Independent review of the same eight finals scored 35/60 and 39/60, with one regression; a scoped third review fell between interpretations.
3. The lead downgraded the claim and introduced argument/error/coherence calibration requirements.

**Verified outcome.** Apparent benefit shrank from +13 to +4 across FOUR essays, not a full 40-item exam.

| Effect | Finding |
|---|---|
| Quality | Magnitude and consistency were less secure; no deployment on the raw gain was traced. |
| Operations | About 51 minutes elapsed from announcement to lead correction, not measured active reviewer time. |
| Learning | Raw grades had guided replication; independent review changed subsequent claims/protocol. |

**Historical decision.** Keep original grades and treat gain as development evidence; calibrate consequential rubric judgments.

**Retrospective implication.** Threshold interpretation and factual-error disputes made numerical feedback unstable.

**Initiative and attribution.** Worker grader, independent Sol and scoped Astra review; no verified human grading override.

**Interpretation.** Threshold interpretation and factual-error disputes made numerical feedback unstable.

**Limits and alternative explanations.** Same broad framework, but exact full grader instructions/model versions not all preserved. Independent reviewer knew arm identities/direction, though exact owner grades were opened after score freeze.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C32](#c32), [C33](#c33). **Time entries:** E04.

**Correction history:** R10 — They sum four essays at 15 points each. Both totals use the same /60 denominator but are not the 40-item exam.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-essay-c3-replication-review.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-essay-c3-replication-review.json)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5848937914)

## C32

### Conservative essay span edits gave no added benefit

**Group:** Essays · **Classification:** valid narrow negative and measurement checks · **Record type:** case.

**Initial expectation.** Restricting edits to factual spans might avoid harmful whole-essay rewriting.

**Recorded sequence**

1. Six DEV essays totaled 46/90 for nonthinking drafts and 57.5/90 for thinking drafts; patched thinking also totaled 57.5/90.
2. There was only one changed essay, four zero-edit identities and one unchanged fallback; the changed essay still contained an incorrect replacement.
3. Independent review reproduced aggregation, not every historical grade, and the patcher was not promoted.
4. A separate independent six-slot mixed review corrected deduction arithmetic from 53 to 57 while preserving its original freeze and historical judgments; it did not replace the owner's 46/57.5/57.5 totals or adjudicate the whole wave.

**Verified outcome.** No measured patch benefit; the count of patched outputs overstated how many texts actually changed.

| Effect | Finding |
|---|---|
| Quality | No gain beyond the thinking drafts under the recorded grading. |
| Operations | 18 calls took 18m09.809s; one verifier output hit a length limit. |
| Learning | Evidence relevance did not guarantee a replacement claim was entailed. |

**Historical decision.** Move toward explicit argument planning rather than further patch tuning.

**Retrospective implication.** A meaningful narrow negative followed by a different mechanism proposal.

**Initiative and attribution.** Agent/lead progression from prior essay results.

**Interpretation.** A meaningful narrow negative followed by a different mechanism proposal.

**Limits and alternative explanations.** Two-rater overwrite was fixed before this aggregation; a remaining narrative-floor bug affected zero actual ratings. Do not treat every arithmetic bug as corrupting these totals.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C21](#c21), [C31](#c31), [C33](#c33). **Time entries:** T10.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-26-essay-edit-independent-review.md)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/80#issuecomment-5849836497)

## C33

### Three-rater aggregation bug caught before use

**Group:** Grading · **Classification:** evaluator defect and successful prevention · **Record type:** case.

**Initial expectation.** A third review would resolve disagreement using the declared median rule.

**Recorded sequence**

1. A synthetic [0,6,6] check returned mean 4 instead of median 6 and kept asking for another review.
2. The review isolated the three-rater path from the existing two-rater dry run.
3. The aggregation path was fixed and tested in PR22.

**Verified outcome.** A consequential evaluator bug was corrected without invalidating unrelated existing grades.

| Effect | Finding |
|---|---|
| Quality | No demonstrated affected exam score. |
| Operations | Preventive correction rather than a model rerun. |
| Learning | The evaluator itself was subjected to adversarial checks. |

**Historical decision.** Use the repaired aggregation; avoid rewriting unaffected results.

**Retrospective implication.** A strong example of testing a deterministic control against its actual contract.

**Initiative and attribution.** Agent/lead-side audit; no direct human trigger established.

**Interpretation.** A strong example of testing a deterministic control against its actual contract.

**Limits and alternative explanations.** Distinct from subjective C3 calibration and from other essay arithmetic bugs.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C31](#c31), [C32](#c32). **Time entries:** No quantified interval.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/11#issuecomment-5844023940)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/11#issuecomment-5844879825)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/pull/22)

## C34

### Recovery rehearsal qualified complete-answer delivery

**Group:** Delivery · **Classification:** operational success with limited quality benefit · **Record type:** case.

**Initial expectation.** Preserve usable answers and autonomously recover failed calls within a bounded final workflow.

**Recorded sequence**

1. The owner priority reset required recovery and no blanks; root prepared a complete pinned package.
2. The real full rehearsal included two frozen injected faults plus a natural failure.
3. 46 calls in 19m17s produced 40 nonblank answers and zero placeholders; cleanup/context behavior were observed.

**Verified outcome.** Recovery worked operationally; the score remained 38/60 and recovered answers were not automatically correct.

| Effect | Finding |
|---|---|
| Quality | Previously blank items recovered only 1/6 points; other changes offset quality gains. |
| Operations | The tested recovery harness was reused. |
| Learning | Failure behavior was exercised end-to-end rather than inferred from mocked success. |

**Historical decision.** Reuse the qualified harness, address a narrow mechanical essay-selection issue, and allocate headroom to research.

**Retrospective implication.** The actual acceptance unit and tests matched the delivery requirement.

**Initiative and attribution.** Owner priority reset is documented; exact authorship of each implementation choice is not established.

**Interpretation.** The actual acceptance unit and tests matched the delivery requirement.

**Limits and alternative explanations.** A single rehearsal does not guarantee every later candidate/runtime. It did not establish the 48-point target.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C15](#c15), [C35](#c35), [C37](#c37). **Time entries:** T02.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5850602964)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-champion-rehearsal-result.md)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/blob/b4f2d9abdc546788d09b64d352cda35ed8e5f2cf/agentsLog/kwiscion/2026-09-27-champion-rehearsal-score-delta.md)

## C35

### Full Qwen confirmation replaced an optimistic composite

**Group:** Selection · **Classification:** measured confirmation and successful handoff · **Record type:** case.

**Initial expectation.** Check whether a promising standalone essay translated into a complete exam result.

**Recorded sequence**

1. 33 prior ordinary points plus an 11-point essay were explicitly labeled an unmeasured 44-point composite.
2. One execution owner closed concrete host/input prerequisites and launched about 98 seconds after declaration.
3. 44 calls in 27m58s completed all 40 answers, recovering four timeouts; the measured score was 40/60, including an 8-point essay.
4. The lead selected the measured direct candidate and retained the prior fallback.

**Verified outcome.** A real full-system result replaced posthoc composition and informed selection.

| Effect | Finding |
|---|---|
| Quality | 40/60 measured on known validation; not proof of robust superiority over Gemma 39 or final-exam uplift. |
| Operations | A complete executable path yielded fast dispatch and terminal evidence. |
| Learning | The standalone essay gain did not repeat fully, and that was retained rather than hidden. |

**Historical decision.** Select the measured Qwen route while acknowledging the unmet 48/60 target.

**Retrospective implication.** A bounded uncertainty, available interfaces and an actual selection consequence formed a closed loop.

**Initiative and attribution.** Lead/agents executed the confirmation after owner-directed Qwen reassessment. The user clarified that revisiting Qwen was their intervention; the detailed confirmation design is not independently attributed.

**Interpretation.** A successful execution and evidence-to-selection loop, not evidence that the initial strategic reconsideration was autonomous.

**Limits and alternative explanations.** Single provisional grading pass; configuration and stochastic changes prevent attributing the improvement to one component.

**Evidence status.** Primary records support the technical sequence; firsthand user clarification supplies initiative attribution where original prompts were not recovered.

**Related cases:** [C02](#c02), [C04](#c04), [C20](#c20), [C34](#c34), [C37](#c37), [C39](#c39). **Time entries:** T08, E07.

**Correction history:** R04 — The documented 40-point full validation used direct Qwen with RAG off. Multiple configuration changes confound the earlier comparison; the final exam was different. R15 — The user explicitly clarifies that both resulted from their intervention. Preserve the technical successes as owner-directed follow-through; exact contemporaneous prompt locations remain unrecovered.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5852386688)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5852637129)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/95#issuecomment-5852886959)
- [Evidence 4](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5853248498)
- Current retrospective user clarification: revisiting Qwen and changing reasoning budgets resulted from owner intervention.

## C36

### Reopened parallel essay RAG exceeded actual serving concurrency

**Group:** Retrieval · **Classification:** capacity assumption and mixed result · **Record type:** case.

**Initial expectation.** Run up to three quick essay retrieval trials after the owner reopened the route.

**Recorded sequence**

1. The user asked whether essay RAG existed and requested a short multi-attempt diagnostic.
2. Three clients launched, but the model runtime admitted only one inference slot; a writer blocked auxiliary calls.
3. One essay completed at 9/15 against a saved direct 8/15; two trials timed out. Serial recovery missed its cutoff and made no calls.

**Verified outcome.** One limited positive essay signal and a useful concurrency finding, not a completed three-way comparison.

| Effect | Finding |
|---|---|
| Quality | No full-exam gain or causal one-point retrieval estimate established. |
| Operations | Approximately 2m33s execution, 88 calls, 16 failed attempts; not a 20-minute executed run. |
| Learning | Requested parallelism was not demonstrated capacity. |

**Historical decision.** Use serial execution in the final workflow; owner still chose both RAG routes.

**Retrospective implication.** A resource capability assumption survived into a deadline-sensitive experiment.

**Initiative and attribution.** Explicit human reactivation and final route choice; agents implemented and measured.

**Interpretation.** A resource capability assumption survived into a deadline-sensitive experiment.

**Limits and alternative explanations.** Failures include quote-filter and transport issues. Do not multiply the shared operator duration by three.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C23](#c23), [C26](#c26), [C37](#c37). **Time entries:** T09.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/issues/191)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/191#issuecomment-5853732755)
- [Evidence 3](https://github.com/kwiscion/machinekind-matura/issues/191#issuecomment-5853950686)

## C37

### Frozen manual workflow passed a real limited delivery smoke

**Group:** Delivery · **Classification:** integration and resumability success · **Record type:** case.

**Initial expectation.** Provide one usable offline command for the owner to run and export the final package.

**Recorded sequence**

1. The owner selected ordinary and essay RAG and a 65-minute total target.
2. PR192 staged a pinned Qwen model, full index, direct-answer preservation, serial routes, bounded recovery and export.
3. A real two-item image/essay smoke passed in 5m34s with 49 completed calls and zero placeholders.
4. Resume returned byte-identical outputs with no additional model calls.

**Verified outcome.** The reviewed manual integration and resume path worked on a limited DEV package.

| Effect | Finding |
|---|---|
| Quality | No full-exam quality gain was measured by the smoke. |
| Operations | A runnable delivery entry point and recovery behavior were demonstrated. |
| Learning | The actual PowerShell-to-remote-to-export path was exercised. |

**Historical decision.** Freeze the manual solution for owner-run submission.

**Retrospective implication.** Concrete delivery criteria and a complete execution owner produced a usable artifact.

**Initiative and attribution.** Explicit human route/deadline decision and agent integration.

**Interpretation.** Concrete delivery criteria and a complete execution owner produced a usable artifact.

**Limits and alternative explanations.** Two items do not qualify full-exam runtime or quality. Reviewed Windows dependency hashes were environment-specific. Submission itself remained manual.

**Evidence status.** Primary records inspected during this retrospective; causal interpretation separately qualified

**Related cases:** [C20](#c20), [C26](#c26), [C34](#c34), [C35](#c35), [C36](#c36), [C39](#c39). **Time entries:** T11.

**Sources**

- [Evidence 1](https://github.com/kwiscion/machinekind-matura/pull/192)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/3#issuecomment-5854111304)

## C38

### Aggregate weight constraint changed architecture scope

**Group:** Governance · **Classification:** external constraint and replanning · **Record type:** case.

**Initial expectation.** All submitted weights together must satisfy the aggregate size limit.

**Recorded sequence**

1. The user clarified the aggregate 8 GB plus tolerance rule in the lead chat.
2. The lead adjusted the plan toward one shared model, communicated the constraint and updated documentation.
3. Multi-model/adapter routes required compatibility with the aggregate budget.

**Verified outcome.** A material external constraint was incorporated into the strategy.

| Effect | Finding |
|---|---|
| Quality | No isolated score effect. |
| Operations | Some previously plausible architecture options became ineligible or required new serving proof. |
| Learning | Rule clarification was distinct from an autonomous research failure. |

**Historical decision.** Use a conservative aggregate cap and avoid duplicate full-model serving in the final package.

**Retrospective implication.** Changing constraints can explain scope changes without implying a bad original estimate.

**Initiative and attribution.** Explicit human clarification; agent replanning and integration.

**Interpretation.** Changing constraints can explain scope changes without implying a bad original estimate.

**Limits and alternative explanations.** This episode was examined mainly through the lead chat, not a full independent audit of every affected experiment.

**Evidence status.** Mixed primary records and user/chat context; see limitations

**Related cases:** [C01](#c01), [C30](#c30), [C37](#c37). **Time entries:** No quantified interval.

**Sources**

- [Evidence 1](thread://01a0da6d-1f45-7ae0-a046-5c2f651c5fed?hostId=local)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/pull/132)

## C39

### Final competition result and limits of attribution

**Group:** Outcome context · **Classification:** user-reported outcome · **Record type:** context.

**Initial expectation.** Compete strongly and test autonomous research with little human strategic involvement.

**Recorded sequence**

1. The user reported 46/60 on the final evaluation, versus the winner's 54/60 and a lower-half placement.
2. The preserved full validation candidate had scored 40/60 on a different exam.
3. The user reported substantial strategic intervention despite expecting mainly resource provisioning and submission duties.

**Verified outcome.** Useful delivery was achieved, but the reported competitive and autonomy expectations were not met.

| Effect | Finding |
|---|---|
| Quality | Final score and placement are user-reported; not independently verified here. |
| Operations | Submission occurred according to the user; full final elapsed runtime is not established by the smoke. |
| Learning | A different final exam cannot provide a causal RAG or configuration delta. |

**Historical decision.** The final solution was submitted according to the user's outcome report.

**Retrospective implication.** Use the project as evidence for autonomous-team workflow analysis, not a retrospective proof of one model component's value.

**Initiative and attribution.** User supplies outcome and expectations.

**Interpretation.** The numerical outcome and human effort are separate dimensions of project success.

**Limits and alternative explanations.** No counterfactual score for alternative choices or architecture. Target 48/60 referred to known validation, not an identical final test.

**Evidence status.** Mixed primary records and user/chat context; see limitations

**Related cases:** [C01](#c01), [C35](#c35), [C37](#c37), [C40](#c40). **Time entries:** No quantified interval.

**Correction history:** R04 — The documented 40-point full validation used direct Qwen with RAG off. Multiple configuration changes confound the earlier comparison; the final exam was different.

**Sources**

- [Evidence 1](thread://01a0ea46-3646-7080-a3ee-ea712bee6660?hostId=local)
- Current retrospective user account (2026-10-08)

## C40

### Activity counts and incomplete project time accounting

**Group:** Outcome context · **Classification:** measurement limit · **Record type:** context.

**Initial expectation.** Quantify coordination, repair, experimentation and waiting across the project.

**Recorded sequence**

1. The earlier audit recorded 145 PRs, 47 issues, 583 discussion comments, 9 review records, 385 main commits and six accounts over roughly 33 hours of repository activity.
2. This retrospective reconstructed selected run receipts and correction/no-launch intervals.
3. No complete active-time ledger across agents, hosts and human work was available.

**Verified outcome.** Local elapsed costs and summed run durations are quantifiable; the share of the project spent on bureaucracy is not.

| Effect | Finding |
|---|---|
| Quality | No direct quality effect. |
| Operations | Selected batch runtimes must not be added to overlapping repair windows or interpreted as staff-hours. |
| Learning | Message volume and issue lifetime are not productivity or active-time measures. |

**Historical decision.** No separate historical decision asserted in this record.

**Retrospective implication.** Keep time types, overlap and coverage explicit; do not invent a whole-project percentage.

**Initiative and attribution.** User requested quantification; retrospective agents reconstructed the evidence.

**Interpretation.** Instrumentation limits constrain the strength of the bureaucracy hypothesis.

**Limits and alternative explanations.** Counts are a prior snapshot, not current live totals. 583 discussion plus 9 review messages explains the earlier 592 combined figure; neither equals active coordination time.

**Evidence status.** Mixed primary records and user/chat context; see limitations

**Related cases:** [C01](#c01), [C39](#c39). **Time entries:** No quantified interval.

**Correction history:** R12 — They measure activity or elapsed spans. No complete active-time accounting exists, and concurrent intervals cannot be added as wall-clock loss. R14 — The frozen primary report states 907.22 seconds; it is recorded as supplemental and excluded from the historical core-nine subtotal.

**Sources**

- [Evidence 1](thread://01a0ea46-3646-7080-a3ee-ea712bee6660?hostId=local)
- [Evidence 2](https://github.com/kwiscion/machinekind-matura/issues/151#issuecomment-5851470230)
