#!/usr/bin/env bash
# run-baseline.sh — reproducible CPU baseline for issue #5 (machinekind-matura)
# Machine: ljaniec-PC (x86_64, 12 cores, 19 GB RAM). No purchases.
# Creates: python3.10 venv, installs llama.cpp prebuilt wheel, downloads GGUF
# models from Hugging Face, runs 10-20 fixed DEV smoke prompts, records metrics.
set -euo pipefail

REPO=/home/ljaniec/Repositories/machinekind-matura
BASE="$REPO/agentsLog/ljaniec"
VENV="$BASE/.venv"
MODELS="$BASE/models"
RAW="$BASE/raw"
mkdir -p "$VENV" "$MODELS" "$RAW"

cd "$REPO"

# ---------- 1. environment ----------
if [ ! -x "$VENV/bin/python" ]; then
  python3.10 -m venv "$VENV"
fi
source "$VENV/bin/activate"
python -m pip install -q --upgrade pip 2>/dev/null || true
python -m pip install -q "llama-cpp-python==0.3.9" "huggingface_hub==0.26.5" "hf_transfer" 2>/dev/null

echo "== python: $(python --version 2>&1)"
python -c "import llama_cpp, sys; print('llama-cpp-python', llama_cpp.__version__)" 2>/dev/null || echo "WARN: llama_cpp not importable yet"

# ---------- 2. model download (GGUF, quantized) ----------
# Candidate A: Gemma 3 12B (google/gemma-3-12b-it-qat-q4_0-gguf) — QAT Q4_0, gated repo (needs HF token+license accept)
# Candidate B: Qwen 3 (Qwen/Qwen3-8B-GGUF, Q4_K_M) — Apache-2.0, ungated
download() {
  local repo=$1 fname=$2 out=$3
  if [ -s "$out" ]; then echo "already present: $out"; return 0; fi
  python - "$repo" "$fname" "$out" <<'PYEOF'
import sys
from huggingface_hub import hf_hub_download
repo, fname, out = sys.argv[1], sys.argv[2], sys.argv[3]
p = hf_hub_download(repo_id=repo, filename=fname, local_dir=out)
print("downloaded:", p)
PYEOF
}

MODEL_A="$MODELS/gemma3-12b-qat-q4_0/gemma-3-12b-it-q4_0.gguf"
MODEL_B="$MODELS/qwen3-8b-q4_k_m/Qwen3-8B-Q4_K_M.gguf"

download google/gemma-3-12b-it-qat-q4_0-gguf "gemma-3-12b-it-q4_0.gguf" "$MODELS/gemma3-12b-qat-q4_0" || echo "BLOCKED-A: gemma download failed (likely gated repo / no token)"
download Qwen/Qwen3-8B-GGUF "Qwen3-8B-Q4_K_M.gguf" "$MODELS/qwen3-8b-q4_k_m" || echo "BLOCKED-B: qwen download failed"

# ---------- 3. file hashes + bytes ----------
echo "== computing SHA-256 and sizes"
for f in "$MODELS"/*/*.gguf; do
  [ -f "$f" ] || continue
  B=$(stat -c%s "$f")
  S=$(sha256sum "$f" | cut -d' ' -f1)
  echo "FILE $f bytes=$B sha256=$S"
done

# ---------- 4. smoke run ----------
python "$BASE/run_smoke.py"
