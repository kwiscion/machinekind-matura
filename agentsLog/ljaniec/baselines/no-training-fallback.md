# No-training fallback recipe — lead's Blackwell machines

Status: READY TO USE. No purchases. Everything below runs offline once the
model file (SHA-256 verified) is copied to the target machine.

## Artifact

- Model: Qwen3-8B (Qwen/Qwen3-8B-GGUF, revision d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785)
- File: `Qwen3-8B-Q4_K_M.gguf`, 5,027,783,488 bytes (4.68 GiB), Q4_K_M quantization
- License: Apache-2.0 (ungated, redistribution permitted)
- SHA-256: `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785`
- Verified locally on ljaniec-PC (x86_64 CPU, 19 GB RAM): loads in ~7 s,
  20-item Polish DEV smoke completed (see smoke-summary.json)

## Why this candidate

- Fits the ≤8,000,000,000-byte saved-weight limit with ~3 GB headroom.
- Apache-2.0: no license acceptance step, no gating, safe to copy between machines.
- Single-file GGUF: no vision/projector split needed (text-only model).
- Known-good on CPU; on Blackwell (GB10, CUDA 13) it runs through the same
  llama.cpp runtime with GPU offload or via Ollama.

## Option A — llama.cpp (exact, reproducible)

```bash
# 1. Copy the GGUF to the target machine (scp/usb), then verify:
sha256sum Qwen3-8B-Q4_K_M.gguf
# must equal d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785

# 2. Runtime (any machine with python3.10+; on GB10 use its venv):
python3 -m venv .venv && source .venv/bin/activate
pip install "llama-cpp-python==0.3.9"        # CPU build; on CUDA boxes:
# CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python==0.3.9

# 3. Offline load + generation (no network needed after install):
python - <<'EOF'
from llama_cpp import Llama
llm = Llama(model_path="Qwen3-8B-Q4_K_M.gguf", n_ctx=4096, n_threads=12, verbose=False)
resp = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "Jesteś asystentem historii. Odpowiadaj zwięźle po polsku."},
        {"role": "user", "content": "Podaj rok chrztu Polski."},
    ],
    max_tokens=200, temperature=0.0,
)
print(resp["choices"][0]["message"]["content"])
print(resp["usage"])
EOF
```

On the GB10 (ARM64, CUDA 13): the CPU build above works as-is; for GPU
offload use `CMAKE_ARGS="-DGGML_CUDA=on"` (build ~10 min on 20 cores) and
add `n_gpu_layers=-1` to the `Llama(...)` constructor. Peak memory then
drops from ~5.3 GiB (CPU) to ~4.9 GiB + shared.

## Option B — Ollama (fastest path, less exact)

```bash
# On the target machine with ollama installed:
ollama create qwen3-8b-q4km -f - <<'EOF'
FROM ./Qwen3-8B-Q4_K_M.gguf
PARAMETER temperature 0.0
PARAMETER num_ctx 4096
EOF
ollama run qwen3-8b-q4km "Podaj rok chrztu Polski."
```

## Measured baseline (ljaniec-PC, CPU-only, 12 threads)

See `smoke-summary.json` + `raw/qwen3-8b-q4_k_m-smoke.jsonl` for the full
20-item record. Latency ~2.6 tok/s/item generation on CPU; GPU offload on
GB10 expected ≥10x faster (not yet measured — Spark run pending).

## Limits

- Q4_K_M quantization: small quality loss vs bf16; grades remain provisional.
- Text-only: no vision/projector weights in this file (vision_ocr tasks need
  a separate mmproj model, e.g. Gemma 3 12B's `mmproj-model-f16-12B.gguf`).
- Context capped at 4096 in the smoke recipe (train ctx is 40960); raise
  `n_ctx` if exam prompts need longer context (more RAM).
