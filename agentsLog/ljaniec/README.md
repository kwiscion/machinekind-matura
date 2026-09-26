# agentsLog/ljaniec — issue #5 baseline report

Owner: @ljaniec (Łukasz). Issue: #5 "DGX Spark compact-model baseline and bounded specialist pilot".
Branch: `issue-5-ljaniec-spark`. Times: started 2026-09-26 02:08 Europe/Warsaw (00:08 UTC); this report 01:12 UTC (03:12 Warsaw).

## Claim

Claimed issue #5 with ETA: vertical slice (load/smoke/metric) within 60 min of start — this report
lands at ~64 min (60-min budget went to 20-min model download at ~3 MiB/s + 27-min CPU smoke run).
Label flip ready→in-progress pending push access (GitHub auth in progress; see Blockers).

## Artifact inventory

```
agentsLog/ljaniec/
  README.md                          <- this report
  baselines/run-baseline.sh          <- reproducible env+download+hash+smoke driver
  baselines/run_smoke.py             <- 20 fixed DEV prompts, stdlib+llama_cpp only
  baselines/no-training-fallback.md  <- REQUIRED: no-training recipe for lead's Blackwell machines
  baselines/sources.jsonl            <- source manifest (model sources, licenses, hashes)
  baselines/smoke-summary.json       <- metrics summary
  raw/qwen3-8b-q4_k_m-smoke.jsonl    <- raw append-only inference outputs (20 items)
  dispatcher-log.md, dispatcher-*.md <- 15-min repo watcher (baseline commit already pushed)
```

## Model candidate A (verified)

- Repository/revision: Qwen/Qwen3-8B-GGUF @ file revision d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785
- File: `Qwen3-8B-Q4_K_M.gguf` — 5,027,783,488 bytes (4.68 GiB) — **≤8,000,000,000 bytes: PASS (2.97 GB headroom)**
- SHA-256: `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785`
- License: Apache-2.0 (ungated, redistribution OK)
- Quantization: Q4_K_M (k-quants); tokenizer/chat template: Qwen3 (BPE, ChatML-style template embedded in GGUF)
- Vision/projector weights: none (text-only model — no bytes to include)
- LoRA adapters: none yet (0 bytes; adapter bytes excluded from the 8 GB limit per contract)

## Measurements (ljaniec-PC: x86_64, 12 cores, 19 GB RAM, CPU-only inference)

- Offline load command: `python baselines/run_smoke.py` after `bash baselines/run-baseline.sh`
  (llama-cpp-python 0.3.9; model_path=<GGUF>, n_ctx=4096, n_threads=12; no network after download)
- Load time: 7.2 s
- Smoke: 20/20 items, 0 errors, total 1594.5 s (~26.6 min)
- Latency: mean 79.7 s/item, median 74.0 s/item (~2.5 tok/s at 200 max_tokens, temperature 0.0)
- Peak memory: 8666.3 MiB ru_maxrss (includes mmap'd weights + 4096 ctx KV + runtime)
- Raw output SHA-256: 8b6d71eb4d581f4adc0b31ec25b536e546c9df8ef727bfd689f587f9abc26cac

Smoke output quality spot-check: responses are coherent Polish with visible
`<think>` reasoning traces (Qwen3 thinking mode); note "dev-smoke-001" answer
about the Northern War contains imprecise claims (auto-grade would be provisional;
thinking mode leaks into 200-token budget — disable via template flag for scoring runs).

## Model candidate B (hypothesis from issue — NOT verified, BLOCKED overnight)

- google/gemma-3-12b-it-qat-q4_0-gguf: `gated: manual` (exact API check at 00:40 UTC).
  Requires HF token + license acceptance before the file downloads; exact bytes
  unconfirmed (repo lists `gemma-3-12b-it-q4_0.gguf` + `mmproj-model-f16-12B.gguf`).
- Issue's "quantized Gemma 4 12B / Qwen 3.5 9B" hypotheses: no such public repos found
  during candidate scan; treated as unverified. Retried Gemma after token available — still
  blocked by license gate (see Blockers).

## No-training fallback for lead's Blackwell machines

READY — see `baselines/no-training-fallback.md`: Qwen3-8B Q4_K_M GGUF (Apache-2.0,
SHA-256 pinned), offline load commands for llama.cpp (CPU + CUDA build) and Ollama,
measured CPU baseline, limits. Copy file to GB10, verify hash, run offline.

## Blockers

1. **GitHub push access**: device-flow auth attempted twice; user code entry timed out
   (~15 min expiry) while the 20-min model download + 27-min smoke ran. Branch
   `issue-5-ljaniec-spark` exists locally with the watcher baseline commit; label flip
   + this report push as soon as auth completes. Retrying auth (never giving up).
2. **Gemma QAT gate**: needs HF token + manual license acceptance; issue says check
   terms and real bytes before investing — blocked until credentials exist. No purchases.
3. **DGX Spark (dell-gb10)**: reachable via `ssh -i ~/.config/NVIDIA/Sync/config/nvsync.key
   -o IdentitiesOnly=yes ljaniec@dell-gb10` (GB10, CUDA 13, 3.6T disk, 20 cores, git+gh
   installed). Not needed for the required slice (done on CPU); Spark GPU-offload latency
   measurement is next-stretch work.

## Split discipline

- DEV smoke prompts are synthetic, rights-clear, structure-only (no real exam content,
  no DEV/VALIDATION/SEALED_TEST-derived items). No keys consumed. No SEALED_TEST access.
- sources.jsonl records license + SHA-256 per model source; Gemma recorded as blocked/unknown.

## Next action

1. Push branch + flip label to in-progress once GitHub auth completes; comment on #5.
2. GPU-offload latency measurement on the GB10 Spark (stretch).
3. Stretch after baseline: 200–500 sourced TRAIN examples + generalist vs LoRA specialists
   at equal token budget (cap: 4 h total or 08:00 Sat Warsaw).
