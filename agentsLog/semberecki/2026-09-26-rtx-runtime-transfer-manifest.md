# RTX runtime-transfer control — run manifest — 2026-09-26 (owner semberecki / Piotr)

Frozen envelope: lead declaration on [issue #33 comment 15:44:13Z](https://github.com/kwiscion/machinekind-matura/issues/33#issuecomment-5847606619)
(start claim). This is a **runtime/context transfer** arm: full 40-item official
May 2024 source-v2 input on the verified RTX 5090 host — not the identical
laptop 4096 configuration and not an asserted gain.

## Run facts

- **Start UTC 15:54:18Z, end UTC 15:56:44Z — total 2 min 26.6 s for all 40 items**
  (dispatch deadline was min(2400 s, 18:40 Warsaw) = 16:34:18Z; not approached).
- **Dispatched 40/40, unsent 0, stop_reason `all_cases_dispatched`, errors 0,
  empty 0, length-stops 0 — 40/40 complete answers.**
- Latency per answer: **mean 3.66 s, median 3.51 s, max 11.84 s** (includes the
  first-call cold load inside item 1's 7.3 s). No retries, no warmup call.
- Requested output: 40 × 1024 = 40,960 tokens max; actual completion sum 6,513,
  max 717 per item. Prompt tokens max 1,979 — no context truncation
  (context-overflow guard threshold 31,744 not approached; context 32,768
  preserved throughout, no per-call overrides).

## Provenance (verified before start; source metadata separate from load evidence)

- Input: `agentsLog/semberecki/private/validation_2024_keyfree/runner_input.v2.jsonl`,
  SHA-256 `6615fea2e6fd1d6f9db5b781fa84a883899d1c2fb83a28b914638089e6b015a4`
  (exact frozen v2 hash; all 40 items, full original images, no keys). Built by
  the untouched key-free bootstrap + explicit repair-v2 from the official
  question PDF (SHA `ad66a7c4…463d21`, renderer `pdftoppm` Poppler 24.02.0,
  110 DPI, 21 pages). Raw exam artifacts stay private.
- Config: `agentsLog/kwiscion/gemma4-12b-val40-1024.config.json`
  (thinking none, 1024 output, 420 s timeout), SHA-256 `bc3c91d9…8294e3` (full
  value in the private run manifest `rtx-transfer-manifest.json`).
- Model: `gemma4:12b-it-q4_K_M`, served digest
  `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`
  (confirmed via `/api/ps` during the run); model blob
  `1278394b…895a606` (7,381,382,048 B) + projector `675ad6e6…9842`
  (175,115,584 B) = 7,556,497,632 B — verified by `sha256sum` before start;
  Ollama 0.34.4; endpoint loopback `127.0.0.1:11434/v1`, shared `infer.py`
  untouched (no-redirect, loopback-only proxy guards) with an owned wrapper
  (`agentsLog/semberecki/private/rtx_transfer_run.py`) enforcing the frozen
  cutoffs: dispatch deadline check before each dispatch, per-result flush,
  2-consecutive-infrastructure-error stop, context-overflow stop, no retry.
- Driver note (per `@ljaniec`'s correction): the previously reported "13.2" is
  **unverified — likely the CUDA API version** from serve.log, not the NVIDIA
  driver version; actual driver remains unverified.
- Paid spend: **$0** (local loopback inference only).

## Answer-only handoff (for independent scoring — `@Pewciu6`, #11)

`agentsLog/semberecki/model-answers/gemma4-12b-v2-rtx-transfer.jsonl` — 40 rows,
SHA-256 `179ccf382d2b0b87b4899240f604e0f922c1b8856273f4bedaccd9841bef600b`.
Fields per row: `id`, `answer` (final content only), `error`, `finish_reason`,
`latency_seconds`. No question packs, keys, rubrics, source passages, reasoning
channels or provider envelopes. Copied-source check before publishing: max
21-word verbatim overlap answer-vs-own-prompt; all flagged sequences are
task-instruction echoes from the prompts (e.g., "wymień dwie metody…"), no
long verbatim source-passage copies detected. Original raw results preserved
privately (`rtx-transfer-results.jsonl`).

## Limitations

- This arm is a runtime/context transfer comparison point, not a score; scoring
  is owned by `@Pewciu6` on #11. All previous attempts remain preserved.
- 54 tok/s synthetic datapoint not extrapolated; this run's measured full-arm
  throughput is 3.66 s mean per completed answer (~10× the laptop reference
  mean 37.4 s), which still does not by itself establish stage-window compliance.
- May 2025 sealed; no purchases; no RAG/policy/crops/sampling overrides.
