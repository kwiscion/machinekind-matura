# Bounded RAG full-arm preparation — 26 September 2026, 16:59

**Prepared only; no generation or status calls by this preparation task.** The declared 40-case manifest passed native and WSL dispatcher dry preflight. Harness Sol independently reported PR #60 PASS at approximately 17:00 with no builder/pin changes required; the lead owns any launch declaration.

Private files:

- Input: `agentsLog/kwiscion/private/validation_2024_keyfree/runner_input.v2-bounded-rag.jsonl`, SHA-256 **`60728768a527a14b08c81129373e3f62d55418e30bccf968555be0658f090937`**.
- Manifest: `agentsLog/kwiscion/private/bounded-rag-20260926/experiment.json`, SHA-256 **`a7c5a43098693e339446383b2b8925ec8b4117c6db2adc11e61ad3b196d8c4f3`**.
- Preparation trace: same arm directory, `preparation-trace.json`, SHA-256 `3585d34f67eb85f0fdc3edd668ad49ad149cd0c272602aed14e4048ae99874bf`.
- Independent preservation/pin checks: `cpu-audit.json`; reproducible assertions in `freeze_manifest.py` (refuses to overwrite the frozen manifest).
- Proposed fresh raw output: same arm directory, `gemma-bounded-rag.raw.jsonl`. It does not exist yet.

The parent is bare source-v2, SHA-256 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`. Settings are pinned chrono retrieval, **top-k 3**, title weight **1.0**, whole evidence block capped at **1600 characters**, **no question policy**, original full-page images. The builder prepends the evidence block: the original prompt is a byte-identical **suffix**, not an appended retrieval suffix. All 40 IDs/order and every field except `prompt` are unchanged, including all image strings. All 43 image references across 30 image cases resolve to the same 21 original files with matching trace hashes.

The builder checked the pinned **107 sources / 3481 chunks**, index raw SHA-256 `350800b1924b8f0094171fc5d68652da0f9260d03273a51ad6421c1a03e70429`, source/retriever canonical hashes and graph content before importing the retriever. The trace pins those identities, builder, staging helper, input and output. A self-tested socket guard was active; no fetch or rebuild occurred. Independent assertions checked every query hash against its original prompt, block boundaries/length, included/truncated/skipped chunk accounting, image hashes, and the trace's builder hashes against current files.

| Character / excerpt statistic | Result |
|---|---:|
| Added evidence, min / mean / max | 1504 / 1590.3 / 1599 characters |
| Original prompt, min / mean / max | 740 / 1578.0 / 3780 characters |
| RAG prompt, min / mean / max | 2329 / 3168.3 / 5376 characters |
| Cases receiving evidence | 40/40 |
| Retrieved / included excerpts | 120 / 64 |
| Truncated / skipped excerpts | 37 / 56 |

The model/config remain pinned: Gemma digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`; original config `outputs/local-smoke/gemma4-12b-val40-1024.config.json`, SHA-256 `3d9c501891d5307a863096274abdfeec716ee8fa163b5c259569f3592ed8effa`. Thinking off, unchanged sampling defaults, context **4096**, output **1024**, per-request timeout **420 seconds**, maximum **40 calls / 40960 requested output tokens / $0**, no retries or warmup. Elapsed cap is **2400 seconds**, deadline **2026-09-26T17:40:00+02:00**.

**Fit and timing are risks, not verified outcomes.** Character counts do not establish tokenizer fit. Sensitivity calculations using 2, 3, or 4 characters per text token plus approximately 268 image/boundary tokens per full page give maximum case estimates of **2688, 1863, and 1532**, respectively, before chat-template overhead. At the denser 1.5-character scenario, some cases exceed the runtime 2816-prompt-token guard. These ratios are assumptions, not measured tokenizer behavior or bounds. Template overhead and actual tokenization remain uncounted. The dispatcher checks returned usage, context/OOM signals, resident digest/context and the after-five-call completion projection; it cannot prove silent truncation absent. A stop retains unsent IDs in the full denominator.

The 17:40 deadline prevents new dispatch; an in-flight request retains its 420-second timeout and may finish as late as roughly **17:47**. Forty 420-second requests would take 280 minutes, so maximum-call allowance is not a completion-time guarantee. At a 17:00 start the declared window permits at most about 60 seconds per case on average before overhead; RAG may be slower than the completed policy arm. Projection can stop after five, leaving most items unsent. This must be accepted explicitly before the lead spends the bounded arm.

Dry preflight actually run (there is no `--dry-preflight` option; omitting `--execute` selects it):

```powershell
wsl --exec python3 -B /mnt/c/Users/kwisc/Documents/my-projects/matura/agentsLog/kwiscion/run_bounded_gemma.py --manifest agentsLog/kwiscion/private/bounded-rag-20260926/experiment.json
```

Result: `PREPARED ONLY: 40 cases, no model/status calls; separate launch authorization required`. No launch command was executed, and no original input, image, shared core file, or Git state was changed.
