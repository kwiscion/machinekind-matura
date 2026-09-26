# Bounded retrieval arm — lead launch declaration

26 September 2026, 17:02 Europe/Warsaw, before dispatch. Under the owner's standing project authorization, the lead authorizes **one sequential full-arm attempt**, at most **40 calls / 40,960 requested output tokens / $0**, no retries, warmup or resume. The crop diagnostic is terminal; this is the sole laptop inference worker. Do not launch another worker until it terminates.

The hypothesis is that independently sourced historical references improve factual answers over bare Gemma. Compare against the preserved bare source-v2 composite **35/60**; grade all 40 items / 60 points, keeping errors and unsent items in the denominator. Generic policy is excluded: independent adjudication in PR #61 gave it **32/60 [22,35]**, below bare35. Crops are excluded: the three-item diagnostic's possible gain still needs adjudication. No per-item answer selection or score-based stopping.

- Frozen private manifest: `agentsLog/kwiscion/private/bounded-rag-20260926/experiment.json`, SHA-256 `a7c5a43098693e339446383b2b8925ec8b4117c6db2adc11e61ad3b196d8c4f3`. Its preparation-status label records creation state; this separate declaration authorizes execution without changing those bytes.
- Input SHA-256 `60728768a527a14b08c81129373e3f62d55418e30bccf968555be0658f090937`; original source-v2 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`. All original prompts are exact suffixes; all IDs, image strings and other fields are unchanged.
- Pinned 107-source / 3481-chunk index; chrono, top-k3, title weight1, maximum1600 evidence characters including headers. Same budget for every case. No new corpus or held-out content. PR #60 exact head `f6c636ce66a187c00098527e906596873dd0b4db` passed independent review and tests.
- Same Gemma full digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, original config SHA-256 `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`, thinking off, 4096 context, 1024 output/request, 420-second timeout, unchanged stochastic server defaults. No fixed seed or temperature comparison claim.
- Fresh output: `agentsLog/kwiscion/private/bounded-rag-20260926/gemma-bounded-rag.raw.jsonl`, with adjacent run metadata. Preserve every attempt and immutable scoring snapshots. Publish only exact answer strings and safe provenance after quotation review.

Stop new dispatch at **17:40** or 2400 elapsed seconds, on a competing worker, failed runtime identity/context, context/OOM indicator, prompt usage over2816/missing success usage, two consecutive infrastructure failures, or the after-five-call projection exceeding17:40. An in-flight call retains420 seconds and may finish as late as17:47. Completion is not guaranteed; the lead accepts that risk before launch. Character-based input estimates are not tokenizer-fit proof, and returned usage cannot exclude silent truncation.

```powershell
wsl --exec python3 -B /mnt/c/Users/kwisc/Documents/my-projects/matura/agentsLog/kwiscion/run_bounded_gemma.py --manifest agentsLog/kwiscion/private/bounded-rag-20260926/experiment.json --execute
```

The17:00 improvement gate has slipped: policy did not improve the baseline and retrieval preparation/review finished at17:01. Target full output around17:30–17:40, grade immutable halves while it runs, then independently adjudicate before18:00 where feasible. The strongest measured bare configuration remains fallback. Offline rehearsal gets a separate two-call declaration after this worker terminates; no concurrent GPU work or May2025 access.
