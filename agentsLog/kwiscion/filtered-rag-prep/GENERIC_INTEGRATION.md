# Remaining generic integration

**Keep RAG opt-in.** The measured gain is one point on a selected six-item panel, and it changes one previously correct answer to an incorrect answer. This does not justify silently replacing the current full-exam champion.

The current v2 package is an executable diagnostic, not an arbitrary final-package entry point. `prepare_v2.py` requires exactly six items, always declares no essay, fixes52 primary slots/208 attempts, and mechanically probes the first two source-order items. It otherwise already preserves original organizer IDs/text/images through synthetic stage IDs, exact final export and complete-control fallback. The shared runtime, cache guard, native schemas, semantic validation, phase barriers and offline SQLite retrieval are reusable.

The smallest final integration would:

1. Accept an arbitrary organizer package through the existing adapter and preserve its exact template/ID order. Select eligible nonessay items from an explicit checked package/type policy, never known validation IDs. The adapter has no universal essay-type field; the existing checked essay mapping or a separately frozen structural classifier must remain explicit.
2. Parameterize the same phases by eligible count N: each item contributes one direct, one query, five judges and one filtered final (8N primary slots), plus any explicitly declared qualification slots. Recompute four-attempt/token bounds and use one shared60/120-minute deadline. A real final run should not inherit today's benchmark probe IDs.
3. Merge selected final answers back into the original template, retain complete direct answers on filtered failure, and keep all item/status provenance. Essays stay on their separately qualified route; this nonessay study does not validate an essay RAG route.
4. Deploy the already pinned full SQLite index and query code locally with the single eligible model cache. Corpus data adds no model weights, but actual offline deployment/hash checks still apply.

Two quality gaps remain independently of generic plumbing: a planner can put an unsupported identification directly into its query, and a literal quote can concern a namesake or distractor article. The17.2 regression also shows that the solver may follow the article title despite a contrary quoted clue. These are observed limits, not reasons to inject benchmark-specific corrections. No new prompts, ranking changes, model calls or final-package implementation were made during this review.
