#!/bin/bash
# Unmodified-base export control (pinned llama.cpp fcb3074f). FAIL-CLOSED since the
# #117 review (2026-09-26 23:10 CEST): the historical run used `set -u` only and
# echoed return codes while continuing. Its artifacts were verified separately by
# hash (host_logs/control_sha256.txt). Any future export must use this version with a
# FRESH output directory, and must then check the expected hashes and the complete
# aggregate inventory with prepare.py size.
# usage: export_control2.sh BASE_DIR FRESH_OUT_DIR
set -euo pipefail
R=/ephemeral/mm-lora; L=$R/src/llama.cpp; V=$R/venv-convert-pinned
B=${1:?base dir}; C=${2:?fresh output dir}
test ! -e "$C" || { echo "refusing existing output dir $C" >&2; exit 2; }
test -x "$V/bin/python" -a -x "$L/build/bin/llama-quantize" || { echo "missing pinned converter env" >&2; exit 2; }
mkdir -p "$C"
P=$V/bin/python
echo "$(date -u +%FT%TZ) convert text bf16"
"$P" "$L/convert_hf_to_gguf.py" "$B" --outtype bf16 --outfile "$C/base-bf16.gguf" > "$C/convert_text.log" 2>&1
echo "$(date -u +%FT%TZ) convert mmproj bf16"
"$P" "$L/convert_hf_to_gguf.py" "$B" --mmproj --outtype bf16 --outfile "$C/projector.gguf" > "$C/convert_mmproj.log" 2>&1
test -s "$C/base-bf16.gguf" -a -s "$C/projector.gguf"
echo "$(date -u +%FT%TZ) quantize Q4_K_M"
"$L/build/bin/llama-quantize" "$C/base-bf16.gguf" "$C/base-q4_k_m.gguf" Q4_K_M > "$C/quantize.log" 2>&1
test -s "$C/base-q4_k_m.gguf"
sha256sum "$C"/*.gguf > "$C/sha256.txt"
echo "$(date -u +%FT%TZ) EXPORT_DONE"
