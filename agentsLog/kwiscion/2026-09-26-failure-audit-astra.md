# Per-case failure audit and fast experiment menu — Astra

**Recommendation: retain bare Gemma as the quality fallback, use the qualified fast runtime for controlled experiments, and split the next work into source grounding, retrieval relevance, and essay quality. Do not repeat the same global formatting prompt or count formatting as free points.** This is an evaluation analysis and proposal, not an inference/training authorization.

All 40 May 2024 cases were inspected against their exact bare answers, supplied source-v2 text, existing independent reviews and evaluation-only keys; all policy/RAG answer strings were compared. Actual page images were inspected for the visual failures or ambiguities discussed in the private matrix: ten cases, nine distinct pages. The detailed matrix and evidence hashes remain private under `agentsLog/kwiscion/private/failure-audit-astra-20260926/`. No official question, source passage or key is reproduced here. No model calls, training, production edits, Git mutations or May 2025 access occurred.

## What the existing runs establish

| Reviewed arm | Short items /45 | Essay /15 | Total /60 |
|---|---:|---:|---:|
| Bare |27|8|35|
| Generic policy |26|6|32|
| Full bounded RAG |25|2|27|
| RTX runtime transfer |26|8|34|

The bare total is the preserved v1 result; one missing image was subsequently supplied in a separate correction. A 39+1 composite is not a fresh full run. The RTX result uses source-v2 throughout and completed 40 responses in 146.6 seconds. Its image slice is 19/34, the same as the laptop; there is no demonstrated image-quality improvement from that runtime transfer. Two gains and three losses produce the one-point change. These single draws, different runtime versions and unfixed sampling do not isolate treatment effects. The review intervals also overlap substantially. [Baseline review](../Pewciu6/2026-09-26T1551-score-consolidated.md), [policy review](../Pewciu6/2026-09-26T1651-score-gemma-policy.md), [RAG review](../Pewciu6/2026-09-26T1747-score-gemma-rag-full.md), [RTX review](../Pewciu6/2026-09-26T1809-score-gemma-rtx-transfer.md).

**Excluding essays from RAG is sensible damage containment, but not a measured improvement over bare.** Reusing the existing RAG short answers plus bare essay yields a hypothetical 33, still below 35. Reusing policy short answers plus bare essay yields 34. Neither is a freshly executed routed candidate. On short items, RAG gained two points and lost four; policy gained four and lost five. Do not select routes by which validation IDs happened to improve.

| Existing task-type slice | Bare | RAG | Policy |
|---|---:|---:|---:|
| Source analysis |8|7|8|
| Short answer |14|12|14|
| Closed choices / true-false |5|6|4|

The RAG closed-answer gain is a one-draw observation, not enough to prescribe that route. Its improved true-false output still contains false supporting claims. Likewise, one repaired factual answer had irrelevant retrieved material; the answer cannot be credited to retrieval evidence.

## A more useful decomposition of the 25 missing points

These are **disjoint opportunity accounts based on observed symptoms**, not experimentally established causal contributions. Several mechanisms can affect the same answer. They deliberately do not add factual/format losses a second time to essay headroom.

| Primary opportunity | Lost points assigned | What was actually observed |
|---|---:|---|
| Visual recognition and localization |5|Invented inscriptions, objects or historical scenes; a multi-panel label mismatch.|
| Independent comparison of sources |3|A correctly understood text is projected onto a different map; a neighboring label or broad era is mistaken for evidence of identity.|
| Historical entities and relations |7|Wrong office, document, dynasty, person role or era, sometimes despite correctly recognizing the surrounding event.|
| Contradictory or ambiguous answer commitment |3|Correct content coexists with a wrong alternative or initial decision. These points are reviewer-sensitive.|
| Essay argument, knowledge and completion |7|Weak fact-to-claim links, invented terminology and uneven treatment of requested aspects.|
| **Total** |**25**|No separately additive “four free format points.”|

The three commitment losses are not reliably repairable with a parser. One answer's final block still contains an incorrect alternative; another becomes clean but wrong under the policy. A simple “take the last answer” transformation is unsafe. Pure whitespace, Markdown or JSON cleanup does not repair wrong historical knowledge. Automatic parser misses already corrected by human review are not additional model points.

Direct image inspection supports a distinction between **not seeing a detail**, **assigning a visible detail to the wrong panel/role**, and **overriding the image with a familiar historical story**. The present outputs establish severe grounding failures; they do not prove that OCR resolution alone is the bottleneck. A source-comparison failure can persist even when a large country label is legible. Higher DPI, crops, visual-token changes and evidence-first reasoning are different experiments.

The essay already has an introduction, aspects and conclusion. A better template alone is insufficient. Later arms changed the selected topic, so their decline conflates selection, factual coverage, prompting, length and retrieval. The global instruction also asks for concision, while the essay requires substantial development. A task-specific essay route should remove that conflict, not merely append another instruction to it.

## Retrieval: a concrete repairable defect, not just a vague RAG failure

The current builder uses the **entire original prompt as the retrieval query**, including generic instructions and source bibliography. Its chronological ranker extracts every matching three- or four-digit year from that query, then boosts chunks sharing those numbers without distinguishing event dates from publication dates. The year expression has no BCE representation and excludes one- and two-digit years. [Query construction](../../scripts/Bukareszt/prepare_bounded_rag.py), [ranker](../Bukareszt/scripts/retrieval.py).

In the private audit, a query about an ancient source contains a modern bibliographic year, and the injected passage concerns a modern event with that year. Several other passages match incidental words while addressing the wrong event or era. The code path and injected passages strongly support bibliography/lexical contamination as a mechanism; the exact contribution of each rank feature was not recomputed. Sampling still prevents attributing a particular answer loss solely to retrieval.

**First repair the query, then judge RAG.** Remove solver boilerplate, bibliography and answer placeholders from the retrieval query only; retain all original material in the solver input. Extract the requested relation and source-grounded entities. Treat event dates separately from publication dates. Require evidence of entity/relation relevance and compatible era; permit zero hits. Start with one compact supporting passage rather than mechanically filling top-k. A chronological compatibility check must preserve uncertainty instead of inventing a date for an unidentified event.

Before any model call, inspect whether the licensed corpus actually contains useful evidence for a diverse independent DEV set. A relevance gate cannot retrieve missing coverage. Do not add validation-derived facts or examples to repair that coverage.

## Ranked experiments, with bounded first tests

These are separate hypotheses, not one stacked configuration. Proposed limits require the lead to declare the actual worker, model, runtime, token budget and stop time before dispatch. The H100 readiness limit does not implicitly authorize these calls or training.

| Rank | Experiment | Smallest informative test | Opportunity / main risk |
|---|---|---|---|
|0|**Freeze prompt/runtime parity and sampling.** Compare the organizer adapter's actual prompt with the scored harness, including active-subtask selection, image order, chat template, thinking flag and output budget.|CPU inspection first. Freeze exact bytes and metadata. Any parity change gets its own control.|Prevents deploying an unscored prompt. A faster backend is not a quality result.|
|1|**Repair retrieval query and add a relevance gate; exclude essays initially.** Route only externally dependent factual requests, not all short answers or all images.|CPU rank audit on independent DEV; compare raw versus cleaned query and event-date handling. Only if relevance improves, up to 12 paired eligible DEV calls before a frozen full candidate.|Hypothesis 0–3 recovered recall points; not a forecast. Gate errors can discard helpful evidence or admit plausible decoys.|
|2|**Essay-specific plan → answer.** Remove conflicting concision instructions; choose a topic by factual coverage, plan every requested aspect and causal link, then draft and count words.|Use the existing bounded essay-pilot preparation. First compare matched final caps and the same selected topic; separately test automatic topic selection. At most six calls in the initial pilot.|Hypothesis 0–4 of seven essay points. More structure can conceal shallow or wrong history. Extra planning tokens must be recorded.|
|3|**Source-first evidence pass for visual comparisons.** Record visible labels/actions/location independently before matching them to historical context; retain original image in the final pass.|Three independent DEV visual strata, one-pass control versus observation+answer: at most nine calls. Keep crops/token budget unchanged initially.|Hypothesis 0–4 across visual/comparison opportunities, overlapping other rows. Observation errors can propagate; test a genuinely larger visual budget separately.|
|4|**Minimal deterministic task routes.** Closed answer → exact option/statement slots; short identification → requested entities only; comparison → decision plus required source evidence; essay → dedicated prompt.|CPU route/slot tests including neighboring-question decoys, then one frozen full run. This replaces the global instruction pile; it does not repeat the failed policy verbatim.|Primarily regression protection and fewer wrong-subtask answers. Router errors or excessive brevity can delete required justifications.|
|5|**Selective thinking versus thinking off.** Restrict a bounded reasoning phase to chronology, source comparison or logical-consistency tasks, selected from question structure.|At most six matched DEV pairs. Keep final-answer cap constant, log reasoning/latency budget and require one clean final answer. First verify the runtime actually honors the flag.|Targets comparison/commitment errors. Reasoning may elaborate false facts, consume context or recreate visible self-corrections. No evidence yet that thinking helps this model.|
|6|**Three-draw voting for closed answers.** Same frozen configuration and input; vote independently per original statement label, with a predefined deterministic tie/parse-failure fallback.|The current validation has five closed-response records worth seven points: a future full candidate needs ten extra calls for three draws on that entire route. Repeats remain development evidence.|Can reduce unstable flips now that runtime is fast; correlated confident errors survive. Do not vote across already-tested arms as if they were identical samples.|
|7|**Triggered answer-consistency pass.** Detect competing explicit decisions, missing slots or contradiction between decision and explanation; rewrite only flagged outputs with original evidence available.|Independent synthetic fixtures first, including synonyms, wrong-last-answer and self-correction cases. Freeze at most ten triggered passes in a complete candidate; log trigger rate.|Hypothesis 0–2 of three disputed commitment points, overlapping thinking/task routing. Detection is easier than knowing which claim is true.|
|8|**Essay-only LoRA as a bounded parallel research branch.** Route by long-form task structure; leave short-item base untouched.|One frozen dataset/version, one training configuration, a short feasibility check and then at most one 60-minute training job if the lead authorizes it. Stop rather than extend budget. Compare base versus adapter on independent DEV essays before using known validation for selection.|Could teach factual argument and completion; cannot be justified from one essay. Bad synthetic facts, topic memorization, adapter/quantization drift and insufficient review time are substantial risks.|

For essay LoRA, use only rights-cleared pre-2023/informator or independently sourced material allowed by `SOURCE.md`; include multiple eras, different stances and varied aspect structures. Use source-verified facts and claim-to-evidence links, not validation paraphrases or its rubric. Split by source/topic group. The existing 24 smoke records are not a demonstrated essay training set. Preserve the base, evaluate the final merged/quantized artifact actually intended for deployment, and verify the model-plus-projector size and offline runtime. Adapter execution or training success is not evidence of a score gain.

Prompt routing is the faster first intervention because task structure is explicit and it adds no training dependency. Essay-only LoRA is a reasonable **bounded parallel bet after worker readiness**, rather than a prerequisite for improving the essay. A separate specialist model fleet is unnecessary to test this idea. Do not schedule competing jobs onto the sole declared worker without the lead's queue decision.

## Selection discipline

Freeze each generic route on independent DEV evidence, then run a complete known-validation candidate with all unsent/failed cases counted. Review exact unedited answers blind where feasible. Report point gains **and losses**, factual-error counts, required-source coverage, output completion and measured whole-package latency. On uncertain cases, request adjudication rather than silently taking the generous interpretation.

The opportunity ranges overlap and are hypotheses, not additive forecasts. Perfecting the essay alone reaches at most 42 from the 35 baseline. Existing generic policy and RAG do not demonstrate progress toward 48. Repeated controls and a clean rapid experiment loop are more credible than selecting lucky answers or assuming a new prompt must help.

Private audit verification: 40 unique IDs, all expected points present, arm totals 35/27/32, disjoint missing-point allocation sums to 25; every claimed direct image inspection is enumerated. The latest RTX review is included as a separately reviewed result, not merged into the known bare score. Public memo contains aggregate findings and generic proposals only; source/key content remains private.
