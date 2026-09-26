#!/bin/bash
set -u
R=/ephemeral/mm-lora; L=$R/src/llama.cpp; B="$R/base/gemma-4-12B-it@707f0a3b"; C=$R/control; mkdir -p $C
P=$R/venv-convert/bin/python
echo "$(date -u +%FT%TZ) convert text bf16"
$P $L/convert_hf_to_gguf.py "$B" --outtype bf16 --outfile $C/base-bf16.gguf > $R/logs/convert_text.log 2>&1; echo "text rc=$?"
echo "$(date -u +%FT%TZ) convert mmproj bf16"
$P $L/convert_hf_to_gguf.py "$B" --mmproj --outtype bf16 --outfile $C/projector.gguf > $R/logs/convert_mmproj.log 2>&1; echo "mmproj rc=$?"
ls -la $C
echo "$(date -u +%FT%TZ) quantize Q4_K_M"
$L/build/bin/llama-quantize $C/base-bf16.gguf $C/base-q4_k_m.gguf Q4_K_M > $R/logs/quantize.log 2>&1; echo "quant rc=$?"
ls -la $C
echo "$(date -u +%FT%TZ) hashing"
sha256sum $C/*.gguf > $R/logs/control_sha256.txt
echo "$(date -u +%FT%TZ) EXPORT_DONE"
