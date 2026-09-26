# Aggregate submission weight budget

Organizer clarification relayed by the project owner on26September2026:

> If you have a few models for the submission (e.g. vision+text separately, a few models voting), their total size weight size needs to8GB +10%margin.

This supersedes the earlier interpretation of8GB per model. Our operational cap is **8,800,000,000bytes across the entire submitted model set**. DecimalGB is a conservative unit assumption. Count text, vision/projector, OCR, embedding/reranker, router and adapter weights if included. We count adapters conservatively rather than relying on the earlier adapter exemption. Training/development weights are unrestricted by this submission cap, but must not accidentally enter the final package. GPU memory usage and one-at-a-time loading do not establish eligibility.

| Pinned final component | Bytes |
|---|---:|
| Gemma4 12B Q4_K_M text weights |7,381,382,048|
| Matching vision projector |175,115,584|
| Current total |**7,556,497,632**|
| Remaining below8.8GB |**1,243,502,368**|

Text SHA256:`1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606`. Projector SHA256:`675ad6e68101ca9413ec806855c452362f0213f2dfc5800996b086fdb8119842`. These identify the current baseline; inspect the actual final files again before submission.

## Consequences

- **Current full40 thinking run continues:** it calls only pinned Gemma. Its reused runtime guard also checks cached Qwen integrity; that does not make Qwen part of the candidate or authorize its inclusion in the package.
- **Gemma+Qwen observer, Gemma+Bielik experts and separately merged essay/base copies are ineligible together.** Their development evidence remains useful. The observer mechanism was already parked after failed replication.
- **Same-model draft/review/voting and route-specific prompts remain viable:** repeated calls reuse one weight set. Any extra learned OCR/router/embedding model must fit within the aggregate remainder; deterministic routing and lexical retrieval add no model weights.
- **Essay LoRA has two possible paths:** prove a small adapter with one shared base, including actual runtime switching, or submit one merged model for every route and check nonessay regressions. The proposed r8 adapter is roughly10.4MB of BF16 tensors before metadata, but no deployable adapter artifact or dynamic runtime support is yet verified. Loading two full models sequentially does not solve the cap.
- **One final inventory:** list every submitted weight artifact with relative path, purpose, actual bytes and SHA256; sum all files. Reject unlisted weights and accidental base/cache/checkpoint duplicates. Do not assume hardlinks/deduplication reduce counted size. Keep development caches outside the package.

Root owns eligibility and promotion. Łukasz is assigned the final package inventory/check; each lab includes an aggregate footprint estimate in its handoff. Historical reports remain unchanged and may use the obsolete per-model interpretation.
