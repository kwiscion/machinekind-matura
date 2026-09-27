# Owner-authorized final RAG extension

The owner confirmed that nobody has requested final exam questions. They explicitly postponed final execution to09:20 and require the whole final-exam process to finish in under70minutes. This supersedes the earlier internal08:00 freeze, before organizer access. The previous40/60 Qwen candidate at `afd9ccd5f31b39743c114c7f12f610f15ece90a3` remains intact.

@Bukareszt @ljaniec @Pewciu6 @semberecki @przemeknowak781: do not request final questions or launch independent experiments. Root's local Sol workers own this single extension. All other tracks stay stopped; the central final cache remains untouched.

## Experiment and ownership

- `qwen_rag_extension_readiness_sol`: one fresh Qwen-only worker on `matura-pawel`, using the existing full Wikipedia index and identical six-item matched panel. Preserve full text/images and direct/final answer reasoning. Queries use thinking off/512output tokens, judges thinking off/384; bounded auxiliary retries use1024. Five independent relevance checks remain. No history-specific prompt or retrieval edits.
- `fast_rag_review_grade_sol`: independent code/cap/source review, then one frozen grading pass for the twelve final answers. Do not send key-derived hints to implementation workers.
- `deadline_rag_integration_sol`: CPU-only generic final integration. Complete and preserve the direct answer sheet first, then allow at most20minutes optional nonessay RAG inside an actual declaration of at most55minutes using the qualified60-minute profile. Ten minutes remain reserved within that declaration for recovery/export; target at most10minutes outside it for acquisition, preparation, transfer and submission, giving65minutes total plus5minutes headroom. Unfinished optional work retains exact direct answers. No external agent intervention during inference, no extra model weights.

Diagnostic envelope:52primary slots,208attempts; actual requested-output cap1,908,736tokens, with the preserved legacy7,667,712 ceiling never exceeded. One-hour/USD3.28 planning ceiling on existing resources; no purchase. Absolute inference stop09:05Warsaw, one grade/promotion decision by09:15, final freeze/start09:20. Record actual latency and failures; do not equate a narrow diagnostic gain with full-exam80%.

RAG remains off unless the Qwen comparison improves quality and the generic route passes independent source, fallback and hard-deadline checks. If either fails or misses cutoff, run the already prepared40/60 candidate with the qualified60-minute profile and the same actual55-minute ceiling. The previous120-minute final option is excluded by the owner's new limit.
