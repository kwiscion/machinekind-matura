# Task routing and selective retrieval: saved-output diagnostic

26 September 2026. CPU-only inspection; no inference, downloads, keys, private answers, May 2025, or shared-code edits. This is a hypothesis report, not a candidate promotion.

## What actually exists

- `infer.py:run_case` sends one independent user message per case, using the already constructed prompt and images. No system message, conversation history, task classifier, model router, or per-type generation settings exists there.
- The winning validation bare arm uses the same `PROMPT_HEADER` from `agentsLog/Pewciu6/harness/build_validation_2024.py` for every item. It already contains conditional instructions for decision plus justification, P/F labels, and letter choices, alongside Polish, concise, source-and-own-knowledge instructions. Thus it is uniform prompt construction with model-interpreted conditional advice, not completely instruction-free answering.
- `validation-2024-keyfree/bootstrap.py` constructs header + extracted question, with image attachment based on question-only modality signals and essay recognition from printed points. Source-v2 repairs one missing image. The comparison anchor is explicitly a reused 39+1 source-v2 composite, not a fresh full bare run.
- `prepare_question_policy.py` prepends exactly the same longer English policy to all 40 original prompts. It includes conditional visual grounding, decision consistency, required counts, and essay planning/length advice. It does not dispatch different prompt strings by detected type. The independent policy result is 32/60 versus bare 35/60; it does not establish that every individual instruction is harmful.
- `scripts/Bukareszt/matura_package.py:build_prompt` is the organizer adapter, a distinct prompt construction from the measured validation bare arm. It includes exam instructions, question, supplied source text, unknown metadata, image descriptors, and explicit answer format, under a common header/footer. It preserves each source string. Its synthetic qualification is not evidence that this changed prompt reproduces 35/60.
- No file named `policy.py` was found in this checkout; the implemented policy files are the preparation/dispatch helpers above.

Repeated source context means the PDF parser copies a group's shared preamble and source-page references into each related subtask. Each stateless request needs its own source context. Whole-page images can additionally show neighboring tasks. This is not persistent memory, and stripping repeated context across requests would remove required evidence. The generic policy tells the model to solve only the requested subtask. A future group-aware cache can save computation only if the serving stack supports it; it cannot simply omit source bytes.

## Arithmetic from public independent review

Source: `agentsLog/Pewciu6/results/review_gemma-bounded-rag-val40.json`, fields `reviewed_points`, `bare_composite_points`, `max_points`, `task_type`, and uncertainty bounds. All 40 IDs are unique; their maxima sum to 60. Its matched bare composite sums to 35, RAG to 27. No answer text or grading rationale was used to choose individual routes.

| Existing evaluation bucket | Items | Max | Bare composite | RAG | RAG only in this bucket, bare elsewhere |
| --- | ---: | ---: | ---: | ---: | ---: |
| Essay | 1 | 15 | 8 | 2 | 29/60 |
| Multiple choice (includes P/F) | 5 | 7 | 5 | 6 | 36/60 |
| Short answer | 20 | 24 | 14 | 12 | 33/60 |
| Source analysis | 14 | 14 | 8 | 7 | 34/60 |

- RAG for all non-essay items plus bare essay: **25/45 + 8/15 = 33/60**, descriptive uncertainty sum 27–38, below bare 35.
- RAG for multiple-choice and short-answer buckets, bare for essay and source-analysis buckets: **34/60**.
- RAG for multiple-choice only: **36/60**, a one-point post-hoc signal, not a measured deployed router or robust gain.

**Critical category limitation:** these public `task_type` labels originate in evaluator `build_rubric`, which derives categories from marking-rule/solution structure. They are not an independently frozen question-only router. In particular, `source_analysis` means the evaluator's decision-plus-justification class; it does **not** mean every question requiring supplied sources. `short_answer` and `multiple_choice` can require sources too. These aggregates are descriptive only. They cannot establish the score of “exclude all supplied-source tasks,” and these evaluator labels must not become inference inputs. Establish a new question-only classifier before any prospective routing experiment.

This selection follows seeing the same validation outcomes; one stochastic draw per arm, unfixed server defaults, small categories, a single essay, and grading uncertainty prevent causal attribution. The uncertainty sums are not confidence intervals. Never promote the category maximum or call it a new full score.

## Small practical routes to test

Use two independent axes: **required answer form** (choice/PF, short response, decision with justification, essay) and **required evidence** (supplied material, external historical knowledge, mixed). General knowledge and facts are not opposite classes. The useful distinction is where the evidence needed for the answer must come from.

1. Parse explicit question instructions and organizer `answer_format` to choose only a minimal output-format suffix; ambiguous cases retain the bare prompt. Do not use evaluator metadata, answers, or keys.
2. Essay route: no automatic generic chrono prefix; use a separately tested outline/coverage-and-length instruction. Keep all topic requirements.
3. Supplied-source route: retain all relevant text/images and ask for source-grounded justification. A source-dependent question can still require external knowledge; absence of a source is not the only valid RAG gate.
4. External-reference route: retrieval only after a question-only evidence-need decision and a frozen relevance gate; an empty/weak match falls back to bare. Mixed cases must distinguish supplied evidence from retrieved background rather than letting retrieval override a visible source.

## Orthogonal experiments and regression sets

Each is a separate declared arm; do not stack them before measuring its contribution. Prefer licensed pre-2023 development items or question-only synthetic fixtures for implementation checks; they never establish exam accuracy. Freeze routes before a complete independent May-2024 rerun. May 2025 remains sealed.

| Hypothesis | Minimal change | Required regression set |
| --- | --- | --- |
| Format selection is better than a long universal policy | One small suffix selected from explicit requested output form | Choice/PF, multi-part short answers, decision+justification, essays; ambiguous forms retain bare |
| Irrelevant retrieval is the main failure | Frozen relevance/abstention gate with no-retrieval fallback | External-fact, source-only and mixed questions, plus deliberately irrelevant retrieval distractors |
| Raw question/source text pollutes retrieval queries | Construct a compact entity/time/place query from the task demand, preserving source input unchanged | Repeated-source groups, ambiguous entities, dates with similar names, map-based tasks |
| Source grounding fails before historical reasoning | Separate visible-evidence extraction from final response; second pass may use only extracted facts plus original source | Visual and textual sources, contradictions, unreadable features, and matched text-only controls; account for doubled latency |
| Essay generation misses constraints | One-pass coverage checklist/outline instruction, with enough measured output budget | Multiple independently sourced development essay topics and the full validation essay; also check total-exam latency and truncation |
| Extraneous details lose otherwise earned points | Final-answer contradiction/unsupported-detail check without introducing new facts | Correct concise baseline answers as essential non-regression controls, plus decision/justification conflicts and multi-answer tasks |
| Full-page context distracts from the requested subtask | Clear task-boundary marking while preserving all supplied sources and original images | All repeated-source groups, adjacent unrelated questions and required cross-page sources; compare to the unchanged full-page arm |
| Runtime sampling dominates apparent prompt deltas | Explicit fixed sampling candidate before interpreting small category changes | Complete matched source-v2 suite; repeat a predeclared diverse subset to measure stability, with paid/call bounds separately approved |

Recommendation: retain bare as fallback. Selective retrieval is a reasonable research hypothesis, but excluding essays alone produces 33 on the saved outputs, and the available buckets cannot yet answer the stronger source-exclusion proposal. First establish question-only routing and relevance criteria, then test prospectively rather than selecting winning saved answers.

## Follow-up: actual query contamination diagnostic

Read-only CPU ranking reproduced five original queries across three requested source groups on the verified pinned index `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429`. All five query hashes and original top-three chunk IDs match the saved RAG preparation trace. Network was disabled with the existing self-tested socket guard. No inference or key/answer inspection occurred.

Confirmed mechanism: chrono mode extracts every regex-matching year from the complete prompt and boosts matching graph chunks by `0.15 * maximum_BM25_score` per year/entity hit. It does not distinguish event dates from publication dates or page numbers. The graph retains years 476–2026; the regex also misses ordinary two-digit ancient dates and does not encode BCE signs. Query extraction uses the entire original prompt, including the generic answering header and bibliographies.

For this diagnostic only, compare original, header removed, and header plus complete bibliography lines removed. A conservative line detector required a publication city followed by a year and page marker. This changes the query only; no question/source input, corpus, or production retriever was modified. No correct answer entity was inserted.

| Group | Numbers erroneously available as query years | Actual year-boost exposure | Ranking result after header + bibliography removal |
| --- | --- | --- | --- |
| z3.1 / z3.2 | Publication year 1990 | 41 graph chunks | Original top result on Katyn disappears; Roman reference chunks enter the top three, but absolute monarchy remains first. Not a complete relevance fix. |
| z17.1 / z17.2 | Publication year 1998 | 8 graph chunks | Medieval results still lead. Header removal alone brings German-unification material into third place for z17.2; removing the bibliography as well loses it again. |
| z15.1 | Publication years 1971, 2001; page numbers 180, 233 | 6 and 17 graph chunks; page numbers have zero graph matches | Original Kosciuszko-led list becomes a January-1863-manifest-led list; unrelated uprising/confederation material remains. |

In all five cases, the extracted numeric years come from bibliographic material rather than explicit task event dates. Removing those lines leaves no regex-recognized year. This does not mean no historical period is present: text can express centuries, implied periods, or dates outside the regex. Removing whole bibliography lines also removes potentially useful titles and lexical terms, so this is not an isolated year-boost ablation and is not a safe production rule. The z17.2 result demonstrates that indiscriminate cleanup can lose a relevant hit.

Confirmed: metadata affects ranking, publication years enter boosts, and simple query cleanup changes retrieved passages. Unproven: which change would improve generated answers or scores, and whether these passages caused a specific model mistake. A better next CPU experiment separates header removal, publication-year masking only, bibliography-field separation, and disabling chrono boost, then assesses query-only relevance across a frozen diverse set. Preserve source text for answering. Private reproducibility artifacts: `agentsLog/kwiscion/private/routing-query-diagnostic.py` and `.json`.
