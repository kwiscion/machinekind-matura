# agentsLog/ljaniec — issue #5 baseline + Spark stretch report

Owner: @ljaniec (Łukasz). Issue: #5 "DGX Spark compact-model baseline and bounded specialist pilot".
Branch: `issue-5-ljaniec-spark`. Times: started 02:08 Europe/Warsaw (00:08 UTC); this report 06:00 UTC (08:00 Warsaw).

## Claim

Vertical slice (required) DELIVERED: reproducible load/smoke/metric slice committed on
`issue-5-ljaniec-spark` (local commits; push pending GitHub auth, see Blockers — device
codes expired repeatedly while long downloads ran; retried 5x per never-give-up rule).
Spark stretch (GPU measurement) also DELIVERED.

## Model candidate A (verified end-to-end, two machines)

- Repository/revision: Qwen/Qwen3-8B-GGUF @ file revision d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785
- File: `Qwen3-8B-Q4_K_M.gguf` — 5,027,783,488 bytes (4.68 GiB) — **≤8,000,000,000 bytes: PASS (2.97 GB headroom)**
- SHA-256: `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785` (identical on both machines after transfer)
- License: Apache-2.0 (ungated, redistribution OK)
- Quantization: Q4_K_M; tokenizer: Qwen3 BPE, ChatML-style template embedded in GGUF
- Vision/projector: none (text-only); LoRA adapters: none (0 bytes, excluded from 8 GB limit)

## Scorecard — same 20 fixed DEV prompts, two backends (temperature 0, max 200 tok, n_ctx 4096)

| Backend | Machine | Load | Items | Errors | Mean latency/item | Gen rate | Peak mem |
| --- | --- | --- | --- | --- | --- | --- | --- |
| llama.cpp CPU (12 threads) | ljaniec-PC (x86_64, 19 GB) | 7.2 s | 20 | 0 | 79.7 s | ~2.5 tok/s | 8666 MiB |
| ollama GPU | dell-gb10 (GB10, CUDA 13) | 17.3 s (cold) | 20 | 0 | 4.88 s | ~43 tok/s | 5.4 GB (100% GPU) |

- GPU speedup vs CPU baseline: ~16.3x on latency/item.
- Raw outputs: `raw/qwen3-8b-q4_k_m-smoke.jsonl` (CPU, sha256 8b6d71eb...), `raw/spark-smoke.jsonl` (GPU, sha256 10beafb6...)
- Spark artifacts: script `baselines/spark-smoke.py` + prompts file (identical 20 DEV prompts, JSONL).

## Repro commands

CPU: `bash baselines/run-baseline.sh && source .venv/bin/activate && python baselines/run_smoke.py`
GPU (dell-gb10): copy GGUF (verify sha256), `ollama create qwen3-8b-q4km -f Modelfile`, `python3 baselines/spark-smoke.py`
Offline after model file present: both paths need no network at inference.

## No-training fallback for lead's Blackwell machines

READY — `baselines/no-training-fallback.md`: Qwen3-8B Q4_K_M (Apache-2.0, sha-pinned),
offline llama.cpp (CPU+CUDA) and Ollama recipes, measured baselines, limits.
VALIDATED in practice: the exact file now runs on a GB10 via Option B at 100% GPU.

## Blockers

1. **GitHub push/auth**: 5 device-flow attempts; each user code expired (~15 min) while
   the 20-min HF download / 27-min CPU smoke / 60-min Spark transfer ran. Branch and all
   artifacts are committed locally on `issue-5-ljaniec-spark`; push + label flip ready→in-progress
   + issue comment happen the moment auth lands (retry continues).
2. **Gemma QAT gate**: `gated: manual` — needs HF token + license acceptance; issue's
   "Gemma 4 12B / Qwen 3.5 9B" hypotheses: no such public repos found; unverified. No purchases.

## Split discipline

DEV smoke prompts are synthetic, rights-clear, structure-only. No keys consumed,
no SEALED_TEST access, no exam-derived content. Sources manifest: `baselines/sources.jsonl`.

## Next action

Push + comment on #5 when GitHub auth completes. Optional stretch beyond this point:
200–500 sourced TRAIN examples + generalist vs LoRA specialist comparison at equal
token budget (training cap 4 h or 08:00 Sat Warsaw — already 08:00, so no new training;
report only, per contract).
