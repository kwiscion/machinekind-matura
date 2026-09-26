#!/bin/bash
set -u
R=/ephemeral/mm-lora; L=$R/src/llama.cpp; B="$R/base/gemma-4-12B-it@707f0a3b"; C=$R/control; V=$R/venv-convert-pinned
export UV_CACHE_DIR=$R/uv-cache UV_PYTHON_INSTALL_DIR=$R/uv-python
echo "$(date -u +%FT%TZ) venv-convert-pinned"
echo "transformers @ file://$R/src/transformers-96331a9f.zip" > $R/convert-override.txt
( cd $L/requirements && $R/bin/uv venv --clear --python 3.12 $V && $R/bin/uv pip install --python $V/bin/python -r requirements-convert_hf_to_gguf.txt --override $R/convert-override.txt --index-strategy unsafe-best-match ) || { echo FAIL_VENV; exit 1; }
$R/bin/uv pip freeze --python $V/bin/python > $R/logs/convert_pinned_freeze.txt
P=$V/bin/python
echo "$(date -u +%FT%TZ) convert text bf16"
$P $L/convert_hf_to_gguf.py "$B" --outtype bf16 --outfile $C/base-bf16.gguf > $R/logs/convert_text2.log 2>&1; echo "text rc=$?"
echo "$(date -u +%FT%TZ) convert mmproj bf16 (pinned venv)"
$P $L/convert_hf_to_gguf.py "$B" --mmproj --outtype bf16 --outfile $C/projector-pinnedvenv.gguf > $R/logs/convert_mmproj2.log 2>&1; echo "mmproj rc=$?"
echo "$(date -u +%FT%TZ) quantize Q4_K_M"
$L/build/bin/llama-quantize $C/base-bf16.gguf $C/base-q4_k_m.gguf Q4_K_M > $R/logs/quantize2.log 2>&1; echo "quant rc=$?"
ls -la $C
echo "$(date -u +%FT%TZ) hashing"
sha256sum $C/*.gguf > $R/logs/control_sha256.txt
echo "$(date -u +%FT%TZ) EXPORT_DONE"
