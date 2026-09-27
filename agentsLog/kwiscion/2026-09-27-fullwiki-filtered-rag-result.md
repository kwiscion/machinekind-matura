# Full-Wikipedia filtered retrieval: filter contract failed

The runtime completed, but **no retrieved passage reached any final answer**. Of30first-pass relevance judges,26produced nonconforming answers (mostly answering the original exam task),3timed out, and1returned valid negative JSON. Strict admission rejected every candidate. All six filtered finals therefore used the original bare prompt. Any paired score difference is sampling/recovery variation, not evidence for or against full-corpus RAG. No promotion.

The corpus is complete:1,587,721articles and2,729,746passages from all six pinned official20231101.pl shards. Four planners produced valid queries before retrieval; two used the declared lexical fallback. Top5passages were retrieved for every item. Query/filter recovery after evidence freeze did not retroactively alter final inputs.

The selected known-validation study completed53attempts:48primary stages plus5successful recoveries after first-attempt timeouts. All12direct/filtered answer slots have complete nonblank finals; no placeholders or complete-direct substitutions were needed. Actual source text, image bytes/order and durable request hashes matched on53/53requests. One masked12-answer packet was handed to the lead for one grading pass; this is a6-point panel per arm, not a full exam score.

Known usage:69,009prompt and129,131generated tokens; usage from5timed-out calls is unknown, not zero. Requested output reservation total1,736,704tokens, below the192attempt/7,077,888token ceiling. Native Gemma identity and65,536context were verified. The isolated single-model cache totals7,556,509,301bytes; lexical retrieval adds no model weights.

Declared03:11:45.600722UTC; guarded dispatch03:17:07.909267UTC; terminal03:45:55.481310UTC, with operator exit0 and25m50s remaining before the unchanged04:11:45.600722UTCdeadline. Execution lasted1,727.57s, an estimatedUSD1.57 at theUSD3.28/hour planning proxy; actual billing is unverified. The initial authorization-shape rejection happened before any reservation/service/model call and remains preserved. Both owned services were cleaned and the GPU was empty. Network-namespace evidence is retained privately.

Local/remote terminal archive SHA256: `906c2dc01d7b094e54c85ba19e9e2a3fb8fd26641fde4270360a43e61fbf9302`. [Machine-readable metrics](2026-09-27-fullwiki-filtered-rag-result.json) link exact unchanged answer exports. No15-word original-source overlap flags occurred. Raw requests, reasoning, question/images and full passages remain private.

The concrete next correction, if separately authorized, is an explicit auxiliary-task frame and native structured-output schema for query/judge calls, with complete original material retained as context. Do not loosen admission by searching arbitrary prose for an answer or reinterpret these bare fallbacks as successful RAG.
