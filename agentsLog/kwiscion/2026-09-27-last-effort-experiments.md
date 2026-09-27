# Last-effort experiments: ranked proposals

Prepared 27 September 2026 for the 08:00 Warsaw development freeze. **Recommendation: prioritize independently gated retrieval on short factual items, then evidence-led essay construction.** These test new mechanisms; generic RAG, longer outputs and another training sweep do not have supporting evidence. This is a proposal, not a run declaration or authorization expansion. No GPU calls, GitHub writes or implementation changes were made.

## Evidence and limits

- Corrected Gemma: **39/60**, 31/45 nonessay and 8/15 essay; 40 complete answers. Lost: history 7, source interpretation 6, incomplete identification 1, essay depth 7. Recovery has no blank-score upside on this run.
- Earlier bounded RAG: **27/60 versus its matched historical bare baseline 35/60**. Six of eight lost points came from essay; recall fixes were offset by new recall mistakes. This is not a corrected-Gemma comparison. It motivates selective evidence admission and protected controls.
- Native pair: Qwen 6/8 versus Gemma 4/8 on six legacy-image items; both missed 14.1. Full corrected Qwen is already running. Do not run another model comparison.
- Essay control repeatedly supplies concrete military examples but superficial diplomacy/institutions. A longer essay alone moved 7 to 8 points, not toward 15. The training candidate had only 2/16 complete outputs versus 16/16 controls: no further training proposed.
- Three-view vision and topic branching are already claimed/running. The ideas below do not duplicate them. Absolute dispatch ownership must come from current issues/live processes, not this report.

All gain ranges below are **hypotheses**, not forecasts or additive gains. Subsets intentionally include known failures and correct sentinels; results are development diagnostics on reused validation, not unbiased generalization estimates. Keep keys isolated from inference. No new corpus derived from exam questions, answers, rubrics or source packs; use only existing independently licensed, provenance-recorded offline material. Runtime estimates assume the current native eligible single model on an H100; most recent Gemma40 took 948 seconds for 41 calls, but call lengths vary greatly.

## 1. Evidence firewall: top five passages independently earn admission

**Hypothesis / potential:** generic retrieval hurts through irrelevant or misleading context. Direct relevance plus explicit support can recover 1–3 factual points without replacing correct answers with nearby historical facts. Highest information value because it separates retriever failure, admission failure and answerer failure.

**Mechanism:** deterministically retrieve five existing-corpus passages per original question. Give each passage its own fresh call containing the complete original question and only that passage. Return `directly_relevant`, the exact question component supported, a short supporting quote, temporal/entity compatibility, and `contradicts_question`. Do not let judges see the draft answer or other passages. Admit only passages with a literal support span and matching scope; an empty admitted set explicitly falls back to the no-retrieval route. Final call gets original inputs and admitted evidence marked as fallible; prohibit copying unsupported conclusions. Retrieval queries use the original question, never answer keys or the candidate answer.

**Frozen diagnostic panel:** 3.2, 7, 11.2, 12.1, 17.2, 19.1, 15.1, 17.1. The final two are correct sentinels previously harmed by RAG. Order: 3.2, 15.1, 12.1, 17.1, then the remaining four.

**Matched arms:** fresh bare, raw top-five RAG, and gated top-five RAG; same model/runtime/sampling and original inputs. Hold retrieval results fixed. This costs 8 calls/item: 3 answers + 5 independent judges, **64 nominal calls**. Reserve 32 retry calls; **96 total**. Judge output cap 1,024; answer/retry cap 4,096; **270,336 generated-token ceiling** including retries. Per-call input cap 24,576, never silently truncate the original input.

**Stop / time / integration:** first-four checkpoint: stop if gated has no gains and any sentinel regression, or if no passage contains relevant supporting evidence. Such a stop means this retriever/corpus did not justify expansion, not that RAG universally fails. 35–45 minutes, hard 45-minute limit. Integration medium: local retrieval, isolated judge calls, evidence schema and empty-set fallback; no new model weights. Diagnose passage relevance without keys; use isolated grading only after outputs freeze.

## 2. Essay as six evidence questions, followed by causality construction

**Hypothesis / potential:** the essay bottleneck is missing developed evidence per required aspect, not fluent prose or topic count. Potential +2–4 essay points, with substantial risk if retrieved facts are wrong or chronology is confused. Run after the existing branching result; reuse its chosen topic only if that topic was selected autonomously, never choose the best topic using grading.

**Mechanism:** one planner extracts exactly six factual research questions from that topic, allocated across its explicitly requested aspects and time interval. Search top five for each and independently gate all 30 passages as in experiment 1. Before writing, construct an evidence ledger: specific event/institution/person, date, supported claim, causal link to the thesis, limitation/counterexample. Two final writers share the same six-question plan: one uses model knowledge, one admitted evidence. Require each body paragraph to establish an example and explain why it supports or limits the thesis. Writer retains the original topic and may reject planner errors. No supplied historical checklist derived from the validation key.

**Matched control / subset:** the single complete validation essay task with all offered topics retained for selection; fresh direct essay plus planned/no-retrieval essay plus planned/gated-retrieval essay. The two planned arms hold the plan and topic fixed, isolating retrieval; the direct comparison estimates the combined policy. This is one-item evidence, insufficient to claim broad essay reliability.

**Budget:** 1 planner + 30 judges + 3 writers = **34 nominal calls**; 12 recovery calls, **46 total**. Planner cap 4,096; judges 1,024; writers/retries 8,192: **157,696 generated tokens maximum**. Per-call input cap 24,576. No automatic second essay topic or extra judge.

**Stop / time / integration:** stop retrieval after ten judgments if all are rejected; retain the structured/no-retrieval arm. Stop if the plan ignores a required aspect or makes unsupported chronological assumptions that the allowed planner retry cannot resolve. 30–45 minutes, hard 45-minute limit. Integration medium, sharing experiment 1's gate. Candidate must beat the autonomous branch final, not merely a weak direct control. Record topic-selection effects separately.

## 3. Independent historical hypotheses, then a contradiction referee

**Hypothesis / potential:** several misses are confident substitutions or unstable recall. Two genuinely independent solutions may contain the correct candidate; a referee that checks dates/entities against the source might select it. Potential +1–3 short-answer points. Main risk: correlated hallucinations or a selector worse than the candidates.

**Mechanism:** generate two fresh candidates in independent contexts: A uses the existing prompt; B first separates each event/person/date and tests alternative interpretations before answering. Referee sees original complete inputs plus randomized A/B finals, not their private reasoning. It must identify material disagreement, check the competing claims against source clues, then answer. Agreement does not automatically count as correctness. Keep A as the fallback on referee failure; an unchanged answer still counts as a call/result.

**Frozen subset:** 3.1, 3.2, 7, 11.1, 11.2, 12.1, 17.1, 17.2, 19.1, 20.2. Includes unstable previously correct items and two current correct sentinels. Do not spend this on the three-view visual panel.

**Budget / control:** A is the matched fresh direct control; B and referee are the treatment. **30 nominal + 12 retry = 42 total calls**, output cap 4,096 each = **172,032 generated tokens**; input cap 24,576. Report A score, B score, final referee score, candidate-oracle score and referee losses separately. Oracle is diagnostic only, never a submit-ready score.

**Stop / time / integration:** after first five items, stop if neither candidate improves on A, or referee loses two available correct candidates. 20–30 minutes, hard 30-minute limit. Integration low-medium: three-call orchestration with original-input preservation. Promote only an autonomous selector, never manual answer composition. Do not run simultaneously with experiment 1 on the same host.

## 4. Solve each shared source family once, then answer its sibling questions

**Hypothesis / potential:** separate calls reconstruct the same era inconsistently; pooling the supplied source context could repair 1–2 points. This uses no external retrieval and no exam-derived persistent corpus.

**Mechanism:** for each shared-source family, one call builds a temporary factual ledger from all supplied sibling questions and their original sources: entities, offices/dates/events, literal observations, uncertainty. It must not infer a fact merely because another sibling asks about it. A second call answers all siblings jointly with explicit IDs, then a mechanical mapper emits each exact answer. Mark the ledger fallible; the second call retains original inputs. This is an inference context transformation, not training or retrieval ingestion.

**Frozen families:** 3.1–3.2; 11.1–11.2; 12.1–12.3; 17.1–17.2; 19.1–19.2; 20.1–20.2. These contain 13 items and include correct siblings to measure collateral damage.

**Matched control / budget:** fresh independent direct answers on all 13 items, plus 6 ledgers and 6 joint answers: **25 nominal + 12 retry = 37 calls**; output cap 4,096 = **151,552 generated tokens**; input cap 32,768. If a family exceeds the original-input cap, do not truncate it: mark unsupported and use direct answers.

**Stop / time / integration:** stop after first three families if no gain and any correct sibling is broken, or if ID/answer mapping fails twice. 20–30 minutes, hard 30-minute limit. Integration medium-high because arbitrary organizer packages may not expose source-family IDs. Only viable if the existing input schema supplies reliable grouping; do not invent a fragile visual grouping system before freeze. This is lower priority despite an interesting causal test.

## 5. Separate the depicted event from the source's publication date

**Hypothesis / potential:** repeated failure on 14.1 in both models suggests anchoring on bibliographic dates rather than identifying depicted events. A task-specific chronology protocol could recover 1–2 source-analysis points; it is distinct from Greg's image-description experiment.

**Mechanism:** treatment uses one call with two explicitly separate records: (a) date/author/title of the source as an artifact and (b) date/identity of the depicted event, inferred from content. Then compare required sources. Ask the model to test whether a map could be a later historical reconstruction; never assume a publication date dates the event. All original labels remain visible. Do not hide inconvenient text, supply a correct event, or inject an item-specific answer hint.

**Fixed subset / control:** 2, 5.1, 7, 14.1, 23.2, 24. Fresh existing-policy and chronology-policy answers, **12 nominal + 6 retry = 18 calls**; output cap 4,096 = **73,728 generated tokens**; input cap 24,576. These test transfer beyond the single motivating failure, including currently correct cases.

**Stop / time / integration:** stop after 14.1 plus two correct sentinels if the motivating error remains and either sentinel breaks. 10–15 minutes, hard 15-minute limit. Integration low: prompt route selected by generic temporal-comparison task features, not validation IDs. Treat a one-item win with no transfer as weak evidence. No full visual rerun.

## Execution and promotion boundaries

- At most one new experiment per available, verified-free host. Central remains occupied by Qwen; Lukasz by essay branching; Greg by three-view images. Pawel is an obvious candidate for experiment 1 **only after root checks the live claim/process**. Przemek's unrelated work remains untouched. This report claims no host.
- Stop all experimental generation by **07:40 Warsaw**, including recovery. Start no 45-minute experiment after 06:55. Prefer finish/grade/integrate over using every GPU continuously. 07:40–08:00 is integration; 08:00–11:00 only final checks/execution/submission.
- Budgets above are upper bounds for proposals. Before dispatch freeze model/runtime/prompt/corpus hashes, exact input IDs, input and output token accounting, call envelope, absolute deadline and cost estimate in the issue. Per-call input caps imply finite total input ceilings by multiplication. Recovery is included and preserves usable candidates; failures stay in denominators. The existing final three-retry/emergency policy remains intact.
- Planning cost can be estimated from the prior Gemma run's stated ~$3.28/hour assumption: 45 minutes ~$2.46, 30 minutes ~$1.64, 15 minutes ~$0.82 **per host**, excluding already provisioned idle time. These are extrapolated planning assumptions, not verified current provider rates or billing; root must use the host's actual declared rate. No paid external inference or new weights.
- Do not sum subset improvements into a claimed full score. Grade one exact frozen pass, retain per-item gains and regressions, and test only affected compatibility plus measured runtime. A selected policy must fit the final 60-minute run with a 10-minute reserve; the 120-minute option remains configurable. Retrieval itself adds zero model weights, but any new model-based retriever would breach this proposal's scope.

## Evidence consulted

`WINNING_PLAN.md`; `AGENTS.md`; `SOURCE.md`; `2026-09-27-corrected-gemma40-grade.md`; `2026-09-27-corrected-gemma40-result.md`; `2026-09-27-native-pair-comparison.md`; `2026-09-27-eval16-unmasked-comparison.md`; `2026-09-27-champion-rehearsal-score.md`; `2026-09-26-rag-review-reconciliation.md`; Pewciu6's `2026-09-26T1747-score-gemma-rag-full.md`. Paths without owner prefixes are under `agentsLog/kwiscion/`.
